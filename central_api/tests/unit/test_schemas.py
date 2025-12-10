"""Unit tests for Pydantic schemas.

Tests validation, serialization, and default values for API models.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ControllerHeartbeat,
    EdgeController,
    Train,
    TrainPlugin,
)


class TestEdgeController:
    """Tests for EdgeController model."""

    def test_minimal_controller_serialization(self) -> None:
        """EdgeController with only required fields serializes correctly."""
        controller = EdgeController(
            id="ctrl-001",
            name="Test Controller",
        )

        data = controller.model_dump()

        assert data["id"] == "ctrl-001"
        assert data["name"] == "Test Controller"
        assert data["enabled"] is True  # default
        assert data["status"] == "unknown"  # default
        assert data["trains"] == []  # default

    def test_controller_with_telemetry_fields(self) -> None:
        """EdgeController with all telemetry fields serializes correctly."""
        controller = EdgeController(
            id="ctrl-002",
            name="Pi Controller",
            address="192.168.1.100",
            first_seen="2025-12-04T10:00:00",
            last_seen="2025-12-04T12:30:00",
            config_hash="a1b2c3d4e5f6",
            version="1.0.0",
            platform="Linux-5.15.0-aarch64",
            python_version="3.11.2",
            memory_mb=3906,
            cpu_count=4,
            status="online",
        )

        data = controller.model_dump()

        assert data["address"] == "192.168.1.100"
        assert data["first_seen"] == "2025-12-04T10:00:00"
        assert data["last_seen"] == "2025-12-04T12:30:00"
        assert data["config_hash"] == "a1b2c3d4e5f6"
        assert data["version"] == "1.0.0"
        assert data["platform"] == "Linux-5.15.0-aarch64"
        assert data["python_version"] == "3.11.2"
        assert data["memory_mb"] == 3906
        assert data["cpu_count"] == 4
        assert data["status"] == "online"

    def test_controller_with_trains(self) -> None:
        """EdgeController with assigned trains serializes correctly."""
        train = Train(
            id="train-001",
            name="Express",
            plugin=TrainPlugin(name="dc_motor"),
        )
        controller = EdgeController(
            id="ctrl-003",
            name="Controller with Train",
            trains=[train],
        )

        data = controller.model_dump()

        assert len(data["trains"]) == 1
        assert data["trains"][0]["id"] == "train-001"
        assert data["trains"][0]["name"] == "Express"

    def test_controller_telemetry_fields_optional(self) -> None:
        """Telemetry fields can be None without validation errors."""
        controller = EdgeController(
            id="ctrl-004",
            name="Minimal Controller",
            first_seen=None,
            last_seen=None,
            config_hash=None,
            version=None,
            platform=None,
            python_version=None,
            memory_mb=None,
            cpu_count=None,
        )

        data = controller.model_dump()

        assert data["first_seen"] is None
        assert data["last_seen"] is None
        assert data["config_hash"] is None
        assert data["memory_mb"] is None
        assert data["cpu_count"] is None

    def test_controller_backwards_compatible(self) -> None:
        """EdgeController can be created from dict without new fields (API compat)."""
        # Simulate data from older API client that doesn't send new fields
        old_format_data = {
            "id": "ctrl-old",
            "name": "Old Client Controller",
            "enabled": True,
            "trains": [],
        }

        controller = EdgeController(**old_format_data)

        assert controller.id == "ctrl-old"
        assert controller.status == "unknown"  # default applied
        assert controller.first_seen is None
        assert controller.memory_mb is None


class TestControllerHeartbeat:
    """Tests for ControllerHeartbeat model."""

    def test_empty_heartbeat_valid(self) -> None:
        """Heartbeat with no fields is valid (just updates last_seen)."""
        heartbeat = ControllerHeartbeat()

        data = heartbeat.model_dump()

        assert data["config_hash"] is None
        assert data["version"] is None
        assert data["platform"] is None
        assert data["memory_mb"] is None
        assert data["cpu_count"] is None

    def test_full_heartbeat(self) -> None:
        """Heartbeat with all fields validates and serializes correctly."""
        heartbeat = ControllerHeartbeat(
            config_hash="abcdef123456",
            version="2.0.0",
            platform="Linux-6.1.0-rpi-arm64",
            python_version="3.12.0",
            memory_mb=8192,
            cpu_count=8,
        )

        data = heartbeat.model_dump()

        assert data["config_hash"] == "abcdef123456"
        assert data["version"] == "2.0.0"
        assert data["platform"] == "Linux-6.1.0-rpi-arm64"
        assert data["python_version"] == "3.12.0"
        assert data["memory_mb"] == 8192
        assert data["cpu_count"] == 8

    def test_partial_heartbeat(self) -> None:
        """Heartbeat with only some fields is valid."""
        heartbeat = ControllerHeartbeat(
            version="1.5.0",
            cpu_count=4,
        )

        data = heartbeat.model_dump()

        assert data["version"] == "1.5.0"
        assert data["cpu_count"] == 4
        assert data["config_hash"] is None
        assert data["memory_mb"] is None

    def test_heartbeat_memory_validation(self) -> None:
        """Heartbeat rejects negative memory values."""
        with pytest.raises(ValidationError) as exc_info:
            ControllerHeartbeat(memory_mb=-100)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("memory_mb",)
        assert "greater than or equal to 0" in errors[0]["msg"]

    def test_heartbeat_cpu_count_validation(self) -> None:
        """Heartbeat rejects zero or negative CPU count."""
        with pytest.raises(ValidationError) as exc_info:
            ControllerHeartbeat(cpu_count=0)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("cpu_count",)
        assert "greater than or equal to 1" in errors[0]["msg"]
