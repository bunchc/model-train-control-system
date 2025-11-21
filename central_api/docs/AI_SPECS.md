# Central API AI Agent Specifications

**Target Audience:** AI Code Agents, LLM-based Development Tools  
**Purpose:** High-density technical specifications for autonomous code generation and modification  
**Version:** 1.0  
**Last Updated:** November 21, 2025

---

## Quick Reference

| Aspect | Value |
|--------|-------|
| **Language** | Python 3.9+ |
| **Framework** | FastAPI 0.104.1 |
| **Type System** | Strict type hints (MyPy validated) |
| **Code Style** | Ruff (line-length=100, Python 3.9 target) |
| **Docstring Format** | Google-style |
| **Testing Framework** | Pytest (80%+ coverage required) |
| **Security Scanner** | Bandit 1.7.8, Safety 3.1.0 |
| **Primary Dependencies** | FastAPI, Pydantic 2.5.0, paho-mqtt, aiosqlite |
| **Database** | SQLite (development), PostgreSQL (production-ready) |
| **MQTT Broker** | Eclipse Mosquitto (eclipse-mosquitto:latest) |

---

## Code Patterns & Standards

### Type Hints

**REQUIRED:** All function signatures must include complete type hints.

```python
# ✅ CORRECT - Python 3.9 compatible
from typing import Optional

def get_train(self, train_id: str) -> Optional[Train]:
    """Retrieve train by ID."""
    pass

# ✅ CORRECT - Dict/List generic types
def get_full_config(self) -> dict[str, Any]:
    """Return complete configuration."""
    pass

def list_trains(self) -> list[Train]:
    """Return all trains."""
    pass

# ❌ INCORRECT - missing return type
def get_train(self, train_id: str):
    pass

# ❌ INCORRECT - missing parameter type
def get_train(self, train_id) -> Optional[Train]:
    pass

# ❌ INCORRECT - Python 3.10+ syntax (we target 3.9)
def get_train(self, train_id: str) -> Train | None:
    pass
```

**Modern Generic Syntax:** Use `dict[str, Any]` and `list[Train]` (not `Dict`, `List` from typing).

```python
# ✅ CORRECT - lowercase generic types (Python 3.9+)
from typing import Any, Optional

result: dict[str, Any] = {}
trains: list[Train] = []
maybe_train: Optional[Train] = None

# ❌ INCORRECT - old-style typing (pre-3.9)
from typing import Dict, List, Optional

result: Dict[str, Any] = {}
trains: List[Train] = []
```

---

### FastAPI Patterns

#### Endpoint Definition

```python
# ✅ CORRECT - Complete type hints, response model, error handling
from fastapi import APIRouter, HTTPException
from ..models.schemas import Train

router = APIRouter()

@router.get("/trains/{train_id}", response_model=Train)
async def get_train_by_id(train_id: str) -> Train:
    """Retrieve train configuration by ID.

    Args:
        train_id: Unique train identifier (UUID format expected)

    Returns:
        Train configuration object

    Raises:
        HTTPException: 404 if train not found
        HTTPException: 500 if database error

    Example:
        ```bash
        curl http://localhost:8000/api/trains/123e4567-e89b-12d3-a456-426614174000
        ```

        Response:
        ```json
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "name": "Express Train 1",
          "plugins": []
        }
        ```
    """
    train = config_manager.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return train

# ❌ INCORRECT - Missing response_model, no error handling
@router.get("/trains/{train_id}")
async def get_train_by_id(train_id: str):
    return config_manager.get_train(train_id)
```

#### Dependency Injection

```python
# ✅ CORRECT - Use FastAPI dependency injection
from fastapi import Depends

def get_config_manager() -> ConfigManager:
    """Dependency: Get global config manager instance."""
    return config_manager

@router.get("/trains/{train_id}", response_model=Train)
async def get_train_by_id(
    train_id: str,
    manager: ConfigManager = Depends(get_config_manager)
) -> Train:
    """Get train using injected ConfigManager."""
    train = manager.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404)
    return train

# ❌ INCORRECT - Global variable access (hard to test)
@router.get("/trains/{train_id}")
async def get_train_by_id(train_id: str):
    return config_manager.get_train(train_id)  # Global variable
```

---

### Pydantic Models

#### Schema Definition

```python
# ✅ CORRECT - Field validation, descriptions, examples
from pydantic import BaseModel, Field
from typing import Any, Optional

class Train(BaseModel):
    """Train configuration model.

    Represents a physical model train with associated plugins
    and control parameters.

    Example:
        ```json
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "name": "Express Train 1",
          "plugins": [
            {"plugin_id": "motor_control", "config": {"max_speed": 100}}
          ]
        }
        ```
    """

    id: str = Field(
        ...,
        description="Unique train identifier (UUID format)",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"}
    )
    name: str = Field(
        ...,
        description="Human-readable train name",
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "Express Train 1"}
    )
    plugins: list[TrainPlugin] = Field(
        default_factory=list,
        description="Installed plugins for this train"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Express Train 1",
                "plugins": []
            }
        }

# ❌ INCORRECT - No descriptions, no validation
class Train(BaseModel):
    id: str
    name: str
    plugins: list
```

