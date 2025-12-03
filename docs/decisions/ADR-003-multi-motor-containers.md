# ADR-003: Multi-Motor Container Strategy

**Status:** Accepted  
**Date:** 2025-11-25  

## Context

The Waveshare Motor HAT supports 4 DC motors (M1-M4). We needed to decide how to deploy edge controllers when multiple motors are connected to a single Raspberry Pi.

## Options Considered

### Option A: Single Container, Multiple Motors

- One container manages all motors
- Commands include motor identifier
- Shared resources, single point of failure

### Option B: Multiple Containers, One Motor Each

- Each motor gets dedicated container
- Independent lifecycle and fault isolation
- Higher resource usage but better reliability

## Decision

**Selected: Option B - Multiple Containers**

Each motor port on the HAT runs as an independent Docker container with:

- Unique train ID (UUID)
- Dedicated MQTT topics
- Isolated logging
- Independent restart/failure handling

## Implementation

### Ansible Configuration

```yaml
# inventory/production/hosts.yml
rpi-train-01:
  motors:
    - motor_port: 1
      train_id: 9bf2f703-5ba2-5032-a749-01cce962bcf6
      train_name: "Express Line Engine"
      container_name: edge-controller-m1
    - motor_port: 3
      train_id: 7cd3e891-4ab3-6143-b850-12ddf073ce87
      train_name: "Freight Line Engine"
      container_name: edge-controller-m3
```

### Container Environment

Each container receives:

- `MOTOR_PORT` - Which motor to control (1-4)
- `TRAIN_ID` - Unique identifier for MQTT topics
- `MQTT_BROKER` - Central MQTT server address

### MQTT Topics (per motor)

- Commands: `trains/{train_id}/commands`
- Status: `trains/{train_id}/status`

## Consequences

### Positive

- Fault isolation (one crash doesn't affect others)
- Independent scaling and updates
- Clearer logging per motor
- Simpler code (no multi-motor routing)

### Negative

- More containers to manage
- Slightly higher memory usage
- Duplicate MQTT connections

## Migration Path to Option A

If synchronized multi-motor control is needed later:

1. Extend command format: `{"motor": 1, "speed": 50}`
2. Maintain multiple `DCMotorHatController` instances
3. Route commands to appropriate motor
4. Aggregate status from all motors

Currently not needed - defer until required.
