# Multi-Motor Edge Controller Deployment Guide

**Date:** November 29, 2025  
**Configuration:** Multiple DC motors on single Raspberry Pi  
**Your Setup:** RPi at 192.168.2.214 with trains on M1 and M3

---

## Overview

This deployment configuration allows a single Raspberry Pi with a Waveshare Stepper Motor HAT to control **multiple DC motors** (M1-M4), with each motor controlled by a separate Docker container. This provides:

- **Isolation**: Each motor has its own edge controller instance
- **Unique Train IDs**: Each motor can be independently addressed via MQTT
- **Fault Tolerance**: If one container fails, others continue operating
- **Scalability**: Easy to add/remove motors by updating inventory

---

## Your Current Configuration

### Network Setup

- **Mac (Central Infrastructure)**: `192.168.1.199`
  - Central API: Port 8000
  - MQTT Broker: Ports 1883 (MQTT), 9001 (WebSocket)
- **Raspberry Pi (Edge Controller)**: `192.168.2.214`
  - Motor M1: "Express Line Engine"
  - Motor M3: "Freight Line Engine"

### Hardware

- **Board**: Waveshare Stepper Motor HAT
- **Motors**: DC motors on M1 and M3 ports
- **I2C Address**: 0x6F (PCA9685 PWM controller)
- **Power**: External 5-12V supply (ensure connected!)

---

## Pre-Deployment Checklist

### 1. SSH Access

```bash
# Test SSH connection to RPi
ssh pi@192.168.2.214

# If successful, exit and copy SSH key
ssh-copy-id pi@192.168.2.214
```

### 2. Central Infrastructure Running

```bash
# Verify central API is running
curl http://192.168.1.199:8000/api/ping

# Should return: {"status":"ok"}
```

### 3. MQTT Broker Running

```bash
# Check MQTT is listening
nc -zv 192.168.1.199 1883

# Should show: Connection to 192.168.1.199 port 1883 [tcp/*] succeeded!
```

### 4. Ansible Setup

```bash
# Install Ansible if not already installed
pip install ansible

# Install required collections
ansible-galaxy collection install community.docker community.general
```

---

## Deployment Steps

### Step 1: Review Inventory Configuration

The inventory is already configured at:
`infra/ansible/inventory/production/hosts.yml`

```yaml
rpi-train-01:
  ansible_host: 192.168.2.214
  ansible_user: pi

  motors:
    - motor_port: 1  # M1
      train_id: 9bf2f703-5ba2-5032-a749-01cce962bcf6
      train_name: "Express Line Engine"
      container_name: edge-controller-m1

    - motor_port: 3  # M3
      train_id: 7cd3e891-4ab3-6143-b850-12ddf073ce87
      train_name: "Freight Line Engine"
      container_name: edge-controller-m3

  hardware_type: dc_motor
```

**Note**: Train IDs are already generated. Keep these for consistency.

### Step 2: Verify Secrets

```bash
cd infra/ansible

# View vault contents (uses .vault_pass file)
ansible-vault view secrets/vault.yml

# Should show:
# - vault_github_username: bunchc
# - vault_github_token: ghp_...
# - vault_mqtt_password: ...
```

### Step 3: Deploy Edge Controllers

```bash
# From project root
cd /Users/bunchc/Projects/model-train-control-system

# Deploy multi-motor edge controllers
ansible-playbook \
  -i infra/ansible/inventory/production/hosts.yml \
  infra/ansible/playbooks/deploy_edge_multi_motor.yml
```

This will:

1. ✓ Verify Docker is installed on RPi
2. ✓ Verify central API is reachable
3. ✓ Pull edge-controller Docker image
4. ✓ Deploy container for M1 motor
5. ✓ Deploy container for M3 motor
6. ✓ Configure MQTT topics for each
7. ✓ Show deployment summary

**Expected Duration**: 2-5 minutes

### Step 4: Verify Deployment

```bash
# SSH to RPi
ssh pi@192.168.2.214

# Check both containers are running
docker ps -f label=component=edge-controller

# Should show:
# edge-controller-m1   Up X seconds   (Express Line)
# edge-controller-m3   Up X seconds   (Freight Line)

# Check logs for M1
docker logs edge-controller-m1

# Check logs for M3
docker logs edge-controller-m3
```

Look for:

- ✓ `PCA9685 PWM controller initialized`
- ✓ `DC Motor M1 initialized` (or M3)
- ✓ `MQTT client started successfully`
- ✓ `Subscribed to commands on: trains/{train_id}/commands`

---

## Testing the Motors

### Test M1 (Express Line Engine)

```bash
# Subscribe to status updates
mosquitto_sub -h 192.168.1.199 -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/status" -u edge-controller -P <mqtt_password>

# In another terminal, send command
mosquitto_pub -h 192.168.1.199 \
  -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/commands" \
  -u edge-controller \
  -P <mqtt_password> \
  -m '{"action": "start"}'

# Set speed
mosquitto_pub -h 192.168.1.199 \
  -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/commands" \
  -u edge-controller \
  -P <mqtt_password> \
  -m '{"speed": 50}'

# Stop
mosquitto_pub -h 192.168.1.199 \
  -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/commands" \
  -u edge-controller \
  -P <mqtt_password> \
  -m '{"action": "stop"}'
```

### Test M3 (Freight Line Engine)

