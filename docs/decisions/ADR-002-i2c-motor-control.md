# ADR-002: I2C Motor Control Architecture

**Status:** Accepted  
**Date:** 2025-11-25  

## Context

The edge controllers need to control DC motors via the Waveshare Stepper Motor HAT on Raspberry Pi devices. Initial implementation used GPIO (gpiozero), but this didn't work with the HAT's architecture.

## Decision

### Use I2C via PCA9685 PWM Controller

The Waveshare HAT uses a PCA9685 chip (I2C address `0x6F`) to provide 16-channel PWM control. We rewrote the motor controller to use I2C instead of direct GPIO.

**Key specifications:**

- I2C Bus: `/dev/i2c-1`
- I2C Address: `0x6F`
- PWM Frequency: 1600 Hz (optimal for motors)
- Resolution: 12-bit (0-4095)

### Motor Channel Mapping

| Motor | PWM (Speed) | IN2 | IN1 |
|-------|-------------|-----|-----|
| M1 | Channel 8 | Channel 9 | Channel 10 |
| M2 | Channel 13 | Channel 12 | Channel 11 |
| M3 | Channel 2 | Channel 3 | Channel 4 |
| M4 | Channel 7 | Channel 6 | Channel 5 |

### Direction Control

- **Forward:** IN1=HIGH (4096), IN2=LOW (0)
- **Reverse:** IN1=LOW (0), IN2=HIGH (4096)
- **Brake:** IN1=LOW (0), IN2=LOW (0)

## Implementation

### File: `edge-controllers/pi-template/app/dc_motor_hat.py`

- `PCA9685` class: Low-level I2C/PWM controller
- `DCMotorHatController` class: Motor abstraction with speed/direction
- Shared PCA9685 instance across multiple motor instances
- Retry logic for transient I2C errors

### Container Requirements

```yaml
privileged: true
devices:
  - /dev/i2c-1:/dev/i2c-1
```

## Consequences

### Positive

- Works with actual hardware (tested and verified)
- 12-bit PWM provides fine speed control
- Multiple motors share single I2C bus efficiently
- Retry logic handles transient errors

### Negative

- Containers must run privileged for I2C access
- Occasional I2C bus errors (~25% of stop commands)

## Verification

```bash
# Check I2C device
i2cdetect -y 1
# Should show device at 0x6F

# Test command flow
curl -X POST http://api:8000/api/trains/{id}/command \
  -d '{"action":"setSpeed","speed":50}'
```
