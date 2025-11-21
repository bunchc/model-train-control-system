"""Integration tests for central_api.

Tests real interactions between components without mocking internal calls.
"""

from pathlib import Path

import pytest

from app.services.config_loader import ConfigLoader
from app.services.config_manager import ConfigManager, ConfigurationError
from app.services.config_repository import ConfigRepository


@pytest.mark.integration()
class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_config_manager_full_lifecycle(
        self, sample_yaml_file: Path, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test complete configuration lifecycle from YAML to database."""
        # Initialize config manager with real components
        manager = ConfigManager(
            yaml_path=sample_yaml_file, db_path=temp_db_path, schema_path=temp_schema_path
        )

        # Verify plugins loaded
        plugins = manager.get_plugins()
        assert len(plugins) > 0

        # Verify edge controllers loaded
        controllers = manager.get_edge_controllers()
        assert len(controllers) > 0

        # Verify full config retrieval
        full_config = manager.get_full_config()
        assert len(full_config.plugins) > 0
        assert len(full_config.edge_controllers) > 0

    def test_config_loader_and_repository_integration(
        self, sample_yaml_file: Path, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test ConfigLoader and ConfigRepository working together."""
        # Load configuration
        loader = ConfigLoader(sample_yaml_file)
        config = loader.load_config()
        loader.validate_config_structure(config)

        # Store in repository
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        # Verify we can query empty database
        plugins = repo.get_all_plugins()
        assert plugins == []

        # Add data
        repo.insert_plugin("test-plugin", "Test", {"enabled": True})

        # Verify insertion
        plugins = repo.get_all_plugins()
        assert len(plugins) == 1

    def test_add_edge_controller_persistence(
        self, sample_yaml_file: Path, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that added edge controllers persist in database."""
        manager = ConfigManager(
            yaml_path=sample_yaml_file, db_path=temp_db_path, schema_path=temp_schema_path
        )

        # Add a new controller
        new_uuid = manager.add_edge_controller("new-ctrl", "192.168.1.200")

        # Create new manager instance to verify persistence
        manager2 = ConfigManager(
            yaml_path=sample_yaml_file, db_path=temp_db_path, schema_path=temp_schema_path
        )

        # Verify controller exists
        controllers = manager2.get_edge_controllers()
        controller_ids = [c.id for c in controllers]
        assert new_uuid in controller_ids

    def test_config_validation_rejects_invalid_yaml(
        self, temp_yaml_path: Path, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that invalid YAML is rejected during initialization."""
        # Create invalid YAML (missing required fields)
        with temp_yaml_path.open("w") as yaml_file:
            yaml_file.write("plugins: []\n")  # Missing edge_controllers

        with pytest.raises(ConfigurationError, match="missing required keys"):
            ConfigManager(
                yaml_path=temp_yaml_path, db_path=temp_db_path, schema_path=temp_schema_path
            )


@pytest.mark.integration()
class TestDatabaseConsistency:
    """Integration tests for database consistency."""

    def test_update_train_status_and_retrieval(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test updating and retrieving train status."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        # Update status
        repo.update_train_status(
            "train-1", speed=50, voltage=12.0, current=1.5, position="section_A"
        )

        # Retrieve status
        status = repo.get_train_status("train-1")
        assert status is not None
        assert status["speed"] == 50
        assert status["voltage"] == 12.0

        # Update again
        repo.update_train_status(
            "train-1", speed=75, voltage=12.5, current=2.0, position="section_B"
        )

        # Verify update
        status = repo.get_train_status("train-1")
        assert status["speed"] == 75
        assert status["position"] == "section_B"

    def test_edge_controller_update_consistency(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that edge controller updates are consistent."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        # Add controller
        controller_id = "550e8400-e29b-41d4-a716-446655440000"
        repo.add_edge_controller(controller_id, "test-ctrl", "192.168.1.100")

        # Update name
        repo.update_edge_controller(controller_id, name="updated-ctrl")

        # Verify
        controller = repo.get_edge_controller(controller_id)
        assert controller is not None
        assert controller["name"] == "updated-ctrl"
        assert controller["address"] == "192.168.1.100"  # Unchanged

        # Update address
        repo.update_edge_controller(controller_id, address="192.168.1.200")

        # Verify
        controller = repo.get_edge_controller(controller_id)
        assert controller["address"] == "192.168.1.200"
        assert controller["name"] == "updated-ctrl"  # Still updated
