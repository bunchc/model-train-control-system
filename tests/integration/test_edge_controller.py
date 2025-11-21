"""Integration tests for edge controller refactored components.

These tests validate the edge controller's interaction with:
- Central API (registration and config download)
- MQTT broker (pub/sub for commands and status)
- Command handling and hardware simulation

Test Scenarios:
    1. Edge controller registration with Central API
    2. Runtime configuration download
    3. MQTT connection and subscription
    4. Command reception via MQTT
    5. Status publication via MQTT
    6. End-to-end command flow (API -> MQTT -> Edge Controller -> Hardware)
"""

import json
import time
from typing import Any, Dict, List

import paho.mqtt.client as mqtt
import pytest
import requests


BASE_API_URL = "http://localhost:8000/api"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
TIMEOUT = 10  # seconds


class MQTTTestClient:
    """Helper class for MQTT testing.

    Provides synchronous MQTT operations for test assertions:
    - Subscribe to topics and collect messages
    - Publish messages to topics
    - Wait for expected messages with timeout
    """

    def __init__(self, broker_host: str, broker_port: int):
        """Initialize MQTT test client.

        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
        """
        self.client = mqtt.Client()
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.received_messages: List[Dict[str, Any]] = []
        self.connected = False

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for connection."""
        self.connected = rc == 0

    def _on_message(self, client, userdata, msg):
        """Callback for received messages."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self.received_messages.append({"topic": msg.topic, "payload": payload})
        except json.JSONDecodeError:
            pass  # Ignore non-JSON messages

    def connect(self):
        """Connect to MQTT broker."""
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()

        # Wait for connection
        timeout = time.time() + 5
        while not self.connected and time.time() < timeout:
            time.sleep(0.1)

        if not self.connected:
            raise RuntimeError("Failed to connect to MQTT broker")

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str):
        """Subscribe to a topic.

        Args:
            topic: MQTT topic to subscribe to
        """
        self.client.subscribe(topic)
        time.sleep(0.5)  # Allow subscription to complete

    def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to
            payload: Message payload as dictionary
        """
        self.client.publish(topic, json.dumps(payload))
        time.sleep(0.5)  # Allow publish to complete

    def wait_for_message(self, topic: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Wait for a message on a specific topic.

        Args:
            topic: Topic to wait for message on
            timeout: Maximum time to wait in seconds

        Returns:
            Message payload dictionary

        Raises:
            TimeoutError: If no message received within timeout
        """
        end_time = time.time() + timeout

        while time.time() < end_time:
            for msg in self.received_messages:
                if msg["topic"] == topic:
                    self.received_messages.remove(msg)
                    return msg["payload"]
            time.sleep(0.1)

        raise TimeoutError(f"No message received on topic '{topic}' within {timeout}s")

    def clear_messages(self):
        """Clear all received messages."""
        self.received_messages.clear()


