# Central API Architecture

**Target Audience:** Human developers, DevOps engineers, architects  
**Version:** 1.0  
**Last Updated:** November 21, 2025

---

## Overview

The Central API is a FastAPI-based REST service that serves as the central control plane for the model train control system. It provides:

- **REST API** for configuration management and train control
- **MQTT Bridge** connecting web clients to edge controllers
- **Configuration Management** with YAML-based initialization and SQLite persistence
- **Health Monitoring** for system status and diagnostics

### System Position

The Central API sits at the heart of the distributed system:

```
Frontend (React/MQTT) ←→ Gateway (Orchestrator) ←→ Central API ←→ MQTT Broker ←→ Edge Controllers (Pi)
                                                         ↕
                                                    SQLite Database
```

**Key Responsibilities:**
1. Expose REST endpoints for train commands and configuration queries
2. Publish commands to MQTT topics consumed by edge controllers
3. Subscribe to status/telemetry topics from edge controllers
4. Persist configuration and runtime state in SQLite database
5. Validate all inputs/outputs with Pydantic schemas
6. Provide health checks and operational metrics

---

## System Components

### FastAPI Application (`app/main.py`)

**Purpose:** Application entry point with lifecycle management

**Key Features:**
- **Lifespan Events:** Async context manager handling startup/shutdown
  ```python
  @asynccontextmanager
  async def lifespan(app_instance: FastAPI):
      # Startup: Initialize ConfigManager, connect MQTT
      yield
      # Shutdown: Close connections, cleanup resources
  ```
- **Router Registration:** Mounts `/api/config` and `/api/trains` routers
- **CORS Middleware:** Configured for cross-origin requests from frontend
- **Health Endpoints:** `GET /` (welcome), `GET /ping` (health check)

**Startup Flow:**
1. Load environment variables via `Settings`
2. Initialize `ConfigManager` (loads YAML → syncs to DB)
3. Connect `MQTTAdapter` to broker
4. Register routers
5. Start FastAPI server

**Shutdown Flow:**
1. Disconnect MQTT client gracefully
2. Close database connections
3. Log shutdown completion

---

### Configuration Layer

The configuration layer implements a three-tier architecture separating concerns:

#### Settings (`app/config.py`)

**Purpose:** Environment variable validation using Pydantic Settings

**Key Settings:**
- `api_host`, `api_port` - API server binding
- `config_yaml_path` - Path to initial configuration YAML
- `config_db_path` - Path to SQLite database
- `mqtt_broker_host`, `mqtt_broker_port` - MQTT connection
- `log_level` - Logging verbosity

**Validation:**
- Port ranges: 1-65535
- Path objects for file system paths
- Type-safe with Pydantic Field validators

**Example:**
```python
settings = get_settings()
# settings.api_port is guaranteed to be 1-65535
# settings.config_yaml_path is a Path object
```

#### ConfigManager (`app/services/config_manager.py`)

**Purpose:** Facade pattern orchestrating config loading and persistence

**Responsibilities:**
1. **Bootstrap:** Load YAML config and sync to database on startup
2. **Query:** Provide unified access to config data (trains, controllers, plugins)
3. **Mutation:** Handle updates to edge controllers and train status
4. **Validation:** Enforce UUID formats and business rules

**Architecture Pattern:** Facade
- Hides complexity of ConfigLoader + ConfigRepository
- Single entry point for all configuration operations
- Handles cross-cutting concerns (logging, error translation)

**Key Methods:**
- `get_full_config()` - Returns complete system configuration
- `get_train(train_id)` - Retrieve single train
- `list_trains()` - Return all trains
- `add_edge_controller(controller)` - Register new controller
- `update_edge_controller(controller_id, updates)` - Modify controller
- `get_train_status(train_id)` - Latest telemetry from train

**UUID Validation:**
```python
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)
```

#### ConfigLoader (`app/services/config_loader.py`)

**Purpose:** YAML file loading and structural validation

**Validation Rules:**
```python
REQUIRED_TOP_LEVEL_KEYS = ["plugins", "trains", "edge_controllers"]
REQUIRED_PLUGIN_FIELDS = ["id", "name", "version", "config_schema"]
```