#### Nested Models

```python
# ✅ CORRECT - Proper nesting with validation
class TrainPlugin(BaseModel):
    """Plugin configuration for a specific train."""

    plugin_id: str = Field(..., description="Reference to plugin definition")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin-specific configuration"
    )

class Train(BaseModel):
    """Train with plugins."""

    id: str
    name: str
    plugins: list[TrainPlugin] = Field(default_factory=list)

# Example validation
train_data = {
    "id": "train-001",
    "name": "Test Train",
    "plugins": [
        {"plugin_id": "motor_control", "config": {"max_speed": 100}}
    ]
}
train = Train(**train_data)  # Pydantic validates nested structure
```

---

### Error Handling

**Pattern:** Fail fast on critical errors, return proper HTTP status codes.

```python
# ✅ CORRECT - Specific exceptions with HTTP status codes
from fastapi import HTTPException
import sqlite3

def update_edge_controller(self, controller_id: str, updates: dict) -> EdgeController:
    """Update edge controller configuration.

    Args:
        controller_id: UUID of controller to update
        updates: Dictionary of fields to update

    Returns:
        Updated EdgeController object

    Raises:
        HTTPException: 404 if controller not found
        HTTPException: 422 if validation fails
        HTTPException: 500 if database error
    """
    try:
        # Validate UUID format
        if not UUID_PATTERN.match(controller_id):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid UUID format: {controller_id}"
            )

        # Check if exists
        controller = self.repository.get_edge_controller(controller_id)
        if not controller:
            raise HTTPException(
                status_code=404,
                detail=f"Controller {controller_id} not found"
            )

        # Update database
        updated = self.repository.update_edge_controller(controller_id, updates)
        return updated

    except sqlite3.DatabaseError as exc:
        logger.error(f"Database error updating controller: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        ) from exc

# ❌ INCORRECT - Silent failure, no error propagation
def update_edge_controller(self, controller_id: str, updates: dict) -> Optional[EdgeController]:
    try:
        return self.repository.update_edge_controller(controller_id, updates)
    except:
        return None  # Client has no idea what went wrong
```

**Custom Exceptions:**

```python
# Define specific exception classes for different failure modes
class ConfigurationError(Exception):
    """Raised when configuration cannot be initialized.

    This is a terminal error - the application cannot start without
    valid configuration.
    """
    pass

class ConfigLoadError(Exception):
    """Raised when YAML config file cannot be loaded or parsed."""
    pass

# Usage
try:
    config_data = self.loader.load_config()
except ConfigLoadError as exc:
    msg = f"Failed to load configuration: {exc}"
    raise ConfigurationError(msg) from exc
```

---

### SQLite Transaction Handling

```python
# ✅ CORRECT - Context manager handles commit/rollback
def add_edge_controller(self, controller: EdgeController) -> EdgeController:
    """Add new edge controller to database."""
    conn = sqlite3.connect(str(self.db_path))
    try:
        with conn:  # Auto-commit on success, rollback on exception
            conn.execute(
                "INSERT INTO edge_controllers (id, name, location, config_json) VALUES (?, ?, ?, ?)",
                (controller.id, controller.name, controller.location, json.dumps(controller.config))
            )
        return controller
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Controller {controller.id} already exists") from exc
    finally:
        conn.close()

# ❌ INCORRECT - Manual commit (error-prone, no rollback)
def add_edge_controller(self, controller: EdgeController):
    conn = sqlite3.connect(str(self.db_path))
    cursor = conn.execute("INSERT INTO edge_controllers ...")
    conn.commit()  # What if this fails? No cleanup
    conn.close()
```

**Query Pattern with Row Factory:**

```python
# ✅ CORRECT - Row factory for dict-like results
def get_edge_controller(self, controller_id: str) -> Optional[dict[str, Any]]:
    """Retrieve edge controller by ID."""
    conn = sqlite3.connect(str(self.db_path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        cursor = conn.execute(
            "SELECT * FROM edge_controllers WHERE id = ?",
            (controller_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
```

---

### MQTT Message Handling

```python
# ✅ CORRECT - JSON encoding/decoding, error handling
import json
import paho.mqtt.client as mqtt

def publish_command(self, train_id: str, command: dict) -> None:
    """Publish command to MQTT topic.

    Args:
        train_id: UUID of train
        command: Command payload (will be JSON-encoded)

    Raises:
        PublishError: If MQTT publish fails

    Example:
        ```python
        mqtt_adapter.publish_command("train-001", {
            "action": "setSpeed",
            "speed": 75
        })
        # Publishes to: trains/train-001/commands
        ```
    """
    topic = f"trains/{train_id}/commands"
    payload = json.dumps(command)  # MUST encode to JSON string

    result = self.client.publish(topic, payload, qos=1)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        error_msg = mqtt.error_string(result.rc)
        logger.error(f"Failed to publish to {topic}: {error_msg}")
        raise PublishError(f"MQTT publish failed: {error_msg}")

# ❌ INCORRECT - Passing dict directly (will fail)
def publish_command(self, train_id: str, command: dict):
    topic = f"trains/{train_id}/commands"
    self.client.publish(topic, command)  # TypeError: dict not serializable

# ❌ INCORRECT - No error handling
def publish_command(self, train_id: str, command: dict):
    topic = f"trains/{train_id}/commands"
    self.client.publish(topic, json.dumps(command))
    # What if publish fails? No error propagation
```

