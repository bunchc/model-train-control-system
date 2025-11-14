from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import Train, TrainStatus
from services.mqtt_adapter import publish_command, get_train_status

router = APIRouter()


@router.get("/", response_model=List[Train])
async def list_trains():
    # Always return mock trains for dev/testing
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
            # commands removed
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
            # commands removed
        )
    ]
    return trains

@router.post("/{train_id}/command")
async def send_command(train_id: str, command: dict):
    success = publish_command(train_id, command)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to send command")
    return {"message": "Command sent successfully"}

@router.get("/{train_id}/status")
async def get_status(train_id: str):
    status = await get_train_status(train_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Train not found")
    return status