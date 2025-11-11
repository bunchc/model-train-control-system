# Local Development & Testing Guide

This guide covers how to run, test, and verify the Model Train Control System locally.

---

## Prerequisites
- Python 3.10+ (for API/unit tests)
- Docker & docker-compose (for integration tests and full stack)
- Node.js/npm (for frontend/gateway, if running outside Docker)
- MQTT CLI tools (optional, for manual broker checks)

---

## 1. Running the Full Stack

**Recommended:** Use Docker Compose for all services.

```bash
cd infra/docker
docker-compose up --build
```

This starts:
- `mqtt` (Eclipse Mosquitto broker) on ports 1883 (MQTT) and 9001 (WebSocket)
- `central-api` (FastAPI) on port 8000
- `gateway` (Express/Node) on port 3000
- `edge-controller` (simulated Pi app)

---

## 2. Unit Tests

**Location:** `tests/unit/test_mqtt_adapter.py`

**Run:**
```bash
pytest -q tests/unit/test_mqtt_adapter.py
```

---

## 3. Integration Tests

**Location:** `tests/integration/test_end_to_end.py`

**Run:**
Start the stack (see above), then in another terminal:
```bash
pytest -q tests/integration/test_end_to_end.py
```

---

## 4. Manual Verification (MQTT/REST)

**Send a command via API:**
```bash
curl -X POST http://localhost:8000/api/trains/1/command \
  -H "Content-Type: application/json" \
  -d '{"action":"setSpeed","speed":42}'
```

**Subscribe to MQTT topic:**
```bash
mosquitto_sub -h localhost -p 1883 -t 'trains/1/commands' -v
```

**Publish a status (simulate edge):**
```bash
mosquitto_pub -h localhost -p 1883 -t 'trains/1/status' -m '{"train_id":"1","speed":42,"voltage":12.2,"position":"section_A"}'
```

---

## 5. Frontend & Gateway

**Frontend:**
```bash
cd frontend/web
npm install
npm start
```
- Ensure MQTT broker URL is set to `ws://localhost:9001` in `src/services/mqtt.ts`.

**Gateway:**
```bash
cd gateway/orchestrator
npm install
npm start
```

---

## 6. Example Verification Flow

1. Start all services with Docker Compose.
2. Use `curl` to send a command to the API.
3. Use `mosquitto_sub` to verify the command is published to MQTT.
4. Use `mosquitto_pub` to simulate a train status update.
5. Check the frontend or gateway logs for status updates.

---

## 7. Troubleshooting
- If a service fails to connect to MQTT, check that the broker is running (`docker-compose ps`).
- For frontend MQTT issues, confirm the WebSocket URL matches `ws://localhost:9001`.
- For integration tests, ensure all containers are healthy and reachable.

---

## 8. Additional Notes
- See `docs/mqtt-topics.md` for topic conventions and payload examples.
- See `infra/docker/docker-compose.yml` for service wiring and ports.
- Unit and integration tests mock or require the broker; always start the stack for integration tests.

---
