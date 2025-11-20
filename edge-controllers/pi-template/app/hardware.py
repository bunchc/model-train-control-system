"""Hardware controller for GPIO-based train control."""

from typing import List, Optional

from gpiozero import LED, DigitalInputDevice, PWMOutputDevice


class HardwareController:
    """Generic hardware controller for motors, lights, and sensors."""

    def __init__(self, motor_pins: List[int], light_pins: List[int], sensor_pins: List[int]):
        """Initialize hardware controller.

        Args:
            motor_pins: GPIO pin numbers for motors
            light_pins: GPIO pin numbers for lights
            sensor_pins: GPIO pin numbers for sensors
        """
        self.motors: List[PWMOutputDevice] = [PWMOutputDevice(pin) for pin in motor_pins]
        self.lights: List[LED] = [LED(pin) for pin in light_pins]
        self.sensors: List[DigitalInputDevice] = [DigitalInputDevice(pin) for pin in sensor_pins]

    def set_motor_speed(self, motor_index: int, speed: float) -> bool:
        """Set motor speed.

        Args:
            motor_index: Index of motor to control
            speed: Speed value 0-100

        Returns:
            True if successful, False otherwise
        """
        if 0 <= motor_index < len(self.motors):
            # speed should be 0.0 to 1.0 for PWMOutputDevice
            self.motors[motor_index].value = speed / 100.0
            return True
        return False

    def turn_on_light(self, light_index: int) -> bool:
        """Turn on light.

        Args:
            light_index: Index of light to turn on

        Returns:
            True if successful, False otherwise
        """
        if 0 <= light_index < len(self.lights):
            self.lights[light_index].on()
            return True
        return False

    def turn_off_light(self, light_index: int) -> bool:
        """Turn off light.

        Args:
            light_index: Index of light to turn off

        Returns:
            True if successful, False otherwise
        """
        if 0 <= light_index < len(self.lights):
            self.lights[light_index].off()
            return True
        return False

    def read_sensor(self, sensor_index: int) -> Optional[bool]:
        """Read sensor value.

        Args:
            sensor_index: Index of sensor to read

        Returns:
            Sensor value if available, None otherwise
        """
        if 0 <= sensor_index < len(self.sensors):
            return self.sensors[sensor_index].value
        return None

    def cleanup(self) -> None:
        """Cleanup GPIO resources."""
        # gpiozero devices clean up automatically
