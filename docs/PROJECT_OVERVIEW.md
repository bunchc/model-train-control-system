# Model Train Control System — Project Overview

## Elevator Pitch

**Model Train Control System** is a modular, production-grade platform for orchestrating, monitoring, and controlling model trains across distributed edge controllers and a central API, with a modern frontend and robust infrastructure. It is designed for reliability, hardware safety, and extensibility in both simulation and real hardware environments.

---

## Key Goals & Non-Goals

### Goals

- **Safe, reliable control** of model trains via edge hardware and MQTT.
- **Centralized API** for command dispatch, telemetry aggregation, and system orchestration.
- **Modern frontend** for real-time monitoring and control.
- **Scalable, maintainable architecture** with clear separation of concerns.
- **Test-driven development** and strict code quality standards.
- **Simulation support** for development without hardware.

### Non-Goals

- Not a general-purpose IoT platform.
- Not intended for direct hardware hacking outside the provided edge controller abstraction.
- Does not provide cloud-native auto-scaling or multi-tenant SaaS features.
- No support for legacy train control protocols outside documented MQTT contracts.

---

## High-Level Architecture

```mermaid
graph TD
    subgraph Edge Controllers
        EC1[edge-controllers/app]
        EC2[edge-controllers/pi-template/app]
    end
    subgraph Central API
        API[central_api/app]
    end
    subgraph Frontend
        FE[frontend/web]
    end
    subgraph Infra
        MQ[mqtt (Mosquitto)]
        DB1[TimescaleDB]
        DB2[InfluxDB]
    end

    EC1-->|MQTT|MQ
    EC2-->|MQTT|MQ
    MQ-->|Telemetry|API
    API-->|DB|DB1
    API-->|DB|DB2
```

**Explanation:**  

## Major Modules & Services

| `frontend/web/` | React frontend for UI, real-time status, and control. |
| `infra/k8s/` | Kubernetes manifests for production deployment. |
| `persistence/timescaledb/`, `persistence/influxdb/` | Time-series DB schemas and setup. |
| `docs/` | System-wide and module-specific documentation. |
| `scripts/` | Utility scripts for bootstrap, deployment, and testing. |

---

## Data Model & Schemas

- **Main Stores:**  
  - **TimescaleDB** (`persistence/timescaledb/`): Train telemetry, status, and historical data.
  - **InfluxDB** (`persistence/influxdb/`): High-frequency sensor data.
- **Schemas:**  
  - SQL migration: `central_api/migrations/001_add_controller_telemetry.sql`
  - OpenAPI: `openapi.yaml`, `Model Train Control System API 0.1.0-wrk_8d50ef17b2464ceca69ec80fb936efc1.yaml`
- **MQTT Payloads:**  
  - Canonical topic/payloads: `docs/mqtt-topics.md`

    ```json
    { "action": "setSpeed", "speed": 50 }
    ```

---

## Public APIs & Contracts

- **REST API:**  
  - Spec: `openapi.yaml`
- **WebSocket API:**  
  - Implementation: `central_api/app/routers/`
- **MQTT Topics:**  
  - Spec: `docs/mqtt-topics.md`
  - Format: `trains/{train_id}/{topic}`
    - Commands: `trains/{train_id}/commands`
- **Edge Controller API:**  
  - Spec: `edge-controllers/docs/AI_SPECS.md`


## How to Run Locally

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (edge), Python 3.10+ (central)
- Node.js (frontend)


```sh
cd infra/docker
docker-compose up --build

## Central API
make run
## Edge Controller (simulation)
cd edge-controllers/pi-template

## Frontend
cd frontend/web

## Central API tests
cd central_api
make test

## Edge Controller tests
cd edge-controllers/pi-template
make test

## Frontend tests
cd frontend/web
npm test
```

### Debugging

- Python: Use VS Code launch configs or `pytest --pdb`.

## Build & CI/CD

- **Build System:**  
  - Python: `Makefile`, `pyproject.toml`
  - Docker: `infra/docker/Dockerfile`, `edge-controllers/pi-template/Dockerfile`
- **CI/CD:**  
  - GitHub Actions: `docs/local-github-actions.md`
- **Orchestration:** Docker Compose, Kubernetes (`infra/k8s/`)

---

## Operational Concerns

- **Metrics:**  
  - Telemetry via MQTT, stored in TimescaleDB/InfluxDB.
- **Tracing:**  
  - UNCERTAIN (no explicit tracing found; see `central_api/app/services/`).
- **Logging:**  
  - Python logging in edge and API modules.
- **Recovery:**  
  - Edge controllers fail-safe on hardware/MQTT errors (`edge-controllers/docs/ARCHITECTURE.md`).
- **Scalability/HA:**  
  - Horizontal scaling via edge controller instances and stateless API.
  - DBs and MQTT can be clustered (see ADRs).

---

## Security Notes

- **Auth Model:**  
  - UNCERTAIN (no explicit auth found in API; see `central_api/app/routers/`).
