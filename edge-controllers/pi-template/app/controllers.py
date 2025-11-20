import logging

from fastapi import APIRouter
from pydantic import BaseModel

from context import TRAIN_ID


router = APIRouter()


class Command(BaseModel):
    speed: int = None
    action: str = None


train_status = {
    "train_id": TRAIN_ID,
    "speed": 0,
    "voltage": 12.0,
    "current": 0.0,
    "position": "unknown",
}

mqtt_client = None  # Will be set in main.py


@router.post("/command")
async def handle_command(command: Command):
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
        logging.exception(f"[DIAG] Exception in handle_command: {e}")
        return {"error": str(e)}


@router.get("/status")
async def get_status():
    return train_status
