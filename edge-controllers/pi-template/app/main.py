


import logging
import os
import sys
import time
from context import TRAIN_ID, MQTT_BROKER, STATUS_TOPIC, COMMANDS_TOPIC
from mqtt_client import MQTTClient
import controllers

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"

# Only import hardware modules if not in local-dev mode
if not LOCAL_DEV:
	from stepper_hat import StepperMotorHatController
else:
	class StepperMotorHatController:
		def start(self, speed):
			logging.info(f"[LOCAL DEV] start({speed}) called")
		def stop(self):
			logging.info("[LOCAL DEV] stop() called")
		def set_speed(self, speed):
			logging.info(f"[LOCAL DEV] set_speed({speed}) called")

def main():
	logging.info("Starting edge controller and MQTT client.")
	logging.debug("[DEBUG TEST] If you see this, DEBUG logging is enabled.")

	# Check if we have runtime configuration
	if TRAIN_ID is None:
		logging.warning("=" * 60)
		logging.warning("Edge controller registered but no train configuration available yet.")
		logging.warning("Waiting for administrator to assign trains to this controller.")
		logging.warning("The controller will check periodically for configuration updates.")
		logging.warning("=" * 60)
		
		# TODO: Implement periodic config check loop
		# For now, just sleep
		try:
			while True:
				time.sleep(60)
				logging.info("Still waiting for configuration...")
		except KeyboardInterrupt:
			logging.info("Edge controller shutting down due to keyboard interrupt.")
		return

	# Initialize singleton controller
	stepper_controller = StepperMotorHatController()
	mqtt_client = MQTTClient(
		MQTT_BROKER,
		TRAIN_ID,
		status_topic=STATUS_TOPIC,
		commands_topic=COMMANDS_TOPIC,
		stepper_controller=stepper_controller
	)
	controllers.mqtt_client = mqtt_client

	try:
		mqtt_client.start()
		logging.info("MQTT client started and waiting for MQTT messages.")
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info("Edge controller shutting down due to keyboard interrupt.")
	except Exception as e:
		logging.error(f"Failed to start MQTTClient: {e}")
		sys.exit(1)

if __name__ == "__main__":
	main()
