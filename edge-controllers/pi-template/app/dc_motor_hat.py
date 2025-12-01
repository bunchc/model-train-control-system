"""DC motor controller for Waveshare Stepper Motor HAT.

This module provides control for the DC motor channels (M1-M4) on the Waveshare
Stepper Motor HAT using the PCA9685 I2C PWM controller chip.

Hardware Specifications:
    - Board: Waveshare Stepper Motor HAT
    - PWM Controller: PCA9685 (16-channel, 12-bit PWM over I2C)
    - I2C Address: 0x6F (default)
    - DC Motor Channels: M1, M2, M3, M4 (four independent DC motor outputs)
    - Power: External 5-12V supply (separate from Pi)

PCA9685 Channel Mapping (per motor):
    Motor 1 (M1): PWM=8,  IN2=9,  IN1=10
    Motor 2 (M2): PWM=13, IN2=12, IN1=11
    Motor 3 (M3): PWM=2,  IN2=3,  IN1=4
    Motor 4 (M4): PWM=7,  IN2=6,  IN1=5

Direction Control Logic (via PWM channels):
    - Forward:  IN1=4096 (HIGH), IN2=0 (LOW)
    - Reverse:  IN1=0 (LOW), IN2=4096 (HIGH)
    - Brake:    IN1=0 (LOW), IN2=0 (LOW)
    - Coast:    IN1=4096 (HIGH), IN2=4096 (HIGH)

Reference:
    Based on Adafruit Motor HAT design and compatible with Raspi-MotorHat library.
    See: https://github.com/Alictronix/Raspi-MotorHat

Architecture Decision:
    Singleton pattern prevents multiple I2C initializations which would
    cause conflicts. Only one instance can exist per process.

Typical usage:
    controller = DCMotorHatController()
    controller.set_speed(50)  # Forward at 50% speed
    controller.set_direction(0)  # Reverse
    controller.set_speed(30)  # Reverse at 30% speed
    controller.stop()  # Coast to stop
"""

import logging
import time
from functools import wraps
from typing import Callable, ClassVar, Optional, TypeVar


try:
    from smbus2 import SMBus
except ImportError:
    # Fallback for systems without smbus2
    try:
        import smbus

        SMBus = smbus.SMBus
    except ImportError:
        SMBus = None


logger = logging.getLogger(__name__)

# Type variable for retry decorator
T = TypeVar("T")


def retry_i2c_operation(
    max_retries: int = 3,
    initial_delay: float = 0.01,
    backoff_factor: float = 2.0,
    max_delay: float = 0.5,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry I2C operations with exponential backoff.

    I2C operations can fail intermittently due to:
    - Bus contention (multiple devices)
    - Clock stretching issues
    - Electrical noise
    - Timing issues

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 0.01)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 0.5)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_i2c_operation(max_retries=3)
        def write_data(self, register, value):
            self.bus.write_byte_data(self.address, register, value)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except OSError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"I2C operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.3f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.exception(f"I2C operation failed after {max_retries + 1} attempts")

            # If we get here, all retries failed
            raise last_exception

        return wrapper

    return decorator


# PCA9685 Register addresses
_MODE1 = 0x00
_MODE2 = 0x01
_PRESCALE = 0xFE
_LED0_ON_L = 0x06
_LED0_ON_H = 0x07
_LED0_OFF_L = 0x08
_LED0_OFF_H = 0x09

# PCA9685 Mode bits
_RESTART = 0x80
_SLEEP = 0x10
_ALLCALL = 0x01
_OUTDRV = 0x04

# Motor direction constants
FORWARD = 1
BACKWARD = 2
RELEASE = 4


