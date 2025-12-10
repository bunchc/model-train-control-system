"""Integration tests for heartbeat end-to-end flow.

Tests the complete heartbeat lifecycle from EdgeControllerApp through
CentralAPIClient to the (mocked) Central API.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.api.client import CentralAPIClient
from app.main import HEARTBEAT_INTERVAL_SECONDS, EdgeControllerApp


@pytest.fixture()
def api_client() -> CentralAPIClient:
    """Create API client for testing."""
    return CentralAPIClient(host="localhost", port=8000)


@pytest.fixture()
def configured_app(mock_runtime_config: dict[str, Any]) -> EdgeControllerApp:
    """Create a configured EdgeControllerApp for heartbeat testing.

    Args:
        mock_runtime_config: Runtime configuration fixture from conftest.py

    Returns:
        EdgeControllerApp configured for heartbeat testing
    """
    app = EdgeControllerApp()
    app._controller_uuid = mock_runtime_config["uuid"]
    app._runtime_config = mock_runtime_config
    app._api_client = CentralAPIClient(host="localhost", port=8000)
    return app


@pytest.mark.integration()
class TestHeartbeatEndToEnd:
    """Integration tests for the complete heartbeat flow."""

    def test_send_heartbeat_success(self, configured_app: EdgeControllerApp) -> None:
        """Test successful heartbeat sends correct payload and returns True."""
        with patch("app.api.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_response

            result = configured_app._send_heartbeat()

            assert result is True
            mock_post.assert_called_once()

            # Verify URL contains controller UUID and heartbeat endpoint
            call_args = mock_post.call_args
            url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url")
            assert configured_app._controller_uuid in url
            assert "/heartbeat" in url

    def test_send_heartbeat_includes_system_info(self, configured_app: EdgeControllerApp) -> None:
        """Test heartbeat payload includes gathered system info fields."""
        with patch("app.api.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            configured_app._send_heartbeat()

            # Verify POST was called with json payload
            call_kwargs = mock_post.call_args.kwargs
            assert "json" in call_kwargs

            # Payload should exist (contents depend on system)
            payload = call_kwargs["json"]
            assert isinstance(payload, dict)

    def test_send_heartbeat_handles_server_error(self, configured_app: EdgeControllerApp) -> None:
        """Test graceful handling of 500 server error."""
        with patch("app.api.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            result = configured_app._send_heartbeat()

            assert result is False

    def test_send_heartbeat_handles_not_found(self, configured_app: EdgeControllerApp) -> None:
        """Test handling of 404 (controller not registered in central API)."""
        with patch("app.api.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_post.return_value = mock_response

            result = configured_app._send_heartbeat()

            assert result is False

    def test_send_heartbeat_handles_network_error(self, configured_app: EdgeControllerApp) -> None:
        """Test handling of network connection errors."""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        with patch("app.api.client.requests.post") as mock_post:
            mock_post.side_effect = RequestsConnectionError("Connection refused")

            result = configured_app._send_heartbeat()

            assert result is False

    def test_heartbeat_payload_excludes_none_values(
        self, configured_app: EdgeControllerApp
    ) -> None:
        """Test that None values from system info are excluded from payload."""
        with (
            patch.object(configured_app, "_gather_system_info") as mock_gather,
            patch("app.api.client.requests.post") as mock_post,
        ):
            # Return system info with explicit None values
            mock_gather.return_value = {
                "os": "Linux",
                "os_version": "5.15.0",
                "architecture": "aarch64",
                "python_version": "3.9.18",
                "software_version": "0.1.0",
                "memory_mb": None,  # Explicitly None (e.g., non-Linux system)
                "config_hash": "abc123def456",
            }
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            configured_app._send_heartbeat()

            # Verify memory_mb is NOT in payload since it was None
            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs.get("json", {})
            assert "memory_mb" not in payload

    def test_heartbeat_interval_constant_is_reasonable(self) -> None:
        """Verify heartbeat interval is less than frontend online threshold (30s)."""
        # Frontend considers controller "online" if last_seen < 30 seconds ago
        # Heartbeat interval must be less to maintain online status
        assert HEARTBEAT_INTERVAL_SECONDS < 30
        assert HEARTBEAT_INTERVAL_SECONDS > 0

    def test_full_heartbeat_flow_with_real_api_client(
        self, mock_runtime_config: dict[str, Any]
    ) -> None:
        """Test complete flow: EdgeControllerApp → _send_heartbeat → CentralAPIClient."""
        # Create app with real (not mocked) internal wiring
        app = EdgeControllerApp()
        app._controller_uuid = mock_runtime_config["uuid"]
        app._runtime_config = mock_runtime_config
        app._api_client = CentralAPIClient(host="localhost", port=8000)

        with patch("app.api.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_post.return_value = mock_response

            # Execute the heartbeat
            result = app._send_heartbeat()

            # Verify success
            assert result is True

            # Verify the request was made to correct endpoint
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert f"/api/controllers/{mock_runtime_config['uuid']}/heartbeat" in url

            # Verify timeout was set
            assert call_args.kwargs.get("timeout") is not None

            # Verify payload structure
            payload = call_args.kwargs.get("json", {})
            # Should have at least some fields (version, config_hash, etc.)
            # Exact fields depend on system, but payload should be a dict
            assert isinstance(payload, dict)
