# Model Train Control System

A distributed control system for model trains, designed to provide modular, scalable, and resilient control over multiple trains using Raspberry Pi edge controllers. The architecture consists of edge controllers, a central API, an MQTT broker, a gateway/orchestrator, and a web frontend.

## 📚 Documentation

### For Human Developers

- **[Architecture Guide](docs/architecture.md)** - System design, communication patterns, and architectural decisions
- **[MQTT Topics Reference](docs/mqtt-topics.md)** - Message schemas and topic conventions
- **[Onboarding Guide](docs/onboarding.md)** - Getting started as a new developer
- **[Edge Controller Architecture](edge-controllers/docs/ARCHITECTURE.md)** - Deep dive into edge controller design
- **[Local Development Guide](LOCAL_DEV.md)** - Running the system locally with Docker Compose

### For AI Code Agents

- **[Edge Controller AI Specifications](edge-controllers/docs/AI_SPECS.md)** - High-density technical specs for autonomous code generation and modification
- **[Copilot Instructions](.github/copilot-instructions.md)** - AI agent guidance for working in this repository

### API Documentation

- **[OpenAPI Specification](openapi.yaml)** - REST API reference for Central API
- **[Refactor Plan](docs/openapi-refactor-plan.md)** - OpenAPI integration roadmap

## 🏗️ Project Structure

- **[edge-controllers/](edge-controllers/)** - Raspberry Pi controllers for individual trains
  - **[pi-template/](edge-controllers/pi-template/)** - Production-ready edge controller application
  - **[docs/](edge-controllers/docs/)** - Edge controller architecture and AI specifications
  - **[examples/](edge-controllers/examples/)** - Sample configuration files

- **[central_api/](central_api/)** - Central API coordinating commands and telemetry
  - FastAPI-based REST API
  - MQTT adapter for pub/sub communication
  - Configuration management endpoints

- **[gateway/orchestrator/](gateway/orchestrator/)** - Bridge between frontend and MQTT/API
  - Node.js application
  - WebSocket support for real-time updates
  - Command routing and validation

- **[frontend/web/](frontend/web/)** - React-based web interface
  - Real-time train control dashboard
  - MQTT over WebSocket for live updates
  - Train status visualization

- **[infra/](infra/)** - Infrastructure as Code
  - **[docker/](infra/docker/)** - Docker Compose for local development
  - **[k8s/](infra/k8s/)** - Kubernetes manifests for production
  - **[terraform/](infra/terraform/)** - Cloud infrastructure provisioning

- **[persistence/](persistence/)** - Time-series database initialization
  - InfluxDB setup scripts
  - TimescaleDB initialization

- **[tests/](tests/)** - System-wide integration and unit tests
  - Unit tests for core components
  - Integration tests for API and edge controllers
  - End-to-end workflow tests

- **[docs/](docs/)** - Architecture documentation and guides

## 🚀 Quick Start

### Prerequisites

**For Local Development:**

- Docker 20.10+ and Docker Compose 2.0+
- Git

**For Edge Controller Deployment:**

- Raspberry Pi 3/4 (Raspberry Pi OS)
- Python 3.9+
- GPIO-compatible hardware (optional - simulator mode available)

**For Development Without Docker:**

- Python 3.9+ (for Central API and edge controllers)
- Node.js 16+ and npm (for Gateway and Frontend)

### Local Development (Recommended)

Run the complete system locally using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/bunchc/model-train-control-system.git
cd model-train-control-system

# Start all services (MQTT broker, Central API, Gateway, Edge Controller, Frontend)
cd infra/docker
docker-compose up --build

# Access the system
# - Frontend:     http://localhost:3000
# - Central API:  http://localhost:8000
# - API Docs:     http://localhost:8000/docs
# - MQTT Broker:  localhost:1883 (MQTT), localhost:9001 (WebSocket)
```

**What's Running:**

- **Eclipse Mosquitto** - MQTT broker for pub/sub messaging
- **Central API** - FastAPI application managing train configurations
- **Gateway/Orchestrator** - Node.js bridge between frontend and MQTT
- **Edge Controller** - Sample controller in simulator mode (no hardware required)
- **Frontend** - React dashboard for train control

See [LOCAL_DEV.md](LOCAL_DEV.md) for detailed local development instructions.

### Edge Controller Deployment

Deploy to a Raspberry Pi with real hardware:

```bash
# On your development machine
cd edge-controllers/pi-template

# Copy to Raspberry Pi
scp -r . pi@raspberrypi.local:~/edge-controllers/

# SSH to Raspberry Pi
ssh pi@raspberrypi.local

# Install dependencies
cd ~/edge-controllers/
pip3 install -r requirements-pi.txt

# Configure service settings
nano edge-controller.conf  # Set central_api_host and central_api_port

# Run controller
python3 app/main.py