**Process:**
1. Read YAML file with PyYAML
2. Validate presence of required top-level keys
3. Validate each plugin has required fields
4. Validate train and edge_controller structures
5. Raise `ConfigLoadError` if validation fails

**Error Handling:**
- File not found → `ConfigLoadError`
- Invalid YAML syntax → `ConfigLoadError`
- Missing required keys → `ConfigLoadError` with details

#### ConfigRepository (`app/services/config_repository.py`)

**Purpose:** Repository pattern for SQLite database operations

**Architecture Pattern:** Repository
- Encapsulates data access logic
- Provides domain-model interface (not raw SQL)
- Handles connection management and transactions

**Schema:**
```sql
-- Edge controllers (Raspberry Pi devices)
CREATE TABLE edge_controllers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    config_json TEXT
);

-- Model trains
CREATE TABLE trains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config_json TEXT
);

-- Available plugins (motor control, lighting, etc.)
CREATE TABLE plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    config_schema_json TEXT
);

-- Runtime train status (speed, voltage, position)
CREATE TABLE train_status (
    train_id TEXT PRIMARY KEY,
    speed INTEGER,
    voltage REAL,
    current REAL,
    position TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_id) REFERENCES trains(id)
);
```

**Transaction Handling:**
```python
def add_edge_controller(self, controller: EdgeController):
    with self.conn:  # Auto-commit/rollback
        self.conn.execute(
            "INSERT INTO edge_controllers ...",
            (controller.id, controller.name, ...)
        )
```

**CRUD Methods:**
- `get_edge_controller(id)`, `add_edge_controller()`, `update_edge_controller()`
- `get_train(id)`, `list_trains()`, `add_train()`
- `get_plugin(id)`, `list_plugins()`, `add_plugin()`
- `update_train_status()`, `get_train_status()`

---

### Data Models (`app/models/schemas.py`)

**Purpose:** Pydantic models for request/response validation

**Model Hierarchy:**

```
FullConfig
├── plugins: list[Plugin]
├── trains: list[Train]
└── edge_controllers: list[EdgeController]

Plugin
├── id: str
├── name: str
├── version: str
└── config_schema: dict[str, Any]

Train
├── id: str
├── name: str
└── plugins: list[TrainPlugin]

TrainPlugin
├── plugin_id: str
└── config: dict[str, Any]

EdgeController
├── id: str
├── name: str
├── location: Optional[str]
├── trains: list[str]
└── config: dict[str, Any]

TrainStatus
├── train_id: str
├── speed: Optional[int]
├── voltage: Optional[float]
├── current: Optional[float]
├── position: Optional[str]
└── timestamp: Optional[str]
```

**Validation Features:**
- Type coercion (strings to ints, etc.)
- Required vs optional fields
- Nested model validation
- JSON serialization/deserialization
- Field constraints (min/max values)

**Usage in Endpoints:**
```python
@router.get("/trains/{train_id}", response_model=Train)
async def get_train_by_id(train_id: str) -> Train:
    # FastAPI automatically validates return value matches Train schema
    return config_manager.get_train(train_id)
```

---

### API Routers

#### Configuration Router (`app/routers/config.py`)

**Endpoints:**

| Endpoint | Method | Description | Response Model |
|----------|--------|-------------|----------------|
| `/api/config` | GET | Get full system config | `FullConfig` |
| `/api/config/edge-controllers` | GET | List all edge controllers | `list[EdgeController]` |
| `/api/config/edge-controllers/{id}` | GET | Get controller by ID | `EdgeController` |
| `/api/config/edge-controllers/{id}` | PUT | Update controller | `EdgeController` |
| `/api/config/trains` | GET | List all trains | `list[Train]` |
| `/api/config/trains/{id}` | GET | Get train config | `Train` |
| `/api/config/trains/{id}/status` | GET | Get train status | `TrainStatus` |
| `/api/config/trains/{id}/status` | PUT | Update train status | `TrainStatus` |

**Error Responses:**
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Pydantic validation failed
- `500 Internal Server Error` - Database/MQTT error

#### Trains Router (`app/routers/trains.py`)

**Endpoints:**

