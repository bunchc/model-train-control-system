"""Train control API endpoints.

This module provides REST API endpoints for controlling model trains
and retrieving their status. Commands are published to MQTT topics
that edge controllers subscribe to.

Endpoints:
    GET /api/trains - List all trains
    POST /api/trains/{id}/command - Send command to train
    GET /api/trains/{id}/status - Get train status

MQTT Integration:
    Commands are published to: trains/{train_id}/commands
    Status is received from: trains/{train_id}/status
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import Train, TrainStatus
from app.services.mqtt_adapter import get_train_status, publish_command


logger = logging.getLogger("central_api.routers.trains")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

router = APIRouter()


@router.get("/", response_model=list[Train])
async def list_trains():
    """List all available trains.

    Returns a list of all trains currently configured in the system.
    This is currently returning mock data; will be replaced with
    database queries via ConfigManager.

    Returns:
        List of Train objects with current status

    Example:
        ```bash
        curl http://localhost:8000/api/trains
        ```

        Response:
        ```json
        [
          {
            "id": "1",
            "name": "Express",
            "status": {
              "train_id": "1",
              "speed": 0,
              "voltage": 12.0,
              "current": 0.0,
              "position": "section_A"
            }
          }
        ]
        ```
    """
    logger.info("GET /api/trains called")
    trains = [
        Train(
            id="1",
            name="Express",
            status=TrainStatus(
                train_id="1", speed=0, voltage=12.0, current=0.0, position="section_A"
            ),
        ),
        Train(
            id="2",
            name="Freight",
            status=TrainStatus(
                train_id="2", speed=50, voltage=12.3, current=0.8, position="section_B"
            ),
        ),
    ]
    logger.debug(f"Returning mock trains: {[t.id for t in trains]}")
    return trains


@router.post("/{train_id}/command")
async def send_command(train_id: str, command: dict):
    """Send control command to train via MQTT.

    Publishes command to MQTT topic trains/{train_id}/commands.
    The edge controller subscribed to this topic will execute the command.

    Args:
        train_id: Unique identifier of the train
        command: Command payload containing:
            - action: Command type ("setSpeed", "start", "stop")
            - speed: Target speed 0-100 (required for "setSpeed")

    Returns:
        Success confirmation message

    Raises:
        HTTPException: 400 if command publish fails

    Example:
        ```bash
        # Set speed to 75
        curl -X POST http://localhost:8000/api/trains/1/command \
          -H "Content-Type: application/json" \
          -d '{"action": "setSpeed", "speed": 75}'

        # Stop train
        curl -X POST http://localhost:8000/api/trains/1/command \
          -H "Content-Type: application/json" \
          -d '{"action": "stop"}'
        ```

        Response:
        ```json
        {"message": "Command sent successfully"}
        ```
    """
    logger.info(f"POST /api/trains/{train_id}/command called with: {command}")
    success = publish_command(train_id, command)
    if not success:
        logger.error(f"Failed to send command to train {train_id}")
        raise HTTPException(status_code=400, detail="Failed to send command")
    logger.info(f"Command sent successfully to train {train_id}")
    return {"message": "Command sent successfully"}


@router.get("/{train_id}/status")
async def get_status(train_id: str):
    """Get real-time status for a train.

    Queries the edge controller via MQTT for the current train status.
    Returns the most recent status update received from the edge controller.

    Args:
        train_id: Unique identifier of the train

    Returns:
        TrainStatus object containing:
            - train_id: Train identifier
            - speed: Current speed (0-100)
            - voltage: Battery voltage (volts)
            - current: Current draw (amperes)
            - position: Current track position/section
            - timestamp: Status timestamp

    Raises:
        HTTPException: 404 if no status available or timeout

    Example:
        ```bash
        curl http://localhost:8000/api/trains/1/status
        ```

        Response:
        ```json
        {
          "train_id": "1",
          "speed": 50,
          "voltage": 12.3,
          "current": 0.8,
          "position": "section_A",
          "timestamp": "2025-11-21T10:15:32Z"
        }
        ```
    """
    logger.info(f"GET /api/trains/{train_id}/status called")
    status = get_train_status(train_id, local_testing=False)
    if status is None:
        logger.warning(f"No status received for train {train_id}")
        raise HTTPException(status_code=404, detail="Train status not available")
    logger.debug(f"Returning status for train {train_id}: {status}")
    return status
