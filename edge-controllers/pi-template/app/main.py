



import logging
from fastapi import FastAPI
import controllers
from context import CONFIG_PATH, TRAIN_ID, MQTT_BROKER, STATUS_TOPIC, COMMANDS_TOPIC
from stepper_hat import StepperMotorHatController
from mqtt_client import MQTTClient
import sys
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

logging.info("Starting edge controller and MQTT client.")
logging.debug("[DEBUG TEST] If you see this, DEBUG logging is enabled.")

# Initialize singleton controller

stepper_controller = StepperMotorHatController()
mqtt_client = MQTTClient(MQTT_BROKER, TRAIN_ID, status_topic=STATUS_TOPIC, commands_topic=COMMANDS_TOPIC, stepper_controller=stepper_controller)
controllers.mqtt_client = mqtt_client

try:
	mqtt_client.start()
	logging.info("MQTT client started and waiting for MQTT messages.")
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info("Edge controller shutting down due to keyboard interrupt.")
except Exception as e:
	logging.error(f"Failed to start MQTTClient: {e}")
	sys.exit(1)
