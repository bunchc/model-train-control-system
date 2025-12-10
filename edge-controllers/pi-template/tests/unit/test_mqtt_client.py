"""Unit tests for MQTT client."""

from unittest.mock import MagicMock

import pytest

from app.mqtt_client import MQTTClient, MQTTConnectionError, MQTTPublishError


@pytest.mark.unit()
class TestMQTTClient:
    """Tests for MQTTClient class."""

    @pytest.fixture()
    def mock_command_handler(self) -> MagicMock:
        """Create mock command handler."""
        return MagicMock()

    @pytest.fixture()
    def mock_paho_client(self) -> MagicMock:
        """Create mock paho MQTT client for dependency injection."""
        return MagicMock()

    @pytest.fixture()
    def mqtt_client(
        self, mock_command_handler: MagicMock, mock_paho_client: MagicMock
    ) -> MQTTClient:
        """Create MQTT client instance with injected mock."""
        return MQTTClient(
            broker_host="mqtt-broker",
            broker_port=1883,
            train_id="train-1",
            status_topic="trains/train-1/status",
            commands_topic="trains/train-1/commands",
            command_handler=mock_command_handler,
            mqtt_client=mock_paho_client,
        )

    def test_initialization(self, mqtt_client: MQTTClient, mock_command_handler: MagicMock) -> None:
        """Test MQTT client initialization."""
        assert mqtt_client.broker_host == "mqtt-broker"
        assert mqtt_client.broker_port == 1883
        assert mqtt_client.train_id == "train-1"
        assert mqtt_client.command_handler == mock_command_handler

    def test_start_success(self, mqtt_client: MQTTClient, mock_paho_client: MagicMock) -> None:
        """Test successful MQTT client start."""
        mqtt_client.start()

        mock_paho_client.connect.assert_called_once_with("mqtt-broker", 1883, keepalive=60)
        mock_paho_client.loop_start.assert_called_once()

    def test_start_connection_error(
        self, mqtt_client: MQTTClient, mock_paho_client: MagicMock
    ) -> None:
        """Test MQTT client start with connection error."""
        mock_paho_client.connect.side_effect = ConnectionRefusedError("Broker down")

        with pytest.raises(MQTTConnectionError, match="Connection refused"):
            mqtt_client.start()

    def test_on_message_valid_json(
        self, mqtt_client: MQTTClient, mock_command_handler: MagicMock
    ) -> None:
        """Test message handling with valid JSON command."""
        mock_msg = MagicMock()
        mock_msg.topic = "trains/train-1/commands"
        mock_msg.payload = b'{"action": "start", "speed": 50}'

        mqtt_client._on_message(None, None, mock_msg)

        mock_command_handler.assert_called_once_with({"action": "start", "speed": 50})

    def test_publish_status_mqtt_error(
        self, mqtt_client: MQTTClient, mock_paho_client: MagicMock
    ) -> None:
        """Test status publishing with MQTT error."""
        mock_result = MagicMock()
        mock_result.rc = 1
        mock_paho_client.publish.return_value = mock_result

        status = {"speed": 50}

        with pytest.raises(MQTTPublishError, match="Failed to publish"):
            mqtt_client.publish_status(status)
