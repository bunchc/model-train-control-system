"""End-to-end tests for controller lifecycle."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from main import EdgeControllerApp


@pytest.mark.e2e()
class TestControllerLifecycle:
    """End-to-end tests for complete controller lifecycle."""

    @pytest.fixture()
    def setup_environment(
        self, temp_config_dir: Path, mock_runtime_config: dict[str, Any]
    ) -> tuple[Path, Path]:
        """Setup test environment with config files."""
        service_config = {"central_api_host": "localhost", "central_api_port": 8000}
        config_file = temp_config_dir / "edge-controller.conf"
        with config_file.open("w") as file_handle:
            yaml.safe_dump(service_config, file_handle)

        cached_file = temp_config_dir / "edge-controller.yaml"
        with cached_file.open("w") as file_handle:
            yaml.safe_dump(mock_runtime_config, file_handle)

        return config_file, cached_file

    def test_command_handling_flow(self, setup_environment: tuple[Path, Path]) -> None:
        """Test complete command handling flow."""
        config_file, cached_file = setup_environment

        with (
            patch("api.client.requests.get") as mock_get,
            patch("mqtt_client.mqtt.Client"),
            patch("main.HARDWARE_AVAILABLE", False),
            patch("main.Path.__truediv__") as mock_div,
        ):
            mock_div.side_effect = [config_file, cached_file]

            ping_response = MagicMock()
            ping_response.status_code = 200
            config_response = MagicMock()
            config_response.status_code = 200
            config_response.json.return_value = {
                "uuid": "test-uuid",
                "train_id": "train-1",
                "mqtt_broker": {"host": "mqtt", "port": 1883},
                "status_topic": "trains/train-1/status",
                "commands_topic": "trains/train-1/commands",
            }
            mock_get.side_effect = [ping_response, config_response]

            app = EdgeControllerApp()
            app.initialize()

            test_commands = [
                {"action": "start", "speed": 50},
                {"action": "setSpeed", "speed": 75},
                {"action": "stop"},
            ]

            for command in test_commands:
                app._handle_command(command)

            assert app.hardware_controller is not None