class PCA9685:
    """Interface to PCA9685 PWM chip over I2C.

    The PCA9685 is a 16-channel, 12-bit PWM controller with I2C interface.
    Used by the Waveshare Motor HAT for motor control.

    Attributes:
        i2c_address: I2C address of the PCA9685 chip (default 0x6F)
        bus: SMBus instance for I2C communication
    """

    def __init__(self, i2c_address: int = 0x6F, bus_number: int = 1) -> None:
        """Initialize PCA9685 PWM controller.

        Args:
            i2c_address: I2C address of the PCA9685 (default 0x6F for Waveshare HAT)
            bus_number: I2C bus number (1 for Raspberry Pi, 0 for older models)

        Raises:
            RuntimeError: If SMBus is not available
        """
        if SMBus is None:
            raise RuntimeError("SMBus library not available. Install with: pip install smbus2")

        self.i2c_address = i2c_address
        self.bus = SMBus(bus_number)

        # Reset and initialize the PCA9685
        self._reset()

    def _reset(self) -> None:
        """Reset the PCA9685 to default state and configure for motor control."""
        # Set all PWM channels to 0
        self.set_all_pwm(0, 0)

        # Configure MODE2: outputs change on ACK (totem pole output)
        self.bus.write_byte_data(self.i2c_address, _MODE2, _OUTDRV)

        # Configure MODE1: respond to all-call, wake up from sleep
        self.bus.write_byte_data(self.i2c_address, _MODE1, _ALLCALL)
        time.sleep(0.005)  # Wait for oscillator to stabilize

        # Wake up (disable sleep)
        mode1 = self.bus.read_byte_data(self.i2c_address, _MODE1)
        mode1 = mode1 & ~_SLEEP
        self.bus.write_byte_data(self.i2c_address, _MODE1, mode1)
        time.sleep(0.005)  # Wait for oscillator

        # Set PWM frequency to 1600 Hz (good for motors)
        self.set_pwm_freq(1600)

    def set_pwm_freq(self, freq_hz: int) -> None:
        """Set the PWM frequency for all channels.

        Args:
            freq_hz: Desired frequency in Hz (typically 1600 Hz for motors)
        """
        # Calculate prescale value: prescale = round(25MHz / (4096 * freq)) - 1
        prescale_val = 25000000.0  # 25 MHz
        prescale_val /= 4096.0  # 12-bit resolution
        prescale_val /= float(freq_hz)
        prescale_val -= 1.0
        prescale = int(prescale_val + 0.5)

        # Set prescale (must be in sleep mode)
        old_mode = self.bus.read_byte_data(self.i2c_address, _MODE1)
        new_mode = (old_mode & 0x7F) | _SLEEP
        self.bus.write_byte_data(self.i2c_address, _MODE1, new_mode)
        self.bus.write_byte_data(self.i2c_address, _PRESCALE, prescale)
        self.bus.write_byte_data(self.i2c_address, _MODE1, old_mode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.i2c_address, _MODE1, old_mode | _RESTART)

    @retry_i2c_operation(max_retries=3, initial_delay=0.01)
    def set_pwm(self, channel: int, on: int, off: int) -> None:
        """Set PWM value for a specific channel.

        Args:
            channel: PWM channel (0-15)
            on: 12-bit value (0-4095) for when signal turns on
            off: 12-bit value (0-4095) for when signal turns off
        """
        self.bus.write_byte_data(self.i2c_address, _LED0_ON_L + 4 * channel, on & 0xFF)
        self.bus.write_byte_data(self.i2c_address, _LED0_ON_H + 4 * channel, on >> 8)
        self.bus.write_byte_data(self.i2c_address, _LED0_OFF_L + 4 * channel, off & 0xFF)
        self.bus.write_byte_data(self.i2c_address, _LED0_OFF_H + 4 * channel, off >> 8)

    @retry_i2c_operation(max_retries=3, initial_delay=0.01)
    def set_all_pwm(self, on: int, off: int) -> None:
        """Set PWM value for all channels.

        Args:
            on: 12-bit value (0-4095) for when signal turns on
            off: 12-bit value (0-4095) for when signal turns off
        """
        self.bus.write_byte_data(self.i2c_address, 0xFA, on & 0xFF)
        self.bus.write_byte_data(self.i2c_address, 0xFB, on >> 8)
        self.bus.write_byte_data(self.i2c_address, 0xFC, off & 0xFF)
        self.bus.write_byte_data(self.i2c_address, 0xFD, off >> 8)

    def set_pin(self, pin: int, value: int) -> None:
        """Set a pin to full HIGH (4096) or LOW (0).

        Args:
            pin: PWM channel (0-15)
            value: 0 for LOW, 1 for HIGH

        Raises:
            ValueError: If pin or value is out of range
        """
        if pin < 0 or pin > 15:
            raise ValueError("PWM pin must be between 0 and 15")
        if value not in (0, 1):
            raise ValueError("Pin value must be 0 or 1")

        if value == 0:
            self.set_pwm(pin, 0, 4096)  # Full OFF
        else:
            self.set_pwm(pin, 4096, 0)  # Full ON


