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
    status: Optional["TrainStatus"] = None


class EdgeController(BaseModel):
    """Edge controller configuration."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    address: Optional[str] = None
    enabled: bool = True
    trains: list[Train] = Field(default_factory=list)


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
