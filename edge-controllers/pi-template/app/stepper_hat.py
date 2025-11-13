import time
import logging
from gpiozero import OutputDevice

class StepperMotorHatController:
    """
    Controls M1 stepper motor on Waveshare Stepper Motor HAT using GPIO pins.
    DIR: GPIO13
    STEP: GPIO19
    ENABLE: GPIO12
    MODE: GPIO16, GPIO17, GPIO20 (for microstepping, default to full step)
    """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.dir = OutputDevice(13)
        self.step = OutputDevice(19)
        self.enable = OutputDevice(12)
        self.mode_pins = [OutputDevice(16), OutputDevice(17), OutputDevice(20)]
        self.enabled = False
        self.set_full_step()
        self.stop()
        self._initialized = True

    def set_full_step(self):
        # Set all mode pins low for full step
        for pin in self.mode_pins:
            pin.off()
        logging.debug("StepperMotorHatController: Set to full step mode.")

    def enable_motor(self):
        self.enable.off()  # DRV8825: low to enable
        self.enabled = True
        logging.debug("StepperMotorHatController: Motor enabled.")

    def disable_motor(self):
        self.enable.on()  # DRV8825: high to disable
        self.enabled = False
        logging.debug("StepperMotorHatController: Motor disabled.")

    def start(self, speed=50, direction=1):
        self.enable_motor()
        self.set_direction(direction)
        self.run_steps(speed)
        logging.info(f"StepperMotorHatController: Started motor at speed {speed}.")

    def stop(self):
        self.disable_motor()
        logging.info("StepperMotorHatController: Motor stopped.")

    def set_direction(self, direction):
        if direction == 1:
            self.dir.on()
        else:
            self.dir.off()
        logging.debug(f"StepperMotorHatController: Direction set to {'forward' if direction == 1 else 'reverse'}.")

    def run_steps(self, speed, steps=200):
        # speed: 1-100, map to delay between steps
        delay = max(0.001, 0.02 - (speed / 5000.0))
        for _ in range(steps):
            self.step.on()
            time.sleep(delay)
            self.step.off()
            time.sleep(delay)
        logging.debug(f"StepperMotorHatController: Ran {steps} steps at speed {speed}.")

    def set_speed(self, speed):
        self.enable_motor()
        self.run_steps(speed)
        logging.info(f"StepperMotorHatController: Speed set to {speed}.")
