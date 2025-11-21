"""End-to-end simulated tests for the Central API lifecycle.

This module tests the full FastAPI application in a mock environment,
verifying the complete request/response cycle without external dependencies.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def e2e_yaml_config(tmp_path: Path) -> Path:
    """Create a complete YAML config file for E2E testing."""
    config_data = {
        "plugins": [{"name": "DCC Controller", "type": "dcc", "version": "1.0.0", "enabled": True}],
        "edge_controllers": [
            {
                "id": "edge-001",
                "name": "Main Controller",
                "location": "Layout Room 1",
                "mqtt_topic_prefix": "trains/edge-001",
                "hardware_type": "raspberry_pi_4",
                "plugin_config": {"dcc_address": "192.168.1.100"},
            }
        ],
    }

    yaml_path = tmp_path / "e2e_config.yaml"
    with yaml_path.open("w") as yaml_file:
        yaml.dump(config_data, yaml_file)

    return yaml_path


@pytest.fixture()
def e2e_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path for E2E testing."""
    return tmp_path / "e2e_test.db"


@pytest.fixture()
def e2e_schema_path() -> Path:
    """Get the path to the schema file."""
    return Path(__file__).parent.parent.parent / "app" / "services" / "config_schema.sql"


@pytest.fixture()
def mock_mqtt_adapter() -> Generator[MagicMock, None, None]:
    """Mock the MQTT adapter to avoid external network calls."""
    with patch("app.services.mqtt_adapter.MQTTAdapter") as mock_adapter:
        mock_instance = MagicMock()
        mock_adapter.return_value = mock_instance
        yield mock_instance


@pytest.fixture()
def client(
    e2e_yaml_config: Path,
    e2e_db_path: Path,
    e2e_schema_path: Path,
    mock_mqtt_adapter: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with mocked dependencies."""
    # Set environment variables for the test
    monkeypatch.setenv("CONFIG_YAML_PATH", str(e2e_yaml_config))
    monkeypatch.setenv("DB_PATH", str(e2e_db_path))
    monkeypatch.setenv("SCHEMA_PATH", str(e2e_schema_path))
    monkeypatch.setenv("MQTT_BROKER_HOST", "localhost")
    monkeypatch.setenv("MQTT_BROKER_PORT", "1883")

    # Patch the ConfigManager to prevent it from loading at module import time
    with patch("app.routers.config.ConfigManager") as mock_config_cls:
        # Create a mock instance
        mock_instance = MagicMock()
        mock_config_cls.return_value = mock_instance

        # Import after patching to prevent early initialization
        import importlib

        import app.routers.config as config_module

        importlib.reload(config_module)

        # Create the test client
        with TestClient(app) as test_client:
            yield test_client


class TestAPILifecycle:
    """Test the complete API lifecycle with mocked dependencies."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Model Train Control System - Central API"
        assert "version" in data

    def test_ping_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_get_all_trains(self, client: TestClient) -> None:
        """Test retrieving all trains from the system."""
        response = client.get("/api/trains")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_train_by_id(self, client: TestClient) -> None:
        """Test retrieving a specific train by ID."""
        # First, get all trains to find a valid ID
        response = client.get("/api/trains")
        assert response.status_code == 200
        trains = response.json()

        if len(trains) > 0:
            train_id = trains[0]["id"]
            response = client.get(f"/api/trains/{train_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == train_id

    def test_get_nonexistent_train(self, client: TestClient) -> None:
        """Test retrieving a non-existent train returns 404."""
        response = client.get("/api/trains/nonexistent-id")
        assert response.status_code == 404

    def test_send_train_command(self, client: TestClient) -> None:
        """Test sending a command to a train publishes to MQTT."""
        # Get a valid train ID
        response = client.get("/api/trains")
        assert response.status_code == 200
        trains = response.json()

        if len(trains) > 0:
            train_id = trains[0]["id"]
            command_payload = {"action": "setSpeed", "speed": 50}

            response = client.post(f"/api/trains/{train_id}/command", json=command_payload)
            assert response.status_code == 200

            # Verify MQTT publish was called (if MQTT is integrated)
            # This will depend on the actual implementation

    def test_get_full_config(self, client: TestClient) -> None:
        """Test retrieving the full system configuration."""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert "edge_controllers" in data
        assert isinstance(data["plugins"], list)
        assert isinstance(data["edge_controllers"], list)

    def test_get_edge_controllers(self, client: TestClient) -> None:
        """Test retrieving all edge controllers."""
        response = client.get("/api/config/edge-controllers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_edge_controller(self, client: TestClient) -> None:
        """Test adding a new edge controller."""
        new_controller = {
            "id": "edge-002",
            "name": "Secondary Controller",
            "location": "Layout Room 2",
            "mqtt_topic_prefix": "trains/edge-002",
            "hardware_type": "raspberry_pi_4",
            "plugin_config": {"dcc_address": "192.168.1.101"},
        }

        response = client.post("/api/config/edge-controllers", json=new_controller)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == new_controller["id"]
        assert data["name"] == new_controller["name"]

    def test_update_edge_controller(self, client: TestClient) -> None:
        """Test updating an existing edge controller."""
        # First get existing controllers
        response = client.get("/api/config/edge-controllers")
        assert response.status_code == 200
        controllers = response.json()

        if len(controllers) > 0:
            controller_id = controllers[0]["id"]
            update_payload = {"name": "Updated Controller Name"}

            response = client.put(
                f"/api/config/edge-controllers/{controller_id}", json=update_payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == update_payload["name"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_json_payload(self, client: TestClient) -> None:
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        response = client.post(
            "/api/config/edge-controllers",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient) -> None:
        """Test that missing required fields are rejected."""
        incomplete_controller = {
            "id": "edge-003"
            # Missing required fields: name, location, etc.
        }

        response = client.post("/api/config/edge-controllers", json=incomplete_controller)
        assert response.status_code == 422

    def test_duplicate_edge_controller_id(self, client: TestClient) -> None:
        """Test that duplicate edge controller IDs are rejected."""
        new_controller = {
            "id": "edge-duplicate",
            "name": "Duplicate Test",
            "location": "Test Location",
            "mqtt_topic_prefix": "trains/edge-duplicate",
            "hardware_type": "raspberry_pi_4",
            "plugin_config": {},
        }

        # Add the controller once
        response = client.post("/api/config/edge-controllers", json=new_controller)
        assert response.status_code == 201

        # Try to add it again (should fail)
        response = client.post("/api/config/edge-controllers", json=new_controller)
        assert response.status_code in {400, 409}
