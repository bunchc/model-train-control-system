from fastapi import APIRouter, HTTPException
from typing import List
from ..models.schemas import Train, TrainCommand
from ..services.mqtt_adapter import publish_command, get_train_status

router = APIRouter()

@router.get("/", response_model=List[Train])
async def list_trains():
    # Logic to retrieve the list of trains
    # This could be a static list or fetched from a database
    return [{"id": "1", "name": "Express", "status": "stopped"}, {"id": "2", "name": "Freight", "status": "running"}]

@router.post("/{train_id}/command")
async def send_command(train_id: str, command: TrainCommand):
    success = await publish_command(train_id, command)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to send command")
    return {"message": "Command sent successfully"}

@router.get("/{train_id}/status")
async def get_status(train_id: str):
    status = await get_train_status(train_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Train not found")
    return status