"""Stepper motor HAT controller for Waveshare hardware."""

import logging
import time
from typing import List

from gpiozero import OutputDevice


logger = logging.getLogger(__name__)


class StepperMotorHatController:
    """Controls M1 stepper motor on Waveshare Stepper Motor HAT using GPIO pins.

    GPIO Pin Mapping:
        DIR: GPIO13 (direction)
        STEP: GPIO19 (step pulse)
        ENABLE: GPIO12 (enable/disable)
        MODE: GPIO16, GPIO17, GPIO20 (microstepping configuration)

    This is a Singleton to prevent multiple GPIO initializations.
    """

    _instance: "StepperMotorHatController" = None

    def __new__(cls) -> "StepperMotorHatController":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize stepper motor controller (singleton pattern)."""
        if getattr(self, "_initialized", False):
            return

        self.dir: OutputDevice = OutputDevice(13)
        self.step: OutputDevice = OutputDevice(19)
        self.enable: OutputDevice = OutputDevice(12)
        self.mode_pins: List[OutputDevice] = [OutputDevice(16), OutputDevice(17), OutputDevice(20)]
        self.enabled: bool = False
        self.set_full_step()
        self.stop()
        self._initialized = True

    def set_full_step(self) -> None:
        """Configure motor for full step mode."""
        # Set all mode pins low for full step
        for pin in self.mode_pins:
            pin.off()
        logger.debug("Set to full step mode")

    def enable_motor(self) -> None:
        """Enable the stepper motor."""
        self.enable.off()  # DRV8825: low to enable
        self.enabled = True
        logger.debug("Motor enabled")

    def disable_motor(self) -> None:
        """Disable the stepper motor."""
        self.enable.on()  # DRV8825: high to disable
        self.enabled = False
        logger.debug("Motor disabled")

    def start(self, speed: int = 50, direction: int = 1) -> None:
        """Start the motor.

        Args:
            speed: Motor speed (1-100)
            direction: Motor direction (1=forward, 0=reverse)
        """
        self.enable_motor()
        self.set_direction(direction)
        self.run_steps(speed)
        logger.info(f"Started motor at speed {speed}")

    def stop(self) -> None:
        """Stop the motor."""
        self.disable_motor()
        logger.info("Motor stopped")

    def set_direction(self, direction: int) -> None:
        """Set motor direction.

        Args:
            direction: 1 for forward, 0 for reverse
        """
        if direction == 1:
            self.dir.on()
        else:
            self.dir.off()
        logger.debug(f"Direction set to {'forward' if direction == 1 else 'reverse'}")

    def run_steps(self, speed: int, steps: int = 200) -> None:
        """Run a specific number of steps.

        Args:
            speed: Motor speed (1-100)
            steps: Number of steps to execute
        """
        # speed: 1-100, map to delay between steps
        delay = max(0.001, 0.02 - (speed / 5000.0))
        for _ in range(steps):
            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)
        logger.debug(f"Ran {steps} steps at speed {speed}")

    def set_speed(self, speed: int) -> None:
        """Set motor speed.

        Args:
            speed: Motor speed (1-100)
        """
        self.enable_motor()
        self.run_steps(speed)
        logger.info(f"Speed set to {speed}")