class DCMotorHatController:
    """Controls DC Motors (M1-M4) on Waveshare Stepper Motor HAT via I2C.

    PCA9685 PWM Channel Mapping:
        Motor 1 (M1): PWM=8,  IN2=9,  IN1=10
        Motor 2 (M2): PWM=13, IN2=12, IN1=11
        Motor 3 (M3): PWM=2,  IN2=3,  IN1=4
        Motor 4 (M4): PWM=7,  IN2=6,  IN1=5

    Attributes:
        pwm: PCA9685 controller instance (shared across all motors)
        motor_num: Motor number (1-4)
        pwm_pin: PWM channel for speed control
        in1_pin: PWM channel for direction control 1
        in2_pin: PWM channel for direction control 2
        current_speed: Current motor speed (0-100)
        current_direction: Current motor direction (1=forward, 0=reverse)

    Example:
        >>> motor1 = DCMotorHatController(motor_num=1)  # Control M1
        >>> motor3 = DCMotorHatController(motor_num=3)  # Control M3
        >>> motor1.set_speed(75)
        >>> motor3.set_speed(50)
    """

    # Shared PCA9685 instance across all motors (class variable)
    _shared_pwm: ClassVar[Optional[PCA9685]] = None

    # Motor channel mapping: motor_num -> (pwm_pin, in2_pin, in1_pin)
    _MOTOR_CHANNELS: ClassVar[dict[int, tuple[int, int, int]]] = {
        1: (8, 9, 10),  # M1
        2: (13, 12, 11),  # M2
        3: (2, 3, 4),  # M3
        4: (7, 6, 5),  # M4
    }

    def __init__(self, motor_num: int = 1, i2c_address: int = 0x6F) -> None:
        """Initialize DC motor controller for specified motor.

        Args:
            motor_num: Motor number (1-4) corresponding to M1-M4 on the HAT
            i2c_address: I2C address of the PCA9685 (default 0x6F)

        Raises:
            ValueError: If motor_num is not in range 1-4

        Initial State:
            - Motor stopped (PWM = 0)
            - Direction = forward
        """
        if motor_num not in self._MOTOR_CHANNELS:
            raise ValueError(f"motor_num must be 1-4, got {motor_num}")

        # Initialize shared PCA9685 controller (only once)
        if DCMotorHatController._shared_pwm is None:
            DCMotorHatController._shared_pwm = PCA9685(i2c_address=i2c_address)
            logger.info(f"PCA9685 PWM controller initialized (I2C addr 0x{i2c_address:02X})")

        self.pwm = DCMotorHatController._shared_pwm
        self.motor_num = motor_num

        # Get motor-specific PWM channels
        self.pwm_pin, self.in2_pin, self.in1_pin = self._MOTOR_CHANNELS[motor_num]

        # Initialize state
        self.current_speed: int = 0
        self.current_direction: int = 1  # 1=forward, 0=reverse

        # Set initial direction to forward and stop motor
        self._set_forward()
        self.pwm.set_pwm(self.pwm_pin, 0, 0)

        logger.info(
            f"DC Motor M{motor_num} initialized (PWM={self.pwm_pin}, "
            f"IN1={self.in1_pin}, IN2={self.in2_pin})"
        )

    def _set_forward(self) -> None:
        """Set motor direction to forward.

        Sets IN1=HIGH, IN2=LOW for forward direction via PWM channels.
        This does not start the motor - use set_speed() to apply power.
        """
        self.pwm.set_pin(self.in2_pin, 0)  # IN2 = LOW
        self.pwm.set_pin(self.in1_pin, 1)  # IN1 = HIGH
        self.current_direction = 1
        logger.debug("Direction: forward")

    def _set_reverse(self) -> None:
        """Set motor direction to reverse.

        Sets IN1=LOW, IN2=HIGH for reverse direction via PWM channels.
        This does not start the motor - use set_speed() to apply power.
        """
        self.pwm.set_pin(self.in1_pin, 0)  # IN1 = LOW
        self.pwm.set_pin(self.in2_pin, 1)  # IN2 = HIGH
        self.current_direction = 0
        logger.debug("Direction: reverse")

    def _brake(self) -> None:
        """Apply electronic brake.

        Sets IN1=LOW, IN2=LOW and PWM=0 for immediate stop with braking.
        Motor will stop quickly and resist movement.
        """
        self.pwm.set_pin(self.in1_pin, 0)  # IN1 = LOW
        self.pwm.set_pin(self.in2_pin, 0)  # IN2 = LOW
        self.pwm.set_pwm(self.pwm_pin, 0, 0)  # PWM = 0
        logger.debug("Brake applied")

    def set_direction(self, direction: int) -> None:
        """Set motor direction.

        Args:
            direction: 1 for forward, 0 for reverse

        Note:
            Motor continues at current speed in new direction.
            To change direction safely, call stop() first, then
            set_direction(), then set_speed().
        """
        if direction == 1:
            self._set_forward()
        else:
            self._set_reverse()
        logger.info(f"Direction set to {'forward' if direction == 1 else 'reverse'}")

    def set_speed(self, speed: int) -> None:
        """Set motor speed.

        Args:
            speed: Motor speed (0-100)
                - 0: stopped
                - 1-100: speed percentage (higher = faster)

        Note:
            Motor runs in current direction at specified speed.
            Direction can be changed with set_direction().
        """
        # Clamp speed to valid range
        speed = max(0, min(100, speed))

        # Convert 0-100 to 0-4095 (12-bit PWM range)
        # Speed 100 = 4095, Speed 0 = 0
        pwm_value = int((speed / 100.0) * 4095)

        # Apply PWM to motor speed channel
        self.pwm.set_pwm(self.pwm_pin, 0, pwm_value)
        self.current_speed = speed

        logger.info(
            f"Speed set to {speed}% ({'forward' if self.current_direction == 1 else 'reverse'})"
        )

    def start(self, speed: int = 50, direction: int = 1) -> None:
        """Start the motor at specified speed and direction.

        Convenience method that sets both direction and speed.

        Args:
            speed: Motor speed (0-100). Default: 50
            direction: Motor direction (1=forward, 0=reverse). Default: 1
        """
        self.set_direction(direction)
        self.set_speed(speed)
        logger.info(
            f"Motor started: speed={speed}, direction={'forward' if direction == 1 else 'reverse'}"
        )

    def stop(self) -> None:
        """Stop the motor (coast to stop).

        Sets PWM to 0 while maintaining direction state.
        Motor will coast to a stop and can spin freely.

        For immediate stop with braking, use _brake() instead.
        """
        self.pwm.set_pwm(self.pwm_pin, 0, 0)  # Set speed to 0
        self.current_speed = 0
        logger.info("Motor stopped")

    def cleanup(self) -> None:
        """Release all I2C resources.

        Should be called when the controller is no longer needed.
        Stops the motor and closes I2C bus connection.

        Warning:
            After calling cleanup(), this instance cannot be reused.
            Create a new instance if motor control is needed again.
        """
        logger.info("Cleaning up DC motor HAT I2C resources")
        self.stop()  # Ensure motor is stopped
        if hasattr(self, "pwm") and hasattr(self.pwm, "bus"):
            self.pwm.bus.close()
        logger.info("DC motor HAT I2C cleanup complete")
