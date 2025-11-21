"""Main entry point for edge controller application.

This module provides the EdgeControllerApp class which orchestrates the entire
edge controller lifecycle including:
- Configuration initialization (service and runtime configs)
- Hardware controller setup (GPIO or simulation mode)
- MQTT client initialization and command handling
- Main application loop and graceful shutdown

The application supports both production mode (with real hardware) and simulation
mode (LOCAL_DEV=true) for development and testing without physical hardware.

Typical usage:
    python app/main.py

Or in simulation mode:
    LOCAL_DEV=true python app/main.py
"""

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
    """Simulator for stepper motor when hardware is unavailable.

    This class provides a drop-in replacement for StepperMotorHatController
    when running in LOCAL_DEV mode or when hardware modules are not available.
    All methods log their calls but perform no actual hardware operations.

    This enables:
    - Development without physical Raspberry Pi hardware
    - Testing on non-ARM platforms (x86, macOS, etc.)
    - CI/CD pipeline execution without hardware dependencies
    """

    def start(self, speed: int) -> None:
        """Simulate starting the motor.

        Args:
            speed: Motor speed (0-100)
        """
        logger.info(f"[SIMULATION] start({speed}) called")

    def stop(self) -> None:
        """Simulate stopping the motor."""
        logger.info("[SIMULATION] stop() called")

    def set_speed(self, speed: int) -> None:
        """Simulate setting motor speed.

        Args:
            speed: Motor speed (0-100)
        """
        logger.info(f"[SIMULATION] set_speed({speed}) called")


class EdgeControllerApp:
    """Main application for edge controller.

    This class orchestrates the entire edge controller application lifecycle:

    Architecture:
        1. Configuration Management: Loads service config and downloads/caches runtime config
        2. Hardware Initialization: Sets up GPIO controllers or simulation mode
        3. MQTT Communication: Establishes pub/sub with broker for commands and status
        4. Command Handling: Processes incoming MQTT commands and executes on hardware
        5. Graceful Shutdown: Cleans up resources on exit

    Attributes:
        config_manager: Manages service and runtime configuration
        mqtt_client: Handles MQTT pub/sub communication
        hardware_controller: Controls physical hardware or simulation
        train_id: Identifier for the train this controller manages

    Example:
        >>> app = EdgeControllerApp()
        >>> if app.initialize():
        ...     app.run()
    """

    def __init__(self) -> None:
        """Initialize the edge controller application.

        Sets all attributes to None. Actual initialization happens in initialize()
        to allow for proper error handling and logging.
        """
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

        This is the callback function registered with MQTTClient. It receives
        validated command dictionaries from MQTT messages and delegates to
        hardware execution.

        Command Flow:
            1. MQTT message received on commands_topic
            2. MQTTClient validates JSON and calls this handler
            3. Command is logged for audit trail
            4. Command is delegated to _execute_hardware_command()

        Args:
            command: Command dictionary with 'action' key and optional parameters.
                Expected format: {'action': 'start|stop|setSpeed', 'speed': int}

        Note:
            This method does not raise exceptions. All errors are caught and
            logged in _execute_hardware_command() to prevent MQTT callback failures.
        """
        logger.info(f"Received command: {command}")

        # Execute command on hardware
        self._execute_hardware_command(command)

    def _execute_hardware_command(self, command: Dict[str, Any]) -> None:
        """Execute command on hardware controller.

        This method translates MQTT command payloads into hardware controller
        method calls. It implements the command routing logic and error handling.

        Supported Commands:
            - {'action': 'start', 'speed': 50}: Start motor at specified speed
            - {'action': 'stop'}: Stop motor immediately
            - {'action': 'setSpeed', 'speed': 75}: Change motor speed

        Args:
            command: Command dictionary containing:
                - action (str): Required. Command type (start|stop|setSpeed)
                - speed (int): Optional. Motor speed 0-100 (default: 50)

        Error Handling:
            - Unknown actions are logged as warnings and ignored
            - Hardware exceptions are caught, logged, and do not propagate
            - This ensures MQTT callback chain remains stable

        Side Effects:
            - Modifies hardware controller state (motor speed, direction)
            - Logs all command executions and errors

        Example:
            >>> self._execute_hardware_command({'action': 'start', 'speed': 60})
            # Logs: "Started motor at speed 60"
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
