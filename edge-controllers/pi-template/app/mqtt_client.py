"""MQTT client for edge controller communication."""

import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class MQTTClientError(Exception):
    """Base exception for MQTT client errors."""


class MQTTConnectionError(MQTTClientError):
    """Raised when MQTT connection fails."""


class MQTTPublishError(MQTTClientError):
    """Raised when MQTT publish fails."""


class MQTTClient:
    """MQTT client for train control communication."""

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        train_id: str,
        status_topic: str,
        commands_topic: str,
        command_handler: Callable[[dict[str, Any]], None],
        username: str | None = None,
        password: str | None = None,
        central_api_url: str | None = None,
    ) -> None:
        """Initialize MQTT client.

        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            train_id: Train identifier
            status_topic: Topic for publishing status updates
            commands_topic: Topic for receiving commands
            command_handler: Callback function for handling commands
            username: Optional MQTT username
            password: Optional MQTT password
            central_api_url: Optional URL for HTTP status fallback
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

        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            return_code: Connection result code
        """
        if return_code == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")

            try:
                result = client.subscribe(self.commands_topic)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Subscribed to topic: {self.commands_topic}")
                else:
                    logger.error(f"Failed to subscribe to {self.commands_topic}: {result}")
            except Exception as exc:
                logger.error(f"Exception during subscription: {exc}")
        else:
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

        Args:
            client: MQTT client instance
            userdata: User data
            msg: Received message
        """
        try:
            payload = msg.payload.decode("utf-8")
            logger.info(f"Received message on {msg.topic}: {payload}")

            command = json.loads(payload)

            if not isinstance(command, dict):
                logger.error("Command payload is not a JSON object")
                return

            self.command_handler(command)

        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse command JSON: {exc}")
        except Exception as exc:
            logger.error(f"Error handling command: {exc}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, return_code: int) -> None:
        """Callback for when client disconnects from broker.

        Args:
            client: MQTT client instance
            userdata: User data
            return_code: Disconnection result code
        """
        if return_code != 0:
            logger.warning(f"Unexpected MQTT disconnection (code: {return_code})")
        else:
            logger.info("Disconnected from MQTT broker")

    def start(self) -> None:
        """Start the MQTT client and connect to broker.

        Raises:
            MQTTConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT client loop started")

        except ConnectionRefusedError as exc:
            raise MQTTConnectionError(f"Connection refused: {exc}") from exc
        except OSError as exc:
            raise MQTTConnectionError(f"Network error: {exc}") from exc
        except Exception as exc:
            raise MQTTConnectionError(f"Failed to start MQTT client: {exc}") from exc

    def stop(self) -> None:
        """Stop the MQTT client and disconnect from broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")
        except Exception as exc:
            logger.error(f"Error stopping MQTT client: {exc}")

    def publish_status(self, status: dict[str, Any]) -> None:
        """Publish train status to MQTT and optionally HTTP endpoint.

        Args:
            status: Status dictionary to publish

        Raises:
            MQTTPublishError: If publish fails
        """
        logger.debug(
            f"Publishing status - Connected: {self.client.is_connected()}, "
            f"Topic: {self.status_topic}, Payload: {status}"
        )

        # Publish to MQTT
        self._publish_to_mqtt(status)

        # Optionally push to central API HTTP endpoint
        if self.central_api_url:
            self._push_to_http(status)

    def _publish_to_mqtt(self, status: dict[str, Any]) -> None:
        """Publish status to MQTT broker.

        Args:
            status: Status dictionary to publish

        Raises:
            MQTTPublishError: If publish fails
        """
        try:
            payload = json.dumps(status)
            result = self.client.publish(self.status_topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published status to {self.status_topic}: {status}")
            else:
                error_msg = f"Failed to publish to {self.status_topic} (rc={result.rc})"
                logger.error(error_msg)
                raise MQTTPublishError(error_msg)

        except TypeError as exc:
            raise MQTTPublishError(f"Status is not JSON serializable: {exc}") from exc
        except Exception as exc:
            raise MQTTPublishError(f"Unexpected error during publish: {exc}") from exc

    def _push_to_http(self, status: dict[str, Any]) -> None:
        """Push status to central API HTTP endpoint.

        Args:
            status: Status dictionary to push
        """
        try:
            url = f"{self.central_api_url}/api/status/update"
            response = requests.post(url, json=status, timeout=2)

            if response.status_code == 200:
                logger.info(f"Pushed status to central API: {status}")
            else:
                logger.error(
                    f"Failed to push status to central API: {response.status_code} {response.text}"
                )

        except (RequestException, Timeout) as exc:
            logger.error(f"Exception during HTTP push to central API: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error during HTTP push: {exc}")
