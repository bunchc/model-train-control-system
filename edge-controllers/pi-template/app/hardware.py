from RPi import GPIO
import time

class HardwareController:
    def __init__(self, motor_pins, light_pins, sensor_pins):
        self.motor_pins = motor_pins
        self.light_pins = light_pins
        self.sensor_pins = sensor_pins
        
        GPIO.setmode(GPIO.BCM)
        self.setup_pins()

    def setup_pins(self):
        for pin in self.motor_pins:
            GPIO.setup(pin, GPIO.OUT)
        for pin in self.light_pins:
            GPIO.setup(pin, GPIO.OUT)
        for pin in self.sensor_pins:
            GPIO.setup(pin, GPIO.IN)

    def set_motor_speed(self, motor_index, speed):
        if motor_index < len(self.motor_pins):
            pwm = GPIO.PWM(self.motor_pins[motor_index], 100)
            pwm.start(speed)
            return True
        return False

    def turn_on_light(self, light_index):
        if light_index < len(self.light_pins):
            GPIO.output(self.light_pins[light_index], GPIO.HIGH)
            return True
        return False

    def turn_off_light(self, light_index):
        if light_index < len(self.light_pins):
            GPIO.output(self.light_pins[light_index], GPIO.LOW)
            return True
        return False

    def read_sensor(self, sensor_index):
        if sensor_index < len(self.sensor_pins):
            return GPIO.input(self.sensor_pins[sensor_index])
        return None

    def cleanup(self):
        GPIO.cleanup()