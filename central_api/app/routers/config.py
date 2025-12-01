"""Configuration management API endpoints.

This module provides REST API endpoints for managing system configuration
including edge controllers, trains, plugins, and train status.

Endpoints:
    GET /api/config - Get full system configuration
    GET /api/config/edge-controllers/{id} - Get controller by ID
    GET /api/config/trains - List all trains
    GET /api/config/trains/{id} - Get train by ID
    GET /api/trains/{id}/status - Get train status
    GET /api/plugins - List available plugins
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, HTTPException

from app.models.schemas import EdgeController, FullConfig, Plugin, Train, TrainStatus
from app.services.config_manager import ConfigManager


router = APIRouter()

logger = logging.getLogger("central_api.routers.config")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

# Lazy singleton - initialized on first access, can be overridden for testing
_config_instance: Optional[ConfigManager] = None


def _get_config() -> ConfigManager:
    """Get or create the ConfigManager singleton.

    This function retrieves the ConfigManager from app.state.
    For tests, _config_instance can be set to override.

    Returns:
        ConfigManager: The singleton instance from app.state
    """
    if _config_instance is not None:
        return _config_instance

    # Get from app.state (set during lifespan startup)
    from app.main import app

    return app.state.config_manager


# Internal endpoint for updating train status
@router.post("/status/update")
def update_train_status(
    train_id: str = Body(...),
    speed: int = Body(...),
    voltage: float = Body(...),
    current: float = Body(...),
    position: str = Body(...),
):
    """Update the status of a train. Intended for edge-controller or internal use."""
    _get_config().update_train_status(train_id, speed, voltage, current, position)
    logger.info(f"Status updated for train {train_id}")
    return {"message": "Status updated", "train_id": train_id}


@router.get("/config/edge-controllers/{edge_controller_id}", response_model=EdgeController)
def get_edge_controller_config_alias(edge_controller_id: str):
    """Get edge controller configuration by ID (OpenAPI alias).

    Args:
        edge_controller_id: UUID of edge controller

    Returns:
        EdgeController configuration object

    Raises:
        HTTPException: 404 if controller not found
    """
    # Alias for OpenAPI compliance
    return get_edge_controller_config(edge_controller_id)


@router.get("/config", response_model=FullConfig)
def get_full_config():
    """Get complete system configuration.

    Returns complete configuration including all plugins, trains,
    and edge controllers.

    Returns:
        FullConfig object with all system configuration

    Example:
        ```bash
        curl http://localhost:8000/api/config
        ```
    """
    logger.info("GET /config called")
    return _get_config().get_full_config()


# New endpoints for trains (moved to trains.py)
@router.get("/config/trains", response_model=list[Train])
def list_all_trains_config():
    """List all trains in the system (config alias).

    Returns:
        List of Train configuration objects

    Example:
        ```bash
        curl http://localhost:8000/api/config/trains
        ```
    """
    logger.info("GET /config/trains called")
    return _get_config().get_trains()


@router.get("/trains/{train_id}/status", response_model=TrainStatus)
def get_train_status(train_id: str):
    """Get the latest status for a train from the database."""
    status = _get_config().get_train_status(train_id)
    if not status:
        logger.warning(f"No status found for train {train_id}")
        raise HTTPException(status_code=404, detail="Train status not available")
    logger.info(f"Returning status for train {train_id}: {status}")
    return status


@router.get("/config/trains/{train_id}", response_model=Train)
def get_train_config_by_id(train_id: str):
    """Get train configuration by ID.

    Args:
        train_id: Unique train identifier

    Returns:
        Train configuration object

    Raises:
        HTTPException: 404 if train not found

    Example:
        ```bash
        curl http://localhost:8000/api/config/trains/train-001
        ```
    """
    logger.info(f"GET /config/trains/{train_id} called")
    train = _get_config().get_train(train_id)
    if not train:
        logger.warning(f"Train not found: {train_id}")
        raise HTTPException(status_code=404, detail="Train not found")
    return train


@router.get("/plugins", response_model=list[Plugin])
def list_plugins():
    """List all available plugins.

    Returns all plugins that can be attached to trains.

    Returns:
        List of Plugin objects

    Example:
        ```bash
        curl http://localhost:8000/api/plugins
        ```
    """
    logger.info("GET /plugins called")
    return _get_config().get_plugins()


# Controllers endpoints - use /controllers for all controller operations
@router.get("/controllers", response_model=list[EdgeController])
def list_controllers():
    """List all controllers in the system."""
    logger.info("GET /controllers called")
    return _get_config().get_edge_controllers()


# Legacy alias for backward compatibility
@router.get("/edge-controllers", response_model=list[EdgeController])
def list_edge_controllers():
    """Legacy endpoint - use /controllers instead."""
    logger.info("GET /edge-controllers called (legacy)")
    return _get_config().get_edge_controllers()


@router.get("/controllers/{controller_id}", response_model=EdgeController)
def get_controller(controller_id: str):
    """Get a specific controller by UUID."""
    logger.info(f"GET /controllers/{controller_id} called")
    ec = _get_config().get_edge_controller(controller_id)
    if not ec:
        all_ecs = _get_config().get_edge_controllers()
        all_ids = [ec.id for ec in all_ecs]
        logger.warning(f"Controller not found: {controller_id}")
        logger.error(f"Controller 404: requested '{controller_id}', available: {all_ids}")
        raise HTTPException(status_code=404, detail="Controller not found")
    return ec


# Legacy alias
@router.get("/edge-controllers/{edge_controller_id}", response_model=EdgeController)
def get_edge_controller_config(edge_controller_id: str):
    """Legacy endpoint - use /controllers/{id} instead."""
    logger.info(f"GET /edge-controllers/{edge_controller_id} called (legacy)")
    return get_controller(edge_controller_id)


@router.get("/controllers/{controller_id}/trains", response_model=list[Train])
def list_trains_for_controller(controller_id: str):
    """List all trains managed by a specific controller."""
    logger.info(f"GET /controllers/{controller_id}/trains called")
    ec = _get_config().get_edge_controller(controller_id)
    if not ec:
        logger.warning(f"Controller not found: {controller_id}")
        raise HTTPException(status_code=404, detail="Controller not found")
    return ec.trains


# Legacy alias
@router.get("/edge-controllers/{edge_controller_id}/trains", response_model=list[Train])
def list_trains_for_edge_controller(edge_controller_id: str):
    """Legacy endpoint - use /controllers/{id}/trains instead."""
    logger.info(f"GET /edge-controllers/{edge_controller_id}/trains called (legacy)")
    return list_trains_for_controller(edge_controller_id)


@router.get("/controllers/{controller_id}/trains/{train_id}", response_model=Train)
def get_train_for_controller(controller_id: str, train_id: str):
    """Get a specific train managed by a controller."""
    logger.info(f"GET /controllers/{controller_id}/trains/{train_id} called")
    ec = _get_config().get_edge_controller(controller_id)
    if not ec:
        logger.warning(f"Controller not found: {controller_id}")
        raise HTTPException(status_code=404, detail="Controller not found")
    for train in ec.trains:
        if train.id == train_id:
            logger.info(f"Train found: {train_id} for controller {controller_id}")
            return train
    logger.warning(f"Train not found: {train_id} for controller {controller_id}")
    raise HTTPException(status_code=404, detail="Train not found")


# Legacy alias
@router.get("/edge-controllers/{edge_controller_id}/trains/{train_id}", response_model=Train)
def get_train_for_edge_controller(edge_controller_id: str, train_id: str):
    """Legacy endpoint - use /controllers/{id}/trains/{train_id} instead."""
    logger.info(f"GET /edge-controllers/{edge_controller_id}/trains/{train_id} called (legacy)")
    return get_train_for_controller(edge_controller_id, train_id)


@router.get("/controllers/{controller_id}/ping")
def ping_controller(controller_id: str):
    """Check if a controller exists in the system by UUID.

    Returns 200 if the controller is found, 404 otherwise.
    """
    logger.info(f"GET /controllers/{controller_id}/ping called")
    ec = _get_config().get_edge_controller(controller_id)
    if not ec:
        logger.warning(f"Controller not found: {controller_id}")
        raise HTTPException(status_code=404, detail="Controller not found")
    return {"status": "ok", "uuid": controller_id}


@router.post("/controllers/register")
def register_controller(
    name: str = Body(..., description="Hostname of the edge controller"),
    address: str = Body(..., description="IP address of the edge controller"),
):
    """Register a new edge controller and receive a UUID.

    The edge-controller POSTs its hostname as 'name' and IP as 'address'.
    The central API generates a UUID and stores the controller info.

    If a controller with the same name already exists, return its existing UUID.
    """
    logger.info(f"POST /controllers/register called with name={name}, address={address}")

    # Check if controller with this name already exists
    all_controllers = _get_config().get_edge_controllers()
    for ec in all_controllers:
        if ec.name == name:
            logger.info(f"Controller with name '{name}' already exists with UUID {ec.id}")
            return {"uuid": ec.id, "name": name, "address": address, "status": "existing"}

    # Controller doesn't exist - create a new one
    import uuid

    new_uuid = str(uuid.uuid4())

    # Add controller to database using ConfigManager
    try:
        _get_config().add_edge_controller(new_uuid, name, address)
    except Exception as e:
        logger.exception("Failed to register controller")
        msg = f"Failed to register controller: {e!s}"
        raise HTTPException(status_code=500, detail=msg) from e
    else:
        logger.info(f"Registered new controller: name={name}, uuid={new_uuid}, address={address}")
        return {"uuid": new_uuid, "name": name, "address": address, "status": "registered"}


@router.post("/controllers/{controller_uuid}/trains", response_model=Train, status_code=201)
def register_train_for_controller(
    controller_uuid: str,
    train_id: str = Body(..., description="Unique UUID for the train"),
    name: str = Body(..., description="Human-readable train name"),
    description: str = Body("", description="Optional train description"),
    model: str = Body("", description="Train model name/number"),
    plugin: dict = Body(..., description="Plugin configuration"),
    reassign: bool = Body(False, description="If true, reassign train from existing controller"),
):
    r"""Register a new train for a specific edge controller.

    This endpoint is called by edge controllers during initialization to register
    the trains they manage. The controller UUID must exist in the system.

    Args:
        controller_uuid: UUID of the edge controller managing this train
        train_id: Unique identifier for the train
        name: Display name for the train
        description: Optional description
        model: Optional model information
        plugin: Plugin configuration dict with 'name' and 'config' keys
        reassign: If true, reassign train from existing controller to this one

    Returns:
        Train object representing the registered train

    Raises:
        HTTPException: 400 if controller not found, 409 if train already exists

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/controllers/{uuid}/trains \\
          -H "Content-Type: application/json" \\
          -d '{
            "train_id": "abc-123",
            "name": "Express Line",
            "model": "DC Motor",
            "plugin": {"name": "dc_motor", "config": {"motor_port": 1}},
            "reassign": false
          }'
        ```
    """
    logger.info(
        f"POST /controllers/{controller_uuid}/trains called: "
        f"train_id={train_id}, name={name}, reassign={reassign}"
    )

    try:
        train = _get_config().add_train(
            controller_uuid=controller_uuid,
            train_id=train_id,
            name=name,
            description=description,
            model=model,
            plugin_name=plugin.get("name", "dc_motor"),
            plugin_config=plugin.get("config", {}),
            reassign=reassign,
        )
    except Exception as e:
        if "not found" in str(e).lower():
            msg = f"Controller {controller_uuid} not found"
            raise HTTPException(status_code=400, detail=msg) from e
        if "UNIQUE constraint" in str(e) or "already exists" in str(e).lower():
            # Check if train exists and we should return existing controller
            if not reassign:
                existing_controller = _get_config().get_controller_for_train(train_id)
                if existing_controller:
                    logger.info(
                        f"Train {train_id} exists, returning existing controller: "
                        f"{existing_controller.id}"
                    )
                    # Get the train data directly from repository
                    train_data = _get_config().repository.get_train(train_id)
                    if train_data:
                        # Convert to Train model
                        import json

                        from app.models.schemas import Train, TrainPlugin

                        plugin_config = (
                            json.loads(train_data["plugin_config"])
                            if train_data["plugin_config"]
                            else {}
                        )
                        return Train(
                            id=train_data["id"],
                            name=train_data["name"],
                            description=train_data.get("description", ""),
                            model=train_data.get("model", ""),
                            plugin=TrainPlugin(
                                name=train_data["plugin_name"], config=plugin_config
                            ),
                        )
                    # If not found in repository, fallback to 409
                    logger.warning(f"Train {train_id} not found in repository")

            msg = f"Train {train_id} already exists"
            raise HTTPException(status_code=409, detail=msg) from e
        logger.exception("Failed to register train")
        raise HTTPException(status_code=500, detail=f"Failed to register train: {e!s}") from e
    else:
        logger.info(f"Registered train {name} ({train_id}) for controller {controller_uuid}")
        return train


@router.post("/trains", response_model=Train, status_code=201)
def register_train(
    train_id: str = Body(...),
    name: str = Body(...),
    controller_uuid: str = Body(..., description="UUID of managing controller"),
    description: str = Body(""),
    model: str = Body(""),
    plugin: dict = Body(...),
):
    r"""Register a new train (convenience endpoint for manual/admin use).

    This is a convenience endpoint that accepts controller_uuid in the body.
    Edge controllers should prefer POST /api/controllers/{uuid}/trains.

    Args:
        train_id: Unique identifier for the train
        name: Display name
        controller_uuid: UUID of the managing controller
        description: Optional description
        model: Optional model information
        plugin: Plugin configuration

    Returns:
        Train object

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/trains \\
          -d '{"train_id": "...", "name": "...", "controller_uuid": "...", "plugin": {...}}'
        ```
    """
    logger.info(f"POST /trains called: train_id={train_id}, controller={controller_uuid}")
    return register_train_for_controller(
        controller_uuid=controller_uuid,
        train_id=train_id,
        name=name,
        description=description,
        model=model,
        plugin=plugin,
    )


@router.post("/config/trains", response_model=Train, status_code=201)
def register_train_config_alias(
    train_id: str = Body(...),
    name: str = Body(...),
    controller_uuid: str = Body(...),
    description: str = Body(""),
    model: str = Body(""),
    plugin: dict = Body(...),  # noqa: B008
):
    """Register a new train (OpenAPI consistency alias).

    Alias for POST /api/trains to maintain consistency with GET /api/config/trains.

    Args:
        train_id: Unique identifier
        name: Display name
        controller_uuid: Managing controller UUID
        description: Optional description
        model: Optional model
        plugin: Plugin configuration

    Returns:
        Train object
    """
    logger.info(f"POST /config/trains called (alias): train_id={train_id}")
    return register_train(
        train_id=train_id,
        name=name,
        controller_uuid=controller_uuid,
        description=description,
        model=model,
        plugin=plugin,
    )


@router.get("/controllers/{uuid}/config")
def get_controller_runtime_config(uuid: str):
    """Download runtime configuration for an edge controller using its UUID.

    Args:
        uuid: The controller's UUID

    Returns:
        Runtime configuration for the edge controller including:
        - uuid: Controller UUID
        - name: Controller name/hostname
        - train_id: ID of the first train assigned to this controller
        - mqtt_broker: MQTT connection details
        - status_topic: MQTT topic for status updates
        - commands_topic: MQTT topic for commands
    """
    from app.config import get_settings

    logger.info(f"GET /controllers/{uuid}/config called")

    ec = _get_config().get_edge_controller(uuid)
    if not ec:
        logger.warning(f"Controller not found: {uuid}")
        raise HTTPException(status_code=404, detail="Controller not found")

    # Build runtime config
    # For now, use the first train if available
    train_id = ec.trains[0].id if ec.trains else "default_train"

    # Get MQTT broker configuration from settings
    settings = get_settings()

    runtime_config = {
        "uuid": uuid,
        "name": ec.name,
        "train_id": train_id,
        "mqtt_broker": {
            "host": settings.mqtt_broker_host,
            "port": settings.mqtt_broker_port,
            "username": "edge-controller",
            "password": "/yameCjLOFwbskcltRRZZUBWFBg/Q+PAIPNZZz7Kgpg=",
        },
        "status_topic": f"trains/{train_id}/status",
        "commands_topic": f"trains/{train_id}/commands",
    }

    logger.info(f"Returning runtime config for controller {uuid}")
    return runtime_config
