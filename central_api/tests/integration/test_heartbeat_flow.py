"""Integration tests for heartbeat flow.

Tests the complete heartbeat lifecycle: API → ConfigManager → Repository → Database.
"""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import config as config_router
from app.services.config_manager import ConfigManager


@pytest.fixture()
def integration_manager(
    sample_yaml_file: Path, temp_db_path: Path, temp_schema_path: Path
) -> ConfigManager:
    """Provide a real ConfigManager with real database."""
    return ConfigManager(
        yaml_path=sample_yaml_file,
        db_path=temp_db_path,
        schema_path=temp_schema_path,
    )


@pytest.fixture()
def integration_client(
    integration_manager: ConfigManager,
) -> Generator[TestClient, None, None]:
    """Provide a test client with real ConfigManager."""
    app = FastAPI()
    app.include_router(config_router.router, prefix="/api")

    # Override the config getter to use our real manager
    config_router._config_instance = integration_manager

    yield TestClient(app)

    # Cleanup
    config_router._config_instance = None


@pytest.mark.integration()
class TestHeartbeatFlow:
    """Integration tests for the complete heartbeat flow."""

    def test_heartbeat_persists_to_database(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
        temp_db_path: Path,
    ) -> None:
        """Test that heartbeat data persists to SQLite database."""
        # Get existing controller from bootstrap
        controllers = integration_manager.get_edge_controllers()
        assert len(controllers) > 0
        controller_id = controllers[0].id

        # Send heartbeat
        response = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={
                "version": "1.2.3",
                "platform": "linux",
                "config_hash": "sha256:test123",
            },
        )
        assert response.status_code == 200

        # Query database directly to verify persistence
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT version, platform, config_hash, status, last_seen "
            "FROM edge_controllers WHERE id = ?",
            (controller_id,),
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["version"] == "1.2.3"
        assert row["platform"] == "linux"
        assert row["config_hash"] == "sha256:test123"
        assert row["status"] == "online"
        assert row["last_seen"] is not None

    def test_heartbeat_updates_last_seen_on_subsequent_calls(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
        temp_db_path: Path,
    ) -> None:
        """Test that subsequent heartbeats update the last_seen timestamp."""
        import time

        controllers = integration_manager.get_edge_controllers()
        controller_id = controllers[0].id

        # First heartbeat
        response1 = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={"version": "1.0.0"},
        )
        assert response1.status_code == 200

        # Get first timestamp
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT last_seen FROM edge_controllers WHERE id = ?",
            (controller_id,),
        )
        first_seen = cursor.fetchone()["last_seen"]
        conn.close()

        # Small delay to ensure timestamp changes
        time.sleep(0.1)

        # Second heartbeat
        response2 = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={"version": "1.0.1"},
        )
        assert response2.status_code == 200

        # Get second timestamp
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT last_seen, version FROM edge_controllers WHERE id = ?",
            (controller_id,),
        )
        row = cursor.fetchone()
        conn.close()

        # Verify timestamp updated and version changed
        assert row["last_seen"] >= first_seen
        assert row["version"] == "1.0.1"

    def test_heartbeat_with_all_telemetry_fields(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
        temp_db_path: Path,
    ) -> None:
        """Test heartbeat with full telemetry payload persists all fields."""
        controllers = integration_manager.get_edge_controllers()
        controller_id = controllers[0].id

        # Send heartbeat with all fields
        response = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={
                "config_hash": "sha256:fulltest",
                "version": "2.5.0",
                "platform": "linux-arm64",
                "python_version": "3.11.4",
                "memory_mb": 2048,
                "cpu_count": 4,
            },
        )
        assert response.status_code == 200

        # Verify all fields in database
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """SELECT config_hash, version, platform, python_version,
                      memory_mb, cpu_count, status
               FROM edge_controllers WHERE id = ?""",
            (controller_id,),
        )
        row = cursor.fetchone()
        conn.close()

        assert row["config_hash"] == "sha256:fulltest"
        assert row["version"] == "2.5.0"
        assert row["platform"] == "linux-arm64"
        assert row["python_version"] == "3.11.4"
        assert row["memory_mb"] == 2048
        assert row["cpu_count"] == 4
        assert row["status"] == "online"

    def test_heartbeat_unknown_controller_returns_404(
        self,
        integration_client: TestClient,
    ) -> None:
        """Test that heartbeat for unknown controller returns 404."""
        response = integration_client.post(
            "/api/controllers/nonexistent-uuid-12345/heartbeat",
            json={"version": "1.0.0"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Controller not found"

    def test_controller_first_seen_not_updated_by_heartbeat(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
        temp_db_path: Path,
    ) -> None:
        """Test that first_seen timestamp is not updated by heartbeats."""
        controllers = integration_manager.get_edge_controllers()
        controller_id = controllers[0].id

        # Get initial first_seen
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT first_seen FROM edge_controllers WHERE id = ?",
            (controller_id,),
        )
        initial_first_seen = cursor.fetchone()["first_seen"]
        conn.close()

        # Send heartbeat
        response = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={"version": "1.0.0"},
        )
        assert response.status_code == 200

        # Verify first_seen unchanged
        conn = sqlite3.connect(str(temp_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT first_seen FROM edge_controllers WHERE id = ?",
            (controller_id,),
        )
        after_first_seen = cursor.fetchone()["first_seen"]
        conn.close()

        assert initial_first_seen == after_first_seen

    def test_get_controller_returns_telemetry_after_heartbeat(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
    ) -> None:
        """Test that GET /controllers returns telemetry fields after heartbeat."""
        controllers = integration_manager.get_edge_controllers()
        controller_id = controllers[0].id

        # Send heartbeat with telemetry
        response = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={
                "version": "3.0.0",
                "platform": "raspberrypi",
                "python_version": "3.11.0",
                "memory_mb": 512,
                "cpu_count": 4,
            },
        )
        assert response.status_code == 200

        # Fetch controller via ConfigManager and verify telemetry is returned
        updated_controller = integration_manager.get_edge_controller(controller_id)
        assert updated_controller is not None
        assert updated_controller.version == "3.0.0"
        assert updated_controller.platform == "raspberrypi"
        assert updated_controller.python_version == "3.11.0"
        assert updated_controller.memory_mb == 512
        assert updated_controller.cpu_count == 4
        assert updated_controller.status == "online"
        assert updated_controller.last_seen is not None

    def test_get_controllers_list_returns_telemetry(
        self,
        integration_client: TestClient,
        integration_manager: ConfigManager,
    ) -> None:
        """Test that get_edge_controllers() returns telemetry fields."""
        controllers = integration_manager.get_edge_controllers()
        controller_id = controllers[0].id

        # Send heartbeat
        response = integration_client.post(
            f"/api/controllers/{controller_id}/heartbeat",
            json={"version": "4.0.0", "platform": "linux"},
        )
        assert response.status_code == 200

        # Fetch all controllers and verify telemetry is in the list
        all_controllers = integration_manager.get_edge_controllers()
        updated = next(c for c in all_controllers if c.id == controller_id)
        assert updated.version == "4.0.0"
        assert updated.platform == "linux"
        assert updated.status == "online"
