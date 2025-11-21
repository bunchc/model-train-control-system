"""Hardware controller for GPIO-based train control.

This module provides a generic hardware abstraction layer for controlling
model trains via Raspberry Pi GPIO pins. It supports:
- Motors (PWM-based speed control)
- Lights (on/off digital control)
- Sensors (digital input reading)

The HardwareController uses gpiozero library which provides:
- Automatic GPIO cleanup on exit
- Thread-safe pin access
- Clean abstraction over RPi.GPIO

Architecture Decision:
    This generic controller is suitable for simple DC motor + LED setups.
    For stepper motors or specialized hardware (like Waveshare HAT),
    use stepper_hat.py which provides hardware-specific control.

Typical GPIO Setup:
    Motors:  PWM-capable pins (GPIO12, GPIO13, GPIO18, GPIO19)
    Lights:  Any GPIO pins
    Sensors: Pins with pull-up/pull-down resistors

Typical usage:
    controller = HardwareController(
        motor_pins=[18, 19],
        light_pins=[23, 24],
        sensor_pins=[25, 26]
    )
    controller.set_motor_speed(0, 75)  # Motor 0 at 75% speed
    controller.turn_on_light(0)        # Light 0 on
"""

from typing import List, Optional

from gpiozero import LED, DigitalInputDevice, PWMOutputDevice


class HardwareController:
    """Generic hardware controller for motors, lights, and sensors.

    This class provides index-based access to GPIO-controlled hardware.
    Each hardware type (motors, lights, sensors) is managed as a list,
    allowing control of multiple identical devices.

    Attributes:
        motors: List of PWMOutputDevice for speed-controlled motors
        lights: List of LED for on/off lights
        sensors: List of DigitalInputDevice for binary sensors

    Example:
        >>> controller = HardwareController(
        ...     motor_pins=[18],
        ...     light_pins=[23, 24],
        ...     sensor_pins=[25]
        ... )
        >>> controller.set_motor_speed(0, 50)  # 50% speed
        True
        >>> controller.turn_on_light(0)        # Front light on
        True
        >>> occupied = controller.read_sensor(0)  # Track sensor
    """

    def __init__(self, motor_pins: List[int], light_pins: List[int], sensor_pins: List[int]):
        """Initialize hardware controller.

        Creates gpiozero device instances for all specified GPIO pins.
        Devices are automatically configured and ready to use.

        Args:
            motor_pins: GPIO pin numbers for motors (BCM numbering).
                Must be PWM-capable pins (12, 13, 18, 19 on Pi 4).
            light_pins: GPIO pin numbers for lights (BCM numbering).
                Any GPIO pins can be used.
            sensor_pins: GPIO pin numbers for sensors (BCM numbering).
                Configure pull-up/pull-down in hardware or modify code.

        Note:
            gpiozero uses BCM pin numbering by default (GPIO numbers,
            not physical pin numbers).

        Example:
            >>> # Single motor on GPIO18, two lights on GPIO23/24
            >>> controller = HardwareController(
            ...     motor_pins=[18],
            ...     light_pins=[23, 24],
            ...     sensor_pins=[]
            ... )
        """
        self.motors: List[PWMOutputDevice] = [PWMOutputDevice(pin) for pin in motor_pins]
        self.lights: List[LED] = [LED(pin) for pin in light_pins]
        self.sensors: List[DigitalInputDevice] = [DigitalInputDevice(pin) for pin in sensor_pins]

    def set_motor_speed(self, motor_index: int, speed: float) -> bool:
        """Set motor speed.

        Controls motor speed using PWM (Pulse Width Modulation).
        Speed value is converted from 0-100 percentage to 0.0-1.0
        duty cycle for PWMOutputDevice.

        Args:
            motor_index: Index of motor to control (0-based, must be < len(motors))
            speed: Speed value 0-100 (percentage of maximum speed)
                0 = stopped, 100 = full speed

        Returns:
            True if motor exists and speed was set, False if motor_index invalid

        Example:
            >>> controller.set_motor_speed(0, 75)  # 75% speed
            True
            >>> controller.set_motor_speed(99, 50)  # Invalid index
            False
        """
        if 0 <= motor_index < len(self.motors):
            # speed should be 0.0 to 1.0 for PWMOutputDevice
            self.motors[motor_index].value = speed / 100.0
            return True
        return False

    def turn_on_light(self, light_index: int) -> bool:
        """Turn on light.

        Sets GPIO pin HIGH to turn on LED or light circuit.

        Args:
            light_index: Index of light to turn on (0-based, must be < len(lights))

        Returns:
            True if light exists and was turned on, False if light_index invalid

        Example:
            >>> controller.turn_on_light(0)  # Front headlight
            True
        """
        if 0 <= light_index < len(self.lights):
            self.lights[light_index].on()
            return True
        return False

    def turn_off_light(self, light_index: int) -> bool:
        """Turn off light.

        Sets GPIO pin LOW to turn off LED or light circuit.

        Args:
            light_index: Index of light to turn off (0-based, must be < len(lights))

        Returns:
            True if light exists and was turned off, False if light_index invalid

        Example:
            >>> controller.turn_off_light(1)  # Rear light
            True
        """
        if 0 <= light_index < len(self.lights):
            self.lights[light_index].off()
            return True
        return False

    def read_sensor(self, sensor_index: int) -> Optional[bool]:
        """Read sensor value.

        Reads digital input from sensor (typically infrared, hall effect,
        or reed switch for track occupancy detection).

        Args:
            sensor_index: Index of sensor to read (0-based, must be < len(sensors))

        Returns:
            - True: Sensor active (e.g., train present)
            - False: Sensor inactive (e.g., track clear)
            - None: Invalid sensor_index

        Note:
            Interpretation depends on sensor type and wiring (normally-open
            vs. normally-closed).

        Example:
            >>> if controller.read_sensor(0):
            ...     print("Track section occupied")
        """
        if 0 <= sensor_index < len(self.sensors):
            return self.sensors[sensor_index].value
        return None

    def cleanup(self) -> None:
        """Cleanup GPIO resources.

        gpiozero devices clean up automatically when they go out of scope
        or when the process exits. This method is provided for API
        consistency but does not perform explicit cleanup.

        Note:
            gpiozero's auto-cleanup handles:
            - Releasing GPIO pins
            - Stopping PWM
            - Turning off LEDs
        """
        # gpiozero devices clean up automatically
