"""MQTT Status Service for Central API.

This service subscribes to all train status MQTT topics and stores
incoming status messages in the database for later retrieval by the API.

The service runs as a background task and automatically handles:
- MQTT connection management
- Status message parsing and validation
- Database storage of train status
- Error handling and reconnection
"""

import json
import logging
from typing import Any, Optional

import paho.mqtt.client as mqtt

from app.config import settings
from app.services.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class MQTTStatusService:
    """Background service for collecting train status via MQTT."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize MQTT status service.

        Args:
            config_manager: ConfigManager instance for database operations
        """
        self.config_manager = config_manager
        self.client: Optional[mqtt.Client] = None
        self.is_running = False

    def start(self) -> None:
        """Start the MQTT status collection service."""
        if self.is_running:
            return

        logger.info("Starting MQTT status service")

        # Create MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        try:
            # Connect to MQTT broker
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
            self.client.loop_start()
            self.is_running = True
            logger.info(
                f"Connected to MQTT broker at {settings.mqtt_broker_host}:{settings.mqtt_broker_port}"
            )
        except Exception:
            logger.exception("Failed to connect to MQTT broker")

    def stop(self) -> None:
        """Stop the MQTT status collection service."""
        if not self.is_running or not self.client:
            return

        logger.info("Stopping MQTT status service")
        self.client.loop_stop()
        self.client.disconnect()
        self.is_running = False

    def _on_connect(self, client, _userdata, _flags, rc):
        """Handle MQTT connection.

        Args:
            client: MQTT client instance
            userdata: User data (unused)
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            logger.info("MQTT client connected successfully")
            # Subscribe to all train status topics
            client.subscribe("trains/+/status")
            logger.info("Subscribed to trains/+/status")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, _client, _userdata, rc):
        """Handle MQTT disconnection.

        Args:
            client: MQTT client instance
            userdata: User data (unused)
            rc: Disconnection result code
        """
        logger.warning(f"MQTT client disconnected with code {rc}")
        if rc != 0:
            logger.info("Unexpected disconnection, will reconnect automatically")

    def _on_message(self, _client, _userdata, msg):
        """Handle incoming MQTT status messages.

        Args:
            client: MQTT client instance
            userdata: User data (unused)
            msg: MQTT message containing status data
        """
        try:
            # Parse topic to extract train ID
            expected_topic_parts = 3
            topic = msg.topic
            parts = topic.split("/")
            if len(parts) != expected_topic_parts:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return

            train_id = parts[1]

            # Parse status payload
            try:
                status_data = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                logger.exception(f"Failed to parse JSON payload from {msg.topic}")
                return

            # Validate required fields
            required_fields = ["train_id", "speed", "timestamp"]
            missing_fields = [field for field in required_fields if field not in status_data]
            if missing_fields:
                logger.warning(
                    f"Status message missing required fields {missing_fields}: {status_data}"
                )
                # Continue processing - we'll use defaults for missing optional fields

            # Add defaults for optional fields
            status_data.setdefault("voltage", 0.0)
            status_data.setdefault("current", 0.0)
            status_data.setdefault("position", "unknown")

            # Ensure train_id matches topic
            if status_data.get("train_id") != train_id:
                logger.warning(
                    f"Train ID mismatch: topic={train_id}, payload={status_data.get('train_id')}"
                )
                status_data["train_id"] = train_id  # Use topic as source of truth

            # Store status in database
            self._store_status(train_id, status_data)

        except Exception:
            logger.exception(f"Error processing MQTT message from {msg.topic}")

    def _store_status(self, train_id: str, status_data: dict[str, Any]) -> None:
        """Store train status in database.

        Args:
            train_id: Train identifier
            status_data: Status payload from MQTT
        """
        try:
            # Extract individual fields for the config_manager method
            speed = int(status_data.get("speed", 0))
            voltage = float(status_data.get("voltage", 0.0))
            current = float(status_data.get("current", 0.0))
            position = str(status_data.get("position", "unknown"))

            # Call update_train_status with the correct arguments
            self.config_manager.update_train_status(train_id, speed, voltage, current, position)
            logger.debug(
                f"Stored status for train {train_id}: speed={speed}, "
                f"voltage={voltage}, current={current}, position={position}"
            )
        except Exception:
            logger.exception(f"Database error storing status for train {train_id}")


# Global instance - will be initialized in main.py
mqtt_status_service: Optional[MQTTStatusService] = None


def get_mqtt_status_service() -> Optional[MQTTStatusService]:
    """Get the global MQTT status service instance."""
    return mqtt_status_service
