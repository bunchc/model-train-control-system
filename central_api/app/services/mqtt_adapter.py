from paho.mqtt import client as mqtt
import json
import logging

logger = logging.getLogger("central_api.mqtt_adapter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

class MQTTAdapter:
    def __init__(self, broker_address, train_id):
        self.broker_address = broker_address
        self.train_id = train_id
        self.client = mqtt.Client()

    def connect(self):
        self.client.connect(self.broker_address)
        logger.info(f"Connected to MQTT broker at {self.broker_address}")

    def subscribe(self, topic, on_message):
        self.client.subscribe(topic)
        self.client.on_message = on_message
        logger.info(f"Subscribed to topic {topic}")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)
        logger.info(f"Published to topic {topic}: {payload}")

    def loop_start(self):
        self.client.loop_start()
        logger.debug("MQTT loop started")

    def loop_stop(self):
        self.client.loop_stop()
        logger.debug("MQTT loop stopped")

# Example publish_command and get_train_status functions
def publish_command(train_id, command):
    try:
        adapter = MQTTAdapter(broker_address="mqtt", train_id=train_id)
        adapter.connect()
        topic = f"trains/{train_id}/commands"
        if hasattr(command, 'dict'):
            payload = json.dumps(command.dict())
        else:
            payload = json.dumps(command)
        adapter.publish(topic, payload)
        logger.info(f"Command published for train {train_id}")
        return True
    except Exception as e:
        logger.error(f"MQTT publish error: {e}")
        return False

def get_train_status(train_id, local_testing=False):
    """
    Retrieve the real-time status of a train via MQTT.
    If local_testing is True, returns mock data for development.
    """
    from models.schemas import TrainStatus
    if local_testing:
        logger.info(f"Returning mock status for train {train_id}")
        return TrainStatus(
            train_id=train_id,
            speed=50,
            voltage=12.3,
            current=0.8,
            position="section_A"
        )
    status_topic = f"trains/{train_id}/status"
    result = {}
    received = False

    def on_message(client, userdata, msg):
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
        except Exception as e:
            logger.error(f"Error decoding MQTT status: {e}")

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
    else:
        logger.warning(f"No status received for train {train_id} after {timeout}s")
        return None