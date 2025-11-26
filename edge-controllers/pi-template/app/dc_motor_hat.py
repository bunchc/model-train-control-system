"""DC motor controller for Waveshare Stepper Motor HAT.

This module provides control for the DC motor channels (M1-M4) on the Waveshare
Stepper Motor HAT using the PCA9685 I2C PWM controller chip.

Hardware Specifications:
    - Board: Waveshare Stepper Motor HAT
    - PWM Controller: PCA9685 (16-channel, 12-bit PWM over I2C)
    - I2C Address: 0x6F (default)
    - DC Motor Channels: M1, M2, M3, M4 (four independent DC motor outputs)
    - Power: External 5-12V supply (separate from Pi)

PCA9685 Channel Mapping for Motor 2 (M2):
    - PWM Channel 13: Speed control (0-4095, where 4095 = 100% duty cycle)
    - PWM Channel 12: Direction input 2 (IN2)
    - PWM Channel 11: Direction input 1 (IN1)

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
    """Controls DC Motor 2 (M2) on Waveshare Stepper Motor HAT via I2C.

    PCA9685 PWM Channel Mapping for Motor 2:
        - Channel 13: Speed control (PWM)
        - Channel 12: Direction control (IN2)
        - Channel 11: Direction control (IN1)

    This is a Singleton to prevent multiple I2C initializations.

    Attributes:
        pwm: PCA9685 controller instance
        pwm_pin: PWM channel for speed (13)
        in1_pin: PWM channel for direction 1 (11)
        in2_pin: PWM channel for direction 2 (12)
        current_speed: Current motor speed (0-100)
        current_direction: Current motor direction (1=forward, 0=reverse)

    Example:
        >>> controller = DCMotorHatController()
        >>> controller.set_speed(75)  # 75% speed forward
        >>> controller.set_direction(0)  # Change to reverse
        >>> controller.stop()  # Stop motor
    """

    _instance: "DCMotorHatController" = None

    def __new__(cls) -> "DCMotorHatController":
        """Singleton pattern implementation.

        Ensures only one instance of this controller exists per process.
        Subsequent calls to DCMotorHatController() return the same instance.

        Returns:
            Singleton instance of DCMotorHatController
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, i2c_address: int = 0x6F) -> None:
        """Initialize DC motor controller (singleton pattern).

        Sets up I2C communication with PCA9685 for Motor 2 (M2) control.
        Only runs once due to singleton pattern - subsequent calls are no-ops.

        Args:
            i2c_address: I2C address of the PCA9685 (default 0x6F)

        Initial State:
            - Motor stopped (PWM = 0)
            - Direction = forward
            - _initialized flag set to True
        """
        # Check if already initialized (singleton pattern)
        if getattr(self, "_initialized", False):
            return  # Already initialized, skip I2C setup

        # Initialize PCA9685 PWM controller
        self.pwm = PCA9685(i2c_address=i2c_address)

        # Motor 2 uses PWM channels 11, 12, 13
        # Based on Raspi_MotorHAT.py: motor num=1 (second motor, 0-indexed)
        self.pwm_pin = 13  # Speed control
        self.in2_pin = 12  # Direction control 2
        self.in1_pin = 11  # Direction control 1

        # Initialize state
        self.current_speed: int = 0
        self.current_direction: int = 1  # 1=forward, 0=reverse

        # Set initial direction to forward and stop motor
        self._set_forward()
        self.pwm.set_pwm(self.pwm_pin, 0, 0)

        # Mark as initialized to prevent repeated I2C setup
        self._initialized = True
        logger.info(f"DC Motor HAT controller initialized (Motor 2, I2C addr 0x{i2c_address:02X})")

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
