from fastapi import APIRouter, HTTPException

from services.config_manager import ConfigManager
from models.schemas import Plugin, EdgeController, Train, FullConfig
from typing import List

router = APIRouter()
config = ConfigManager()

@router.get("/config", response_model=FullConfig)
def get_full_config():
    return config.get_full_config()

@router.get("/plugins", response_model=List[Plugin])
def list_plugins():
    return config.get_plugins()

@router.get("/edge-controllers", response_model=List[EdgeController])
def list_edge_controllers():
    return config.get_edge_controllers()

@router.get("/edge-controllers/{edge_controller_id}", response_model=EdgeController)
def get_edge_controller_config(edge_controller_id: str):
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Edge controller not found")
    return ec

@router.get("/edge-controllers/{edge_controller_id}/trains", response_model=List[Train])
def list_trains_for_controller(edge_controller_id: str):
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Edge controller not found")
    return ec.trains

@router.get("/edge-controllers/{edge_controller_id}/trains/{train_id}", response_model=Train)
def get_train_for_controller(edge_controller_id: str, train_id: str):
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Edge controller not found")
    for train in ec.trains:
        if train.id == train_id:
            return train
    raise HTTPException(status_code=404, detail="Train not found")
