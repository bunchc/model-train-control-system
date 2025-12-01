# Quick Deployment Summary

## ✅ Implementation Complete

### What Was Built

**Multi-Motor DC Motor Support** for deploying multiple edge controllers to a single Raspberry Pi, each controlling a different motor port (M1-M4) on the Waveshare Stepper Motor HAT.

### Files Modified

1. **`edge-controllers/pi-template/app/dc_motor_hat.py`**
   - ✓ Removed singleton pattern
   - ✓ Added `motor_num` parameter (1-4) to constructor
   - ✓ Added PWM channel mapping for all 4 motors (M1-M4)
   - ✓ Shared PCA9685 controller across instances
   - ✓ Each instance controls specific motor channels

2. **`edge-controllers/pi-template/app/main.py`**
   - ✓ Added `MOTOR_PORT` environment variable support
   - ✓ Passes motor_num to DCMotorHatController
   - ✓ Logs which motor port is being controlled

3. **`infra/ansible/inventory/production/hosts.yml`**
   - ✓ Updated to multi-motor configuration
   - ✓ Defined two motors: M1 (Express Line) and M3 (Freight Line)
   - ✓ Each motor has unique train_id, train_name, container_name
   - ✓ Hardware type set to `dc_motor`

4. **`infra/ansible/playbooks/deploy_edge_multi_motor.yml`** (NEW)
   - ✓ Deploys multiple containers per host
   - ✓ Iterates through motors list
   - ✓ Includes per-motor task file

5. **`infra/ansible/playbooks/tasks/deploy_single_motor.yml`** (NEW)
   - ✓ Creates motor-specific configuration
   - ✓ Deploys individual container
   - ✓ Sets MOTOR_PORT environment variable
   - ✓ Maps /dev/i2c-1 device for I2C access
   - ✓ Validates deployment

6. **`docs/MULTI_MOTOR_DEPLOYMENT.md`** (NEW)
   - ✓ Complete deployment guide
   - ✓ Your specific configuration documented
   - ✓ Testing procedures
   - ✓ Troubleshooting steps

---

## 🚀 Ready to Deploy

### Current Configuration

**Central Infrastructure (Mac at 192.168.1.199)**

- Central API: http://192.168.1.199:8000
- MQTT Broker: mqtt://192.168.1.199:1883

**Edge Controller (RPi at 192.168.2.214)**

- Motor M1 → Container: `edge-controller-m1` → "Express Line Engine"
- Motor M3 → Container: `edge-controller-m3` → "Freight Line Engine"

---

## 📝 Deployment Command

```bash
cd /Users/bunchc/Projects/model-train-control-system

ansible-playbook \
  -i infra/ansible/inventory/production/hosts.yml \
  infra/ansible/playbooks/deploy_edge_multi_motor.yml
```

**What this does:**

1. Verifies Docker is installed on RPi
2. Checks central API is reachable
3. Pulls latest edge-controller image
4. Deploys container for M1 with train_id `9bf2f703-5ba2-5032-a749-01cce962bcf6`
5. Deploys container for M3 with train_id `7cd3e891-4ab3-6143-b850-12ddf073ce87`
6. Configures MQTT topics for each motor
7. Shows deployment summary

---

## ✓ Pre-Deployment Checks

Before running the deployment, verify:

```bash
# 1. SSH access to RPi
ssh pi@192.168.2.214
# Should connect without password

# 2. Central API is running
curl http://192.168.1.199:8000/api/ping
# Should return: {"status":"ok"}

# 3. MQTT broker is running
nc -zv 192.168.1.199 1883
# Should show: Connection succeeded

# 4. Ansible is installed
ansible --version
# Should show version 2.9+
```

---

## 🧪 Testing After Deployment

### Verify Containers Running

```bash
ssh pi@192.168.2.214
docker ps -f label=component=edge-controller
```

Expected output:

