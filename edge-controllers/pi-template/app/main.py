"""Main entry point for edge controller application."""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Configuration management
from config.manager import ConfigManager, ConfigurationError
from mqtt_client import MQTTClient, MQTTClientError


# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)

# Check if running in local dev mode
LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"

# Hardware controllers - only import if not in local-dev mode
if not LOCAL_DEV:
    try:
        from stepper_hat import StepperMotorHatController

        HARDWARE_AVAILABLE = True
    except ImportError:
        HARDWARE_AVAILABLE = False
        logger.warning("Hardware modules not available, running in simulation mode")
else:
    HARDWARE_AVAILABLE = False
    logger.info("LOCAL_DEV mode enabled, running in simulation mode")


class StepperMotorSimulator:
    """Simulator for stepper motor when hardware is unavailable."""

    def start(self, speed: int) -> None:
        logger.info(f"[SIMULATION] start({speed}) called")

    def stop(self) -> None:
        logger.info("[SIMULATION] stop() called")

    def set_speed(self, speed: int) -> None:
        logger.info(f"[SIMULATION] set_speed({speed}) called")


class EdgeControllerApp:
    """Main application for edge controller."""

    def __init__(self):
        self.config_manager: Optional[ConfigManager] = None
        self.mqtt_client: Optional[MQTTClient] = None
        self.hardware_controller: Optional[Any] = None
        self.train_id: Optional[str] = None

    def initialize(self) -> bool:
        """Initialize application components.

        Returns:
            True if initialization successful, False otherwise
        """
        # Initialize configuration
        try:
            config_path = Path(__file__).parent / "edge-controller.conf"
            cached_config_path = Path(__file__).parent / "edge-controller.yaml"

            self.config_manager = ConfigManager(config_path, cached_config_path)
            service_config, runtime_config = self.config_manager.initialize()

        except ConfigurationError as e:
            logger.error(f"Configuration initialization failed: {e}")
            return False

        # Check if we have runtime configuration
        if runtime_config is None:
            logger.warning("=" * 60)
            logger.warning("Edge controller registered but no train configuration available.")
            logger.warning("Waiting for administrator to assign trains to this controller.")
            logger.warning("The controller will check periodically for configuration updates.")
            logger.warning("=" * 60)
            return True  # Valid state - waiting for config

        # Extract runtime configuration
        self.train_id = runtime_config.get("train_id")
        mqtt_broker = runtime_config.get("mqtt_broker", {})
        status_topic = runtime_config.get("status_topic", f"trains/{self.train_id}/status")
        commands_topic = runtime_config.get("commands_topic", f"trains/{self.train_id}/commands")

        # Initialize hardware controller
        if HARDWARE_AVAILABLE:
            try:
                from stepper_hat import StepperMotorHatController

                self.hardware_controller = StepperMotorHatController()
                logger.info("Hardware controller initialized")
            except Exception as e:
                logger.error(f"Failed to initialize hardware controller: {e}")
                return False
        else:
            self.hardware_controller = StepperMotorSimulator()
            logger.info("Running in simulation mode (no hardware)")

        # Initialize MQTT client
        try:
            central_api_host = service_config.get("central_api_host", "localhost")
            central_api_port = service_config.get("central_api_port", 8000)
            central_api_url = f"http://{central_api_host}:{central_api_port}"

            self.mqtt_client = MQTTClient(
                broker_host=mqtt_broker.get("host", "localhost"),
                broker_port=mqtt_broker.get("port", 1883),
                train_id=self.train_id,
                status_topic=status_topic,
                commands_topic=commands_topic,
                command_handler=self._handle_command,
                username=mqtt_broker.get("username"),
                password=mqtt_broker.get("password"),
                central_api_url=central_api_url,
            )

            self.mqtt_client.start()
            logger.info("MQTT client started successfully")

        except MQTTClientError as e:
            logger.error(f"Failed to start MQTT client: {e}")
            return False

        return True

    def _handle_command(self, command: Dict[str, Any]) -> None:
        """Handle incoming MQTT command.

        Args:
            command: Command dictionary from MQTT
        """
        logger.info(f"Received command: {command}")

        # Execute command on hardware
        self._execute_hardware_command(command)

    def _execute_hardware_command(self, command: Dict[str, Any]) -> None:
        """Execute command on hardware.

        Args:
            command: Command dictionary
        """
        action = command.get("action")

        try:
            if action == "start":
                speed = command.get("speed", 50)
                self.hardware_controller.start(speed)
                logger.info(f"Started motor at speed {speed}")

            elif action == "stop":
                self.hardware_controller.stop()
                logger.info("Stopped motor")

            elif action == "setSpeed":
                speed = command.get("speed", 50)
                self.hardware_controller.set_speed(speed)
                logger.info(f"Set speed to {speed}")

            else:
                logger.warning(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Hardware command execution failed: {e}")

    def run(self) -> None:
        """Run the main application loop."""
        try:
            logger.info("Edge controller running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down due to keyboard interrupt")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Cleanup and shutdown application."""
        logger.info("Shutting down edge controller")

        if self.mqtt_client:
            self.mqtt_client.stop()

        if self.hardware_controller and hasattr(self.hardware_controller, "cleanup"):
            self.hardware_controller.cleanup()


def main() -> None:
    """Application entry point."""
    logger.info("Starting edge controller and MQTT client.")
    logger.debug("[DEBUG TEST] If you see this, DEBUG logging is enabled.")

    app = EdgeControllerApp()

    if not app.initialize():
        logger.error("Failed to initialize application")
        sys.exit(1)

    app.run()


if __name__ == "__main__":
    main()