# OR install as systemd service (auto-start on boot)
sudo cp edge-controller.service /etc/systemd/system/
sudo systemctl enable edge-controller
sudo systemctl start edge-controller
sudo systemctl status edge-controller
```

See [edge-controllers/pi-template/README.md](edge-controllers/pi-template/README.md) for complete setup instructions.

### Production Deployment

Deploy to Kubernetes:

```bash
# Configure kubectl context
kubectl config use-context production

# Deploy infrastructure
cd infra/k8s/manifests
kubectl apply -f central-api-deployment.yaml
kubectl apply -f pi-controller-deployment.yaml

# Verify deployments
kubectl get pods
kubectl get services
```

See [infra/k8s/](infra/k8s/) for Kubernetes deployment details.

## 🛠️ Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest tests/ --cov=edge-controllers/pi-template/app --cov-report=html
```

### Code Quality

```bash
# Linting (Ruff)
ruff check edge-controllers/pi-template/app/

# Type checking (MyPy)
mypy edge-controllers/pi-template/app/

# Security scanning (Bandit)
bandit -r edge-controllers/pi-template/app/ -ll

# Pre-commit hooks (auto-runs on commit)
pre-commit install
pre-commit run --all-files
```

### Adding a New Feature

1. **Read Documentation**: Review [docs/architecture.md](docs/architecture.md) and relevant component docs
2. **Create Branch**: `git checkout -b feature/my-new-feature`
3. **Write Tests**: Add unit tests in `tests/unit/`
4. **Implement Feature**: Follow existing code patterns and type hints
5. **Update Docstrings**: Maintain Google-style docstrings
6. **Run Quality Checks**: Ensure linting, type checking, and tests pass
7. **Update Docs**: Modify relevant documentation files
8. **Submit PR**: Open pull request with clear description

See [docs/onboarding.md](docs/onboarding.md) for detailed contribution guidelines.

## 📊 System Architecture

```text
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Web Frontend   │────────▶│ Gateway/Orch.    │────────▶│  Central API    │
│  (React)        │◀────────│ (Node.js)        │◀────────│  (FastAPI)      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
       │                             │                            │
       │ WebSocket                   │ MQTT                       │ HTTP
       │                             │                            │
       ▼                             ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MQTT Broker (Mosquitto)                         │
│                    Topic: trains/{train_id}/commands                    │
│                    Topic: trains/{train_id}/status                      │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ MQTT Pub/Sub
                                     │
                      ┌──────────────┴──────────────┐
                      │                             │
               ┌──────▼──────┐             ┌────────▼────────┐
               │Edge Ctrl #1 │             │ Edge Ctrl #2    │
               │ (Pi + GPIO) │             │ (Pi + GPIO)     │
               │  Train A    │             │   Train B       │
               └─────────────┘             └─────────────────┘
```

**Key Communication Patterns:**

- **Frontend → API**: REST endpoints for configuration and control
- **Frontend → MQTT**: Real-time status updates via WebSocket
- **API → MQTT**: Command publishing to edge controllers
- **Edge Controllers → MQTT**: Status telemetry and command acknowledgment
- **Edge Controllers → API**: Registration and configuration download (HTTP)

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## 🔒 Security

This project implements security best practices including:

- **Secrets Management**: Environment variables and Docker secrets (no hardcoded credentials)
- **Input Validation**: All MQTT and API inputs validated before processing
- **Security Scanning**: Bandit (SAST), Safety (dependency vulnerabilities), Trivy (container scanning)
- **Pre-commit Hooks**: Automated security checks before commits
- **Type Safety**: MyPy strict type checking prevents common vulnerabilities
- **Least Privilege**: Non-root containers, minimal permissions

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

## 📈 Performance

**Edge Controller Specifications (Raspberry Pi 3/4):**

- Command latency: <50ms (MQTT to GPIO)
- Status publish rate: 1Hz (configurable)
- Memory usage: ~50MB active, ~60MB peak
- CPU usage: <5% active, <20% peak

**System Throughput:**

- MQTT messages: 100+ msg/sec per broker
- API endpoints: 1000+ req/sec (FastAPI)
- Concurrent trains: 50+ per MQTT broker instance

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Read Documentation**: Familiarize yourself with [docs/architecture.md](docs/architecture.md)
2. **Check Issues**: Look for existing issues or create a new one
3. **Follow Conventions**: Maintain code style, type hints, and docstrings
4. **Write Tests**: Maintain 80%+ code coverage
5. **Security First**: Run security scans before submitting PR
6. **Documentation**: Update relevant docs and docstrings

For AI code agents, follow [edge-controllers/docs/AI_SPECS.md](edge-controllers/docs/AI_SPECS.md) specifications.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Hardware**: Waveshare Stepper Motor HAT for Raspberry Pi
- **MQTT Broker**: Eclipse Mosquitto
- **Frameworks**: FastAPI, React, paho-mqtt
- **Infrastructure**: Docker, Kubernetes, Terraform

---

**Project Status**: Active Development  
**Latest Release**: v0.1.0  
**Maintainers**: [@bunchc](https://github.com/bunchc)

For questions or support, please [open an issue](https://github.com/bunchc/model-train-control-system/issues).