- **Secrets Management:**  
  - Environment variables, `.env` files, and (suggested) Vault.
- **Sensitive Components:**  
  - Hardware control logic, MQTT topics, DB credentials.

---

## Conventions & Style

- **Python:**  
  - Type hints, strict generics, `pathlib.Path`, f-strings, pydantic/dataclasses for config.
  - Linting: `ruff`, `mypy`
  - No bare `except:`, always catch specific exceptions.
- **Frontend:**  
  - React, TypeScript, ESLint, Prettier.
- **Branching:**  
  - Feature branches (`feat/xyz`), atomic commits, Conventional Commits.
- **Testing:**  
  - TDD required, tests in `tests/` per module.
- **Docs:**  
  - Update docstrings and `AI_SPECS.md` on API changes.

---

## Key Configs & Environment Variables

- **Config Files:**  
  - `config.yaml` (root)
  - `edge-controllers/examples/pi-config.yaml`
  - `.env` files (UNCERTAIN: no `.env.example` found)
- **Secrets:**  
  - DB credentials, MQTT broker, API keys via env vars or secret manager.

---

## Known Limitations & Technical Debt

- No explicit tracing or metrics aggregation (suggested improvement).
- Auth model is unclear; recommend adding OAuth/JWT for API.
- No `.env.example` for onboarding; suggest creating one.
- Some ADRs suggest further automation and multi-motor support.
- See `docs/TODO/` for prioritized improvements.

---

## Who/Where to Ask

- **Maintainers:**  
  - UNCERTAIN (no explicit MAINTAINERS file; check `README.md` and commit history).
- **Docs:**  
  - `docs/`, module-specific `docs/AI_SPECS.md`
- **Contact:**  
  - UNCERTAIN (no Slack/channel info found).

---

## Quick Links

| Path | Description |
|------|-------------|
| `README.md` | Project root overview. |
| `docs/architecture.md` | High-level system map. |
| `docs/mqtt-topics.md` | Canonical MQTT topic/payloads. |
| `central_api/app/main.py` | FastAPI entrypoint. |
| `central_api/app/routers/` | API endpoints. |
| `central_api/app/models/` | Data models. |
| `central_api/app/services/` | Business logic. |
| `edge-controllers/app/` | Edge controller logic. |
| `edge-controllers/docs/AI_SPECS.md` | Edge controller API surface. |
| `frontend/web/` | React frontend. |
| `infra/docker/` | Docker Compose files. |
| `infra/k8s/` | Kubernetes manifests. |
| `persistence/timescaledb/` | TimescaleDB setup. |
| `persistence/influxdb/` | InfluxDB setup. |
| `scripts/` | Utility scripts. |
| `tests/` | Test suites. |

---

## Suggested Next Tasks for Incoming Engineer

1. **Run the full stack locally** using Docker Compose (`infra/docker/`).
2. **Review and run tests** for each module (`central_api/tests/`, `edge-controllers/pi-template/tests/`, `frontend/web/tests/`).
3. **Inspect and extend the API** via `central_api/app/routers/` and OpenAPI spec.
4. **Add or improve tracing/metrics** in API and edge controllers.
5. **Document environment variables** and create `.env.example` files.
6. **Review and update ADRs** in `docs/decisions/` for architectural alignment.
7. **Contribute to TODOs** in `docs/TODO/`.
8. **Validate fail-safe logic** in edge controllers for hardware/MQTT errors.

---

## Changelog / History

- **ADR-001:** Deployment automation (see `docs/decisions/ADR-001-deployment-automation.md`)
- **ADR-002:** I2C motor control (see `docs/decisions/ADR-002-i2c-motor-control.md`)
- **ADR-003:** Multi-motor containers (see `docs/decisions/ADR-003-multi-motor-containers.md`)
- **Recent changes:**  
  - Controller UI implementation (`docs/TODO/2025-12-04-controller-ui-implementation.md`)
  - Consolidated TODOs (`docs/TODO/2025-12-04-consolidated-todo.md`)
- **Release notes:**  
  - UNCERTAIN (no explicit HISTORY.md or release notes found).

---

# Validation Checklist

- [ ] Run `docker-compose up --build` in `infra/docker/` and confirm all services start.
- [ ] Open `central_api/app/main.py` and verify FastAPI launches.
- [ ] Run `make test` in `central_api/` and `edge-controllers/pi-template/`.
- [ ] Open `frontend/web/` and run `npm run dev` to confirm UI loads.
- [ ] Inspect `docs/mqtt-topics.md` for topic/payload contracts.
- [ ] Check `openapi.yaml` for API endpoint definitions.
- [ ] Review `docs/architecture.md` for system map.
- [ ] Confirm presence of test suites in `tests/` folders.
- [ ] Check for `.env` or config files in each module.
- [ ] Review ADRs in `docs/decisions/` for architectural decisions.

---

*End of `docs/PROJECT_OVERVIEW.md`*
