from pydantic import BaseModel
from typing import Optional

class TrainCommand(BaseModel):
    speed: Optional[int] = None
    direction: Optional[str] = None  # e.g., "forward" or "reverse"
    action: Optional[str] = None  # e.g., "start" or "stop"

class TrainStatus(BaseModel):
    train_id: str
    speed: int
    voltage: float
    current: float
    position: str  # e.g., "section A", "section B"

class Train(BaseModel):
    id: str
    name: str
    status: TrainStatus
    commands: TrainCommand