"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for config files.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_service_config(temp_config_dir: Path) -> dict[str, Any]:
    """Create a mock service configuration.

    Args:
        temp_config_dir: Temporary directory for config files

    Returns:
        Service configuration dictionary
    """
    config = {
        "central_api_host": "localhost",
        "central_api_port": 8000,
    }

    config_file = temp_config_dir / "edge-controller.conf"
    with config_file.open("w") as file_handle:
        yaml.safe_dump(config, file_handle)

    return config


@pytest.fixture
def mock_runtime_config() -> dict[str, Any]:
    """Create a mock runtime configuration.

    Returns:
        Runtime configuration dictionary
    """
    return {
        "uuid": "test-uuid-1234",
        "train_id": "train-1",
        "mqtt_broker": {
            "host": "mqtt-broker",
            "port": 1883,
            "username": None,
            "password": None,
        },
        "status_topic": "trains/train-1/status",
        "commands_topic": "trains/train-1/commands",
    }


@pytest.fixture
def mock_mqtt_client() -> MagicMock:
    """Create a mock MQTT client.

    Returns:
        Mocked MQTT client
    """
    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    mock_client.publish.return_value = MagicMock(rc=0)
    return mock_client


@pytest.fixture
def mock_hardware_controller() -> MagicMock:
    """Create a mock hardware controller.

    Returns:
        Mocked hardware controller
    """
    mock_hw = MagicMock()
    mock_hw.start.return_value = None
    mock_hw.stop.return_value = None
    mock_hw.set_speed.return_value = None
    return mock_hw
