"""Unit tests for config_manager module.

Tests orchestration logic with mocked repository and loader.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.schemas import EdgeController, FullConfig, Plugin
from app.services.config_loader import ConfigLoader, ConfigLoadError
from app.services.config_manager import UUID_PATTERN, ConfigManager, ConfigurationError
from app.services.config_repository import ConfigRepository


@pytest.mark.unit()
class TestConfigManager:
    """Test suite for ConfigManager class."""

    @patch.object(ConfigLoader, "__init__", return_value=None)
    @patch.object(ConfigRepository, "__init__", return_value=None)
    def test_init_success(self, _mock_repo_init: Mock, _mock_loader_init: Mock) -> None:
        """Test successful initialization of ConfigManager."""
        yaml_path = Path("config.yaml")
        db_path = Path("test.db")

        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager(yaml_path=yaml_path, db_path=db_path)

        assert manager.yaml_path == yaml_path
        assert manager.db_path == db_path

    @patch.object(ConfigLoader, "__init__", side_effect=ConfigLoadError("Test error"))
    @patch.object(ConfigRepository, "__init__", return_value=None)
    def test_init_loader_error(self, _mock_repo_init: Mock, _mock_loader_init: Mock) -> None:
        """Test initialization failure when loader fails."""
        with pytest.raises(ConfigurationError, match="Failed to initialize"):
            ConfigManager(yaml_path=Path("config.yaml"))

    def test_ensure_valid_uuid_valid(self) -> None:
        """Test _ensure_valid_uuid with valid UUID."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = manager._ensure_valid_uuid(valid_uuid, "test")

        assert result == valid_uuid.lower()

    def test_ensure_valid_uuid_uppercase(self) -> None:
        """Test _ensure_valid_uuid normalizes uppercase to lowercase."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        uppercase_uuid = "550E8400-E29B-41D4-A716-446655440000"
        result = manager._ensure_valid_uuid(uppercase_uuid, "test")

        assert result == uppercase_uuid.lower()

    def test_ensure_valid_uuid_invalid_format(self) -> None:
        """Test _ensure_valid_uuid with invalid UUID format."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="invalid UUID format"):
            manager._ensure_valid_uuid("not-a-uuid", "test-name")

    def test_ensure_valid_uuid_non_string(self) -> None:
        """Test _ensure_valid_uuid with non-string input."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="non-string ID"):
            manager._ensure_valid_uuid(12345, "test-name")  # type: ignore[arg-type]

    @patch.object(ConfigRepository, "add_edge_controller")
    def test_add_edge_controller_success(self, mock_add: Mock) -> None:
        """Test successful edge controller registration."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()
            manager.repository = MagicMock()
            manager.repository.add_edge_controller = mock_add

        controller_uuid = manager.add_edge_controller("test-ctrl", "192.168.1.100")

        assert UUID_PATTERN.match(controller_uuid)
        mock_add.assert_called_once()

    @patch.object(ConfigRepository, "add_edge_controller", side_effect=Exception("DB error"))
    def test_add_edge_controller_db_error(self, mock_add: Mock) -> None:
        """Test edge controller registration failure."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()
            manager.repository = MagicMock()
            manager.repository.add_edge_controller = mock_add

        with pytest.raises(ConfigurationError, match="Failed to register controller"):
            manager.add_edge_controller("test-ctrl", "192.168.1.100")

    def test_get_full_config(self) -> None:
        """Test retrieving full configuration."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        # Mock repository methods
        manager.repository = MagicMock()
        manager.repository.get_all_plugins.return_value = [
            {"name": "plugin1", "description": "Test plugin", "config": "{}"}
        ]
        manager.repository.get_all_edge_controllers.return_value = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "controller1",
                "description": "Test controller",
                "address": "192.168.1.100",
                "enabled": 1,
            }
        ]
        manager.repository.get_trains_for_controller.return_value = []

        config = manager.get_full_config()

        assert isinstance(config, FullConfig)
        assert len(config.plugins) == 1
        assert len(config.edge_controllers) == 1
        assert config.plugins[0].name == "plugin1"
        assert config.edge_controllers[0].name == "controller1"

    def test_get_plugins(self) -> None:
        """Test retrieving plugins."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_all_plugins.return_value = [
            {"name": "plugin1", "description": "Test", "config": "{}"},
            {"name": "plugin2", "description": "Test 2", "config": "{}"},
        ]

        plugins = manager.get_plugins()

        assert len(plugins) == 2
        assert all(isinstance(p, Plugin) for p in plugins)
        assert plugins[0].name == "plugin1"

    def test_get_edge_controllers(self) -> None:
        """Test retrieving edge controllers."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_all_edge_controllers.return_value = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "ctrl1",
                "description": "Test",
                "address": "192.168.1.100",
                "enabled": 1,
            }
        ]
        manager.repository.get_trains_for_controller.return_value = []

        controllers = manager.get_edge_controllers()

        assert len(controllers) == 1
        assert isinstance(controllers[0], EdgeController)
        assert controllers[0].name == "ctrl1"

    def test_uuid_pattern_constant(self) -> None:
        """Test that UUID_PATTERN constant is properly defined."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        invalid_uuid = "not-a-uuid"

        assert UUID_PATTERN.match(valid_uuid)
        assert not UUID_PATTERN.match(invalid_uuid)

    def test_update_train_name_only(self) -> None:
        """Test updating only the train name."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()

        # Mock existing train check and updated train fetch
        manager.repository.get_train.side_effect = [
            # First call: check train exists
            {
                "id": "train-123",
                "name": "Old Name",
                "description": "Test Desc",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
            # Second call: fetch updated train
            {
                "id": "train-123",
                "name": "New Name",
                "description": "Test Desc",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
        ]
        manager.repository.update_train.return_value = True

        # Execute
        result = manager.update_train("train-123", name="New Name")

        # Verify
        assert result.name == "New Name"
        assert result.description == "Test Desc"
        assert result.invert_directions is False
        manager.repository.update_train.assert_called_once_with(
            train_id="train-123",
            name="New Name",
            description=None,
            invert_directions=None,
        )

    def test_update_train_description_only(self) -> None:
        """Test updating only the train description."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.side_effect = [
            {
                "id": "train-456",
                "name": "Express",
                "description": "Old description",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
            {
                "id": "train-456",
                "name": "Express",
                "description": "New description",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
        ]
        manager.repository.update_train.return_value = True

        result = manager.update_train("train-456", description="New description")

        assert result.description == "New description"
        assert result.name == "Express"
        manager.repository.update_train.assert_called_once_with(
            train_id="train-456",
            name=None,
            description="New description",
            invert_directions=None,
        )

    def test_update_train_invert_directions_only(self) -> None:
        """Test updating only the invert_directions flag."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.side_effect = [
            {
                "id": "train-789",
                "name": "Freight",
                "description": "Heavy cargo",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
            {
                "id": "train-789",
                "name": "Freight",
                "description": "Heavy cargo",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 1,
            },
        ]
        manager.repository.update_train.return_value = True

        result = manager.update_train("train-789", invert_directions=True)

        assert result.invert_directions is True
        assert result.name == "Freight"
        manager.repository.update_train.assert_called_once_with(
            train_id="train-789",
            name=None,
            description=None,
            invert_directions=True,
        )

    def test_update_train_multiple_fields(self) -> None:
        """Test updating name, description, and invert_directions together."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.side_effect = [
            {
                "id": "train-abc",
                "name": "Old Name",
                "description": "Old Desc",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
            {
                "id": "train-abc",
                "name": "New Name",
                "description": "New Desc",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 1,
            },
        ]
        manager.repository.update_train.return_value = True

        result = manager.update_train(
            "train-abc",
            name="New Name",
            description="New Desc",
            invert_directions=True,
        )

        assert result.name == "New Name"
        assert result.description == "New Desc"
        assert result.invert_directions is True
        manager.repository.update_train.assert_called_once_with(
            train_id="train-abc",
            name="New Name",
            description="New Desc",
            invert_directions=True,
        )

    def test_update_train_not_found(self) -> None:
        """Test updating non-existent train raises ValueError."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.return_value = None  # Train doesn't exist

        with pytest.raises(ValueError, match="Train train-999 not found"):
            manager.update_train("train-999", name="New Name")

    def test_update_train_repository_fails(self) -> None:
        """Test update failure in repository layer."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.return_value = {
            "id": "train-123",
            "name": "Test",
            "plugin_name": "dc_motor",
            "plugin_config": "{}",
        }
        manager.repository.update_train.return_value = False  # Update failed

        with pytest.raises(RuntimeError, match="Failed to update train"):
            manager.update_train("train-123", name="New Name")

    def test_update_train_disappears_after_update(self) -> None:
        """Test edge case where train is deleted during update."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        manager.repository.get_train.side_effect = [
            {"id": "train-123", "name": "Test", "plugin_name": "dc_motor", "plugin_config": "{}"},
            None,  # Gone after update
        ]
        manager.repository.update_train.return_value = True

        with pytest.raises(RuntimeError, match="disappeared after update"):
            manager.update_train("train-123", name="New Name")

    def test_update_train_bool_conversion(self) -> None:
        """Test that SQLite integer is converted back to bool."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()

        # Test with invert_directions = 1 (True)
        manager.repository.get_train.side_effect = [
            {
                "id": "train-bool",
                "name": "Test",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 0,
            },
            {
                "id": "train-bool",
                "name": "Test",
                "plugin_name": "dc_motor",
                "plugin_config": "{}",
                "invert_directions": 1,
            },
        ]
        manager.repository.update_train.return_value = True

        result = manager.update_train("train-bool", invert_directions=True)
        assert result.invert_directions is True
        assert isinstance(result.invert_directions, bool)

    def test_update_train_plugin_config_parsing(self) -> None:
        """Test that plugin_config JSON is properly parsed."""
        with patch.object(ConfigManager, "_initialize_configuration"):
            manager = ConfigManager()

        manager.repository = MagicMock()
        plugin_config_json = '{"motor_type": "DC", "max_voltage": 12}'

        manager.repository.get_train.side_effect = [
            {
                "id": "train-plugin",
                "name": "Test",
                "plugin_name": "dc_motor",
                "plugin_config": plugin_config_json,
                "invert_directions": 0,
            },
            {
                "id": "train-plugin",
                "name": "Updated Test",
                "plugin_name": "dc_motor",
                "plugin_config": plugin_config_json,
                "invert_directions": 0,
            },
        ]
        manager.repository.update_train.return_value = True

        result = manager.update_train("train-plugin", name="Updated Test")

        assert result.plugin.name == "dc_motor"
        assert result.plugin.config["motor_type"] == "DC"
        assert result.plugin.config["max_voltage"] == 12