| Endpoint | Method | Description | Response Model |
|----------|--------|-------------|----------------|
| `/api/trains` | GET | List all trains | `list[Train]` |
| `/api/trains/{id}` | GET | Get train by ID | `Train` |
| `/api/trains/{id}/command` | POST | Send command to train | `dict` |
| `/api/trains/{id}/status` | GET | Get train status | `TrainStatus` |

**Command Flow:**
```
Frontend → POST /api/trains/{id}/command
         → Router validates payload
         → MQTTAdapter.publish_command()
         → MQTT topic: trains/{id}/commands
         → Edge controller receives command
         → Edge controller publishes status
         → MQTT topic: trains/{id}/status
         → Central API receives status
         → Store in database
```

---

### MQTT Integration (`app/services/mqtt_adapter.py`)

**Purpose:** MQTT client wrapper for pub/sub operations

**Topic Structure:**
```
trains/{train_id}/commands     → Publish commands to edge controller
trains/{train_id}/status       → Subscribe to status updates from edge controller
trains/{train_id}/telemetry    → Subscribe to telemetry data (future)
```

**Connection Management:**
- Automatic reconnection on disconnect
- QoS level 1 (at least once delivery)
- Clean session = False (persistent subscriptions)

**Publishing Commands:**
```python
def publish_command(train_id: str, command: dict):
    topic = f"trains/{train_id}/commands"
    payload = json.dumps(command)
    client.publish(topic, payload, qos=1)
```

**Subscribing to Status:**
```python
def on_message(client, userdata, message):
    topic = message.topic  # trains/123/status
    payload = json.loads(message.payload)

    # Extract train_id from topic
    train_id = topic.split('/')[1]

    # Update database
    config_manager.update_train_status(train_id, payload)
```

**Message Formats:**

Command (Central API → Edge Controller):
```json
{
  "action": "setSpeed",
  "speed": 50,
  "timestamp": "2025-11-21T10:15:30Z"
}
```

Status (Edge Controller → Central API):
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

---

## Data Flow

### Configuration Bootstrap Flow

```
1. Application Startup
   ↓
2. Load config.yaml (ConfigLoader)
   ↓
3. Validate YAML structure
   ↓
4. Initialize SQLite database (ConfigRepository)
   ↓
5. Sync YAML data to database
   ↓
6. ConfigManager ready for API requests
```

**Detailed Steps:**

1. **FastAPI lifespan event triggers**
   - `settings = get_settings()` loads environment variables
   - `config_manager = ConfigManager(yaml_path, db_path)` initializes

2. **ConfigLoader loads YAML**
   ```python
   config_data = loader.load_config()
   # Returns: {"plugins": [...], "trains": [...], "edge_controllers": [...]}
   ```

3. **ConfigRepository initializes database**
   ```python
   # Read config_schema.sql
   # Execute CREATE TABLE statements
   # Database ready for inserts
   ```

4. **ConfigManager syncs YAML → Database**
   ```python
   for plugin in config_data["plugins"]:
       repository.add_plugin(Plugin(**plugin))

   for train in config_data["trains"]:
       repository.add_train(Train(**train))

   for controller in config_data["edge_controllers"]:
       repository.add_edge_controller(EdgeController(**controller))
   ```

5. **Application ready to serve requests**

---

### Train Command Flow

```
Frontend → API → MQTT → Edge Controller → MQTT → API → Database
```

**Step-by-Step:**

1. **Frontend sends command**
   ```bash
   curl -X POST http://localhost:8000/api/trains/train-001/command \
     -H "Content-Type: application/json" \
     -d '{"action": "setSpeed", "speed": 75}'
   ```

2. **Router validates request**
   ```python
   @router.post("/trains/{train_id}/command")
   async def send_command(train_id: str, command: dict):
       # Pydantic validates command structure
       train = config_manager.get_train(train_id)
       if not train:
           raise HTTPException(404)
   ```

3. **MQTTAdapter publishes to topic**
   ```python
   mqtt_adapter.publish_command(train_id, command)
   # Publishes to: trains/train-001/commands
   ```

4. **Edge controller receives command**
   - Subscribes to `trains/train-001/commands`
   - Parses JSON payload
   - Executes motor control action

