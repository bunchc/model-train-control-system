# Edge Controller for Model Trains (Raspberry Pi)

Production-ready edge controller application for managing individual model trains. Runs on Raspberry Pi devices with GPIO hardware or in simulator mode for development.

## 📚 Documentation

- **[Edge Controller Architecture](../docs/ARCHITECTURE.md)** - Comprehensive architecture guide for human developers
- **[AI Agent Specifications](../docs/AI_SPECS.md)** - High-density technical specs for autonomous code generation
- **[Testing Guide](../TESTING.md)** - Unit, integration, and E2E testing strategies
- **[System Architecture](../../docs/architecture.md)** - Overall system design and communication patterns
- **[MQTT Topics Reference](../../docs/mqtt-topics.md)** - Message schemas and topic conventions

## 🏗️ Architecture Overview

The edge controller is a distributed agent that:

1. **Registers** with Central API and downloads runtime configuration
2. **Connects** to MQTT broker for real-time command/status communication
3. **Controls** train hardware (stepper motors, DC motors, lights, sensors)
4. **Publishes** telemetry (speed, voltage, current, position) at 1Hz
5. **Handles** graceful degradation when offline (uses cached configuration)

### Component Responsibilities

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **ConfigManager** | Configuration state machine, registration, caching | `app/config/manager.py` |
| **ConfigLoader** | File I/O for YAML configs | `app/config/loader.py` |
| **CentralAPIClient** | HTTP client for API communication | `app/api/client.py` |
| **MQTTClient** | Pub/sub for commands and status | `app/mqtt_client.py` |
| **HardwareController** | Generic GPIO control (DC motors, lights) | `app/hardware.py` |
| **StepperMotorHatController** | Waveshare stepper HAT control (I2C) | `app/stepper_hat.py` |
| **EdgeControllerApp** | Main orchestration and lifecycle | `app/main.py` |

See [Architecture Guide](../docs/ARCHITECTURE.md) for detailed component diagrams and workflows.

## 🚀 Quick Start

### Local Development (Simulator Mode)

Run the edge controller without physical hardware using Docker Compose:

```bash
# From repository root
cd infra/docker
docker-compose up --build

# Edge controller runs in simulator mode (no GPIO required)
# Access logs: docker-compose logs -f edge-controller
```

**What's Running:**

- MQTT broker (Mosquitto) on `localhost:1883`
- Central API on `http://localhost:8000`
- Edge controller connected to both (simulator mode)
- Frontend on `http://localhost:3000`

### Raspberry Pi Deployment

Deploy to Raspberry Pi with real hardware:

#### 1. Prerequisites

```bash
# On Raspberry Pi
sudo apt-get update
sudo apt-get install -y python3-pip python3-gpiozero i2c-tools git

# Enable I2C (for stepper motor HAT)
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable

# Reboot
sudo reboot
```

#### 2. Installation

```bash
# Clone repository
git clone https://github.com/bunchc/model-train-control-system.git
cd model-train-control-system/edge-controllers/pi-template

# Install Python dependencies
pip3 install -r requirements-pi.txt
```

#### 3. Configuration

Create service configuration file:

```bash
# Copy example config
cp ../../examples/pi-config.yaml edge-controller.conf

# Edit configuration
nano edge-controller.conf
```

**Minimal Configuration (`edge-controller.conf`):**

```yaml
central_api_host: api.example.com  # Your Central API hostname/IP
central_api_port: 8000             # Central API port
logging_level: INFO                # DEBUG, INFO, WARNING, ERROR
```

**Note:** Runtime configuration (train_id, MQTT broker, topics) is automatically downloaded from Central API after registration.

#### 4. Run Controller

##### Option A: Manual Execution (Testing)

```bash
cd app
python3 -m app.main
```

##### Option B: Systemd Service (Production)

For persistent operation, configure a systemd service:

```bash
# Install service
sudo cp edge-controller.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start service
sudo systemctl enable edge-controller
sudo systemctl start edge-controller

# Check status
sudo systemctl status edge-controller

# View logs
sudo journalctl -u edge-controller -f
```

#### 5. Verify Registration

```bash
# Check logs for successful registration
sudo journalctl -u edge-controller -n 50

# Expected output:
# INFO - Registered controller uuid=abc-123-def-456
# INFO - Connected to MQTT broker
# INFO - Subscribed to trains/train-1/commands
# INFO - Controller initialized
```

## 📋 Configuration Reference

### Service Configuration (`edge-controller.conf`)

Loaded from local filesystem on startup. Defines how to connect to Central API.

```yaml
central_api_host: api.example.com  # Required: Central API hostname or IP
central_api_port: 8000             # Required: Central API port
logging_level: INFO                # Optional: DEBUG, INFO, WARNING, ERROR (default: INFO)
```

