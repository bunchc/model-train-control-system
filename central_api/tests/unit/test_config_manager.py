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
