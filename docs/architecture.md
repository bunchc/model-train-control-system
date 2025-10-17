# Architecture Overview of the Model Train Control System

## 1. Edge Layer (Train Controllers)
- **Devices**: Raspberry Pis (one per train or per section of track)
- **Responsibilities**:
  - Direct control of train hardware (motors, sensors, lights, etc.)
  - Expose a lightweight local API (or MQTT client) for receiving commands
  - Send telemetry data (speed, position, current, etc.) upstream

### Implementation Options:
- **REST API**: FastAPI, Flask, or Node.js Express running locally
- **MQTT Client**: paho-mqtt or asyncio-mqtt
- **Hardware Control**: GPIO, I2C, or serial (e.g., to an Arduino motor controller)

## 2. Connectivity Layer (Messaging or Gateway)
### Option A – Message Broker (Event-driven)
- Use MQTT broker (like Mosquitto, EMQX, or AWS IoT Core)
- All Pis subscribe/publish to topics like:
  - `trains/{train_id}/commands`
  - `trains/{train_id}/status`
- The web API publishes commands, and trains respond with telemetry
- Enables low latency and bidirectional communication

### Option B – REST Gateway (API-driven)
- A central REST API forwards commands to each Pi’s API endpoint
- The Pi runs a microservice exposing `/start`, `/stop`, `/setSpeed`, etc.
- Simpler to reason about, but less scalable and slower for real-time control

## 3. Application Layer (Central API Gateway / Orchestrator)
- **Purpose**:
  - Provide a unified interface for all trains
  - Manage authentication, user sessions, train discovery, telemetry history
  - Serve the frontend web app and API docs
- **Implementation**: FastAPI or NestJS (excellent for REST + WebSocket/MQTT integration)

### Example Endpoints:
- `GET /api/trains` → list available trains
- `POST /api/trains/{id}/command` → send a control command
- `GET /api/trains/{id}/status` → get current telemetry

## 4. Frontend Layer (Responsive Control UI)
- **Frameworks**: React, SvelteKit, or Vue
- **UI Features**:
  - Real-time dashboard (train speed, lights, track sensors)
  - Controls (sliders, toggles, direction buttons)
  - Map of train layout
- **Data Flow**:
  - Uses WebSocket or MQTT-over-WebSocket for live updates
  - REST calls for configuration or manual control

## 5. Optional Cloud / Persistence Layer
- If you want history, analytics, or remote access:
  - Store telemetry in a time-series DB (e.g., InfluxDB, TimescaleDB, or DynamoDB)
  - Use AWS IoT Core, Azure IoT Hub, or a self-hosted Mosquitto + Grafana stack
  - Run cloud functions (e.g., AWS Lambda) for automation rules

## Example Stack Summary
| Layer               | Technology                          | Notes                                      |
|---------------------|-------------------------------------|--------------------------------------------|
| Train control       | Python (RPi.GPIO, FastAPI)         | Local REST + hardware control              |
| Messaging           | MQTT (Mosquitto)                   | Publish/subscribe to commands and status   |
| API Gateway         | FastAPI / NestJS                   | Central orchestrator + web backend         |
| Frontend            | React / Svelte                     | Web UI with live data                      |
| Persistence         | InfluxDB / SQLite / DynamoDB       | Optional telemetry/history                  |
| Deployment          | Docker Compose / K8s / AWS Lambda   | Distributed or serverless                  |

## Example Flow
1. Frontend UI → Sends command: `POST /api/trains/1/command {"speed": 50}`
2. API Gateway → Publishes to topic `trains/1/commands`
3. Raspberry Pi (train 1) → Subscribed to `trains/1/commands`
4. Pi executes hardware control (set PWM for motor speed)
5. Pi publishes status update → `trains/1/status {"speed":50,"voltage":12}`
6. UI subscribes to `trains/+/status` via WebSocket and updates dashboard live.

## Serverless Twist (Optional)
- If you want to make this “cloud-native”:
  - Use AWS IoT Core for MQTT management
  - AWS Lambda or Azure Functions for the REST API
  - AWS Amplify for the web frontend
  - Each Pi just needs an MQTT client with its device certificate

This gives you scalability, automatic discovery, and global remote control with minimal infrastructure.