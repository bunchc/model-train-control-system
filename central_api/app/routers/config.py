
from fastapi import APIRouter, HTTPException
import logging
from services.config_manager import ConfigManager
from models.schemas import Plugin, EdgeController, Train, FullConfig
from typing import List

logger = logging.getLogger("central_api.routers.config")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

router = APIRouter()
config = ConfigManager()


@router.get("/config/edge-controllers/{edge_controller_id}", response_model=EdgeController)
def get_edge_controller_config_alias(edge_controller_id: str):
    # Alias for OpenAPI compliance
    return get_edge_controller_config(edge_controller_id)


@router.get("/config", response_model=FullConfig)
def get_full_config():
    logger.info("GET /config called")
    return config.get_full_config()

# New endpoints for trains
@router.get("/trains", response_model=List[Train])
def list_all_trains():
    logger.info("GET /trains called")
    return config.get_trains()

@router.get("/config/trains", response_model=List[Train])
def list_all_trains_config():
    logger.info("GET /config/trains called")
    return config.get_trains()

@router.get("/trains/{train_id}", response_model=Train)
def get_train_by_id(train_id: str):
    logger.info(f"GET /trains/{train_id} called")
    train = config.get_train(train_id)
    if not train:
        logger.warning(f"Train not found: {train_id}")
        raise HTTPException(status_code=404, detail="Train not found")
    return train

@router.get("/config/trains/{train_id}", response_model=Train)
def get_train_config_by_id(train_id: str):
    logger.info(f"GET /config/trains/{train_id} called")
    train = config.get_train(train_id)
    if not train:
        logger.warning(f"Train not found: {train_id}")
        raise HTTPException(status_code=404, detail="Train not found")
    return train

@router.get("/plugins", response_model=List[Plugin])
def list_plugins():
    logger.info("GET /plugins called")
    return config.get_plugins()

@router.get("/edge-controllers", response_model=List[EdgeController])
def list_edge_controllers():
    logger.info("GET /edge-controllers called")
    return config.get_edge_controllers()

@router.get("/edge-controllers/{edge_controller_id}", response_model=EdgeController)
def get_edge_controller_config(edge_controller_id: str):
    logger.info(f"GET /edge-controllers/{edge_controller_id} called")
    all_ecs = config.get_edge_controllers()
    all_ids = [ec.id for ec in all_ecs]
    logger.debug(f"Available edge controller IDs: {all_ids}")
    logger.debug(f"Requested edge controller ID: {edge_controller_id}")
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        logger.warning(f"Edge controller not found: {edge_controller_id}")
        logger.error(f"Edge controller 404: requested '{edge_controller_id}', available: {all_ids}")
        raise HTTPException(status_code=404, detail="Edge controller not found")
    return ec

@router.get("/edge-controllers/{edge_controller_id}/trains", response_model=List[Train])
def list_trains_for_controller(edge_controller_id: str):
    logger.info(f"GET /edge-controllers/{edge_controller_id}/trains called")
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        logger.warning(f"Edge controller not found: {edge_controller_id}")
        raise HTTPException(status_code=404, detail="Edge controller not found")
    return ec.trains

@router.get("/edge-controllers/{edge_controller_id}/trains/{train_id}", response_model=Train)
def get_train_for_controller(edge_controller_id: str, train_id: str):
    logger.info(f"GET /edge-controllers/{edge_controller_id}/trains/{train_id} called")
    ec = config.get_edge_controller(edge_controller_id)
    if not ec:
        logger.warning(f"Edge controller not found: {edge_controller_id}")
        raise HTTPException(status_code=404, detail="Edge controller not found")
    for train in ec.trains:
        if train.id == train_id:
            logger.info(f"Train found: {train_id} for edge controller {edge_controller_id}")
            return train
    logger.warning(f"Train not found: {train_id} for edge controller {edge_controller_id}")
    raise HTTPException(status_code=404, detail="Train not found")
