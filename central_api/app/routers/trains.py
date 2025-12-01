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

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import Train, TrainStatus
from app.services.mqtt_adapter import publish_command


logger = logging.getLogger("central_api.routers.trains")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

router = APIRouter()


@router.get("/trains", response_model=list[Train])
async def list_trains(request: Request):
    """List all available trains.

    Returns a list of all trains currently configured in the system.
    Retrieved from the database via ConfigManager with current status.

    Returns:
        List of Train objects with current status

    Example:
        ```bash
        curl http://localhost:8000/api/trains
        ```
    """
    logger.info("GET /trains called")
    config_manager = request.app.state.config_manager
    trains = config_manager.get_trains()

    # Add status data to each train
    for train in trains:
        try:
            status = config_manager.get_train_status(train.id)
            train.status = status
        except Exception as e:
            logger.debug(f"No status found for train {train.id}: {e}")
            # Provide default status instead of None to show trains as "online" with zero values
            from app.models.schemas import TrainStatus

            train.status = TrainStatus(
                train_id=train.id, speed=0, voltage=0.0, current=0.0, position="unknown"
            )

    logger.debug(f"Returning {len(trains)} trains from database")
    return trains


@router.post("/trains/{train_id}/command")
async def send_command(train_id: str, command: dict, request: Request):
    """Send control command to train via MQTT.

    Publishes command to MQTT topic trains/{train_id}/commands.
    The edge controller subscribed to this topic will execute the command.

    Args:
        train_id: Unique identifier of the train
        command: Command payload containing:
            - action: Command type ("setSpeed", "start", "stop")
            - speed: Target speed 0-100 (required for "setSpeed")
        request: FastAPI request object

    Returns:
        Success confirmation message

    Raises:
        HTTPException: 404 if train not found
        HTTPException: 400 if command publish fails

    Example:
        ```bash
        # Set speed to 75
        curl -X POST http://localhost:8000/api/trains/{train_id}/command \
          -H "Content-Type: application/json" \
          -d '{"action": "setSpeed", "speed": 75}'

        # Stop train
        curl -X POST http://localhost:8000/api/trains/{train_id}/command \
          -H "Content-Type: application/json" \
          -d '{"action": "stop"}'
        ```

        Response:
        ```json
        {"message": "Command sent successfully"}
        ```
    """
    logger.info(f"POST /trains/{train_id}/command called with: {command}")

    # Verify train exists
    config_manager = request.app.state.config_manager
    train = config_manager.get_train(train_id)
    if not train:
        logger.warning(f"Train not found: {train_id}")
        raise HTTPException(status_code=404, detail="Train not found")

    # Send command via MQTT
    success = publish_command(train_id, command)
    if not success:
        logger.error(f"Failed to send command to train {train_id}")
        raise HTTPException(status_code=400, detail="Failed to send command")

    logger.info(f"Command sent successfully to train {train_id}")
    return {"message": "Command sent successfully"}


@router.get("/trains/{train_id}/status")
async def get_status(train_id: str, request: Request):
    """Get real-time status for a train from the database.

    Retrieves the latest status for a train that was previously stored
    from MQTT status updates. The Central API subscribes to MQTT status
    topics and automatically stores updates in the database.

    Args:
        train_id: Unique identifier of the train
        request: FastAPI request object

    Returns:
        TrainStatus object containing:
            - train_id: Train identifier
            - speed: Current speed (0-100)
            - voltage: Battery voltage (volts)
            - current: Current draw (amperes)
            - position: Current track position/section
            - timestamp: Status timestamp

    Raises:
        HTTPException: 404 if no status available

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
          "timestamp": "2025-12-01T19:15:32Z"
        }
        ```
    """
    logger.info(f"GET /api/trains/{train_id}/status called")

    config_manager = getattr(request.app.state, "config_manager", None)

    if not config_manager:
        logger.error("Config manager not available")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Get status from database (stored by MQTT service)
    status_data = config_manager.repository.get_train_status(train_id)
    if not status_data:
        logger.warning(f"No status found for train {train_id}")
        raise HTTPException(status_code=404, detail="Train status not available")

    logger.debug(f"Returning status for train {train_id}: {status_data}")

    # Convert to TrainStatus model
    return TrainStatus(
        train_id=status_data["train_id"],
        speed=status_data["speed"],
        voltage=status_data.get("voltage", 0.0),
        current=status_data.get("current", 0.0),
        position=status_data.get("position", "unknown"),
        timestamp=status_data.get("timestamp"),
    )
