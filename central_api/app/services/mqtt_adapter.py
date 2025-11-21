"""MQTT client wrapper for train control communication.

This module provides an adapter for MQTT pub/sub operations used to
communicate with edge controllers. Commands are published to topics
and status updates are received from topics.

Topic Structure:
    trains/{train_id}/commands - Publish commands to edge controllers
    trains/{train_id}/status - Subscribe to status updates

Example:
    Publishing a command:

        >>> publish_command("train-001", {"action": "setSpeed", "speed": 75})
        True

    Getting train status:

        >>> status = get_train_status("train-001")
        >>> print(status.speed)
        75
"""

import json
import logging

from paho.mqtt import client as mqtt


logger = logging.getLogger("central_api.mqtt_adapter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


class MQTTAdapter:
    """MQTT client wrapper for train control system.

    Provides methods for connecting to MQTT broker, subscribing to topics,
    and publishing messages. Each adapter instance is associated with a
    specific train.

    Attributes:
        broker_address: MQTT broker hostname or IP address
        train_id: Unique identifier of the train
        client: Paho MQTT client instance

    Example:
        >>> adapter = MQTTAdapter("mqtt-broker", "train-001")
        >>> adapter.connect()
        >>> adapter.publish("trains/train-001/commands", '{"action":"stop"}')
    """

    def __init__(self, broker_address, train_id):
        """Initialize MQTT adapter.

        Args:
            broker_address: MQTT broker hostname or IP
            train_id: Unique train identifier
        """
        self.broker_address = broker_address
        self.train_id = train_id
        self.client = mqtt.Client()

    def connect(self):
        """Connect to MQTT broker.

        Establishes connection to the MQTT broker specified in broker_address.
        Logs connection success.
        """
        self.client.connect(self.broker_address)
        logger.info(f"Connected to MQTT broker at {self.broker_address}")

    def subscribe(self, topic, on_message):
        """Subscribe to MQTT topic.

        Args:
            topic: MQTT topic to subscribe to (e.g., 'trains/+/status')
            on_message: Callback function (client, userdata, message) => None
        """
        self.client.subscribe(topic)
        self.client.on_message = on_message
        logger.info(f"Subscribed to topic {topic}")

    def publish(self, topic, payload):
        """Publish message to MQTT topic.

        Args:
            topic: MQTT topic to publish to
            payload: Message payload (string, typically JSON)
        """
        self.client.publish(topic, payload)
        logger.info(f"Published to topic {topic}: {payload}")

    def loop_start(self):
        """Start MQTT client background loop.

        Starts background thread to handle MQTT network traffic.
        """
        self.client.loop_start()
        logger.debug("MQTT loop started")

    def loop_stop(self):
        """Stop MQTT client background loop.

        Stops the background thread.
        """
        self.client.loop_stop()
        logger.debug("MQTT loop stopped")


# Example publish_command and get_train_status functions
def publish_command(train_id, command):
    """Publish command to train via MQTT.

    Creates MQTT adapter, connects to broker, and publishes command
    to trains/{train_id}/commands topic.

    Args:
        train_id: Unique identifier of the train
        command: Command dict or Pydantic model with .dict() method
            Expected fields:
                - action: "setSpeed", "start", or "stop"
                - speed: Target speed 0-100 (for setSpeed action)

    Returns:
        True if command published successfully, False otherwise

    Example:
        >>> success = publish_command("train-001", {"action": "setSpeed", "speed": 75})
        >>> if success:
        ...     print("Command sent")
    """
    try:
        adapter = MQTTAdapter(broker_address="mqtt", train_id=train_id)
        adapter.connect()
        topic = f"trains/{train_id}/commands"
        payload = json.dumps(command.dict()) if hasattr(command, "dict") else json.dumps(command)
        adapter.publish(topic, payload)
    except Exception:
        logger.exception("MQTT publish error")
        return False
    else:
        logger.info(f"Command published for train {train_id}")
        return True


def get_train_status(train_id, local_testing=False):
    """Retrieve the real-time status of a train via MQTT.

    If local_testing is True, returns mock data for development.
    """
    from models.schemas import TrainStatus

    if local_testing:
        logger.info(f"Returning mock status for train {train_id}")
        return TrainStatus(
            train_id=train_id, speed=50, voltage=12.3, current=0.8, position="section_A"
        )
    status_topic = f"trains/{train_id}/status"
    result = {}
    received = False

    def on_message(_client, _userdata, msg):
        nonlocal received
        try:
            payload = json.loads(msg.payload.decode())
            # Validate payload keys
            required_keys = {"train_id", "speed", "voltage", "current", "position"}
            if not required_keys.issubset(payload.keys()):
                logger.error(f"Received status missing required keys: {payload}")
                return
            result.update(payload)
            received = True
            logger.debug(f"Received status message: {payload}")
        except Exception:
            logger.exception("Error decoding MQTT status")

    adapter = MQTTAdapter(broker_address="mqtt", train_id=train_id)
    try:
        adapter.connect()
        adapter.client.on_message = on_message
        adapter.client.subscribe(status_topic)
        adapter.client.loop_start()
        import time

        timeout = 3  # seconds
        start = time.time()
        while not received and time.time() - start < timeout:
            time.sleep(0.1)
    finally:
        adapter.client.loop_stop()

    if received:
        logger.info(f"Returning real status for train {train_id}")
        return TrainStatus(**result)
    logger.warning(f"No status received for train {train_id} after {timeout}s")
    return None