5. **Edge controller publishes status**
   ```python
   # Publishes to: trains/train-001/status
   {
       "train_id": "train-001",
       "speed": 75,
       "voltage": 12.1,
       "current": 0.9,
       "timestamp": "2025-11-21T10:15:32Z"
   }
   ```

6. **Central API receives status update**
   ```python
   def on_message(client, userdata, message):
       status = TrainStatus(**json.loads(message.payload))
       config_manager.update_train_status(status.train_id, status)
   ```

7. **Status stored in database**
   ```sql
   UPDATE train_status
   SET speed = 75, voltage = 12.1, current = 0.9, timestamp = '2025-11-21T10:15:32Z'
   WHERE train_id = 'train-001';
   ```

---

### Configuration Update Flow

```
Client → PUT /api/config/edge-controllers/{id} → Validate → Database → Response
```

**Step-by-Step:**

1. **Client sends update request**
   ```bash
   curl -X PUT http://localhost:8000/api/config/edge-controllers/controller-001 \
     -H "Content-Type: application/json" \
     -d '{"location": "Section B"}'
   ```

2. **Router receives request**
   ```python
   @router.put("/config/edge-controllers/{controller_id}")
   async def update_edge_controller(controller_id: str, updates: dict):
       # FastAPI parses JSON body to dict
   ```

3. **Pydantic validates updates**
   - Type checking (location must be string)
   - Field validation (if defined in schema)

4. **ConfigManager processes update**
   ```python
   updated_controller = config_manager.update_edge_controller(
       controller_id, updates
   )
   # Calls repository.update_edge_controller()
   ```

5. **Repository updates database**
   ```python
   with self.conn:
       self.conn.execute(
           "UPDATE edge_controllers SET location = ? WHERE id = ?",
           (updates["location"], controller_id)
       )
   ```

6. **Response returned to client**
   ```json
   {
     "id": "controller-001",
     "name": "Pi Controller 1",
     "location": "Section B",
     "trains": ["train-001"],
     "config": {}
   }
   ```

---

## Deployment

### Docker

**Multi-Stage Dockerfile:**

```dockerfile
# Stage 1: Build dependencies
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY app/ ./app/
COPY config.yaml ./

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Environment Variables:**
```bash
API_HOST=0.0.0.0
API_PORT=8000
CENTRAL_API_CONFIG_YAML=/app/config.yaml
CENTRAL_API_CONFIG_DB=/app/data/central_api_config.db
MQTT_BROKER_HOST=mqtt-broker
MQTT_BROKER_PORT=1883
LOG_LEVEL=INFO
```

**Volume Mounts:**
- `/app/config.yaml` - Configuration file
- `/app/data/` - SQLite database directory

**Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ping || exit 1
```

---

### Local Development

**Requirements:**
- Python 3.9+
- SQLite 3.x
- MQTT broker (Mosquitto)

**Setup:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example config
cp config.yaml.example config.yaml

# Run migrations (if needed)
python -m app.services.config_repository --init-schema

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Development Workflow:**
```bash
# Run linter
make lint

# Run type checker
make typecheck

# Run tests
make test

# Run security scan
make security

# Run all checks
make ci
```

---

### Docker Compose Integration

**Service Definition:**
```yaml
services:
  mqtt-broker:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf

  central_api:
    build: ./central_api
    ports:
      - "8000:8000"
    depends_on:
      - mqtt-broker
    environment:
      - MQTT_BROKER_HOST=mqtt-broker
      - MQTT_BROKER_PORT=1883
      - LOG_LEVEL=DEBUG
    volumes:
      - ./central_api/config.yaml:/app/config.yaml
      - central_api_data:/app/data

  gateway:
    build: ./gateway/orchestrator
    ports:
      - "3001:3001"
    depends_on:
      - central_api
      - mqtt-broker

volumes:
  central_api_data:
```

**Network Configuration:**
- All services on shared Docker network
- Service discovery via DNS (service names)
- MQTT broker accessible as `mqtt-broker:1883`
- Central API accessible as `central_api:8000`

---

## Security

### Input Validation

