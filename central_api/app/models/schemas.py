from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PluginConfig(BaseModel):
    i2c_address: Optional[str] = None
    port: Optional[int] = None
    default_speed: Optional[int] = None
    enabled: Optional[bool] = None

class Plugin(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]

class TrainPlugin(BaseModel):
    name: str
    config: Dict[str, Any]

class Train(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    plugin: TrainPlugin

class EdgeController(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    enabled: bool = True
    trains: List[Train]

class FullConfig(BaseModel):
    plugins: List[Plugin]
    edge_controllers: List[EdgeController]

class TrainStatus(BaseModel):
    train_id: str
    speed: int
    voltage: float
    current: float
    position: str  # e.g., "section A", "section B"


class TrainPlugin(BaseModel):
    name: str
    config: Dict[str, Any]

class Train(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    plugin: TrainPlugin

class EdgeController(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    enabled: bool = True
    trains: List[Train]

# --- Added for OpenAPI alignment ---
from typing import List, Dict
