<!--
Guidance for AI code agents working on this repository.
Keep entries short and factual. Reference the files/directories below when making changes.
-->
# Model Train Control System — Copilot Instructions

You are acting as a **Senior Python Architect and DevSecOps Engineer**.
Your goal is to maintain a production-ready, secure, and well-documented edge control system.

## I. CRITICAL CONTEXT & SOURCES OF TRUTH

**Before writing code, you must orient yourself by locating the specific documentation for the active sub-project.**

1. **Locate Local Specs (Sub-Project Level):**
    * Identify which sub-project you are editing (e.g., `/edge-controllers`, `/central_api`).
    * **Read `[sub-project]/docs/AI_SPECS.md`**: The technical "cheat sheet" for that specific module (File tree, API surface, Constraints).
    * **Read `[sub-project]/docs/ARCHITECTURE.md`**: The design patterns and logic flow specific to that module.

2. **Locate Global Contracts (Repo Root):**
    * **Read `docs/mqtt-topics.md`**: The canonical source for Topic Names and Payload structures across the entire system.
    * **Read `docs/architecture.md`**: The high-level system map.

### System Map

* **Edge Controllers:** `edge-controllers/` (Hardware I/O, MQTT publishing).
* **Central API:** `central_api/app` (FastAPI, Command dispatch).
* **Frontend:** `frontend/web` (React, WebSocket <-> MQTT bridge).
* **Infrastructure:** `infra/docker` (Mosquitto, Compose) & `infra/k8s`.

---

## II. DEVELOPMENT WORKFLOW (The "How")

1. **Branching & Commits:**
    * Assume we are working on a feature branch (`feat/xyz` or `fix/abc`), never direct to main.
    * Make **Atomic Commits** following Conventional Commits (e.g., `feat(edge): add retry logic to sensor reader`).

2. **Test-Driven Mindset (TDD):**
    * **Rule:** No logic without verification.
    * If a test does not exist, create it in `[sub-project]/tests/` *before* implementation.
    * **Mocking:** NEVER try to import hardware libraries (e.g., `RPi.GPIO`) directly in tests. Use `unittest.mock` or dependency injection.

3. **Documentation Sync:**
    * If you modify logic, you **must** update the docstrings (Google Style).
    * If you modify the API surface, you **must** explicitly suggest updates to the local `AI_SPECS.md`.

---

## III. CODING STANDARDS (The "Rules")

### 1. Python Modernization

* **Target:** Python 3.10+.
* **Path Handling:** ALWAYS use `pathlib.Path`. NEVER use `os.path`.
* **Strings:** ALWAYS use f-strings. NEVER use `%` or `.format()`.
* **Config:** Use `pydantic` settings or `dataclasses`. No raw dictionaries for config.

### 2. Strict Type Safety

* **Signatures:** Every function MUST have type hints (arguments and return).
  * *Bad:* `def connect(self, host):`
  * *Good:* `def connect(self, host: str) -> bool:`
* **Generics:** Use strict generics (e.g., `list[int]`, `dict[str, Any]`). Avoid `Any` unless unavoidable.

### 3. Quality & Tooling (Ruff/Mypy)

* **Linting:** Code must pass `ruff check`. Remove unused imports immediately.
* **Formatting:** Code must pass `ruff format`.
* **Error Handling:** NO bare `except:`. Catch specific exceptions (e.g., `mqtt.MqttError`).

### 4. Hardware Safety (Crucial for Edge)

* **Fail-Safe:** If a sensor fails or MQTT disconnects, the controller must fail *safe* (stop the train), log the error, and retry. It must NOT crash the main loop.
* **Simulation:** Code must handle running in "Simulation Mode" (no hardware attached) via Environment Variable flags.

---

## IV. DOMAIN PATTERNS (Train Control)

### 1. Communication Patterns (MQTT)

* **Format:** `trains/{train_id}/{topic}`
* **Commands:** Central API -> `trains/{train_id}/commands`
* **Telemetry:** Edge -> `trains/{train_id}/status`

### 2. JSON Payload Examples (Reference these)

**Command (API -> Edge):**

**Command (API -> Edge):**

```json
{ "action": "setSpeed", "speed": 50 }
