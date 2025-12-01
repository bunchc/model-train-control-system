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

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Configuration management
from .config.manager import ConfigManager, ConfigurationError
from .mqtt_client import MQTTClient, MQTTClientError


# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)

# Check if running in local dev mode
LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"

# Hardware controllers - only import if not in local-dev mode
if not LOCAL_DEV:
    try:
        from .dc_motor_hat import DCMotorHatController  # noqa: F401

        HARDWARE_AVAILABLE = True
    except ImportError:
        HARDWARE_AVAILABLE = False
        logger.warning("Hardware modules not available, running in simulation mode")
else:
    HARDWARE_AVAILABLE = False
    logger.info("LOCAL_DEV mode enabled, running in simulation mode")


class DCMotorSimulator:
    """Simulator for DC motor when hardware is unavailable.

    This class provides a drop-in replacement for DCMotorHatController
    when running in LOCAL_DEV mode or when hardware modules are not available.
    All methods log their calls but perform no actual hardware operations.

    This enables:
    - Development without physical Raspberry Pi hardware
    - Testing on non-ARM platforms (x86, macOS, etc.)
    - CI/CD pipeline execution without hardware dependencies
    """

    def start(self, speed: int = 50, direction: int = 1) -> None:
        """Simulate starting the motor.

        Args:
            speed: Motor speed (0-100)
            direction: Motor direction (1=forward, 0=reverse)
        """
        logger.info(f"[SIMULATION] start(speed={speed}, direction={direction}) called")

    def stop(self) -> None:
        """Simulate stopping the motor."""
        logger.info("[SIMULATION] stop() called")

    def set_speed(self, speed: int) -> None:
        """Simulate setting motor speed.

        Args:
            speed: Motor speed (0-100)
        """
        logger.info(f"[SIMULATION] set_speed({speed}) called")

    def set_direction(self, direction: int) -> None:
        """Simulate setting motor direction.

        Args:
            direction: Motor direction (1=forward, 0=reverse)
        """
        logger.info(f"[SIMULATION] set_direction({direction}) called")


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
        self.speed_task: Optional[asyncio.Task] = None  # Track speed ramping task

    def initialize(self) -> bool:  # noqa: PLR0915
        """Initialize edge controller components.

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("EDGE CONTROLLER INITIALIZATION STARTED")
        logger.info("=" * 60)
        logger.info(f"Environment: LOCAL_DEV={LOCAL_DEV}")
        logger.info(f"Hardware Available: {HARDWARE_AVAILABLE}")

        # Initialize configuration
        try:
            # Check for config file in mounted location first, then fall back to app directory
            mounted_config = Path("/app/edge-controller.conf")
            if mounted_config.exists():
                config_path = mounted_config
            else:
                config_path = Path(__file__).parent / "edge-controller.conf"

            cached_config_path = Path(__file__).parent / "edge-controller.yaml"

            logger.info(f"Loading service config from: {config_path}")
            logger.info(f"Cached runtime config path: {cached_config_path}")

            # Load service config and download/cache runtime config
            self.config_manager = ConfigManager(config_path, cached_config_path)
            logger.info("Initializing configuration manager...")
            service_config, runtime_config = self.config_manager.initialize()
            logger.info("✓ Configuration manager initialized successfully")

        except ConfigurationError:
            # Critical error - cannot proceed (service config missing or API unreachable with no cache)
            logger.exception("=" * 60)
            logger.exception("CRITICAL ERROR: Configuration initialization failed")
            logger.exception("Configuration error")
            logger.exception("=" * 60)
            return False

        # Check if we have runtime configuration
        # runtime_config will be None if controller is registered but not assigned to a train
        if runtime_config is None:
            # Valid state: Controller is registered but waiting for admin to assign trains
            # In production, implement a polling loop to check for config updates
            logger.warning("=" * 60)
            logger.warning("Edge controller registered but no train configuration available.")
            logger.warning("Waiting for administrator to assign trains to this controller.")
            logger.warning("The controller will check periodically for configuration updates.")
            logger.warning("=" * 60)
            return True  # Valid state - waiting for config

        # Extract runtime configuration
        logger.info("Extracting runtime configuration...")
        self.train_id = runtime_config.get("train_id")
        logger.info(f"✓ Assigned to train: {self.train_id}")
        mqtt_broker = runtime_config.get("mqtt_broker", {})
        status_topic = runtime_config.get("status_topic", f"trains/{self.train_id}/status")
        commands_topic = runtime_config.get("commands_topic", f"trains/{self.train_id}/commands")

        logger.info("MQTT Configuration:")
        logger.info(
            f"  Broker: {mqtt_broker.get('host', 'localhost')}:{mqtt_broker.get('port', 1883)}"
        )
        logger.info(f"  Status Topic: {status_topic}")
        logger.info(f"  Commands Topic: {commands_topic}")

        # Initialize hardware controller
        logger.info("Initializing hardware controller...")
        if HARDWARE_AVAILABLE:
            try:
                from .dc_motor_hat import DCMotorHatController

                # Get motor port from environment (default to 1 for M1)
                motor_port = int(os.getenv("MOTOR_PORT", "1"))
                logger.info(f"Motor port configured: M{motor_port}")

                self.hardware_controller = DCMotorHatController(motor_num=motor_port)
                logger.info(f"✓ Hardware controller initialized (DC Motor M{motor_port})")
            except Exception:
                logger.exception("✗ Failed to initialize hardware controller")
                return False
        else:
            self.hardware_controller = DCMotorSimulator()
            logger.info("✓ Hardware controller initialized (SIMULATION MODE)")

        # Initialize MQTT client
        logger.info("Setting up MQTT client...")
        try:
            # Construct Central API URL for HTTP fallback (status publishing)
            central_api_host = service_config.get("central_api_host", "localhost")
            central_api_port = service_config.get("central_api_port", 8000)
            central_api_url = f"http://{central_api_host}:{central_api_port}"
            logger.info(f"Central API URL: {central_api_url}")

            # Create MQTT client with connection details from runtime config
            logger.info("Creating MQTT client instance...")
            self.mqtt_client = MQTTClient(
                broker_host=mqtt_broker.get("host", "localhost"),
                broker_port=mqtt_broker.get("port", 1883),
                train_id=self.train_id,
                status_topic=status_topic,  # Publish: trains/{train_id}/status
                commands_topic=commands_topic,  # Subscribe: trains/{train_id}/commands
                command_handler=self._handle_command,  # Callback for incoming commands
                username=mqtt_broker.get("username"),  # Optional authentication
                password=mqtt_broker.get("password"),  # Optional authentication
                central_api_url=central_api_url,  # HTTP fallback for status
            )

            # Connect to broker and subscribe to commands topic
            # This is blocking until connection succeeds or timeout
            logger.info("Connecting to MQTT broker...")
            self.mqtt_client.start()
            logger.info("✓ MQTT client started successfully")
            logger.info(f"✓ Subscribed to commands on: {commands_topic}")
            logger.info(f"✓ Publishing status to: {status_topic}")

        except MQTTClientError:
            # MQTT connection failed - cannot proceed without real-time communication
            logger.exception("=" * 60)
            logger.exception("CRITICAL ERROR: MQTT connection failed")
            logger.exception("MQTT connection error")
            logger.exception("=" * 60)
            return False

        logger.info("=" * 60)
        logger.info("✓ EDGE CONTROLLER INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        return True

    def _handle_command(self, command: dict[str, Any]) -> None:
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
        logger.info("=" * 40)
        logger.info(f">>> COMMAND RECEIVED: {command}")
        logger.info("=" * 40)

        # For setSpeed commands, use async speed ramping
        action = command.get("action")
        if action == "setSpeed" or ("speed" in command and action is None):
            speed = command.get("speed")
            if speed is not None:
                # Cancel any existing speed ramp
                if self.speed_task and not self.speed_task.done():
                    self.speed_task.cancel()
                # Schedule async task for speed ramping
                try:
                    # Get the running event loop and schedule the coroutine
                    loop = asyncio.get_event_loop()
                    future = asyncio.run_coroutine_threadsafe(
                        self._handle_speed_command(speed), loop
                    )
                    self.speed_task = future
                except RuntimeError:
                    logger.exception("Failed to schedule speed ramping")
                    # Fall back to synchronous execution
                    self._execute_hardware_command(command)
                return

        # Execute other commands on hardware
        self._execute_hardware_command(command)

    async def _handle_speed_command(self, target_speed: int) -> None:
        """Handle speed command with gradual ramping.

        Uses the same speed ramping logic as the HTTP controller
        but updates train_status and publishes status via MQTT.

        Args:
            target_speed: Target speed (0-100)
        """
        try:
            # Import here to avoid circular imports
            from .controllers import train_status

            logger.info(f"Starting speed ramp to {target_speed}")

            # Use the speed ramping from controllers.py but with MQTT publishing
            current_speed = train_status["speed"]
            speed_diff = target_speed - current_speed

            if speed_diff == 0:
                logger.info(f"Speed already at target: {target_speed}")
                return

            # Calculate timing: 3 seconds total, steps of 1 speed unit
            total_steps = abs(speed_diff)
            step_delay = 3.0 / total_steps if total_steps > 0 else 0
            step_direction = 1 if speed_diff > 0 else -1

            logger.info(
                f"Speed ramp: {current_speed} -> {target_speed} over 3 seconds ({total_steps} steps)"
            )

            # Ramp through intermediate speeds
            for step in range(1, total_steps + 1):
                new_speed = current_speed + (step * step_direction)
                train_status["speed"] = new_speed

                # Update hardware controller
                self.hardware_controller.set_speed(new_speed)

                # Publish intermediate status via MQTT
                logger.debug(f"Ramping speed to {new_speed}")
                self._publish_current_status()

                # Wait before next step (except on final step)
                if step < total_steps:
                    await asyncio.sleep(step_delay)

            logger.info(f"Speed ramp completed: final speed = {target_speed}")

        except Exception:
            logger.exception("Error in speed ramp command")
            # Publish current status even if there was an error
            self._publish_current_status()

    def _execute_hardware_command(self, command: dict[str, Any]) -> None:
        """Execute command on hardware controller.

        This method translates MQTT command payloads into hardware controller
        method calls. It implements the command routing logic and error handling.

        Supported Commands:
            - {'action': 'start', 'speed': 50, 'direction': 'FORWARD'}: Start motor at specified speed and direction
            - {'action': 'stop'}: Stop motor immediately
            - {'action': 'setSpeed', 'speed': 75, 'direction': 'BACKWARD'}: Change motor speed and direction
            - {'action': 'setDirection', 'direction': 'FORWARD'}: Change motor direction

        Args:
            command: Command dictionary containing:
                - action (str): Required. Command type (start|stop|setSpeed|setDirection)
                - speed (int): Optional. Motor speed 0-100 (default: 50)
                - direction (str|int): Optional. Motor direction "FORWARD"/"BACKWARD" or 1/0 (default: "FORWARD")

        Error Handling:
            - Unknown actions are logged as warnings and ignored
            - Hardware exceptions are caught, logged, and do not propagate
            - This ensures MQTT callback chain remains stable

        Side Effects:
            - Modifies hardware controller state (motor speed, direction)
            - Logs all command executions and errors

        Example:
            >>> self._execute_hardware_command(
            ...     {"action": "start", "speed": 60, "direction": "BACKWARD"}
            ... )
            # Logs: "Started motor at speed 60"

        Note:
            Command routing follows a simple if/elif chain for clarity.
            More complex routing would use command pattern or strategy pattern.
        """
        # Extract action from command payload
        action = command.get("action")

        # Handle speed-only commands (backwards compatibility)
        if action is None and "speed" in command:
            action = "setSpeed"

        # Helper function to normalize direction parameter
        def normalize_direction(direction_param: Any) -> int:
            """Convert direction parameter to integer (1=forward, 0=reverse).

            Accepts:
                - String: "FORWARD" or "BACKWARD"
                - Integer: 1 (forward) or 0 (reverse)
                - None: defaults to 1 (forward)
            """
            if direction_param is None:
                return 1  # Default to forward
            if isinstance(direction_param, str):
                return 1 if direction_param.upper() == "FORWARD" else 0
            return int(direction_param)  # Pass through integers

        # Execute hardware action with exception isolation
        # Each exception is caught to prevent MQTT callback failures
        try:
            # Command: start motor at specified speed and direction
            if action == "start":
                speed = command.get("speed", 50)  # Default to 50% if not specified
                direction = normalize_direction(command.get("direction"))
                logger.info(
                    f"Executing START command (speed={speed}, direction={'forward' if direction == 1 else 'reverse'})..."
                )
                self.hardware_controller.start(speed, direction)
                logger.info(
                    f"✓ Motor started at speed {speed} ({'forward' if direction == 1 else 'reverse'})"
                )
                # Publish status update after command execution
                self._publish_current_status()

            # Command: stop motor immediately
            elif action == "stop":
                logger.info("Executing STOP command...")
                self.hardware_controller.stop()
                logger.info("✓ Motor stopped")
                # Publish status update after command execution
                self._publish_current_status()

            # Command: change speed without stopping
            elif action == "setSpeed":
                speed = command.get("speed", 50)  # Default to 50% if not specified
                # If direction is provided with setSpeed, change direction first
                if "direction" in command:
                    direction = normalize_direction(command.get("direction"))
                    logger.info(
                        f"Executing SET_SPEED command with direction change (speed={speed}, direction={'forward' if direction == 1 else 'reverse'})..."
                    )
                    self.hardware_controller.set_direction(direction)
                    self.hardware_controller.set_speed(speed)
                    logger.info(
                        f"✓ Speed set to {speed} ({'forward' if direction == 1 else 'reverse'})"
                    )
                else:
                    logger.info(f"Executing SET_SPEED command (speed={speed})...")
                    self.hardware_controller.set_speed(speed)
                    logger.info(f"✓ Speed set to {speed}")
                # Publish status update after command execution
                self._publish_current_status()

            # Command: change direction
            elif action == "setDirection":
                direction = normalize_direction(command.get("direction"))
                logger.info(
                    f"Executing SET_DIRECTION command (direction={'forward' if direction == 1 else 'reverse'})..."
                )
                self.hardware_controller.set_direction(direction)
                logger.info(f"✓ Direction set to {'forward' if direction == 1 else 'reverse'}")
                # Publish status update after command execution
                self._publish_current_status()

            # Unknown action - log warning but don't fail
            # This allows for future command types without code changes
            else:
                logger.warning(f"⚠ Unknown action: {action}")

        except Exception:
            # Catch all hardware exceptions to prevent MQTT loop crash
            # Log error but allow controller to continue processing commands
            logger.exception("Hardware command execution failed")

    def _publish_current_status(self) -> None:
        """Publish current train status to MQTT.

        Collects current state from hardware controller and publishes
        to the status topic. This is called after command execution to
        notify subscribers of state changes.

        Status includes:
            - train_id: Train identifier
            - speed: Current motor speed (0-100)
            - direction: Current direction (FORWARD/BACKWARD)
            - timestamp: ISO 8601 timestamp

        Note:
            Errors during status publishing are caught and logged to prevent
            command execution failures.
        """
        try:
            import datetime

            # Build status payload from current hardware state
            status = {
                "train_id": self.train_id,
                "speed": self.hardware_controller.current_speed,
                "direction": "FORWARD"
                if self.hardware_controller.current_direction == 1
                else "BACKWARD",
                "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            }

            # Publish to MQTT broker
            self.mqtt_client.publish_status(status)
            logger.info(f"✓ Published status: {status}")

        except Exception:
            # Log error but don't fail - status publishing is best-effort
            logger.exception("Failed to publish status update")

    async def run_async(self) -> None:
        """Run the main application loop with async support."""
        try:
            logger.info("Edge controller running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down due to keyboard interrupt")
        finally:
            self.shutdown()

    def run(self) -> None:
        """Run the main application loop."""
        # Run the async event loop
        asyncio.run(self.run_async())

    def shutdown(self) -> None:
        """Cleanup and shutdown application."""
        logger.info("Shutting down edge controller")

        if self.mqtt_client:
            self.mqtt_client.stop()

        if self.hardware_controller and hasattr(self.hardware_controller, "cleanup"):
            self.hardware_controller.cleanup()


def main() -> None:
    """Application entry point."""
    logger.info("")
    logger.info("#" * 70)
    logger.info("#" + " " * 68 + "#")
    logger.info("#" + " " * 20 + "EDGE CONTROLLER STARTING" + " " * 24 + "#")
    logger.info("#" + " " * 68 + "#")
    logger.info("#" * 70)
    logger.info("")
    logger.debug("[DEBUG TEST] Debug logging is enabled")

    app = EdgeControllerApp()

    if not app.initialize():
        logger.error("")
        logger.error("#" * 70)
        logger.error("#  INITIALIZATION FAILED - EXITING" + " " * 33 + "#")
        logger.error("#" * 70)
        logger.error("")
        sys.exit(1)

    app.run()


if __name__ == "__main__":
    main()
