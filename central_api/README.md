# Central API

FastAPI-based central controller for the model train control system. Provides REST API for configuration management, train control, and MQTT integration.

## Features

- 🚂 **Train Control** - REST API for sending commands to model trains
- ⚙️ **Configuration Management** - YAML-based config with SQLite persistence
- 📡 **MQTT Integration** - Pub/sub bridge to edge controllers
- 🔍 **Health Monitoring** - Built-in health checks and status endpoints
- 🔒 **Type Safety** - Pydantic validation on all endpoints
- 🧪 **Well Tested** - 98% test pass rate with unit/integration/e2e tests

## Quick Start

### Prerequisites

- Python 3.9+
- SQLite 3.x
- MQTT broker (Mosquitto recommended)

### Installation

```bash
# Navigate to central_api directory
cd central_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy example config
cp ../config.yaml.example config.yaml

# Run database migration (if needed)
# Schema is auto-initialized on first run
```

### Running Locally

```bash
# Development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
# Build image
docker build -t central-api:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/data:/app/data \
  -e MQTT_BROKER_HOST=mqtt-broker \
  central-api:latest
```

### Docker Compose

```bash
# Start all services (from project root)
cd ../infra/docker
docker-compose up -d

# View logs
docker-compose logs -f central_api
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint, returns welcome message |
| `/ping` | GET | Health check |
| `/api/config` | GET | Get full system configuration |
| `/api/config/edge-controllers` | GET | List edge controllers |
| `/api/config/edge-controllers/{id}` | GET/PUT | Get/update controller config |
| `/api/trains` | GET | List all trains |
| `/api/trains/{id}` | GET | Get train configuration |
| `/api/trains/{id}/command` | POST | Send command to train |
| `/api/trains/{id}/status` | GET | Get train status |

### Example Usage

```bash
# List all trains
curl http://localhost:8000/api/trains

# Send speed command
curl -X POST http://localhost:8000/api/trains/train-001/command \
  -H "Content-Type: application/json" \
  -d '{"action": "setSpeed", "speed": 75}'

# Get train status
curl http://localhost:8000/api/trains/train-001/status
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `CENTRAL_API_CONFIG_YAML` | `/app/config.yaml` | Path to YAML config |
| `CENTRAL_API_CONFIG_DB` | `/app/central_api_config.db` | Path to SQLite database |
| `MQTT_BROKER_HOST` | `mqtt-broker` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Configuration File

See `../config.yaml` for structure. Key sections:

```yaml
plugins:
  - id: motor_control
    name: Motor Control
    version: 1.0.0
    config_schema: {}

trains:
  - id: train-001
    name: Express Train 1
    plugins:
      - plugin_id: motor_control
        config:
          max_speed: 100

edge_controllers:
  - id: controller-001
    name: Pi Controller 1
    location: Section A
    trains: [train-001]
```

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run linting
make lint

# Run type checking
make typecheck

# Run security scan
make security
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Coverage report
make coverage
```

### Code Quality Tools

- **Ruff 0.3.4** - Linting and formatting (100 char line length)
- **MyPy 1.9.0** - Static type checking (strict mode)
- **Bandit 1.7.8** - Security scanning
- **Safety 3.1.0** - Dependency vulnerability scanning
- **Pytest 8.1.1** - Testing framework

### Project Structure

```
central_api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic Settings
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── config.py        # Configuration endpoints
│   │   └── trains.py        # Train control endpoints
│   └── services/
│       ├── config_manager.py    # Business logic facade
│       ├── config_loader.py     # YAML loading
│       ├── config_repository.py # Database operations
│       └── mqtt_adapter.py      # MQTT client wrapper
├── tests/
│   ├── unit/                # Unit tests (mocked dependencies)
│   ├── integration/         # Integration tests (real components)
│   └── e2e/                 # End-to-end tests (full system)
├── docs/
│   ├── ARCHITECTURE.md      # System architecture documentation
│   └── AI_SPECS.md          # AI agent development specifications
├── Dockerfile               # Multi-stage Docker build
├── requirements.txt         # Production dependencies
├── pyproject.toml           # Python project config (Ruff, MyPy, Pytest)
├── Makefile                 # Development commands
└── README.md                # This file
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

**Key Components:**
- **FastAPI App** - REST API with lifespan events
- **ConfigManager** - Facade orchestrating config loading and database
- **ConfigRepository** - Repository pattern for database operations
- **MQTTAdapter** - MQTT pub/sub client wrapper
- **Pydantic Models** - Type-safe request/response validation

**Data Flow:**
1. Frontend → REST API → ConfigManager → Database
2. REST API → MQTTAdapter → Edge Controller
3. Edge Controller → MQTT → Central API → Database

## MQTT Integration

### Topic Structure

```
trains/{train_id}/commands     → Publish commands to edge controllers
trains/{train_id}/status       → Subscribe to status updates
trains/{train_id}/telemetry    → Subscribe to telemetry data
```

### Message Formats

**Command Message:**
```json
{
  "action": "setSpeed",
  "speed": 50,
  "timestamp": "2025-11-21T10:15:30Z"
}
```

**Status Message:**
```json
{
  "train_id": "train-001",
  "speed": 50,
  "voltage": 12.3,
  "current": 0.8,
  "position": "section_A",
  "timestamp": "2025-11-21T10:15:31Z"
}
```

See [../docs/mqtt-topics.md](../docs/mqtt-topics.md) for complete topic specifications.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test`, `make lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style Guidelines

- Follow PEP 8 (enforced by Ruff)
- Add type hints to all functions (validated by MyPy)
- Write Google-style docstrings
- Maintain 80%+ test coverage
- Update documentation for API changes

## Troubleshooting

### Common Issues

**Issue: `ConfigurationError: Failed to initialize ConfigManager`**
- Check that `config.yaml` exists and is valid YAML
- Verify `config_schema.sql` is present
- Check file permissions

**Issue: MQTT connection refused**
- Verify MQTT broker is running (`docker-compose ps`)
- Check `MQTT_BROKER_HOST` environment variable
- Confirm broker port (default 1883)

**Issue: Database locked**
- SQLite is single-writer - ensure no concurrent writes
- Consider upgrading to PostgreSQL for production

**Issue: Tests failing**
- Check Python version (3.9+ required)
- Verify all dependencies installed (`pip install -r requirements.txt`)
- Ensure no other instance running on port 8000

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Related Projects

- [Edge Controllers](../edge-controllers/) - Raspberry Pi-based train controllers
- [Frontend](../frontend/web/) - React web UI
- [Gateway](../gateway/orchestrator/) - MQTT/HTTP bridge
- [Infrastructure](../infra/) - Docker Compose and Kubernetes manifests
