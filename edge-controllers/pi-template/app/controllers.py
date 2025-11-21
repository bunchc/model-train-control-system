"""FastAPI router for local HTTP control endpoints.

This module provides HTTP endpoints for direct control of the edge controller,
enabling local testing and debugging without requiring MQTT infrastructure.

Endpoints:
    POST /command: Execute train control commands (start, stop, setSpeed)
    GET /status: Retrieve current train status

Architecture Decision:
    These HTTP endpoints are primarily for development and debugging.
    Production control flow uses MQTT (commands received via MQTT, status
    published via MQTT). These endpoints provide a synchronous alternative
    for testing scenarios.

Dual Control Paths:
    1. MQTT Path (production):
       Command -> MQTT Broker -> Edge Controller -> Hardware

    2. HTTP Path (development/testing):
       Command -> HTTP POST /command -> Edge Controller -> Hardware

    Both paths converge at the same command handling logic and publish
    status updates via MQTT.

Typical usage:
    # Start train via HTTP
    POST http://edge-controller:8080/command
    {"action": "start"}

    # Set speed via HTTP
    POST http://edge-controller:8080/command
    {"speed": 75}

    # Check status
    GET http://edge-controller:8080/status
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from context import TRAIN_ID


router = APIRouter()


class Command(BaseModel):
    """Pydantic model for train control commands.

    Supports two command patterns:
    1. Action-based: {"action": "start"} or {"action": "stop"}
    2. Speed-based: {"speed": 75}

    Attributes:
        speed: Target speed (0-100). None if not specified.
        action: Command action ("start", "stop"). None if not specified.

    Example:
        >>> # Start command
        >>> cmd = Command(action="start")
        >>>
        >>> # Set speed command
        >>> cmd = Command(speed=50)
    """

    speed: int = None
    action: str = None


train_status = {
    "train_id": TRAIN_ID,
    "speed": 0,
    "voltage": 12.0,
    "current": 0.0,
    "position": "unknown",
}
"""Global train status dictionary.

Maintains current state of the train. Updated by handle_command() and
published to MQTT after each command.

Fields:
    train_id: Identifier for this train (from runtime config)
    speed: Current speed (0-100)
    voltage: Motor voltage in volts (simulated)
    current: Motor current in amps (simulated)
    position: Current position/state ("unknown", "started", "stopped")
"""

mqtt_client = None  # Will be set in main.py
"""Global MQTT client instance.

Initialized in main.py and used by handle_command() to publish status updates.
Must be set before any commands are processed.
"""


@router.post("/command")
async def handle_command(command: Command):
    """Handle train control commands via HTTP POST.

    Processes commands and updates train_status. After updating status,
    publishes to MQTT to notify subscribers (Central API, frontend).

    Supported Commands:
        1. Start: {"action": "start"}
           - Maintains current speed
           - Sets position to "started"

        2. Stop: {"action": "stop"}
           - Sets speed to 0
           - Sets position to "stopped"

        3. Set Speed: {"speed": 75}
           - Updates speed (0-100)
           - Position unchanged

    Args:
        command: Command model containing action or speed

    Returns:
        Success response with status message or error dict

    Example:
        >>> # Start train
        >>> POST /command {"action": "start"}
        {"status": "Train started"}

        >>> # Set speed
        >>> POST /command {"speed": 50}
        {"status": "Train speed set to 50"}

    Note:
        Requires mqtt_client to be initialized. Returns error if not set.
    """
    logging.info(
        f"[DIAG] POST /command called with: action={command.action}, speed={command.speed}"
    )
    try:
        if mqtt_client is None:
            logging.error("MQTT client not initialized in controller.")
            return {"error": "MQTT client not initialized"}
        if command.action == "start":
            logging.info("Train start requested.")
            train_status["speed"] = train_status.get("speed", 0)
            train_status["position"] = "started"
            logging.info(
                f"[DIAG] About to publish train status to topic: {mqtt_client.status_topic} with payload: {train_status}"
            )
            logging.debug(f"Command handler: train_status before publish: {train_status}")
            mqtt_client.publish_status(train_status)
            logging.info("[DIAG] Publish status call completed.")
            return {"status": "Train started"}
        if command.action == "stop":
            logging.info("Train stop requested.")
            train_status["speed"] = 0
            train_status["position"] = "stopped"
            logging.info(
                f"[DIAG] About to publish train status to topic: {mqtt_client.status_topic} with payload: {train_status}"
            )
            logging.debug(f"Command handler: train_status before publish: {train_status}")
            mqtt_client.publish_status(train_status)
            logging.info("[DIAG] Publish status call completed.")
            return {"status": "Train stopped"}
        if command.speed is not None:
            logging.info(f"Train speed set requested: {command.speed}")
            train_status["speed"] = command.speed
            logging.info(
                f"[DIAG] About to publish train status to topic: {mqtt_client.status_topic} with payload: {train_status}"
            )
            logging.debug(f"Command handler: train_status before publish: {train_status}")
            mqtt_client.publish_status(train_status)
            logging.info("[DIAG] Publish status call completed.")
            return {"status": f"Train speed set to {command.speed}"}
        logging.warning("Invalid command received.")
        return {"error": "Invalid command"}
    except Exception as e:
        logging.exception("[DIAG] Exception in handle_command")
        return {"error": str(e)}


@router.get("/status")
async def get_status():
    """Get current train status via HTTP GET.

    Returns the current state of train_status dictionary.

    Returns:
        Dict containing:
        - train_id: Train identifier
        - speed: Current speed (0-100)
        - voltage: Motor voltage (V)
        - current: Motor current (A)
        - position: Current position/state

    Example:
        >>> GET / status
        {
            "train_id": "1",
            "speed": 50,
            "voltage": 12.0,
            "current": 0.8,
            "position": "started"
        }
    """
    return train_status
