"""Integration tests for configuration flow."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from config.manager import ConfigManager


@pytest.mark.integration()
class TestConfigIntegration:
    """Integration tests for config loading and management."""

    def test_full_config_initialization_new_controller(self, temp_config_dir: Path) -> None:
        """Test complete config initialization for new controller."""
        service_config = {"central_api_host": "localhost", "central_api_port": 8000}
        config_file = temp_config_dir / "edge-controller.conf"
        with config_file.open("w") as file_handle:
            yaml.safe_dump(service_config, file_handle)

        cached_file = temp_config_dir / "edge-controller.yaml"

        with (
            patch("api.client.requests.get") as mock_get,
            patch("api.client.requests.post") as mock_post,
            patch("api.client.socket.gethostname") as mock_hostname,
        ):
            ping_response = MagicMock()
            ping_response.status_code = 200

            register_response = MagicMock()
            register_response.status_code = 200
            register_response.json.return_value = {
                "uuid": "new-uuid-123",
                "status": "registered",
            }

            config_response = MagicMock()
            config_response.status_code = 404

            mock_get.side_effect = [ping_response, config_response]
            mock_post.return_value = register_response
            mock_hostname.return_value = "test-pi"

            manager = ConfigManager(config_file, cached_file)
            service, runtime = manager.initialize()

            assert service == service_config
            assert runtime is None

    def test_config_initialization_existing_controller(
        self, temp_config_dir: Path, mock_runtime_config: dict[str, Any]
    ) -> None:
        """Test config initialization for existing controller."""
        service_config = {"central_api_host": "localhost", "central_api_port": 8000}
        config_file = temp_config_dir / "edge-controller.conf"
        with config_file.open("w") as file_handle:
            yaml.safe_dump(service_config, file_handle)

        cached_file = temp_config_dir / "edge-controller.yaml"
        with cached_file.open("w") as file_handle:
            yaml.safe_dump(mock_runtime_config, file_handle)

        with patch("api.client.requests.get") as mock_get:
            ping_response = MagicMock()
            ping_response.status_code = 200

            config_response = MagicMock()
            config_response.status_code = 200
            config_response.json.return_value = mock_runtime_config

            mock_get.side_effect = [ping_response, config_response]

            manager = ConfigManager(config_file, cached_file)
            service, runtime = manager.initialize()

            assert service == service_config
            assert runtime is not None
            assert runtime["uuid"] == "test-uuid-1234"
