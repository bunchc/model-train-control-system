"""Unit tests for API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.api.client import CentralAPIClient


@pytest.mark.unit()
class TestCentralAPIClient:
    """Tests for CentralAPIClient class."""

    @pytest.fixture()
    def api_client(self) -> CentralAPIClient:
        """Create API client instance."""
        return CentralAPIClient(host="localhost", port=8000, timeout=1, max_retries=2)

    def test_initialization(self, api_client: CentralAPIClient) -> None:
        """Test client initialization."""
        assert api_client.host == "localhost"
        assert api_client.port == 8000
        assert api_client.base_url == "http://localhost:8000"
        assert api_client.timeout == 1
        assert api_client.max_retries == 2

    @patch("api.client.requests.get")
    def test_check_accessibility_success(
        self, mock_get: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test successful API accessibility check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = api_client.check_accessibility()

        assert result is True
        mock_get.assert_called_once_with("http://localhost:8000/api/ping", timeout=1)

    @patch("api.client.requests.get")
    def test_check_accessibility_failure(
        self, mock_get: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test API accessibility check when server is down."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        result = api_client.check_accessibility()

        assert result is False
        assert mock_get.call_count == 2

    @patch("api.client.requests.get")
    def test_check_controller_exists_true(
        self, mock_get: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test controller existence check - controller exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = api_client.check_controller_exists("test-uuid")

        assert result is True

    @patch("api.client.socket.gethostname")
    @patch("api.client.socket.gethostbyname")
    @patch("api.client.requests.post")
    def test_register_controller_success(
        self,
        mock_post: MagicMock,
        mock_gethostbyname: MagicMock,
        mock_gethostname: MagicMock,
        api_client: CentralAPIClient,
    ) -> None:
        """Test successful controller registration."""
        mock_gethostname.return_value = "test-pi"
        mock_gethostbyname.return_value = "192.168.1.100"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uuid": "new-uuid-123",
            "status": "registered",
        }
        mock_post.return_value = mock_response

        result = api_client.register_controller()

        assert result == "new-uuid-123"
        mock_post.assert_called_once()

    @patch("api.client.requests.get")
    def test_download_runtime_config_success(
        self, mock_get: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test successful runtime config download."""
        config_data = {"train_id": "train-1", "mqtt_broker": {"host": "mqtt"}}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = config_data
        mock_get.return_value = mock_response

        result = api_client.download_runtime_config("test-uuid")

        assert result is not None
        assert result["train_id"] == "train-1"
        assert result["uuid"] == "test-uuid"

    @patch("api.client.requests.get")
    def test_download_runtime_config_not_found(
        self, mock_get: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test runtime config download when config not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = api_client.download_runtime_config("test-uuid")

        assert result is None


@pytest.mark.unit()
class TestSendHeartbeat:
    """Tests for CentralAPIClient.send_heartbeat() method."""

    @pytest.fixture()
    def api_client(self) -> CentralAPIClient:
        """Create API client instance for heartbeat tests."""
        return CentralAPIClient(host="localhost", port=8000, timeout=1)

    @patch("api.client.requests.post")
    def test_send_heartbeat_success(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test successful heartbeat returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = api_client.send_heartbeat(
            controller_uuid="test-uuid-123",
            version="1.0.0",
            platform="Linux-test",
        )

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "test-uuid-123" in call_args[0][0]  # URL contains UUID
        assert call_args[1]["json"]["version"] == "1.0.0"
        assert call_args[1]["json"]["platform"] == "Linux-test"

    @patch("api.client.requests.post")
    def test_send_heartbeat_not_found(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat returns False when controller not registered (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        result = api_client.send_heartbeat(controller_uuid="unknown-uuid")

        assert result is False

    @patch("api.client.requests.post")
    def test_send_heartbeat_server_error(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat returns False on server error (500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = api_client.send_heartbeat(controller_uuid="test-uuid")

        assert result is False

    @patch("api.client.requests.post")
    def test_send_heartbeat_network_error(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat returns False on network failure (no exception raised)."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        result = api_client.send_heartbeat(controller_uuid="test-uuid")

        assert result is False

    @patch("api.client.requests.post")
    def test_send_heartbeat_timeout(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat returns False on timeout (no exception raised)."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        result = api_client.send_heartbeat(controller_uuid="test-uuid")

        assert result is False

    @patch("api.client.requests.post")
    def test_send_heartbeat_excludes_none_fields(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test that None fields are excluded from the payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        api_client.send_heartbeat(
            controller_uuid="test-uuid",
            version="1.0.0",
            platform=None,  # Should be excluded
            memory_mb=1024,
            cpu_count=None,  # Should be excluded
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "version" in payload
        assert "memory_mb" in payload
        assert payload["version"] == "1.0.0"
        assert payload["memory_mb"] == 1024
        assert "platform" not in payload  # None was excluded
        assert "cpu_count" not in payload  # None was excluded

    @patch("api.client.requests.post")
    def test_send_heartbeat_all_fields(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat with all fields populated."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        api_client.send_heartbeat(
            controller_uuid="test-uuid",
            config_hash="abc123def456",
            version="1.0.0",
            platform="Linux-5.15.0-rpi4",
            python_version="3.11.5",
            memory_mb=3906,
            cpu_count=4,
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["config_hash"] == "abc123def456"
        assert payload["version"] == "1.0.0"
        assert payload["platform"] == "Linux-5.15.0-rpi4"
        assert payload["python_version"] == "3.11.5"
        assert payload["memory_mb"] == 3906
        assert payload["cpu_count"] == 4

    @patch("api.client.requests.post")
    def test_send_heartbeat_minimal(
        self, mock_post: MagicMock, api_client: CentralAPIClient
    ) -> None:
        """Test heartbeat with only UUID (empty payload body)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = api_client.send_heartbeat(controller_uuid="test-uuid")

        assert result is True
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload == {}  # Empty payload when all optional fields are None
