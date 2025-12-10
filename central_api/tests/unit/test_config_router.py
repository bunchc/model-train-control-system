"""Unit tests for config router endpoints.

Tests API endpoints with mocked ConfigManager.
"""

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.schemas import ControllerHeartbeat
from app.routers import config as config_router


@pytest.fixture()
def mock_config_manager() -> MagicMock:
    """Provide a mocked ConfigManager."""
    return MagicMock()


@pytest.fixture()
def client(mock_config_manager: MagicMock) -> Generator[TestClient, None, None]:
    """Provide a test client with mocked ConfigManager."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(config_router.router, prefix="/api")

    # Override the config getter
    config_router._config_instance = mock_config_manager

    yield TestClient(app)

    # Cleanup
    config_router._config_instance = None


@pytest.mark.unit()
class TestControllerHeartbeatEndpoint:
    """Test suite for POST /controllers/{id}/heartbeat endpoint."""

    def test_heartbeat_success(self, client: TestClient, mock_config_manager: MagicMock) -> None:
        """Test successful heartbeat returns 200."""
        mock_config_manager.update_controller_heartbeat.return_value = True

        response = client.post(
            "/api/controllers/ctrl-123/heartbeat",
            json={"version": "1.0.0", "config_hash": "abc123"},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_config_manager.update_controller_heartbeat.assert_called_once()

        # Verify the heartbeat model was passed correctly
        call_args = mock_config_manager.update_controller_heartbeat.call_args
        assert call_args[0][0] == "ctrl-123"
        heartbeat = call_args[0][1]
        assert isinstance(heartbeat, ControllerHeartbeat)
        assert heartbeat.version == "1.0.0"
        assert heartbeat.config_hash == "abc123"

    def test_heartbeat_controller_not_found(
        self, client: TestClient, mock_config_manager: MagicMock
    ) -> None:
        """Test heartbeat for unknown controller returns 404."""
        mock_config_manager.update_controller_heartbeat.return_value = False

        response = client.post(
            "/api/controllers/unknown-ctrl/heartbeat",
            json={"version": "1.0.0"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Controller not found"

    def test_heartbeat_minimal_payload(
        self, client: TestClient, mock_config_manager: MagicMock
    ) -> None:
        """Test heartbeat with empty body (all fields optional)."""
        mock_config_manager.update_controller_heartbeat.return_value = True

        response = client.post(
            "/api/controllers/ctrl-123/heartbeat",
            json={},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_heartbeat_full_payload(
        self, client: TestClient, mock_config_manager: MagicMock
    ) -> None:
        """Test heartbeat with all fields populated."""
        mock_config_manager.update_controller_heartbeat.return_value = True

        response = client.post(
            "/api/controllers/ctrl-full/heartbeat",
            json={
                "config_hash": "sha256:deadbeef",
                "version": "2.1.0",
                "platform": "linux",
                "python_version": "3.11.4",
                "memory_mb": 1024,
                "cpu_count": 4,
            },
        )

        assert response.status_code == 200

        # Verify all fields were passed
        call_args = mock_config_manager.update_controller_heartbeat.call_args
        heartbeat = call_args[0][1]
        assert heartbeat.config_hash == "sha256:deadbeef"
        assert heartbeat.version == "2.1.0"
        assert heartbeat.platform == "linux"
        assert heartbeat.python_version == "3.11.4"
        assert heartbeat.memory_mb == 1024
        assert heartbeat.cpu_count == 4

    def test_heartbeat_invalid_payload_type(
        self, client: TestClient, mock_config_manager: MagicMock
    ) -> None:
        """Test heartbeat with invalid field types returns 422."""
        response = client.post(
            "/api/controllers/ctrl-123/heartbeat",
            json={"memory_mb": "not-a-number"},  # Should be int
        )

        assert response.status_code == 422