```
NAMES                 STATUS              PORTS
edge-controller-m1    Up X seconds  
edge-controller-m3    Up X seconds  
```

### Test M1 Motor (Express Line)

```bash
# Get MQTT password from vault
MQTT_PASS=$(ansible-vault view infra/ansible/secrets/vault.yml | grep vault_mqtt_password | awk '{print $2}')

# Send speed command to M1
mosquitto_pub -h 192.168.1.199 \
  -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/commands" \
  -u edge-controller \
  -P "$MQTT_PASS" \
  -m '{"speed": 50}'

# Subscribe to status
mosquitto_sub -h 192.168.1.199 \
  -t "trains/9bf2f703-5ba2-5032-a749-01cce962bcf6/status" \
  -u edge-controller \
  -P "$MQTT_PASS"
```

### Test M3 Motor (Freight Line)

```bash
# Send speed command to M3
mosquitto_pub -h 192.168.1.199 \
  -t "trains/7cd3e891-4ab3-6143-b850-12ddf073ce87/commands" \
  -u edge-controller \
  -P "$MQTT_PASS" \
  -m '{"speed": 75}'
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ Mac (192.168.1.199)                                 │
│  ├── Central API (port 8000)                        │
│  └── MQTT Broker (port 1883)                        │
└─────────────────────────────────────────────────────┘
                        │
                        │ MQTT over network
                        │
┌─────────────────────────────────────────────────────┐
│ RPi (192.168.2.214)                                 │
│  ├── edge-controller-m1 (Motor M1)                  │
│  │   ├── Train ID: 9bf2f703...                      │
│  │   ├── PWM Channels: 8, 9, 10                     │
│  │   └── Commands: trains/9bf2f703.../commands      │
│  │                                                   │
│  ├── edge-controller-m3 (Motor M3)                  │
│  │   ├── Train ID: 7cd3e891...                      │
│  │   ├── PWM Channels: 2, 3, 4                      │
│  │   └── Commands: trains/7cd3e891.../commands      │
│  │                                                   │
│  └── Waveshare Stepper Motor HAT                    │
│      ├── PCA9685 PWM Controller (I2C 0x6F)          │
│      └── DC Motors: M1, M2, M3, M4                  │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Troubleshooting

### Containers Won't Start

```bash
# Check logs
ssh pi@192.168.2.214
docker logs edge-controller-m1
docker logs edge-controller-m3

# Common issues:
# - I2C device not accessible → Check /dev/i2c-1 permissions
# - PCA9685 not found → Run: i2cdetect -y 1
# - MQTT connection failed → Check broker IP and credentials
```

### Motors Don't Move

1. **External power connected?** The HAT needs 5-12V external power
2. **Motor wired correctly?** Check M1/M3 terminal blocks
3. **I2C communication?** Run `i2cdetect -y 1` (should show 0x6F)

### Check I2C Device

```bash
ssh pi@192.168.2.214
i2cdetect -y 1
```

Should show:

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
...
60:                                                -- -- -- 6f
```

---

## 📚 Full Documentation

For detailed information, see:

- **`docs/MULTI_MOTOR_DEPLOYMENT.md`** - Complete deployment guide
- **`infra/ansible/README.md`** - Ansible infrastructure overview
- **`edge-controllers/docs/AI_SPECS.md`** - Edge controller technical specs

---

## 🎯 Next Steps

1. **Run Pre-Deployment Checks** (above)
2. **Execute Deployment Command**
3. **Verify Containers Running**
4. **Test Motor Control via MQTT**
5. **Monitor Container Logs**

---

## Future: Option A (Single Container, Multiple Motors)

When you're ready to investigate **Option A**, the changes needed are:

1. Extend MQTT command format to include motor selection
2. Maintain multiple DCMotorHatController instances in one process
3. Route commands to appropriate motor
4. Aggregate status from all motors

Current implementation (Option B) is production-ready and recommended for now.