**Message Subscription:**

```python
# ✅ CORRECT - Proper callback handling, JSON parsing
def on_message(client, userdata, message):
    """Handle incoming MQTT messages."""
    try:
        # Parse JSON payload
        payload = json.loads(message.payload.decode('utf-8'))

        # Extract train_id from topic: trains/{train_id}/status
        topic_parts = message.topic.split('/')
        train_id = topic_parts[1]

        # Update database
        status = TrainStatus(**payload)
        config_manager.update_train_status(train_id, status)

    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON in MQTT message: {exc}")
    except Exception as exc:
        logger.error(f"Error processing MQTT message: {exc}")

def subscribe_status(self, train_id: str) -> None:
    """Subscribe to train status updates."""
    topic = f"trains/{train_id}/status"
    self.client.subscribe(topic, qos=1)
    self.client.on_message = on_message
```

---

## Component Specifications

### ConfigManager (`app/services/config_manager.py`)

**Purpose:** Facade pattern orchestrating config loading and database sync

**Initialization Pattern:**

```python
class ConfigManager:
    """Orchestrates configuration management across YAML files and database."""

    def __init__(
        self,
        yaml_path: Union[str, Path, None] = None,
        db_path: Union[str, Path, None] = None,
        schema_path: Union[str, Path, None] = None,
    ) -> None:
        """Initialize configuration manager.

        Args:
            yaml_path: Path to config.yaml (defaults to ./config.yaml)
            db_path: Path to SQLite database (defaults to ./central_api_config.db)
            schema_path: Path to SQL schema file (defaults to ./config_schema.sql)

        Raises:
            ConfigurationError: If paths are invalid or initialization fails
        """
        self.yaml_path = Path(yaml_path) if yaml_path else Path("config.yaml")
        self.db_path = Path(db_path) if db_path else Path("central_api_config.db")

        default_schema = Path(__file__).parent / "config_schema.sql"
        self.schema_path = Path(schema_path) if schema_path else default_schema

        try:
            self.loader = ConfigLoader(self.yaml_path)
            self.repository = ConfigRepository(self.db_path, self.schema_path)
        except (ConfigLoadError, OSError) as initialization_error:
            msg = f"Failed to initialize ConfigManager: {initialization_error}"
            raise ConfigurationError(msg) from initialization_error

        self._initialize_configuration()
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `yaml_path`, `db_path`, `schema_path` | None | Initialize manager, bootstrap config |
| `get_full_config` | None | `FullConfig` | Return complete system configuration |
| `get_train` | `train_id: str` | `Optional[Train]` | Retrieve single train config |
| `list_trains` | None | `list[Train]` | Return all trains |
| `get_edge_controller` | `controller_id: str` | `Optional[EdgeController]` | Get controller by ID |
| `add_edge_controller` | `controller: EdgeController` | `EdgeController` | Register new controller |
| `update_edge_controller` | `controller_id: str`, `updates: dict` | `EdgeController` | Update controller config |
| `get_train_status` | `train_id: str` | `Optional[TrainStatus]` | Get latest train status |
| `update_train_status` | `train_id: str`, `status: TrainStatus` | None | Store new train status |
| `get_plugin` | `plugin_id: str` | `Optional[Plugin]` | Get plugin definition |
| `list_plugins` | None | `list[Plugin]` | Return all available plugins |

**UUID Validation Pattern:**

```python
import re

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)

def _validate_uuid(self, uuid_str: str, field_name: str) -> None:
    """Validate UUID format.

    Args:
        uuid_str: String to validate
        field_name: Field name for error messages

    Raises:
        ValueError: If UUID format is invalid
    """
    if not UUID_PATTERN.match(uuid_str):
        raise ValueError(f"Invalid UUID format for {field_name}: {uuid_str}")
```

**Error Handling:**

```python
# Initialization errors
raise ConfigurationError("Failed to initialize ConfigManager: {reason}")

# UUID validation errors
raise ValueError(f"Invalid UUID format: {controller_id}")

# Not found (return None, let router handle 404)
def get_train(self, train_id: str) -> Optional[Train]:
    """Get train by ID, return None if not found."""
    return self.repository.get_train(train_id)
```

**Usage Example:**

```python
# Startup
manager = ConfigManager(
    yaml_path=Path("config.yaml"),
    db_path=Path("central_api_config.db")
)

# Query
train = manager.get_train("123e4567-e89b-12d3-a456-426614174000")
if train:
    print(f"Found train: {train.name}")

# Update
manager.update_edge_controller("controller-001", {"location": "Section B"})
```

---

### ConfigLoader (`app/services/config_loader.py`)

**Purpose:** Load and validate YAML configuration files

**Validation Constants:**

```python
# Required top-level keys in config.yaml
REQUIRED_TOP_LEVEL_KEYS = ["plugins", "trains", "edge_controllers"]

