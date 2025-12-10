"""Pydantic models for API request/response validation.

All models use strict type hints and field validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PluginConfig(BaseModel):
    """Configuration for a hardware plugin."""

    i2c_address: Optional[str] = None
    port: Optional[int] = None
    default_speed: Optional[int] = Field(None, ge=0, le=100)
    enabled: Optional[bool] = None


class Plugin(BaseModel):
    """Plugin definition with configuration."""

    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)


class TrainPlugin(BaseModel):
    """Train-specific plugin configuration."""

    name: str = Field(..., min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)


class Train(BaseModel):
    """Train configuration and assignment."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    model: Optional[str] = None
    plugin: TrainPlugin
    invert_directions: bool = False
    status: Optional["TrainStatus"] = None


class TrainUpdateRequest(BaseModel):
    """Request model for updating train configuration.

    All fields are optional to support partial updates.
    Only provided fields will be updated in the database.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    invert_directions: Optional[bool] = None


class EdgeController(BaseModel):
    """Edge controller configuration."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    address: Optional[str] = None
    enabled: bool = True
    trains: list[Train] = Field(default_factory=list)
    # Telemetry fields (populated by heartbeat)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    config_hash: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None
    python_version: Optional[str] = None
    memory_mb: Optional[int] = None
    cpu_count: Optional[int] = None
    status: str = "unknown"


class ControllerHeartbeat(BaseModel):
    """Heartbeat payload from edge controller.

    All fields are optional - controllers can send partial updates.
    """

    config_hash: Optional[str] = Field(None, description="MD5 hash of runtime config")
    version: Optional[str] = Field(None, description="Controller software version")
    platform: Optional[str] = Field(None, description="OS platform string")
    python_version: Optional[str] = Field(None, description="Python interpreter version")
    memory_mb: Optional[int] = Field(None, ge=0, description="Total RAM in MB")
    cpu_count: Optional[int] = Field(None, ge=1, description="Number of CPU cores")


class FullConfig(BaseModel):
    """Complete system configuration."""

    plugins: list[Plugin] = Field(default_factory=list)
    edge_controllers: list[EdgeController] = Field(default_factory=list)


class TrainStatus(BaseModel):
    """Real-time train telemetry."""

    train_id: str = Field(..., min_length=1)
    speed: int = Field(..., ge=0, le=100)
    voltage: float = Field(..., ge=0)
    current: float = Field(..., ge=0)
    position: str = Field(..., min_length=1)


# Resolve forward references after all models are defined
Train.model_rebuild()
