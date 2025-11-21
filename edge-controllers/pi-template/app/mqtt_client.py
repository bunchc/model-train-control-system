"""MQTT client for edge controller communication.

This module implements bidirectional MQTT communication between edge controllers
and the central control system:

Data Flow:
    Commands:  Central API -> MQTT Broker -> Edge Controller
    Status:    Edge Controller -> MQTT Broker -> Central API/Frontend

Topics:
    - trains/{train_id}/commands: Inbound command topic (subscribed)
    - trains/{train_id}/status: Outbound status topic (published)

The MQTTClient wraps paho-mqtt and provides:
- Automatic reconnection on disconnect
- JSON payload encoding/decoding
- Command validation and routing to handlers
- Dual publishing (MQTT + HTTP fallback)
- Comprehensive error handling and logging

Architecture Decision:
    MQTT is used for real-time bidirectional communication because:
    - Low latency for command/control (< 100ms typical)
    - Pub/sub decouples edge controllers from central API
    - QoS guarantees message delivery
    - Lightweight protocol suitable for edge devices

    HTTP fallback ensures telemetry reaches API even if MQTT subscriber
    is temporarily down (e.g., frontend disconnected).

Typical usage:
    client = MQTTClient(
        broker_host="192.168.1.10",
        broker_port=1883,
        train_id="1",
        status_topic="trains/1/status",
        commands_topic="trains/1/commands",
        command_handler=handle_command
    )
    client.start()
    client.publish_status({"speed": 50, "voltage": 12.3})
"""

import json
import logging
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class MQTTClientError(Exception):
    """Base exception for MQTT client errors.

    All exceptions raised by MQTTClient inherit from this class,
    allowing callers to catch all MQTT-related errors with a single handler.

    Example:
        >>> try:
        ...     client.publish_status(status)
        ... except MQTTClientError as e:
        ...     logger.error(f"MQTT error: {e}")
    """


class MQTTConnectionError(MQTTClientError):
    """Raised when MQTT connection fails.

    Indicates connection-level failures such as:
    - Broker unreachable (network down, wrong host/port)
    - Connection refused (broker not accepting connections)
    - Authentication failure (bad username/password)
    - TLS/SSL handshake failure

    This error is raised by start() method and indicates the MQTT client
    cannot establish communication with the broker.
    """


class MQTTPublishError(MQTTClientError):
    """Raised when MQTT publish fails.

    Indicates failures during message publishing:
    - Client not connected to broker
    - Broker rejected publish (quota exceeded, permission denied)
    - Payload not JSON serializable
    - Network error during publish

    This error is raised by publish_status() and indicates the status
    update did not reach the broker.
    """