**Pydantic Schema Validation:**
```python
# All endpoints automatically validate inputs
@router.post("/trains/{train_id}/command")
async def send_command(train_id: str, command: dict):
    # Pydantic validates:
    # - command is valid JSON
    # - command matches expected structure
    # - Types are correct (speed is int, not string)
```

**UUID Format Validation:**
```python
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)

if not UUID_PATTERN.match(controller_id):
    raise ValueError(f"Invalid UUID format: {controller_id}")
```

**Path Traversal Prevention:**
- All file paths validated with `pathlib.Path`
- No user-supplied path components
- Config paths from environment variables only

---

### MQTT Security

**Current Implementation:**
- Unauthenticated MQTT broker (development only)
- Plain TCP (no TLS)
- No topic ACLs

**Production Recommendations:**

1. **Authentication:**
   ```python
   client.username_pw_set(username="central_api", password=os.getenv("MQTT_PASSWORD"))
   ```

2. **TLS Encryption:**
   ```python
   client.tls_set(ca_certs="/path/to/ca.crt", certfile="/path/to/client.crt", keyfile="/path/to/client.key")
   client.tls_insecure_set(False)
   ```

3. **Topic ACLs:**
   ```
   # Mosquitto ACL file
   user central_api
   topic write trains/+/commands
   topic read trains/+/status
   ```

---

### API Security (Future)

**Planned Enhancements:**
1. **Authentication:** OAuth2 with JWT tokens
2. **Authorization:** Role-based access control (RBAC)
3. **Rate Limiting:** Per-client request throttling
4. **API Keys:** Machine-to-machine authentication
5. **HTTPS:** TLS termination at load balancer

---

## Performance Considerations

### Database

**SQLite Limitations:**
- Single-writer constraint (serial writes)
- File-based (no network access)
- Limited concurrency under high write load

**Production Migration Path:**
```python
# Replace SQLite with PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./central_api_config.db")

if DATABASE_URL.startswith("postgresql"):
    engine = create_async_engine(DATABASE_URL)
    # Use SQLAlchemy ORM for PostgreSQL
else:
    # Keep sqlite3 for development
```

**Connection Pooling:**
- SQLite: Use same connection (thread-safe with check_same_thread=False)
- PostgreSQL: Use async connection pool (10-20 connections)

**Indexing Strategy:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_trains_id ON trains(id);
CREATE INDEX idx_train_status_train_id ON train_status(train_id);
CREATE INDEX idx_edge_controllers_id ON edge_controllers(id);
```

---

### MQTT

**QoS Levels:**
- QoS 0: At most once (fast, no guarantees)
- QoS 1: At least once (reliable, possible duplicates) ← **Current**
- QoS 2: Exactly once (slow, no duplicates)

**Recommendation:** QoS 1 for commands, QoS 0 for status updates

**Message Retention:**
```python
# Retain last status message for new subscribers
client.publish(topic, payload, qos=1, retain=True)
```

**Connection Pooling:**
- Single persistent MQTT client per Central API instance
- Automatic reconnection with exponential backoff
- Shared subscriptions for horizontal scaling (future)

---

### Caching (Future)

**Redis Integration:**
```python
# Cache frequently accessed config
@cache(ttl=300)  # 5 minutes
def get_full_config():
    return config_manager.get_full_config()

# Cache train status (short TTL)
@cache(ttl=5)  # 5 seconds
def get_train_status(train_id):
    return config_manager.get_train_status(train_id)
```

---

## Testing Strategy

### Unit Tests (`tests/unit/`)

**Scope:** Individual components in isolation with mocked dependencies

**Coverage:**
- ConfigManager business logic (47 tests)
- ConfigLoader validation
- ConfigRepository CRUD operations
- Pydantic model validation
- UUID validation
- Error handling

**Example:**
```python
@pytest.mark.unit
def test_get_train_by_id_not_found(config_manager_mock):
    """Test train retrieval with invalid ID returns None."""
    train = config_manager_mock.get_train("nonexistent-uuid")
    assert train is None