# Required fields for each plugin
REQUIRED_PLUGIN_FIELDS = ["id", "name", "version", "config_schema"]
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `yaml_path: Path` | None | Initialize loader with file path |
| `load_config` | None | `dict[str, Any]` | Parse YAML and validate structure |
| `validate_config_structure` | `config_data: dict` | None | Verify required keys present |

**Validation Flow:**

```python
def load_config(self) -> dict[str, Any]:
    """Load and validate YAML configuration.

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigLoadError: If file not found, invalid YAML, or validation fails

    Example:
        ```python
        loader = ConfigLoader(Path("config.yaml"))
        config = loader.load_config()
        # config = {
        #     "plugins": [...],
        #     "trains": [...],
        #     "edge_controllers": [...]
        # }
        ```
    """
    if not self.yaml_path.exists():
        raise ConfigLoadError(f"Config file not found: {self.yaml_path}")

    try:
        with self.yaml_path.open("r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML syntax: {exc}") from exc

    self.validate_config_structure(config_data)
    return config_data

def validate_config_structure(self, config_data: dict) -> None:
    """Validate configuration structure.

    Args:
        config_data: Parsed YAML data

    Raises:
        ConfigLoadError: If required keys missing or structure invalid
    """
    # Check top-level keys
    missing_keys = set(REQUIRED_TOP_LEVEL_KEYS) - set(config_data.keys())
    if missing_keys:
        raise ConfigLoadError(f"Missing required keys: {missing_keys}")

    # Validate each plugin
    for plugin in config_data.get("plugins", []):
        missing_fields = set(REQUIRED_PLUGIN_FIELDS) - set(plugin.keys())
        if missing_fields:
            raise ConfigLoadError(
                f"Plugin {plugin.get('id', 'unknown')} missing fields: {missing_fields}"
            )
```

**Error Handling:**

```python
# File not found
raise ConfigLoadError(f"Config file not found: {yaml_path}")

# Invalid YAML syntax
raise ConfigLoadError(f"Invalid YAML syntax: {exc}")

# Missing required keys
raise ConfigLoadError(f"Missing required keys: {missing_keys}")

# Structural errors
raise ConfigLoadError(f"Invalid plugin structure: {details}")
```

---

### ConfigRepository (`app/services/config_repository.py`)

**Purpose:** Repository pattern for SQLite database operations

**Database Schema:**

