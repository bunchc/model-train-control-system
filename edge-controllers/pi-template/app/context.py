import yaml
import os
from mqtt_client import MQTTClient
from stepper_hat import StepperMotorHatController

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../pi-config.yaml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

TRAIN_ID = config.get('train_id', 'train_1')
MQTT_BROKER = config.get('mqtt_broker', {}).get('host', 'localhost')
MQTT_PORT = config.get('mqtt_broker', {}).get('port', 1883)
MQTT_USER = config.get('mqtt_broker', {}).get('username', None)
MQTT_PASS = config.get('mqtt_broker', {}).get('password', None)

STATUS_TOPIC = config.get('status_topic', f'trains/{TRAIN_ID}/status')
COMMANDS_TOPIC = config.get('commands_topic', f'trains/{TRAIN_ID}/commands')