```

**Mock Strategy:**
- Mock database connections
- Mock MQTT client
- Mock file system operations
- Use pytest fixtures for test data

---

### Integration Tests (`tests/integration/`)

**Scope:** Multiple components working together with real dependencies

**Coverage:**
- YAML → Database synchronization
- API endpoint contracts
- MQTT publish/subscribe
- Database transactions
- Error propagation

**Example:**
```python
@pytest.mark.integration
def test_yaml_to_database_sync(tmp_path):
    """Test full YAML → Database synchronization."""
    yaml_path = tmp_path / "config.yaml"
    db_path = tmp_path / "test.db"

    # Write test config
    yaml_path.write_text("""
    plugins: [...]
    trains: [...]
    edge_controllers: []
    """)

    # Initialize manager
    manager = ConfigManager(yaml_path=yaml_path, db_path=db_path)

    # Verify data in database
    trains = manager.list_trains()
    assert len(trains) > 0
```

**Test Environment:**
- Temporary database files
- Isolated MQTT broker (test container)
- Separate test config files

---

### End-to-End Tests (`tests/e2e/`)

**Scope:** Full request lifecycle across all system components

**Coverage:**
- Complete train command flow (API → MQTT → Edge → Status)
- Configuration updates end-to-end
- Error scenarios (network failures, invalid data)
- Performance under load

**Example:**
```python
@pytest.mark.e2e
async def test_full_train_command_flow(test_client, mqtt_broker_running):
    """Test complete train command flow."""
    # Send command via API
    response = test_client.post(
        "/api/trains/train-001/command",
        json={"action": "setSpeed", "speed": 75}
    )
    assert response.status_code == 200

    # Wait for MQTT propagation
    await asyncio.sleep(1)

    # Verify status was updated
    status_response = test_client.get("/api/trains/train-001/status")
    status = status_response.json()
    assert status["speed"] == 75
```

**Test Environment:**
- Docker Compose with all services
- Real MQTT broker
- Mock edge controllers (simulated responses)

---

### Test Metrics

**Current Status:**
- **Unit Tests:** 47/48 passing (98% pass rate)
- **Coverage:** 48% (target: 80%+)
- **Integration Tests:** Created, needs expansion
- **E2E Tests:** Created, needs implementation

**CI/CD Integration:**
```yaml
# GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run unit tests
        run: pytest tests/unit/ -v

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Generate coverage report
        run: pytest --cov=app --cov-report=html
```

---

## Dependencies

### Production Requirements

```
fastapi==0.104.1          # Web framework
pydantic==2.5.0           # Data validation
pydantic-settings==2.1.0  # Settings management
uvicorn==0.24.0           # ASGI server
paho-mqtt==1.6.1          # MQTT client
aiosqlite==0.19.0         # Async SQLite
pyyaml==6.0.1             # YAML parsing
```

**Dependency Rationale:**
- **FastAPI:** Modern async framework with automatic OpenAPI docs
- **Pydantic V2:** Type-safe validation, 5-50x faster than V1
- **Uvicorn:** Production-ready ASGI server with worker management
- **Paho MQTT:** Eclipse Foundation official MQTT client
- **aiosqlite:** Async SQLite for non-blocking database operations
- **PyYAML:** Industry-standard YAML parser

---

### Development Requirements

```
ruff==0.3.4               # Linter and formatter
mypy==1.9.0               # Static type checker
pytest==8.1.1             # Testing framework
pytest-cov==5.0.0         # Coverage plugin
pytest-asyncio==0.23.6    # Async test support
bandit==1.7.8             # Security scanner
safety==3.1.0             # Dependency scanner
httpx==0.27.0             # TestClient for FastAPI
```

**Tool Rationale:**
- **Ruff:** 10-100x faster than Flake8/Black, single tool for lint+format
- **MyPy:** Industry-standard Python type checker
- **Pytest:** Most popular Python testing framework
- **Bandit:** OWASP-recommended security scanner
- **Safety:** Checks dependencies against vulnerability database

---

### Version Constraints

**Python Version:** 3.9+
- Uses `Optional[]` syntax (not `|`) for compatibility
- Modern async/await support
- Type hint improvements from 3.8+

**Pydantic V2 Migration:**
- Breaking changes from V1 → V2
- 5-50x performance improvement
- New `pydantic-settings` package required
- Updated validation error format

**Dependency Alignment:**
- Central API dependencies match edge-controllers versions
- Consistent Ruff/MyPy/Bandit configurations
- Shared CI/CD patterns

---

## Future Enhancements

### WebSocket Support

**Use Case:** Real-time train status updates to frontend

```python
from fastapi import WebSocket