### Runtime Configuration (`edge-controller.yaml`)

Downloaded from Central API after registration. Cached locally for offline operation.

```yaml
uuid: abc-123-def-456              # Assigned by Central API
train_id: train-1                  # Assigned by administrator
mqtt_broker:
  host: mqtt.example.com           # MQTT broker hostname
  port: 1883                       # MQTT broker port (1883 plain, 8883 TLS)
  username: edge-controller        # Optional: MQTT username
  password: secret                 # Optional: MQTT password
status_topic: trains/train-1/status      # Topic for publishing status
commands_topic: trains/train-1/commands  # Topic for receiving commands
hardware_type: stepper_hat         # Optional: stepper_hat, generic, simulator
```

**Configuration Flow:**

1. **Startup**: Load `edge-controller.conf` from filesystem
2. **Registration**: Check if `edge-controller.yaml` exists with `uuid`
3. **Download**: If no UUID or API accessible, register or refresh config
4. **Fallback**: If API unreachable, use cached `edge-controller.yaml`
5. **Operation**: Use runtime config for MQTT and hardware initialization

See [Architecture Guide - Configuration Lifecycle](../docs/ARCHITECTURE.md#configuration-lifecycle) for detailed flow diagrams.

## 🎮 MQTT Command Interface

### Subscribes To

**Topic:** `trains/{train_id}/commands`

**Command Payloads:**

```json
// Start motor at default speed (50%)
{"action": "start"}

// Start motor at specific speed
{"action": "start", "speed": 75}

// Stop motor immediately
{"action": "stop"}

// Change speed without stopping
{"action": "setSpeed", "speed": 60}
```

### Publishes To

**Topic:** `trains/{train_id}/status`

**Status Payload:**

```json
{
  "train_id": "train-1",
  "speed": 75,
  "voltage": 12.3,
  "current": 0.8,
  "position": "section_A",
  "timestamp": "2025-11-21T12:34:56Z"
}
```

**Publish Rate:** 1Hz (configurable)

See [MQTT Topics Reference](../../docs/mqtt-topics.md) for complete message schemas.

## 🔧 Hardware Support

### Supported Hardware

| Hardware | Type | Use Case | Configuration |
|----------|------|----------|---------------|
| **Waveshare Stepper Motor HAT** | Stepper Motor | Precise speed control, high torque | `hardware_type: stepper_hat` |
| **Generic GPIO** | DC Motor + PWM | Simple speed control, low cost | `hardware_type: generic` |
| **Simulator** | Software Only | Development, testing (no GPIO) | `hardware_type: simulator` |

### GPIO Pin Mapping

**Stepper Motor HAT (I2C):**

- Direction: GPIO 13
- Step Pulse: GPIO 19
- Enable: GPIO 12
- Mode Pins: GPIO 16, 17, 20

**Generic GPIO (BCM numbering):**

- Motor PWM: GPIO 18, 19 (PWM-capable pins)
- Lights: GPIO 23, 24, 25
- Sensors: GPIO 26, 27

### Hardware Initialization

The controller automatically detects hardware availability:

```python
# Raspberry Pi with GPIO libraries installed
→ Uses real hardware controller

# Linux/macOS without GPIO libraries
→ Falls back to simulator mode
```

**Force Simulator Mode:**

```bash
export LOCAL_DEV=true
python3 app/main.py
```

## 🧪 Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_config_manager.py

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html
```

### Integration Tests

```bash
# Run integration tests (requires MQTT broker)
pytest tests/integration/

# Run with local Docker Compose stack
cd ../../infra/docker
docker-compose up -d
pytest tests/integration/
docker-compose down
```

### E2E Tests

```bash
# Run full lifecycle tests
pytest tests/e2e/

# Run with verbose output
pytest tests/e2e/ -v -s
```

See [Testing Guide](../TESTING.md) for detailed testing strategies.

## 🛠️ Development

### Code Quality

```bash
# Linting (Ruff)
ruff check app/

# Auto-fix linting issues
ruff check app/ --fix

# Type checking (MyPy)
mypy app/

# Security scanning (Bandit)
bandit -r app/ -ll

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Project Structure

```text
pi-template/
├── app/
│   ├── main.py                    # Entry point, EdgeControllerApp
│   ├── config/
│   │   ├── loader.py              # File I/O for YAML configs
│   │   └── manager.py             # Configuration state machine
│   ├── api/
│   │   └── client.py              # HTTP client for Central API
│   ├── mqtt_client.py             # MQTT pub/sub implementation
│   ├── hardware.py                # Generic GPIO controller
│   ├── stepper_hat.py             # Waveshare HAT controller
│   ├── context.py                 # Legacy config helper (deprecated)
│   └── controllers.py             # FastAPI endpoints (dev only)
├── tests/
│   ├── unit/                      # Fast, isolated unit tests
│   ├── integration/               # Multi-component integration tests
│   └── e2e/                       # Full lifecycle end-to-end tests
├── requirements.txt               # Python dependencies (development)
├── requirements-pi.txt            # Python dependencies (Raspberry Pi)
├── Dockerfile                     # Production container image
├── Dockerfile-local               # Local development image
├── edge-controller.service        # Systemd service file
├── pyproject.toml                 # Ruff, MyPy configuration
└── README.md                      # This file
```

### Adding New Features

1. **Read Specs**: Review [AI_SPECS.md](../docs/AI_SPECS.md) for code patterns
2. **Write Tests**: Add unit tests in `tests/unit/` first (TDD approach)
3. **Implement**: Follow type hints, docstrings, and error handling patterns
4. **Run Quality Checks**: Ensure linting, type checking, and tests pass
5. **Update Docs**: Modify relevant docstrings and documentation

## 🐛 Troubleshooting

### Controller Won't Start

```bash
# Check service logs
sudo journalctl -u edge-controller -n 100

# Common issues:
# 1. Missing service config
#    → Create edge-controller.conf with central_api_host

# 2. Central API unreachable
#    → Verify network connectivity: ping api.example.com
#    → Check firewall rules

# 3. Python dependencies missing
#    → Reinstall: pip3 install -r requirements-pi.txt
```

### MQTT Connection Fails

```bash
# Test MQTT broker connectivity
mosquitto_sub -h mqtt.example.com -p 1883 -t 'trains/#' -v

# Check runtime config
cat edge-controller.yaml

# Verify MQTT broker settings:
# - Correct hostname and port
# - Valid credentials (if authentication enabled)
# - Firewall allows port 1883 (or 8883 for TLS)
```

### GPIO Errors

```bash
# Verify I2C is enabled
sudo raspi-config  # Interface Options → I2C → Enable

# Check I2C devices
sudo i2cdetect -y 1

# Verify GPIO permissions
sudo usermod -a -G gpio pi
sudo reboot

# Test GPIO access
python3 -c "from gpiozero import LED; LED(23).on()"
```

### Configuration Not Downloading

```bash
# Check Central API accessibility
curl http://api.example.com:8000/api/ping

# Manually register controller
curl -X POST http://api.example.com:8000/api/controllers/register \
  -H "Content-Type: application/json" \
  -d '{"name": "my-pi", "address": "192.168.1.100"}'

# Force configuration refresh (delete cached config)
rm edge-controller.yaml
sudo systemctl restart edge-controller
```

## 📊 Performance Tuning

### Latency Optimization

```python
# Reduce MQTT QoS for faster command delivery (less reliable)
# In mqtt_client.py:
self.client.publish(topic, payload, qos=0)  # Default: qos=1

# Increase status publish rate
# In main.py:
self.status_interval = 0.5  # Publish every 500ms instead of 1s
```

### Resource Usage

```bash
# Monitor CPU and memory
htop

# Check network usage
sudo iftop

# Typical resource usage (Raspberry Pi 3):
# CPU: <5% active, <1% idle
# Memory: ~50MB active, ~40MB idle
# Network: ~5KB/s active, ~1KB/s idle
```

## 🔒 Security

### Best Practices

1. **Secrets Management**: Use environment variables or Docker secrets for MQTT passwords
2. **Network Isolation**: Run edge controllers on isolated VLAN
3. **TLS Encryption**: Use MQTT over TLS (port 8883) for production
4. **Regular Updates**: Keep OS and Python packages updated
5. **Minimal Permissions**: Run as non-root user (systemd service uses `User=pi`)

### Enable MQTT TLS

```yaml
# In runtime config (edge-controller.yaml)
mqtt_broker:
  host: mqtt.example.com
  port: 8883  # TLS port
  username: edge-controller
  password: ${MQTT_PASSWORD}  # Load from environment
  tls_ca_cert: /etc/ssl/certs/ca-certificates.crt
```

## 📄 License

This project is licensed under the MIT License. See [LICENSE](../../LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please:

1. Read [Architecture Guide](../docs/ARCHITECTURE.md) and [AI Specifications](../docs/AI_SPECS.md)
2. Follow existing code patterns (type hints, docstrings, error handling)
3. Add tests for new functionality (80%+ coverage)
4. Run quality checks (`ruff`, `mypy`, `bandit`)
5. Update documentation and docstrings

For questions or issues, please [open an issue](https://github.com/bunchc/model-train-control-system/issues).
