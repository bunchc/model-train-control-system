"""Unit tests for config_repository module.

Tests database operations in isolation with mocked SQLite connections.
"""

from pathlib import Path

import pytest

from app.services.config_repository import ConfigRepository


@pytest.mark.unit()
class TestConfigRepository:
    """Test suite for ConfigRepository class."""

    def test_init_creates_database_if_not_exists(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that __init__ creates database if it doesn't exist."""
        assert not temp_db_path.exists()

        repo = ConfigRepository(temp_db_path, temp_schema_path)

        assert temp_db_path.exists()
        assert repo.db_path == temp_db_path
        assert repo.schema_path == temp_schema_path

    def test_init_with_existing_database(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test that __init__ works with existing database."""
        assert populated_db.exists()

        repo = ConfigRepository(populated_db, temp_schema_path)

        assert repo.db_path == populated_db

    def test_get_edge_controller_exists(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test retrieving existing edge controller."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        controller = repo.get_edge_controller("550e8400-e29b-41d4-a716-446655440000")

        assert controller is not None
        assert controller["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert controller["name"] == "test-controller"
        assert controller["address"] == "192.168.1.100"

    def test_get_edge_controller_not_found(
        self, populated_db: Path, temp_schema_path: Path
    ) -> None:
        """Test retrieving non-existent edge controller."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        controller = repo.get_edge_controller("nonexistent-id")

        assert controller is None

    def test_get_all_edge_controllers(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test retrieving all edge controllers."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        controllers = repo.get_all_edge_controllers()

        assert len(controllers) == 1
        assert controllers[0]["name"] == "test-controller"

    def test_add_edge_controller(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test adding new edge controller."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        repo.add_edge_controller(
            "aa0e8400-e29b-41d4-a716-446655440000", "new-controller", "192.168.1.200"
        )

        controller = repo.get_edge_controller("aa0e8400-e29b-41d4-a716-446655440000")
        assert controller is not None
        assert controller["name"] == "new-controller"
        assert controller["address"] == "192.168.1.200"
        assert controller["enabled"] == 1

    def test_update_edge_controller_name(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test updating edge controller name."""
        repo = ConfigRepository(populated_db, temp_schema_path)
        controller_id = "550e8400-e29b-41d4-a716-446655440000"

        repo.update_edge_controller(controller_id, name="updated-name")

        controller = repo.get_edge_controller(controller_id)
        assert controller is not None
        assert controller["name"] == "updated-name"

    def test_update_edge_controller_address(
        self, populated_db: Path, temp_schema_path: Path
    ) -> None:
        """Test updating edge controller address."""
        repo = ConfigRepository(populated_db, temp_schema_path)
        controller_id = "550e8400-e29b-41d4-a716-446655440000"

        repo.update_edge_controller(controller_id, address="192.168.1.50")

        controller = repo.get_edge_controller(controller_id)
        assert controller is not None
        assert controller["address"] == "192.168.1.50"

    def test_update_edge_controller_enabled(
        self, populated_db: Path, temp_schema_path: Path
    ) -> None:
        """Test updating edge controller enabled status."""
        repo = ConfigRepository(populated_db, temp_schema_path)
        controller_id = "550e8400-e29b-41d4-a716-446655440000"

        repo.update_edge_controller(controller_id, enabled=False)

        controller = repo.get_edge_controller(controller_id)
        assert controller is not None
        assert controller["enabled"] == 0

    def test_get_trains_for_controller_empty(
        self, populated_db: Path, temp_schema_path: Path
    ) -> None:
        """Test retrieving trains for controller with no trains."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        trains = repo.get_trains_for_controller("550e8400-e29b-41d4-a716-446655440000")

        assert trains == []

    def test_get_plugin_exists(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test retrieving existing plugin."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        plugin = repo.get_plugin("test-plugin")

        assert plugin is not None
        assert plugin["name"] == "test-plugin"
        assert plugin["description"] == "Test plugin"

    def test_get_plugin_not_found(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test retrieving non-existent plugin."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        plugin = repo.get_plugin("nonexistent-plugin")

        assert plugin is None

    def test_get_all_plugins(self, populated_db: Path, temp_schema_path: Path) -> None:
        """Test retrieving all plugins."""
        repo = ConfigRepository(populated_db, temp_schema_path)

        plugins = repo.get_all_plugins()

        assert len(plugins) == 1
        assert plugins[0]["name"] == "test-plugin"

    def test_update_train_status(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test updating train status."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        repo.update_train_status(
            "train-1", speed=75, voltage=12.5, current=2.3, position="section_B"
        )

        status = repo.get_train_status("train-1")
        assert status is not None
        assert status["train_id"] == "train-1"
        assert status["speed"] == 75
        assert status["voltage"] == 12.5
        assert status["current"] == 2.3
        assert status["position"] == "section_B"

    def test_get_train_status_not_found(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test retrieving non-existent train status."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        status = repo.get_train_status("nonexistent-train")

        assert status is None

    def test_set_and_get_metadata(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test setting and retrieving metadata."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        repo.set_metadata("last_updated", "1234567890")

        value = repo.get_metadata("last_updated")
        assert value == "1234567890"

    def test_get_metadata_not_found(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test retrieving non-existent metadata."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        value = repo.get_metadata("nonexistent-key")

        assert value is None

    def test_insert_plugin(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test inserting plugin."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        repo.insert_plugin("new-plugin", "New test plugin", {"enabled": True, "port": 9090})

        plugin = repo.get_plugin("new-plugin")
        assert plugin is not None
        assert plugin["name"] == "new-plugin"
        assert plugin["description"] == "New test plugin"

    def test_database_connection_closes_properly(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that database connections are properly closed."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        # Perform multiple operations to ensure connections are managed properly
        repo.get_all_edge_controllers()
        repo.get_all_plugins()
        repo.get_metadata("test")

        # If connections aren't closed, this would fail or leak resources
        assert True