class MQTTClient:
    """MQTT client for train control communication.

    This client manages the MQTT connection lifecycle and provides methods
    for publishing status and receiving commands. It wraps paho-mqtt with
    application-specific logic for train control.

    Lifecycle:
        1. Initialize with broker details and topics
        2. start() - Connect to broker and subscribe to commands
        3. publish_status() - Publish status updates (continuous)
        4. Receive commands via command_handler callback
        5. stop() - Disconnect and cleanup

    Attributes:
        broker_host: MQTT broker hostname or IP address
        broker_port: MQTT broker port (typically 1883)
        train_id: Identifier for this train (used in topics)
        status_topic: Topic for publishing status (e.g., trains/1/status)
        commands_topic: Topic for receiving commands (e.g., trains/1/commands)
        command_handler: Callback function(dict) for processing commands
        central_api_url: Optional HTTP URL for status fallback
        client: Paho MQTT client instance

    Example:
        >>> def handle_cmd(cmd: dict[str, Any]) -> None:
        ...     print(f"Command: {cmd}")
        >>>
        >>> client = MQTTClient(
        ...     broker_host="192.168.1.10",
        ...     broker_port=1883,
        ...     train_id="1",
        ...     status_topic="trains/1/status",
        ...     commands_topic="trains/1/commands",
        ...     command_handler=handle_cmd
        ... )
        >>> client.start()
    """

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        train_id: str,
        status_topic: str,
        commands_topic: str,
        command_handler: Callable[[dict[str, Any]], None],
        username: Optional[str] = None,
        password: Optional[str] = None,
        central_api_url: Optional[str] = None,
    ) -> None:
        """Initialize MQTT client.

        Args:
            broker_host: MQTT broker hostname or IP address
            broker_port: MQTT broker port (1883 for plain, 8883 for TLS)
            train_id: Unique identifier for this train (e.g., "1")
            status_topic: Full topic path for publishing status
                (e.g., "trains/1/status")
            commands_topic: Full topic path for receiving commands
                (e.g., "trains/1/commands")
            command_handler: Callback function to process commands. Must
                accept dict[str, Any] parameter. Example:
                def handle_command(cmd: dict[str, Any]) -> None:
                    if cmd.get("action") == "setSpeed":
                        set_speed(cmd["speed"])
            username: Optional MQTT username for authentication
            password: Optional MQTT password for authentication
            central_api_url: Optional HTTP URL for status fallback. If provided,
                status updates will be sent to both MQTT and HTTP endpoints.

        Note:
            This constructor does not connect to the broker. Call start() to
            establish the connection.
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.train_id = train_id
        self.status_topic = status_topic
        self.commands_topic = commands_topic
        self.command_handler = command_handler
        self.central_api_url = central_api_url

        # Initialize MQTT client
        self.client = mqtt.Client()

        if username and password:
            self.client.username_pw_set(username, password)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict[str, int],
        return_code: int,
    ) -> None:
        """Callback for when client connects to broker.

        Automatically subscribes to commands_topic on successful connection.
        Logs detailed error messages for connection failures.

        MQTT Return Codes:
            0: Success
            1: Incorrect protocol version
            2: Invalid client identifier
            3: Server unavailable
            4: Bad username or password
            5: Not authorized

        Args:
            client: MQTT client instance (paho-mqtt)
            userdata: User-defined data (unused)
            flags: Connection flags from broker
            return_code: Connection result code (0 = success)

        Side Effects:
            - Subscribes to commands_topic if return_code == 0
            - Logs connection status at INFO or ERROR level
        """
        # Check connection result code (0 = success)
        if return_code == 0:
            logger.info("="*50)
            logger.info(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            logger.info("="*50)

            # Automatically subscribe to commands topic on successful connection
            # This ensures we receive commands even after reconnection
            try:
                logger.info(f"Subscribing to commands topic: {self.commands_topic}")
                result = client.subscribe(self.commands_topic)
                # result is tuple: (result_code, message_id)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"✓ Subscribed to topic: {self.commands_topic}")
                else:
                    logger.error(f"✗ Failed to subscribe to {self.commands_topic}: {result}")
            except Exception as exc:
                logger.error(f"✗ Exception during subscription: {exc}")
        else:
            # Connection failed - translate MQTT error codes to human-readable messages
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error_msg = error_messages.get(return_code, f"Unknown error code: {return_code}")
            logger.error(f"MQTT connection failed: {error_msg}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Callback for when message is received.

        Decodes JSON payload and invokes command_handler. All errors are
        caught and logged to prevent exceptions from crashing the MQTT loop.

        Message Processing:
            1. Decode UTF-8 payload
            2. Parse JSON
            3. Validate payload is dict (not array, string, etc.)
            4. Invoke command_handler(payload)

        Expected Command Format:
            {
                "action": "setSpeed",
                "speed": 50
            }

        Args:
            client: MQTT client instance (paho-mqtt)
            userdata: User-defined data (unused)
            msg: Received MQTT message containing:
                - topic: Source topic path
                - payload: Raw bytes
                - qos: Quality of service level

        Note:
            This callback runs in the paho-mqtt network thread. Long-running
            operations in command_handler may block message processing.
        """
        try:
            # Step 1: Decode raw bytes to UTF-8 string
            payload = msg.payload.decode("utf-8")
            logger.info("")
            logger.info(">>> MQTT MESSAGE RECEIVED <<<")
            logger.info(f"Topic: {msg.topic}")
            logger.info(f"Payload: {payload}")
            logger.info(f"QoS: {msg.qos}")

            # Step 2: Parse JSON string to Python dict
            command = json.loads(payload)
            logger.info(f"Parsed command: {command}")

            # Step 3: Validate payload is a dict (not array, string, number, etc.)
            # This prevents TypeError when accessing command.get('action')
            if not isinstance(command, dict):
                logger.error("✗ Command payload is not a JSON object")
                return

            # Step 4: Invoke application-specific command handler
            # Handler is responsible for validating action, speed, etc.
            logger.info("Invoking command handler...")
            self.command_handler(command)
            logger.info("✓ Command handler completed")

        except json.JSONDecodeError as exc:
            # JSON parsing failed - malformed JSON from sender
            logger.error(f"✗ Failed to parse command JSON: {exc}")
            logger.error(f"Raw payload: {msg.payload}")
        except Exception as exc:
            # Catch-all for any other errors to prevent MQTT loop crash
            logger.error(f"Error handling command: {exc}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, return_code: int) -> None:
        """Callback for when client disconnects from broker.

        Logs disconnect events. Paho-mqtt automatically attempts reconnection
        when using loop_start().

        Args:
            client: MQTT client instance (paho-mqtt)
            userdata: User-defined data (unused)
            return_code: Disconnection result code:
                0: Clean disconnect (client.disconnect() called)
                Non-zero: Unexpected disconnect (network error, broker down)

        Note:
            Automatic reconnection is handled by paho-mqtt when using loop_start().
            This callback is for logging/monitoring only.
        """
        if return_code != 0:
            logger.warning("="*50)
            logger.warning(f"⚠ Unexpected MQTT disconnection (code: {return_code})")
            logger.warning("MQTT client will attempt automatic reconnection...")
            logger.warning("="*50)
        else:
            logger.info("✓ Disconnected from MQTT broker (clean disconnect)")

    def start(self) -> None:
        """Start the MQTT client and connect to broker.

        Initiates connection to MQTT broker and starts background network loop.
        Subscription to commands_topic happens automatically in _on_connect callback.

        Network Loop:
            loop_start() creates a background thread that:
            - Handles automatic reconnection
            - Processes incoming messages
            - Sends outgoing publishes
            - Maintains keepalive pings

        Raises:
            MQTTConnectionError: If connection fails:
                - ConnectionRefusedError: Broker refusing connections
                - OSError: Network unreachable, DNS failure
                - Other exceptions: Unexpected errors

        Example:
            >>> try:
            ...     client.start()
            ...     logger.info("MQTT connected")
            ... except MQTTConnectionError as e:
            ...     logger.error(f"Connection failed: {e}")
            ...     sys.exit(1)
        """
        try:
            logger.info("Initiating MQTT connection...")
            logger.info(f"  Broker: {self.broker_host}:{self.broker_port}")
            logger.info(f"  Train ID: {self.train_id}")
            logger.info(f"  Keepalive: 60 seconds")

            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            logger.info("✓ TCP connection established")

            self.client.loop_start()
            logger.info("✓ MQTT client loop started (background thread)")

        except ConnectionRefusedError as exc:
            logger.error(f"✗ Connection refused by broker: {exc}")
            raise MQTTConnectionError(f"Connection refused: {exc}") from exc
        except OSError as exc:
            logger.error(f"✗ Network error connecting to broker: {exc}")
            raise MQTTConnectionError(f"Network error: {exc}") from exc
        except Exception as exc:
            logger.error(f"✗ Unexpected error starting MQTT client: {exc}")
            raise MQTTConnectionError(f"Failed to start MQTT client: {exc}") from exc

    def stop(self) -> None:
        """Stop the MQTT client and disconnect from broker.

        Gracefully shuts down the MQTT client by:
        1. Stopping the background network loop
        2. Disconnecting from broker (sends DISCONNECT packet)

        This method is idempotent and safe to call multiple times.
        All exceptions are caught and logged to ensure cleanup proceeds.

        Note:
            Call this method during application shutdown or when switching
            MQTT configurations.
        """
        try:
            logger.info("Stopping MQTT client...")
            self.client.loop_stop()
            logger.info("✓ MQTT loop stopped")
            self.client.disconnect()
            logger.info("✓ MQTT client disconnected")
        except Exception as exc:
            logger.error(f"✗ Error stopping MQTT client: {exc}")

    def publish_status(self, status: dict[str, Any]) -> None:
        """Publish train status to MQTT and optionally HTTP endpoint.

        Dual Publishing Strategy:
            1. Primary: Publish to MQTT broker (real-time, pub/sub)
            2. Secondary: POST to HTTP endpoint if central_api_url configured

        This ensures telemetry reaches the central system even if MQTT
        subscribers (frontend) are temporarily disconnected.

        Expected Status Format:
            {
                "train_id": "1",
                "speed": 50,
                "voltage": 12.3,
                "current": 0.8,
                "position": "section_A",
                "timestamp": "2024-01-15T10:30:00Z"
            }

        Args:
            status: Status dictionary to publish. Must be JSON serializable.

        Raises:
            MQTTPublishError: If MQTT publish fails:
                - Client not connected to broker
                - Broker rejected publish
                - Status not JSON serializable

        Note:
            HTTP push errors are logged but do not raise exceptions.
        """
        logger.debug(
            f"Publishing status - Connected: {self.client.is_connected()}, "
            f"Topic: {self.status_topic}, Payload: {status}"
        )

        # PRIMARY: Publish to MQTT broker for real-time subscribers (frontend, other controllers)
        # This is the primary telemetry channel - low latency, pub/sub pattern
        self._publish_to_mqtt(status)

        # SECONDARY: Push to Central API HTTP endpoint (if configured)
        # This ensures telemetry reaches the database even if MQTT subscribers are offline
        # HTTP push is best-effort - errors are logged but don't fail the publish
        if self.central_api_url:
            self._push_to_http(status)

    def _publish_to_mqtt(self, status: dict[str, Any]) -> None:
        """Publish status to MQTT broker.

        Serializes status dict to JSON and publishes to status_topic.
        Validates publish result and raises exception on failure.

        Args:
            status: Status dictionary to publish (must be JSON serializable)

        Raises:
            MQTTPublishError: If publish fails:
                - TypeError: Status contains non-JSON-serializable values
                - MQTT error: Client not connected or broker rejected

        Note:
            The publish is asynchronous. result.rc indicates whether the
            message was queued successfully, not whether it was delivered.
        """
        try:
            # Serialize Python dict to JSON string
            payload = json.dumps(status)

            # Publish to MQTT broker (asynchronous operation)
            # result.rc indicates if message was queued, not if it was delivered
            result = self.client.publish(self.status_topic, payload)

            # Check if publish was queued successfully
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published status to {self.status_topic}: {status}")
            else:
                # Publish failed - likely client not connected or broker rejected
                error_msg = f"Failed to publish to {self.status_topic} (rc={result.rc})"
                logger.error(error_msg)
                raise MQTTPublishError(error_msg)

        except TypeError as exc:
            # JSON serialization failed - status contains non-serializable objects
            raise MQTTPublishError(f"Status is not JSON serializable: {exc}") from exc
        except Exception as exc:
            # Catch-all for unexpected errors
            raise MQTTPublishError(f"Unexpected error during publish: {exc}") from exc

    def _push_to_http(self, status: dict[str, Any]) -> None:
        """Push status to central API HTTP endpoint.

        Sends HTTP POST to Central API as fallback telemetry channel.
        This ensures status reaches the database even if MQTT subscribers
        are offline.

        HTTP Endpoint:
            POST {central_api_url}/api/status/update
            Body: {"train_id": "1", "speed": 50, ...}

        Args:
            status: Status dictionary to push (will be JSON-encoded)

        Note:
            All errors are caught and logged. HTTP push failures do NOT
            raise exceptions or stop MQTT publishing. This is a best-effort
            fallback mechanism.
        """
        try:
            # Construct HTTP endpoint URL
            url = f"{self.central_api_url}/api/status/update"

            # Send POST request with JSON body (short timeout for non-critical operation)
            response = requests.post(url, json=status, timeout=2)

            # Check HTTP response status
            if response.status_code == 200:
                logger.info(f"Pushed status to central API: {status}")
            else:
                # HTTP error - log but don't fail (this is best-effort fallback)
                logger.error(
                    f"Failed to push status to central API: {response.status_code} {response.text}"
                )

        except (RequestException, Timeout) as exc:
            # Network error or timeout - log but don't fail
            # MQTT publish already succeeded, this is just supplementary
            logger.error(f"Exception during HTTP push to central API: {exc}")
        except Exception as exc:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error during HTTP push: {exc}")
