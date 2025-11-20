import paho.mqtt.client as mqtt
import json
import logging

class MQTTClient:
    def __init__(self, broker_address, train_id, status_topic=None, commands_topic=None, stepper_controller=None):
        self.broker_address = broker_address
        self.train_id = train_id
        self.status_topic = status_topic or f"trains/{train_id}/status"
        self.commands_topic = commands_topic or f"trains/{train_id}/commands"
        self.client = mqtt.Client()
        self.setup_logging()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.stepper_controller = stepper_controller

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"Successfully connected to MQTT broker {self.broker_address} (rc={rc})")
        else:
            logging.error(f"Failed to connect to MQTT broker {self.broker_address} (rc={rc})")
        result, mid = client.subscribe(self.commands_topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"Subscribed to topic: {self.commands_topic}")
        else:
            logging.error(f"Failed to subscribe to topic: {self.commands_topic} (result={result})")
    def on_disconnect(self, client, userdata, rc):
        if rc == 0:
            logging.info(f"Disconnected cleanly from MQTT broker {self.broker_address}")
        else:
            logging.warning(f"Unexpected disconnect from MQTT broker {self.broker_address} (rc={rc})")

    def on_message(self, client, userdata, message):
        payload = message.payload.decode()
        logging.info(f"MQTT message received on topic '{message.topic}': {payload}")
        try:
            command = json.loads(payload)
            self.handle_command(command)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding MQTT message as JSON: {e}. Raw payload: {payload}")
        except Exception as e:
            logging.error(f"Unexpected error processing MQTT message: {e}. Raw payload: {payload}")

    def handle_command(self, command):
        logging.info(f"Edge controller received command: {command}")
        try:
            stepper = self.stepper_controller
            status = {
                "train_id": self.train_id,
                "speed": None,
                "voltage": 12.0,
                "current": 0.0,
                "position": "unknown"
            }
            if command.get('action') == 'start':
                speed = command.get('speed', 50)
                logging.info(f"Starting train 1 (M1) at speed {speed}")
                stepper.start(speed)
                status["speed"] = speed
                status["position"] = "started"
                self.publish_status(status)
            elif command.get('action') == 'stop':
                logging.info("Stopping train 1 (M1)")
                stepper.stop()
                status["speed"] = 0
                status["position"] = "stopped"
                self.publish_status(status)
            elif command.get('action') == 'setSpeed' and 'speed' in command:
                speed = command['speed']
                logging.info(f"Setting train 1 (M1) speed to {speed}")
                stepper.set_speed(speed)
                status["speed"] = speed
                status["position"] = "speed_set"
                self.publish_status(status)
            else:
                logging.warning(f"Unknown or invalid command: {command}")
        except Exception as e:
            logging.error(f"Exception in handle_command: {e}")

    def publish_status(self, status):
        logging.debug(f"publish_status called. Client connected: {self.client.is_connected()}, topic: {self.status_topic}, payload: {status}")
        # Publish to MQTT as before
        try:
            result = self.client.publish(self.status_topic, json.dumps(status))
            logging.debug(f"Publish result object: {result}")
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Published status to {self.status_topic}: {status}")
            else:
                logging.error(f"Failed to publish status to {self.status_topic}: {status} (result={result.rc})")
        except Exception as e:
            logging.error(f"Exception during publish_status: {e}")

        # Also push status to central API /status/update
        try:
            import requests
            api_url = "http://central_api:8000/api/status/update"  # Use docker compose service name or localhost if running locally
            resp = requests.post(api_url, json=status, timeout=2)
            if resp.status_code == 200:
                logging.info(f"Pushed status to central API: {status}")
            else:
                logging.error(f"Failed to push status to central API: {resp.status_code} {resp.text}")
        except Exception as e:
            logging.error(f"Exception during HTTP push to central API: {e}")

    def start(self):
        try:
            logging.info(f"Connecting to MQTT broker at {self.broker_address}...")
            self.client.connect(self.broker_address)
            self.client.loop_start()
            logging.info("MQTT client network loop started.")
        except Exception as e:
            logging.error(f"Exception during MQTT client start: {e}")