```sql
-- Edge controllers (Raspberry Pi devices)
CREATE TABLE IF NOT EXISTS edge_controllers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    config_json TEXT
);

-- Model trains
CREATE TABLE IF NOT EXISTS trains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config_json TEXT
);

-- Available plugins (motor control, lighting, etc.)
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    config_schema_json TEXT
);

-- Runtime train status (speed, voltage, position)
CREATE TABLE IF NOT EXISTS train_status (
    train_id TEXT PRIMARY KEY,
    speed INTEGER,
    voltage REAL,
    current REAL,
    position TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_id) REFERENCES trains(id)
);
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `db_path: Path`, `schema_path: Path` | None | Initialize DB connection, run schema |
| `get_edge_controller` | `controller_id: str` | `Optional[dict]` | Retrieve controller by ID |
| `get_all_edge_controllers` | None | `list[dict]` | Return all controllers |
| `add_edge_controller` | `controller_id`, `name`, `address` | None | Insert new controller |
| `update_edge_controller` | `controller_id: str`, `updates: dict` | `dict` | Update existing controller |
| `get_train` | `train_id: str` | `Optional[dict]` | Retrieve train by ID |
| `list_trains` | None | `list[dict]` | Return all trains |
| `add_train` | `train_id`, `name`, `config_json` | None | Insert new train |
| `update_train_status` | `train_id`, `status: TrainStatus` | None | Store latest status |
| `get_train_status` | `train_id: str` | `Optional[dict]` | Retrieve latest status |
| `get_plugin` | `plugin_id: str` | `Optional[dict]` | Get plugin by ID |
| `list_plugins` | None | `list[dict]` | Return all plugins |
| `add_plugin` | `plugin_id`, `name`, `version`, `schema` | None | Insert new plugin |

**Transaction Pattern:**

```python
def add_edge_controller(
    self, controller_id: str, name: str, address: str
) -> None:
    """Add new edge controller to database.

    Args:
        controller_id: Unique UUID for controller
        name: Human-readable name
        address: Network address (IP or hostname)

    Raises:
        sqlite3.IntegrityError: If controller_id already exists

    Example:
        ```python
        repository.add_edge_controller(
            "123e4567-e89b-12d3-a456-426614174000",
            "Pi Controller 1",
            "192.168.1.100"
        )
        ```
    """
    conn = sqlite3.connect(str(self.db_path))
    try:
        with conn:
            conn.execute(
                "INSERT INTO edge_controllers (id, name, location) VALUES (?, ?, ?)",
                (controller_id, name, address)
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Controller {controller_id} already exists") from exc
    finally:
        conn.close()
```

**Query Pattern with JSON Storage:**

```python
def add_train(self, train_id: str, name: str, config: dict) -> None:
    """Add new train to database.

    Args:
        train_id: Unique UUID
        name: Train name
        config: Configuration dict (stored as JSON)
    """
    conn = sqlite3.connect(str(self.db_path))
    try:
        with conn:
            conn.execute(
                "INSERT INTO trains (id, name, config_json) VALUES (?, ?, ?)",
                (train_id, name, json.dumps(config))
            )
    finally:
        conn.close()

def get_train(self, train_id: str) -> Optional[dict[str, Any]]:
    """Retrieve train by ID, parse JSON config."""
    conn = sqlite3.connect(str(self.db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM trains WHERE id = ?", (train_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON config
            if result.get("config_json"):
                result["config"] = json.loads(result["config_json"])
            return result
        return None
    finally:
        conn.close()
```

---

### MQTTAdapter (`app/services/mqtt_adapter.py`)

**Purpose:** MQTT client wrapper for pub/sub operations

**Topic Structure:**

```
trains/{train_id}/commands     → Publish commands to edge controller
trains/{train_id}/status       → Subscribe to status updates from edge controller
trains/{train_id}/telemetry    → Subscribe to telemetry data (future)
```

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `broker_host: str`, `broker_port: int` | None | Initialize MQTT client |
| `connect` | None | None | Connect to broker |
| `disconnect` | None | None | Disconnect from broker |
| `publish_command` | `train_id: str`, `command: dict` | None | Publish to trains/{id}/commands |
| `subscribe_status` | `train_id: str`, `callback: Callable` | None | Subscribe to trains/{id}/status |
| `get_train_status` | `train_id: str` | `Optional[TrainStatus]` | Retrieve cached status |

**Message Formats:**

```python
# Command message (Central API → Edge Controller)
{
  "action": "setSpeed",  # or "start", "stop"
  "speed": 50,           # 0-100 (optional, required for setSpeed)
  "timestamp": "2025-11-21T10:15:30Z"
}

# Status message (Edge Controller → Central API)
{
  "train_id": "123e4567-e89b-12d3-a456-426614174000",
  "speed": 50,
  "voltage": 12.3,
  "current": 0.8,
  "position": "section_A",
  "timestamp": "2025-11-21T10:15:31Z"
}
```

**Implementation Pattern:**

```python
import paho.mqtt.client as mqtt
import json

class MQTTAdapter:
    """MQTT client wrapper for train control system."""

    def __init__(self, broker_host: str, broker_port: int):
        """Initialize MQTT client.

        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port (typically 1883)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()  # Start background thread
        except ConnectionError as exc:
            logger.error(f"Failed to connect to MQTT broker: {exc}")
            raise

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_command(self, train_id: str, command: dict) -> None:
        """Publish command to train.

        Args:
            train_id: UUID of train
            command: Command payload

        Raises:
            PublishError: If MQTT publish fails
        """
        topic = f"trains/{train_id}/commands"
        payload = json.dumps(command)

        result = self.client.publish(topic, payload, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            error_msg = mqtt.error_string(result.rc)
            raise PublishError(f"MQTT publish failed: {error_msg}")

    def subscribe_status(self, train_id: str) -> None:
        """Subscribe to train status updates.

        Args:
            train_id: UUID of train (or '+' for all trains)
        """
        topic = f"trains/{train_id}/status"
        self.client.subscribe(topic, qos=1)

    def _on_message(self, client, userdata, message):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(message.payload.decode('utf-8'))

            # Extract train_id from topic: trains/{train_id}/status
            topic_parts = message.topic.split('/')
            train_id = topic_parts[1]

            # Update database with status
            status = TrainStatus(**payload)
            config_manager.update_train_status(train_id, status)

        except (json.JSONDecodeError, IndexError) as exc:
            logger.error(f"Error processing MQTT message: {exc}")
```

**Error Handling:**

```python
# Connection errors
try:
    client.connect(broker_host, broker_port)
except ConnectionError as exc:
    logger.error(f"Failed to connect to MQTT broker: {exc}")
    raise

# Publish errors (retry logic)
def publish_command(self, train_id: str, command: dict) -> None:
    result = self.client.publish(topic, payload, qos=1)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        raise PublishError(f"MQTT publish failed: {mqtt.error_string(result.rc)}")
```

---

## API Endpoint Reference

### Configuration Endpoints

#### GET /api/config

```python
@router.get("/config", response_model=FullConfig)
async def get_full_config() -> FullConfig:
    """Return complete system configuration.

    Returns:
        Complete configuration including plugins, trains, edge controllers

    Example:
        ```bash
        curl http://localhost:8000/api/config
        ```
    """
    return config_manager.get_full_config()
```

#### GET /api/config/edge-controllers/{controller_id}

```python
@router.get("/config/edge-controllers/{controller_id}", response_model=EdgeController)
async def get_edge_controller(controller_id: str) -> EdgeController:
    """Retrieve edge controller configuration.

    Args:
        controller_id: UUID of edge controller

    Returns:
        EdgeController configuration

    Raises:
        HTTPException: 404 if controller not found

    Example:
        ```bash
        curl http://localhost:8000/api/config/edge-controllers/controller-001
        ```
    """
    controller = config_manager.get_edge_controller(controller_id)
    if not controller:
        raise HTTPException(status_code=404, detail=f"Controller {controller_id} not found")
    return controller
```

#### PUT /api/config/edge-controllers/{controller_id}

```python
@router.put("/config/edge-controllers/{controller_id}", response_model=EdgeController)
async def update_edge_controller(controller_id: str, updates: dict) -> EdgeController:
    """Update edge controller configuration.

    Args:
        controller_id: UUID of controller
        updates: Dictionary of fields to update

    Returns:
        Updated EdgeController object

    Raises:
        HTTPException: 404 if controller not found
        HTTPException: 422 if validation fails

    Example:
        ```bash
        curl -X PUT http://localhost:8000/api/config/edge-controllers/controller-001 \
          -H "Content-Type: application/json" \
          -d '{"location": "Section B"}'
        ```
    """
    try:
        return config_manager.update_edge_controller(controller_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
```

---

### Train Endpoints

#### GET /api/trains

```python
@router.get("/trains", response_model=list[Train])
async def list_trains() -> list[Train]:
    """Return all trains.

    Returns:
        List of all train configurations

    Example:
        ```bash
        curl http://localhost:8000/api/trains
        ```

        Response:
        ```json
        [
          {
            "id": "train-001",
            "name": "Express Train 1",
            "plugins": []
          },
          {
            "id": "train-002",
            "name": "Freight Train 1",
            "plugins": [{"plugin_id": "motor_control", "config": {}}]
          }
        ]
        ```
    """
    return config_manager.list_trains()
```

#### GET /api/trains/{train_id}

```python
@router.get("/trains/{train_id}", response_model=Train)
async def get_train_by_id(train_id: str) -> Train:
    """Retrieve train by ID.

    Args:
        train_id: UUID of train

    Returns:
        Train configuration

    Raises:
        HTTPException: 404 if train not found

    Example:
        ```bash
        curl http://localhost:8000/api/trains/train-001
        ```
    """
    train = config_manager.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return train
```

#### POST /api/trains/{train_id}/command

```python
@router.post("/trains/{train_id}/command")
async def send_command(train_id: str, command: dict) -> dict[str, str]:
    """Send command to train via MQTT.

    Args:
        train_id: UUID of the train
        command: Command payload

    Returns:
        Status confirmation

    Raises:
        HTTPException: 404 if train not found
        HTTPException: 500 if MQTT publish fails

    Example:
        ```bash
        # Set speed to 75
        curl -X POST http://localhost:8000/api/trains/train-001/command \
          -H "Content-Type: application/json" \
          -d '{"action": "setSpeed", "speed": 75}'

        # Stop train
        curl -X POST http://localhost:8000/api/trains/train-001/command \
          -H "Content-Type: application/json" \
          -d '{"action": "stop"}'
        ```

        Response:
        ```json
        {"status": "published"}
        ```
    """
    train = config_manager.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")

    try:
        mqtt_adapter.publish_command(train_id, command)
        return {"status": "published"}
    except PublishError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
```

#### GET /api/trains/{train_id}/status

```python
@router.get("/trains/{train_id}/status", response_model=TrainStatus)
async def get_train_status(train_id: str) -> TrainStatus:
    """Retrieve latest train status.

    Args:
        train_id: UUID of train

    Returns:
        Current train status (speed, voltage, current, position)

    Raises:
        HTTPException: 404 if no status available

    Example:
        ```bash
        curl http://localhost:8000/api/trains/train-001/status
        ```

        Response:
        ```json
        {
          "train_id": "train-001",
          "speed": 75,
          "voltage": 12.3,
          "current": 0.85,
          "position": "section_A",
          "timestamp": "2025-11-21T10:15:32Z"
        }
        ```
    """
    status = config_manager.get_train_status(train_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"No status for train {train_id}")
    return status
```

---

## Testing Patterns

### Unit Test Structure

```python
# tests/unit/test_config_manager.py
import pytest
from app.services.config_manager import ConfigManager
from app.models.schemas import Train

@pytest.mark.unit
def test_get_train_by_id_success(config_manager, sample_train):
    """Test successful train retrieval."""
    # Arrange - sample_train is a pytest fixture

    # Act
    train = config_manager.get_train(sample_train.id)

    # Assert
    assert train is not None
    assert train.id == sample_train.id
    assert train.name == sample_train.name

@pytest.mark.unit
def test_get_train_by_id_not_found(config_manager):
    """Test train retrieval with invalid ID."""
    # Act
    train = config_manager.get_train("nonexistent-uuid")

    # Assert
    assert train is None

@pytest.mark.unit
def test_add_edge_controller_duplicate_raises_error(config_manager, sample_controller):
    """Test adding duplicate controller raises ValueError."""
    # Arrange
    config_manager.add_edge_controller(sample_controller)

    # Act & Assert
    with pytest.raises(ValueError, match="already exists"):
        config_manager.add_edge_controller(sample_controller)
```

**Fixtures Pattern:**

```python
# tests/conftest.py
import pytest
from pathlib import Path
from app.services.config_manager import ConfigManager
from app.models.schemas import Train, EdgeController

@pytest.fixture
def tmp_db_path(tmp_path):
    """Provide temporary database path."""
    return tmp_path / "test.db"

@pytest.fixture
def config_manager(tmp_db_path, tmp_path):
    """Provide ConfigManager instance with test database."""
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("""
    plugins: []
    trains: []
    edge_controllers: []
    """)

    return ConfigManager(yaml_path=yaml_path, db_path=tmp_db_path)

@pytest.fixture
def sample_train():
    """Provide sample train for testing."""
    return Train(
        id="train-001",
        name="Test Train",
        plugins=[]
    )
```

---

### Integration Test Structure

```python
# tests/integration/test_config_integration.py
import pytest
from pathlib import Path
from app.services.config_manager import ConfigManager

@pytest.mark.integration
def test_yaml_to_database_sync(tmp_path):
    """Test full YAML → Database synchronization."""
    # Arrange
    yaml_path = tmp_path / "config.yaml"
    db_path = tmp_path / "test.db"

    yaml_content = """
plugins:
  - id: motor_control
    name: Motor Control
    version: 1.0.0
    config_schema: {}

trains:
  - id: train-001
    name: Express Train 1
    plugins: []

edge_controllers:
  - id: controller-001
    name: Pi Controller 1
    location: Section A
    trains: [train-001]
"""
    yaml_path.write_text(yaml_content)

    # Act
    manager = ConfigManager(yaml_path=yaml_path, db_path=db_path)

    # Assert - Verify data in database
    trains = manager.list_trains()
    assert len(trains) == 1
    assert trains[0].id == "train-001"
    assert trains[0].name == "Express Train 1"

    controllers = manager.list_edge_controllers()
    assert len(controllers) == 1
    assert controllers[0].id == "controller-001"
```

---

### End-to-End Test Structure

```python
# tests/e2e/test_end_to_end.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_client():
    """Provide FastAPI test client."""
    return TestClient(app)

@pytest.mark.e2e
async def test_full_train_command_flow(test_client, mqtt_broker_running):
    """Test complete train command flow: API → MQTT → Status Update.

    This test requires a running MQTT broker and mock edge controller.
    """
    # Arrange
    train_id = "train-001"

    # Act 1: Send command via API
    response = test_client.post(
        f"/api/trains/{train_id}/command",
        json={"action": "setSpeed", "speed": 75}
    )

    # Assert 1: Command accepted
    assert response.status_code == 200
    assert response.json()["status"] == "published"

    # Act 2: Wait for MQTT propagation (mock edge controller publishes status)
    await asyncio.sleep(1)

    # Act 3: Check status was updated
    status_response = test_client.get(f"/api/trains/{train_id}/status")

    # Assert 2: Status reflects command
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["speed"] == 75
    assert status["train_id"] == train_id
```

---

## Common Modification Patterns

### Adding a New API Endpoint

**Steps:**

1. Define Pydantic request/response models in `app/models/schemas.py`
2. Add endpoint function in appropriate router (`app/routers/`)
3. Add business logic to `ConfigManager` if needed
4. Add repository method if database access required
5. Write unit tests for new logic
6. Write integration test for endpoint
7. Update this AI_SPECS.md with endpoint specification
8. Update OpenAPI schema documentation

**Example: Add emergency stop endpoint**

```python
# 1. Add model (if needed - in this case, using existing models)

# 2. Add endpoint in app/routers/trains.py
@router.post("/trains/{train_id}/emergency-stop", response_model=dict)
async def emergency_stop(train_id: str) -> dict:
    """Emergency stop for train.

    Args:
        train_id: UUID of train

    Returns:
        Status confirmation

    Raises:
        HTTPException: 404 if train not found
        HTTPException: 500 if MQTT publish fails

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/trains/train-001/emergency-stop
        ```
    """
    train = config_manager.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404)

    command = {"action": "stop", "emergency": True}
    try:
        mqtt_adapter.publish_command(train_id, command)
        return {"status": "emergency_stop_sent"}
    except PublishError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# 3. Write unit test
@pytest.mark.unit
def test_emergency_stop_publishes_mqtt_message(mqtt_adapter_mock):
    """Test emergency stop sends MQTT command."""
    # Test implementation
    mqtt_adapter_mock.publish_command = Mock()

    # Call endpoint
    response = test_client.post("/api/trains/train-001/emergency-stop")

    # Verify MQTT publish called
    mqtt_adapter_mock.publish_command.assert_called_once_with(
        "train-001",
        {"action": "stop", "emergency": True}
    )
```

---

### Adding a New Configuration Field

**Steps:**

1. Update YAML schema documentation
2. Add field to Pydantic model (`app/models/schemas.py`)
3. Update database schema (`app/services/config_schema.sql`) if persistent
4. Add migration script if schema change breaks existing DBs
5. Update `ConfigLoader` validation if new required field
6. Update tests with new field
7. Update this AI_SPECS.md

**Example: Add max_speed to Train model**

```python
# 1. Update Pydantic model in app/models/schemas.py
class Train(BaseModel):
    """Train configuration model."""

    id: str = Field(..., description="Unique train identifier")
    name: str = Field(..., description="Train name")
    max_speed: int = Field(
        default=100,
        description="Maximum speed limit (0-100)",
        ge=0,
        le=100
    )  # NEW FIELD
    plugins: list[TrainPlugin] = Field(default_factory=list)

# 2. Update SQL schema in app/services/config_schema.sql
CREATE TABLE IF NOT EXISTS trains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    max_speed INTEGER DEFAULT 100,  -- NEW COLUMN
    config_json TEXT
);

# 3. Add migration (if needed)
# For SQLite, might need to recreate table or use ALTER TABLE
ALTER TABLE trains ADD COLUMN max_speed INTEGER DEFAULT 100;

# 4. Update tests
@pytest.mark.unit
def test_train_with_max_speed():
    """Test train creation with max_speed field."""
    train = Train(id="test", name="Test", max_speed=80)
    assert train.max_speed == 80

@pytest.mark.unit
def test_train_max_speed_validation():
    """Test max_speed must be 0-100."""
    with pytest.raises(ValidationError):
        Train(id="test", name="Test", max_speed=150)  # Over limit
```

---

## Error Code Reference

| HTTP Code | Meaning | When to Use |
|-----------|---------|-------------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST creating resource |
| 400 | Bad Request | Invalid request payload (manually validated) |
| 404 | Not Found | Resource doesn't exist (train, controller, etc.) |
| 422 | Unprocessable Entity | FastAPI/Pydantic schema validation error |
| 500 | Internal Server Error | Database error, MQTT error, unexpected exception |

**Usage Patterns:**

```python
# 404 - Resource not found
train = config_manager.get_train(train_id)
if not train:
    raise HTTPException(status_code=404, detail=f"Train {train_id} not found")

# 422 - Validation error (manual)
if not UUID_PATTERN.match(controller_id):
    raise HTTPException(status_code=422, detail=f"Invalid UUID: {controller_id}")

# 500 - Internal error
try:
    mqtt_adapter.publish_command(train_id, command)
except PublishError as exc:
    raise HTTPException(status_code=500, detail="MQTT publish failed") from exc
```

---

## Dependencies & Versions

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

---

## Gotchas & Common Mistakes

### 1. Python 3.9 Type Hints

**❌ INCORRECT:**
```python
def get_train(train_id: str) -> Train | None:  # Python 3.10+ syntax
    pass
```

**✅ CORRECT:**
```python
from typing import Optional

def get_train(train_id: str) -> Optional[Train]:  # Python 3.9 compatible
    pass
```

---

### 2. FastAPI Response Models

**❌ INCORRECT:**
```python
@router.get("/trains/{id}")
async def get_train(id: str):  # Missing response_model
    return config_manager.get_train(id)
```

**✅ CORRECT:**
```python
@router.get("/trains/{id}", response_model=Train)
async def get_train(id: str) -> Train:
    train = config_manager.get_train(id)
    if not train:
        raise HTTPException(status_code=404)
    return train
```

---

### 3. SQLite Transaction Handling

**❌ INCORRECT:**
```python
def add_train(self, train: Train):
    cursor = self.conn.execute("INSERT INTO trains ...")  # No transaction
    self.conn.commit()  # Manual commit (error-prone)
```

**✅ CORRECT:**
```python
def add_train(self, train: Train):
    with self.conn:  # Context manager handles commit/rollback
        self.conn.execute("INSERT INTO trains ...")
```

---

### 4. MQTT Message Encoding

**❌ INCORRECT:**
```python
self.client.publish(topic, command)  # Passing dict directly
```

**✅ CORRECT:**
```python
import json
payload = json.dumps(command)
self.client.publish(topic, payload)
```

---

### 5. Pydantic V2 Field Validation

**❌ INCORRECT (Pydantic V1 syntax):**
```python
from pydantic import BaseModel

class Train(BaseModel):
    id: str
    name: str

    class Config:
        schema_extra = {"example": {...}}  # V1 syntax
```

**✅ CORRECT (Pydantic V2 syntax):**
```python
from pydantic import BaseModel, Field

class Train(BaseModel):
    id: str = Field(..., description="Train ID")
    name: str = Field(..., description="Train name")

    class Config:
        json_schema_extra = {"example": {...}}  # V2 syntax
```

---

### 6. Async vs Sync in FastAPI

**❌ INCORRECT - Blocking call in async endpoint:**
```python
@router.get("/trains")
async def list_trains():
    # time.sleep blocks entire event loop!
    time.sleep(5)
    return config_manager.list_trains()
```

**✅ CORRECT - Use sync endpoints for blocking operations:**
```python
@router.get("/trains")
def list_trains():  # Sync function, FastAPI runs in thread pool
    # Blocking operations OK in sync endpoints
    return config_manager.list_trains()
```

---

## References

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Pydantic V2 Documentation:** https://docs.pydantic.dev/2.5/
- **Paho MQTT Client:** https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html
- **Project MQTT Topics:** `../../docs/mqtt-topics.md`
- **Overall System Architecture:** `../../docs/architecture.md`
- **Central API Architecture:** `./ARCHITECTURE.md`
- **Edge Controller AI Specs:** `../../edge-controllers/docs/AI_SPECS.md`
- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **MyPy Documentation:** https://mypy.readthedocs.io/
- **Pytest Documentation:** https://docs.pytest.org/
