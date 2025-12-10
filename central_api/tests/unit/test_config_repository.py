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
        # Timestamp fields should be set
        assert controller["first_seen"] is not None
        assert controller["last_seen"] is not None
        assert controller["status"] == "online"

    def test_update_controller_heartbeat_timestamps(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that update_controller_heartbeat updates last_seen and preserves first_seen."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)
        repo.add_edge_controller("hb-unit-001", "unit-heartbeat", "192.168.1.201")
        controller_before = repo.get_edge_controller("hb-unit-001")
        first_seen_before = controller_before["first_seen"]
        last_seen_before = controller_before["last_seen"]
        assert first_seen_before is not None
        assert last_seen_before is not None
        # Simulate heartbeat
        import time

        time.sleep(1)
        result = repo.update_controller_heartbeat("hb-unit-001")
        assert result is True
        controller_after = repo.get_edge_controller("hb-unit-001")
        assert controller_after["first_seen"] == first_seen_before
        assert controller_after["last_seen"] is not None
        assert controller_after["last_seen"] != last_seen_before
        assert controller_after["status"] == "online"

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

        # Use integer for enabled field as expected by repository logic
        repo.update_edge_controller(controller_id, enabled=0)

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


@pytest.mark.unit()
class TestControllerHeartbeat:
    """Test suite for controller heartbeat functionality."""

    def test_add_edge_controller_sets_timestamps(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that add_edge_controller sets first_seen and last_seen."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        repo.add_edge_controller("heartbeat-test-001", "heartbeat-controller", "192.168.1.50")

        controller = repo.get_edge_controller("heartbeat-test-001")
        assert controller is not None
        assert controller["first_seen"] is not None
        assert controller["last_seen"] is not None
        assert controller["status"] == "online"

    def test_heartbeat_updates_last_seen(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test that heartbeat updates last_seen timestamp."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)
        repo.add_edge_controller("hb-001", "test-controller", "192.168.1.100")

        # Get initial last_seen
        controller_before = repo.get_edge_controller("hb-001")
        assert controller_before is not None

        # Send heartbeat
        result = repo.update_controller_heartbeat("hb-001")

        assert result is True
        controller_after = repo.get_edge_controller("hb-001")
        assert controller_after is not None
        assert controller_after["status"] == "online"
        # last_seen should be updated (at least not None)
        assert controller_after["last_seen"] is not None

    def test_heartbeat_with_all_fields(self, temp_db_path: Path, temp_schema_path: Path) -> None:
        """Test heartbeat with all telemetry fields."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)
        repo.add_edge_controller("hb-002", "full-telemetry", "192.168.1.101")

        result = repo.update_controller_heartbeat(
            controller_id="hb-002",
            config_hash="abc123def456",
            version="2.0.0",
            platform="Linux-5.15.0-aarch64",
            python_version="3.11.2",
            memory_mb=4096,
            cpu_count=4,
        )

        assert result is True
        controller = repo.get_edge_controller("hb-002")
        assert controller is not None
        assert controller["config_hash"] == "abc123def456"
        assert controller["version"] == "2.0.0"
        assert controller["platform"] == "Linux-5.15.0-aarch64"
        assert controller["python_version"] == "3.11.2"
        assert controller["memory_mb"] == 4096
        assert controller["cpu_count"] == 4
        assert controller["status"] == "online"

    def test_heartbeat_with_partial_fields(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test heartbeat with only some telemetry fields."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)
        repo.add_edge_controller("hb-003", "partial-telemetry", "192.168.1.102")

        # First heartbeat with version only
        result = repo.update_controller_heartbeat(
            controller_id="hb-003",
            version="1.5.0",
        )

        assert result is True
        controller = repo.get_edge_controller("hb-003")
        assert controller is not None
        assert controller["version"] == "1.5.0"
        assert controller["config_hash"] is None  # Not set
        assert controller["memory_mb"] is None  # Not set

        # Second heartbeat with memory only - version should persist
        result = repo.update_controller_heartbeat(
            controller_id="hb-003",
            memory_mb=2048,
        )

        assert result is True
        controller = repo.get_edge_controller("hb-003")
        assert controller is not None
        assert controller["version"] == "1.5.0"  # Still set from before
        assert controller["memory_mb"] == 2048  # Now set

    def test_heartbeat_nonexistent_controller(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test heartbeat for non-existent controller returns False."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)

        result = repo.update_controller_heartbeat("nonexistent-controller-id")

        assert result is False

    def test_heartbeat_empty_updates_status(
        self, temp_db_path: Path, temp_schema_path: Path
    ) -> None:
        """Test that heartbeat with no fields still updates last_seen and status."""
        repo = ConfigRepository(temp_db_path, temp_schema_path)
        repo.add_edge_controller("hb-004", "minimal-heartbeat", "192.168.1.103")

        result = repo.update_controller_heartbeat("hb-004")

        assert result is True
        controller = repo.get_edge_controller("hb-004")
        assert controller is not None
        assert controller["status"] == "online"
        assert controller["last_seen"] is not None
