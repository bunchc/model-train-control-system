<!--
Guidance for AI code agents working on this repository.
Keep entries short and factual. Reference the files/directories below when making changes.
-->
# Model Train Control System — Copilot instructions

This file highlights the concrete, discoverable patterns and entry points an AI agent needs to be productive in this repo.

1. Big picture & primary components
   - Edge controllers: `edge-controllers/pi-template` (Pi app template). Controls hardware and publishes telemetry via MQTT.
   - Central API: `central_api/app` (FastAPI). Exposes endpoints such as `GET /api/trains`, `POST /api/trains/{id}/command` and uses `app/services/mqtt_adapter.py` to publish/subscribe MQTT topics.
   - Frontend: `frontend/web` (React + MQTT over WebSocket). Key files: `src/services/mqtt.ts`, `src/components/Dashboard.tsx`.
   - Gateway / Orchestrator: `gateway/orchestrator` (bridges MQTT/HTTP for the web UI). Look for MQTT client glue here.
   - Infra: `infra/docker/docker-compose.yml` defines local compose setup using `eclipse-mosquitto`, `central_api`, `gateway`, and a sample `edge-controller`.

2. Communication patterns
   - MQTT is the primary runtime integration. Topics follow the pattern `trains/{train_id}/commands` and `trains/{train_id}/status`. See `docs/mqtt-topics.md` for examples.
   - Central API publishes commands to MQTT (see `central_api/app/services/mqtt_adapter.py`) and exposes REST endpoints in `central_api/app/routers/trains.py`.
   - Frontend subscribes to status topics via `frontend/web/src/services/mqtt.ts` and updates `Dashboard.tsx`.

3. Conventions & code patterns to follow
   - Keep MQTT topic strings and payload shapes consistent with `docs/mqtt-topics.md` and `central_api/app/models/schemas.py` (Pydantic models).
   - Central API uses FastAPI; preserve async endpoints and Pydantic models for request/response validation.
   - Edge controller template is minimal: prefer reusing `pi-template` for new controllers.
   - Docker Compose in `infra/docker/docker-compose.yml` is authoritative for local integration testing. When adding services, wire them into compose and set `depends_on` for MQTT.

4. Tests & quick checks
   - Unit tests live under `tests/unit` (e.g., `test_mqtt_adapter.py`) — mock MQTT interactions when adding logic.
   - Integration tests in `tests/integration` assume local compose network; run `cd infra/docker && docker-compose up --build` before the end-to-end test.

5. Files to read before editing runtime behavior
   - `docs/architecture.md` — high-level intent and flow.
   - `docs/mqtt-topics.md` — canonical topic names and payload examples.
   - `central_api/app/services/mqtt_adapter.py` — how the API publishes/subscribes.
   - `frontend/web/src/services/mqtt.ts` — frontend subscription and publishing behavior.

6. Small, low-risk improvements preferred
   - Fix mismatched topic names or JSON shapes between API and frontend/edge code.
   - Add or update Pydantic models in `central_api/app/models/schemas.py` and keep routers' response_model in sync.
   - Add unit tests for MQTT publish/subscribe logic (mocking external network calls).

7. What not to change without human review
   - Hardware control logic in `edge-controllers` that touches GPIO or serial; these need real-device testing.
   - Production deployment manifests in `infra/k8s/manifests` or `infra/terraform` — these are environment-sensitive.

8. Example snippets (use as templates)
   - Publish command from API: central API calls into `publish_command(train_id, command)` in `central_api/app/services/mqtt_adapter.py`.
   - Frontend publishes user actions via `fetch('/api/trains/{id}/command', { method: 'POST', body: JSON.stringify(...) })` and listens to `trains/+/status` in `frontend/web/src/services/mqtt.ts`.

    - Example MQTT payloads (copy/paste-ready):
       - Command (topic: `trains/1/commands`):
          ```json
          { "action": "setSpeed", "speed": 50 }
          ```
       - Start/Stop (topic: `trains/1/commands`):
          ```json
          { "action": "start" }
          { "action": "stop" }
          ```
       - Status update (topic: `trains/1/status`):
          ```json
          {
             "train_id": "1",
             "speed": 50,
             "voltage": 12.3,
             "current": 0.8,
             "position": "section_A"
          }
          ```

If any section above is unclear or you need more examples (edge code, specific topic names, or expected JSON shapes), tell me which area to expand and I will update this file.
