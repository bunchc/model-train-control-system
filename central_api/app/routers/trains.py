
from fastapi import APIRouter, HTTPException
import logging
from typing import List
from models.schemas import Train, TrainStatus
from services.mqtt_adapter import publish_command, get_train_status

logger = logging.getLogger("central_api.routers.trains")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

router = APIRouter()


@router.get("/", response_model=List[Train])
async def list_trains():
    logger.info("GET /api/trains called")
    trains = [
        Train(
            id="1",
            name="Express",
            status=TrainStatus(
                train_id="1",
                speed=0,
                voltage=12.0,
                current=0.0,
                position="section_A"
            ),
        ),
        Train(
            id="2",
            name="Freight",
            status=TrainStatus(
                train_id="2",
                speed=50,
                voltage=12.3,
                current=0.8,
                position="section_B"
            ),
        )
    ]
    logger.debug(f"Returning mock trains: {[t.id for t in trains]}")
    return trains

@router.post("/{train_id}/command")
async def send_command(train_id: str, command: dict):
    logger.info(f"POST /api/trains/{train_id}/command called with: {command}")
    success = publish_command(train_id, command)
    if not success:
        logger.error(f"Failed to send command to train {train_id}")
        raise HTTPException(status_code=400, detail="Failed to send command")
    logger.info(f"Command sent successfully to train {train_id}")
    return {"message": "Command sent successfully"}

@router.get("/{train_id}/status")
async def get_status(train_id: str):
    logger.info(f"GET /api/trains/{train_id}/status called")
    status = await get_train_status(train_id)
    if status is None:
        logger.warning(f"Train not found: {train_id}")
        raise HTTPException(status_code=404, detail="Train not found")
    logger.debug(f"Returning status for train {train_id}: {status}")
    return status