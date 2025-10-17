from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Command(BaseModel):
    speed: int = None
    action: str = None

@router.post("/command")
async def handle_command(command: Command):
    if command.action == "start":
        # Logic to start the train
        return {"status": "Train started"}
    elif command.action == "stop":
        # Logic to stop the train
        return {"status": "Train stopped"}
    elif command.speed is not None:
        # Logic to set the train speed
        return {"status": f"Train speed set to {command.speed}"}
    else:
        return {"error": "Invalid command"}