@app.websocket("/ws/trains/{train_id}/status")
async def websocket_train_status(websocket: WebSocket, train_id: str):
    await websocket.accept()

    # Subscribe to MQTT status updates
    def on_status(status):
        await websocket.send_json(status)

    mqtt_adapter.subscribe_status(train_id, on_status)

    # Keep connection alive
    while True:
        await websocket.receive_text()
```

---

### PostgreSQL/TimescaleDB Backend

**Migration Path:**

1. **Replace SQLite with PostgreSQL:**
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

   engine = create_async_engine(DATABASE_URL)
   async_session = sessionmaker(engine, class_=AsyncSession)
   ```

2. **Use TimescaleDB for time-series data:**
   ```sql
   -- Hypertable for train telemetry
   CREATE TABLE train_telemetry (
       time TIMESTAMPTZ NOT NULL,
       train_id TEXT NOT NULL,
       speed INTEGER,
       voltage REAL,
       current REAL
   );

   SELECT create_hypertable('train_telemetry', 'time');
   ```

3. **Benefits:**
   - Horizontal scaling (read replicas)
   - Advanced querying (time-series analytics)
   - Better concurrency (multi-writer)

---

### Authentication & Authorization

**OAuth2 with JWT:**

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/trains/{train_id}/command")
async def send_command(
    train_id: str,
    command: dict,
    token: str = Depends(oauth2_scheme)
):
    # Validate JWT token
    user = decode_jwt(token)

    # Check permissions
    if not user.has_permission("train:command"):
        raise HTTPException(403, "Forbidden")

    # Execute command
    mqtt_adapter.publish_command(train_id, command)
```

**Role-Based Access Control:**
- **Admin:** Full access (all endpoints)
- **Operator:** Train commands, read config
- **Viewer:** Read-only access

---

### Rate Limiting

**Per-Client Throttling:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/trains/{train_id}/command")
@limiter.limit("10/minute")  # Max 10 commands per minute
async def send_command(request: Request, train_id: str, command: dict):
    mqtt_adapter.publish_command(train_id, command)
```

---

### Message Queue for Command Buffering

**RabbitMQ/Redis Queue:**

```python
# Instead of direct MQTT publish, enqueue command
redis_queue.enqueue("train_commands", {
    "train_id": train_id,
    "command": command,
    "timestamp": datetime.utcnow()
})

# Background worker processes queue
while True:
    cmd = redis_queue.dequeue("train_commands")
    mqtt_adapter.publish_command(cmd["train_id"], cmd["command"])
```

**Benefits:**
- Guaranteed delivery (persistent queue)
- Rate limiting (process N commands per second)
- Retry logic (dead letter queue)
- Observability (queue depth metrics)

---

### Observability

**Prometheus Metrics:**

```python
from prometheus_client import Counter, Histogram

command_counter = Counter("train_commands_total", "Total train commands", ["train_id"])
command_latency = Histogram("train_command_latency_seconds", "Command latency")

@router.post("/trains/{train_id}/command")
async def send_command(train_id: str, command: dict):
    command_counter.labels(train_id=train_id).inc()

    with command_latency.time():
        mqtt_adapter.publish_command(train_id, command)
```

**Structured Logging:**

```python
import structlog

logger = structlog.get_logger()

logger.info("train_command_sent",
    train_id=train_id,
    action=command["action"],
    speed=command.get("speed")
)
```

---

## References

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Pydantic V2 Documentation:** https://docs.pydantic.dev/2.5/
- **Paho MQTT Client:** https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html
- **Project MQTT Topics:** `../../docs/mqtt-topics.md`
- **Overall System Architecture:** `../../docs/architecture.md`
- **AI Agent Specifications:** `./AI_SPECS.md`
- **Edge Controller Docs:** `../../edge-controllers/docs/`
