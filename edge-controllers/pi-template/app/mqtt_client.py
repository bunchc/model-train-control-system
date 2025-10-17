import paho.mqtt.client as mqtt
import json
import logging

class MQTTClient:
    def __init__(self, broker_address, train_id):
        self.broker_address = broker_address
        self.train_id = train_id
        self.client = mqtt.Client()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def on_connect(self, client, userdata, flags, rc):
        logging.info(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(f"trains/{self.train_id}/commands")
        logging.info(f"Subscribed to topic: trains/{self.train_id}/commands")

    def on_message(self, client, userdata, message):
        command = json.loads(message.payload.decode())
        logging.info(f"Received command: {command}")
        self.handle_command(command)

    def handle_command(self, command):
        # Implement command handling logic here
        pass

    def publish_status(self, status):
        topic = f"trains/{self.train_id}/status"
        self.client.publish(topic, json.dumps(status))
        logging.info(f"Published status to {topic}: {status}")

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address)
        self.client.loop_start()