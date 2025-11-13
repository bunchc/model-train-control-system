from gpiozero import PWMOutputDevice, LED, DigitalInputDevice
import time

class HardwareController:
    def __init__(self, motor_pins, light_pins, sensor_pins):
        self.motors = [PWMOutputDevice(pin) for pin in motor_pins]
        self.lights = [LED(pin) for pin in light_pins]
        self.sensors = [DigitalInputDevice(pin) for pin in sensor_pins]

    # Pin setup is handled by gpiozero device constructors

    def set_motor_speed(self, motor_index, speed):
        if motor_index < len(self.motors):
            # speed should be 0.0 to 1.0 for PWMOutputDevice
            self.motors[motor_index].value = speed / 100.0
            return True
        return False

    def turn_on_light(self, light_index):
        if light_index < len(self.lights):
            self.lights[light_index].on()
            return True
        return False

    def turn_off_light(self, light_index):
        if light_index < len(self.lights):
            self.lights[light_index].off()
            return True
        return False

    def read_sensor(self, sensor_index):
        if sensor_index < len(self.sensors):
            return self.sensors[sensor_index].value
        return None

    def cleanup(self):
        # gpiozero devices clean up automatically
        pass