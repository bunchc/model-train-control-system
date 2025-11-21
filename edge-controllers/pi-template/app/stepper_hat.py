"""Stepper motor HAT controller for Waveshare hardware.

This module provides hardware-specific control for the Waveshare Stepper Motor HAT
using the DRV8825 stepper motor driver. It controls stepper motors via GPIO pins.

Hardware Specifications:
    - Board: Waveshare Stepper Motor HAT
    - Driver: DRV8825 (supports 1/32 microstepping)
    - Motors: Bipolar stepper motors (typically NEMA 17)
    - Power: External 12V supply (separate from Pi)

GPIO Pin Mapping (M1 motor channel):
    - DIR (GPIO13):    Direction control (HIGH=forward, LOW=reverse)
    - STEP (GPIO19):   Step pulse (rising edge triggers one step)
    - ENABLE (GPIO12): Enable/disable motor (LOW=enabled, HIGH=disabled)
    - MODE (GPIO16, GPIO17, GPIO20): Microstepping configuration

Microstepping Modes:
    Full step:    MODE pins all LOW  (highest torque, lowest precision)
    1/2 step:     MODE0 HIGH
    1/4 step:     MODE1 HIGH
    1/8 step:     MODE0+MODE1 HIGH
    1/16 step:    MODE2 HIGH
    1/32 step:    MODE0+MODE1+MODE2 HIGH (lowest torque, highest precision)

Architecture Decision:
    Singleton pattern prevents multiple GPIO initializations which would
    cause conflicts. Only one instance can exist per process.

Typical usage:
    controller = StepperMotorHatController()
    controller.start(speed=50, direction=1)  # Forward at 50% speed
    time.sleep(5)
    controller.stop()
"""

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

    Singleton Pattern:
        Only one instance can exist per process. Repeated calls to
        StepperMotorHatController() return the same instance.

    Attributes:
        dir: OutputDevice for direction control (GPIO13)
        step: OutputDevice for step pulses (GPIO19)
        enable: OutputDevice for motor enable (GPIO12)
        mode_pins: List of OutputDevice for microstepping (GPIO16, 17, 20)
        enabled: Boolean indicating if motor is currently enabled

    Example:
        >>> controller = StepperMotorHatController()
        >>> controller.set_direction(1)  # Forward
        >>> controller.enable_motor()
        >>> controller.run_steps(speed=50, steps=200)  # One revolution
        >>> controller.stop()
    """

    _instance: "StepperMotorHatController" = None

    def __new__(cls) -> "StepperMotorHatController":
        """Singleton pattern implementation.

        Ensures only one instance of this controller exists per process.
        Subsequent calls to StepperMotorHatController() return the same instance.

        Returns:
            Singleton instance of StepperMotorHatController

        Note:
            The _initialized flag prevents __init__ from running multiple times.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize stepper motor controller (singleton pattern).

        Sets up GPIO pins for DRV8825 stepper driver. Only runs once due to
        singleton pattern - subsequent calls are no-ops.

        Initial State:
            - Full step mode (MODE pins all LOW)
            - Motor disabled (ENABLE HIGH)
            - _initialized flag set to True

        Note:
            Due to singleton pattern, this only initializes GPIO on first call.
        """
        # Check if already initialized (singleton pattern)
        # __new__ sets _initialized to False on first instantiation
        if getattr(self, "_initialized", False):
            return  # Already initialized, skip GPIO setup

        # Initialize GPIO pins for DRV8825 stepper driver
        # Using BCM pin numbering (GPIO numbers, not physical pin numbers)
        self.dir: OutputDevice = OutputDevice(13)  # Direction control
        self.step: OutputDevice = OutputDevice(19)  # Step pulse (PWM-capable pin)
        self.enable: OutputDevice = OutputDevice(12)  # Enable/disable (active-low)

        # Microstepping mode configuration (3 pins for 6 modes)
        self.mode_pins: List[OutputDevice] = [
            OutputDevice(16),  # MODE0
            OutputDevice(17),  # MODE1
            OutputDevice(20),  # MODE2
        ]

        # Initialize state
        self.enabled: bool = False

        # Configure default operating mode (full step for maximum torque)
        self.set_full_step()

        # Disable motor initially (de-energize coils to save power)
        self.stop()

        # Mark as initialized to prevent repeated GPIO setup
        self._initialized = True

    def set_full_step(self) -> None:
        """Configure motor for full step mode.

        Sets all MODE pins LOW to select full step mode on the DRV8825.
        Full step provides:
        - Maximum torque
        - Lowest precision (200 steps/revolution for typical NEMA 17)
        - Less smooth operation than microstepping

        Note:
            This is the default mode set during initialization.
        """
        # Set all mode pins low for full step
        for pin in self.mode_pins:
            pin.off()
        logger.debug("Set to full step mode")

    def enable_motor(self) -> None:
        """Enable the stepper motor.

        Sets ENABLE pin LOW to energize the motor coils. DRV8825 driver
        uses active-low enable logic.

        Side Effects:
            - Motor coils energized (motor holds position)
            - Power consumption increases
            - Motor may get warm during extended hold

        Note:
            Motor must be enabled before calling run_steps() or start().
        """
        self.enable.off()  # DRV8825: low to enable
        self.enabled = True
        logger.debug("Motor enabled")

    def disable_motor(self) -> None:
        """Disable the stepper motor.

        Sets ENABLE pin HIGH to de-energize the motor coils. DRV8825 driver
        uses active-low enable logic.

        Side Effects:
            - Motor coils de-energized (motor can spin freely)
            - Power consumption reduced
            - Motor no longer holds position (can be moved by hand)

        Note:
            Call this when motor is not in use to reduce power consumption
            and heat generation.
        """
        self.enable.on()  # DRV8825: high to disable
        self.enabled = False
        logger.debug("Motor disabled")

    def start(self, speed: int = 50, direction: int = 1) -> None:
        """Start the motor.

        Convenience method that enables motor, sets direction, and runs steps.
        Equivalent to calling enable_motor(), set_direction(), and run_steps().

        Args:
            speed: Motor speed (1-100). Higher values = faster rotation.
                Typical range: 10-80 for smooth operation.
            direction: Motor direction (1=forward, 0=reverse).
                Forward/reverse is arbitrary - depends on motor wiring.

        Note:
            This method blocks for the duration of run_steps(). For continuous
            rotation, call this method repeatedly or implement async stepping.
        """
        self.enable_motor()
        self.set_direction(direction)
        self.run_steps(speed)
        logger.info(f"Started motor at speed {speed}")

    def stop(self) -> None:
        """Stop the motor.

        Disables the motor by de-energizing coils. Motor will coast to a stop
        and can be moved freely by hand.

        Note:
            For immediate stop while maintaining position, keep motor enabled.
            Simply stop calling run_steps().
        """
        self.disable_motor()
        logger.info("Motor stopped")

    def set_direction(self, direction: int) -> None:
        """Set motor direction.

        Controls DIR pin which determines rotation direction.

        Args:
            direction: 1 for forward (DIR HIGH), 0 for reverse (DIR LOW)

        Note:
            Direction must be set BEFORE sending step pulses. Changing direction
            while motor is moving may cause skipped steps.
        """
        if direction == 1:
            self.dir.on()
        else:
            self.dir.off()
        logger.debug(f"Direction set to {'forward' if direction == 1 else 'reverse'}")

    def run_steps(self, speed: int, steps: int = 200) -> None:
        """Run a specific number of steps.

        Generates step pulses by toggling STEP pin HIGH then LOW.
        Speed is controlled by delay between pulses.

        Speed Calculation:
            delay = max(0.001, 0.02 - (speed / 5000.0))
            - Speed 1:   19ms delay (slow)
            - Speed 50:  10ms delay (medium)
            - Speed 100: 1ms delay (fast)

        Args:
            speed: Motor speed (1-100). Higher = faster rotation.
            steps: Number of steps to execute. For full step mode:
                - 200 steps = one full revolution (1.8° per step)
                - 400 steps = two revolutions

        Note:
            This method blocks for duration of stepping. For 200 steps at speed 50
            with 10ms delay, this blocks for ~4 seconds.

        Example:
            >>> controller.enable_motor()
            >>> controller.set_direction(1)
            >>> controller.run_steps(speed=50, steps=400)  # Two revolutions
        """
        # Calculate delay between step pulses based on desired speed
        # Formula maps speed 1-100 to delay 19ms-1ms (inverse relationship)
        # min() ensures we never go below 1ms (motor mechanical limit)
        delay = max(0.001, 0.02 - (speed / 5000.0))

        # Generate step pulses - each HIGH/LOW cycle is one step
        for _ in range(steps):
            # Rising edge of STEP pin triggers DRV8825 to advance one step
            self.step.on()
            time.sleep(delay)  # Hold HIGH for timing (driver needs ~1µs minimum)

            # Falling edge completes the pulse
            self.step.off()
            time.sleep(delay)  # Wait before next pulse (prevents motor stall)

        logger.debug(f"Ran {steps} steps at speed {speed}")

    def set_speed(self, speed: int) -> None:
        """Set motor speed.

        Convenience method that enables motor and runs steps at specified speed.
        Uses default 200 steps (one revolution in full step mode).

        Args:
            speed: Motor speed (1-100)

        Note:
            This method blocks while stepping. Consider using run_steps() directly
            for more control over step count.
        """
        self.enable_motor()
        self.run_steps(speed)
        logger.info(f"Speed set to {speed}")