```bash
# Subscribe to status
mosquitto_sub -h 192.168.1.199 -t "trains/7cd3e891-4ab3-6143-b850-12ddf073ce87/status" -u edge-controller -P <mqtt_password>

# Send commands (same pattern as M1, different train_id)
mosquitto_pub -h 192.168.1.199 \
  -t "trains/7cd3e891-4ab3-6143-b850-12ddf073ce87/commands" \
  -u edge-controller \
  -P <mqtt_password> \
  -m '{"speed": 75}'
```

---

## Architecture Details

### Container Layout

Each motor gets its own isolated container:

```
RPi (192.168.2.214)
├── edge-controller-m1 (M1 - Express Line)
│   ├── Train ID: 9bf2f703-5ba2-5032-a749-01cce962bcf6
│   ├── Config: /opt/train-control/config/edge-controller-m1.conf
│   ├── Logs: /opt/train-control/logs/edge-controller-m1.log
│   ├── I2C: Shared PCA9685 at 0x6F
│   └── PWM Channels: 8 (speed), 9 (IN2), 10 (IN1)
│
└── edge-controller-m3 (M3 - Freight Line)
    ├── Train ID: 7cd3e891-4ab3-6143-b850-12ddf073ce87
    ├── Config: /opt/train-control/config/edge-controller-m3.conf
    ├── Logs: /opt/train-control/logs/edge-controller-m3.log
    ├── I2C: Shared PCA9685 at 0x6F
    └── PWM Channels: 2 (speed), 3 (IN2), 4 (IN1)
```

### MQTT Topics

**Express Line (M1)**:

- Commands: `trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/commands`
- Status: `trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/status`

**Freight Line (M3)**:

- Commands: `trains/7cd3e891-4ab3-6143-b850-12ddf073ce87/commands`
- Status: `trains/7cd3e891-4ab3-6143-b850-12ddf073ce87/status`

### PWM Channel Mapping

The PCA9685 chip has 16 PWM channels. The Waveshare HAT maps them as:

| Motor | PWM (Speed) | IN2 (Dir) | IN1 (Dir) |
|-------|-------------|-----------|-----------|
| M1    | Channel 8   | Channel 9 | Channel 10 |
| M2    | Channel 13  | Channel 12 | Channel 11 |
| M3    | Channel 2   | Channel 3 | Channel 4 |
| M4    | Channel 7   | Channel 6 | Channel 5 |

---

## Troubleshooting

### Container Won't Start

```bash
# Check Docker logs
docker logs edge-controller-m1

# Common issues:
# - I2C not accessible: Need privileged mode
# - PCA9685 not found: Check I2C address (should be 0x6F)
# - MQTT connection failed: Verify broker IP and credentials
```

### Motor Doesn't Move

1. **Check power supply**: External 5-12V must be connected to HAT
2. **Check motor wiring**: Ensure motor is connected to correct M1/M3 terminals
3. **Check container logs**: `docker logs edge-controller-m1 -f`
4. **Test I2C**: `i2cdetect -y 1` (should show device at 0x6F)

### MQTT Connection Issues

```bash
# Test MQTT from Mac
mosquitto_pub -h 192.168.1.199 -t test -m "hello" -u edge-controller -P <password>

# If this fails, MQTT broker isn't running or credentials are wrong
```

### Multiple Containers Using Same I2C

This is **normal and expected**. The code uses a shared PCA9685 instance:

- First container to start initializes PCA9685
- Subsequent containers reuse the same I2C connection
- Each container controls different PWM channels

---

## Maintenance

### View All Container Logs

```bash
# On RPi
docker ps -f label=component=edge-controller

docker logs -f edge-controller-m1
docker logs -f edge-controller-m3
```

### Restart a Container

```bash
docker restart edge-controller-m1
```

### Update Containers

```bash
# Re-run deployment (pulls latest image)
ansible-playbook \
  -i infra/ansible/inventory/production/hosts.yml \
  infra/ansible/playbooks/deploy_edge_multi_motor.yml
```

### Remove All Containers

```bash
# On RPi
docker stop edge-controller-m1 edge-controller-m3
docker rm edge-controller-m1 edge-controller-m3
```

---

## Next Steps: Option A Implementation

You mentioned wanting to investigate **Option A** (single container controlling multiple motors) later. Here's what that would involve:

### Required Changes

1. **Command Structure**: Extend MQTT commands to specify motor:

   ```json
   {"motor": 1, "speed": 50}
   {"motor": 3, "action": "stop"}
   ```

2. **Hardware Controller**: Maintain multiple `DCMotorHatController` instances:

   ```python
   self.motors = {
       1: DCMotorHatController(motor_num=1),
       3: DCMotorHatController(motor_num=3),
   }
   ```

3. **Command Routing**: Route commands to correct motor instance

4. **Status Aggregation**: Publish combined status for all motors

### Pros of Option A

- Single container = simpler deployment
- Shared resources (one MQTT connection)
- Easier to coordinate multiple motors

### Cons of Option A

- More complex command routing logic
- Single point of failure (one crash affects all)
- Harder to scale motors independently

**Recommendation**: Stick with Option B (current setup) until you need synchronized multi-motor control.

---

## Support

If deployment fails, check:

1. SSH access: `ssh pi@192.168.2.214`
2. Docker installed: `ssh pi@192.168.2.214 'docker --version'`
3. Central API running: `curl http://192.168.1.199:8000/api/ping`
4. Vault password correct: `ansible-vault view infra/ansible/secrets/vault.yml`

Collect logs:

```bash
# From RPi
docker logs edge-controller-m1 > m1.log 2>&1
docker logs edge-controller-m3 > m3.log 2>&1
```