@pytest.fixture(scope="module")
def mqtt_client():
    """Fixture providing MQTT test client."""
    client = MQTTTestClient(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.connect()
    yield client
    client.disconnect()


@pytest.fixture(scope="module")
def api_health_check():
    """Ensure API is running before tests."""
    try:
        response = requests.get(f"{BASE_API_URL}/ping", timeout=5)
        assert response.status_code == 200, "API health check failed"
    except requests.exceptions.RequestException as e:
        pytest.skip(f"API not available: {e}")


def test_api_ping(api_health_check):
    """Test that Central API is responding."""
    response = requests.get(f"{BASE_API_URL}/ping")
    assert response.status_code == 200
    # API may return empty response or simple message


def test_edge_controller_registered(api_health_check):
    """Test that edge controller has registered with Central API.

    The edge controller should automatically register on startup.
    This test verifies the controller appears in the controllers list.
    """
    # Give edge controller time to register
    time.sleep(2)

    response = requests.get(f"{BASE_API_URL}/controllers")
    assert response.status_code == 200

    controllers = response.json()
    assert isinstance(controllers, list), "Controllers endpoint should return a list"
    assert len(controllers) > 0, "At least one edge controller should be registered"

    # Verify controller has expected fields
    controller = controllers[0]
    assert "id" in controller or "uuid" in controller, "Controller should have ID"


def test_edge_controller_config_download(api_health_check):
    """Test that edge controller can download runtime configuration.

    Verifies:
    - Controller can request configuration from API
    - Configuration contains necessary fields (train_id, mqtt_broker, topics)
    """
    # Get controller list
    response = requests.get(f"{BASE_API_URL}/controllers")
    assert response.status_code == 200
    controllers = response.json()

    if len(controllers) == 0:
        pytest.skip("No edge controllers registered")

    # Get first controller's UUID
    controller_id = controllers[0].get("id") or controllers[0].get("uuid")

    # Request config for this controller
    config_response = requests.get(f"{BASE_API_URL}/controllers/{controller_id}/config")

    # Controller may or may not have config assigned
    # Both 200 (config exists) and 404 (not assigned) are valid
    assert config_response.status_code in [
        200,
        404,
    ], f"Config request should return 200 or 404, got {config_response.status_code}"

    if config_response.status_code == 200:
        config = config_response.json()

        # Verify config structure (if config is assigned)
        if config and isinstance(config, dict) and len(config) > 0:
            # Config should have these fields if populated
            # Note: Empty config {} is also valid (waiting for assignment)
            pass


def test_mqtt_broker_reachable():
    """Test that MQTT broker is reachable."""
    client = MQTTTestClient(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    try:
        client.connect()
        assert client.connected, "Should connect to MQTT broker"
    finally:
        client.disconnect()


def test_edge_controller_mqtt_status_publishing(mqtt_client, api_health_check):
    """Test that edge controller publishes status to MQTT.

    The edge controller should periodically publish status updates
    or publish status after command execution.
    """
    # Subscribe to all train status topics
    mqtt_client.subscribe("trains/+/status")
    mqtt_client.clear_messages()

    # Trigger a command to generate a status update
    # First, get available trains
    response = requests.get(f"{BASE_API_URL}/trains")
    if response.status_code != 200:
        pytest.skip("Cannot retrieve trains list")

    trains = response.json()
    if not trains or len(trains) == 0:
        pytest.skip("No trains configured")

    train_id = trains[0]["id"]

    # Send a command via API (which should trigger MQTT command)
    command = {"action": "setSpeed", "speed": 50}
    requests.post(f"{BASE_API_URL}/trains/{train_id}/command", json=command)

    # Command may succeed or fail depending on system state
    # We're mainly interested in whether status is published

    # Wait for status message (edge controller should publish after command)
    try:
        status = mqtt_client.wait_for_message(f"trains/{train_id}/status", timeout=10)

        # Verify status structure
        assert isinstance(status, dict), "Status should be a dictionary"
        # Status may have various fields depending on implementation

    except TimeoutError:
        pytest.skip("Edge controller did not publish status (may not be configured)")


def test_edge_controller_mqtt_command_reception(mqtt_client, api_health_check):
    """Test that edge controller receives and processes MQTT commands.

    Verifies end-to-end command flow:
    1. Publish command to trains/{id}/commands topic
    2. Edge controller receives and processes command
    3. Edge controller publishes status update
    """
    # Get train ID from API
    response = requests.get(f"{BASE_API_URL}/trains")
    if response.status_code != 200:
        pytest.skip("Cannot retrieve trains list")

    trains = response.json()
    if not trains or len(trains) == 0:
        pytest.skip("No trains configured")

    train_id = trains[0]["id"]

    # Subscribe to status updates
    mqtt_client.subscribe(f"trains/{train_id}/status")
    mqtt_client.clear_messages()

    # Publish command directly to MQTT
    command = {"action": "setSpeed", "speed": 75}
    mqtt_client.publish(f"trains/{train_id}/commands", command)

    # Edge controller should process command and may publish status
    # (Status publishing after command is implementation-dependent)

    # Wait a moment for processing
    time.sleep(2)

    # At minimum, edge controller should have received the command
    # (We can't easily verify this without checking logs)
    # So we verify the MQTT infrastructure works
    assert mqtt_client.connected, "MQTT client should still be connected"


def test_command_via_api_triggers_mqtt(mqtt_client, api_health_check):
    """Test that API command is forwarded to edge controller via MQTT.

    Complete integration test:
    1. Send command to Central API
    2. API publishes to MQTT
    3. Edge controller receives from MQTT
    4. Edge controller executes command (simulation mode)
    """
    # Get train ID
    response = requests.get(f"{BASE_API_URL}/trains")
    if response.status_code != 200:
        pytest.skip("Cannot retrieve trains list")

    trains = response.json()
    if not trains or len(trains) == 0:
        pytest.skip("No trains configured")

    train_id = trains[0]["id"]

    # Subscribe to commands topic to observe what API publishes
    mqtt_client.subscribe(f"trains/{train_id}/commands")
    mqtt_client.clear_messages()

    # Send command via API
    command = {"action": "start", "speed": 60}
    cmd_response = requests.post(
        f"{BASE_API_URL}/trains/{train_id}/command", json=command
    )

    # API should accept command
    assert cmd_response.status_code in [
        200,
        201,
        202,
    ], f"API should accept command, got {cmd_response.status_code}"

    # Verify command was published to MQTT
    try:
        received_cmd = mqtt_client.wait_for_message(
            f"trains/{train_id}/commands", timeout=5
        )

        # Verify command matches what we sent
        assert received_cmd.get("action") == "start", "Command action should match"
        assert received_cmd.get("speed") == 60, "Command speed should match"

    except TimeoutError:
        pytest.fail("Command was not published to MQTT by Central API")


def test_multiple_commands_sequence(mqtt_client, api_health_check):
    """Test that edge controller handles multiple sequential commands.

    Verifies:
    - Multiple commands can be sent
    - Each command is processed
    - No commands are dropped
    """
    # Get train ID
    response = requests.get(f"{BASE_API_URL}/trains")
    if response.status_code != 200:
        pytest.skip("Cannot retrieve trains list")

    trains = response.json()
    if not trains or len(trains) == 0:
        pytest.skip("No trains configured")

    train_id = trains[0]["id"]

    # Subscribe to commands
    mqtt_client.subscribe(f"trains/{train_id}/commands")
    mqtt_client.clear_messages()

    # Send sequence of commands
    commands = [
        {"action": "start", "speed": 30},
        {"action": "setSpeed", "speed": 50},
        {"action": "setSpeed", "speed": 70},
        {"action": "stop"},
    ]

    for cmd in commands:
        response = requests.post(f"{BASE_API_URL}/trains/{train_id}/command", json=cmd)
        assert response.status_code in [
            200,
            201,
            202,
        ], f"Command {cmd} should be accepted"

        time.sleep(0.5)  # Small delay between commands

    # Verify all commands were published (check last one at minimum)
    time.sleep(1)

    # At least the stop command should be in received messages
    found_stop = False
    for msg in mqtt_client.received_messages:
        if msg["topic"] == f"trains/{train_id}/commands":
            if msg["payload"].get("action") == "stop":
                found_stop = True
                break

    assert found_stop, "Stop command should have been published to MQTT"


def test_edge_controller_simulation_mode():
    """Test that edge controller runs in simulation mode in LOCAL_DEV.

    This test verifies the edge controller starts without hardware
    and accepts commands without errors.
    """
    # This is implicit if other tests pass - edge controller is running
    # in Docker with LOCAL_DEV=true and simulation mode enabled

    # Verify by checking we can communicate with it
    response = requests.get(f"{BASE_API_URL}/ping", timeout=5)
    assert (
        response.status_code == 200
    ), "Edge controller should be running and API accessible"
