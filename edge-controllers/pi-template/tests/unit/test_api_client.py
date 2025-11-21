"""Unit tests for API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from api.client import CentralAPIClient


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
