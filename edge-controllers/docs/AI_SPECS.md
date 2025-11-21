# Edge Controller AI Agent Specifications

**Target Audience:** AI Code Agents, LLM-based Development Tools  
**Purpose:** High-density technical specifications for autonomous code generation and modification  
**Version:** 1.0  
**Last Updated:** November 21, 2025

---

## Quick Reference

| Aspect | Value |
|--------|-------|
| **Language** | Python 3.9+ |
| **Type System** | Strict type hints (MyPy validated) |
| **Code Style** | Ruff (line-length=100, Python 3.9 target) |
| **Docstring Format** | Google-style |
| **Testing Framework** | Pytest (80%+ coverage required) |
| **Security Scanner** | Bandit, Safety |
| **Primary Dependencies** | paho-mqtt, requests, gpiozero, pyyaml |
| **Deployment Target** | Raspberry Pi 3/4, Docker, Kubernetes |

---

## Code Patterns & Standards

### Type Hints

**REQUIRED:** All function signatures must include complete type hints.

```python
# ✅ CORRECT
def download_runtime_config(self, controller_uuid: str) -> dict[str, Any] | None:
    """Download runtime configuration."""
    pass

# ❌ INCORRECT - missing return type
def download_runtime_config(self, controller_uuid: str):
    pass

# ❌ INCORRECT - missing parameter type
def download_runtime_config(self, controller_uuid) -> dict[str, Any] | None:
    pass
```

**Modern Union Syntax:** Use `|` for Python 3.10+ style (configured for 3.9 compatibility).

```python
# ✅ CORRECT
result: dict[str, Any] | None = None
values: list[int] | tuple[int, ...] = []

# ❌ INCORRECT - old-style typing
from typing import Optional, Union
result: Optional[dict[str, Any]] = None
values: Union[list[int], tuple[int, ...]] = []
```

### Error Handling

**Pattern:** Fail fast on critical errors, gracefully degrade on transient failures.

```python
# ✅ CORRECT - Critical error (registration failed)
def register_controller(self) -> str:
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["uuid"]
    except RequestException as exc:
        raise APIRegistrationError(f"Registration failed: {exc}") from exc

# ✅ CORRECT - Transient error (config download failed, use cache)
def download_runtime_config(self, uuid: str) -> dict[str, Any] | None:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            logger.info(f"No config for UUID {uuid}")
            return None  # Valid state - not assigned yet
        response.raise_for_status()
        return response.json()
    except RequestException as exc:
        logger.error(f"Failed to download config: {exc}")
        return None  # Caller will use cached config

# ❌ INCORRECT - Silent failure on critical operation
def register_controller(self) -> str | None:
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()["uuid"]
    except:
        return None  # Should raise exception instead
```

**Custom Exceptions:**

```python
# Define specific exception classes for different failure modes
class ConfigurationError(Exception):
    """Raised when configuration cannot be initialized."""

class APIRegistrationError(Exception):
    """Raised when controller registration fails."""

class MQTTConnectionError(Exception):
    """Raised when MQTT connection fails."""
```

### Logging

**Levels:**

- `DEBUG`: Detailed diagnostic info (development only)
- `INFO`: Normal operations (registration, commands, status)
- `WARNING`: Recoverable issues (API unreachable, using cached config)
- `ERROR`: Failures requiring attention (hardware errors, connection failures)

```python
# ✅ CORRECT
logger.info(f"Registered controller uuid={uuid}")
logger.warning(f"API not accessible, using cached config")
logger.error(f"Failed to execute command: {exc}")
logger.debug(f"Raw MQTT payload: {payload}")

# ❌ INCORRECT - wrong level
logger.error(f"Registered controller uuid={uuid}")  # INFO, not ERROR
logger.debug(f"Failed to execute command: {exc}")   # ERROR, not DEBUG
```

**Structured Logging:**

```python
# ✅ CORRECT - includes context
logger.info(f"Subscribed to topic: {self.commands_topic}")
logger.error(f"Failed to publish to {self.status_topic}: {exc}")

# ❌ INCORRECT - lacks context
logger.info("Subscribed to topic")
logger.error(f"Failed to publish: {exc}")
```

### Docstrings

**Format:** Google-style docstrings for all public functions, classes, and modules.

```python
def initialize(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Initialize and load both service and runtime configurations.

    This is the main entry point for configuration initialization. It orchestrates
    the entire configuration workflow including registration, config download, and
    fallback logic.

    Workflow:
        1. Load service config from edge-controller.conf
        2. Check if Central API is accessible
        3. If accessible, download fresh runtime config or register
        4. If not accessible, use cached runtime config

    Returns:
        Tuple of (service_config, runtime_config).
        - service_config: Always present (from edge-controller.conf)
        - runtime_config: May be None if waiting for train assignment

    Raises:
        ConfigurationError: If Central API is not accessible and no cached config exists

    Example:
        >>> manager = ConfigManager(config_path, cached_path)
        >>> service, runtime = manager.initialize()
        >>> if runtime is None:
        ...     logger.info("Waiting for admin to assign trains")
    """
```

**Required Sections:**

1. One-line summary
2. Detailed description (workflow, architecture context)
3. `Args:` (with type and description)
4. `Returns:` (with type and description)
5. `Raises:` (exception types and conditions)
6. `Example:` (concrete code snippet)

---

## Module Architecture

### File Organization

```text
pi-template/app/
├── main.py                    # Entry point, EdgeControllerApp orchestration
├── config/
│   ├── loader.py              # File I/O for YAML configs
│   └── manager.py             # Configuration state machine
├── api/
│   └── client.py              # HTTP client for Central API
├── mqtt_client.py             # MQTT pub/sub implementation
├── hardware.py                # Generic GPIO controller
├── stepper_hat.py             # Waveshare HAT controller (singleton)
├── context.py                 # Legacy context management (deprecated)
└── controllers.py             # FastAPI endpoints (development only)
```

### Dependency Graph

```text
main.py
├── config/manager.py
│   ├── config/loader.py
│   └── api/client.py
├── mqtt_client.py
└── hardware.py / stepper_hat.py
```

**Rules:**

1. `main.py` is the only entry point (no circular imports)
2. `config/` layer has no dependencies on `mqtt_client.py` or `hardware.py`
3. `hardware.py` and `stepper_hat.py` are mutually exclusive (never import both)
4. `context.py` is legacy - prefer using `config/manager.py` for new code

---

## Component Specifications

### main.py - EdgeControllerApp

**Purpose:** Application lifecycle orchestration and command routing.

**Key Methods:**

```python
class EdgeControllerApp:
    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize application with config paths.

        Args:
            config_path: Path to edge-controller.conf (service config)
            cached_config_path: Path to edge-controller.yaml (runtime config)
        """

    def run(self) -> None:
        """Main application loop. Blocks until shutdown signal."""

    def _handle_command(self, command: dict[str, Any]) -> None:
        """Process MQTT command and route to hardware.

        Args:
            command: Parsed JSON command (action, speed fields)
        """

    def _execute_hardware_command(self, action: str, speed: int | None) -> None:
        """Execute hardware action based on command.

        Args:
            action: Command action ("start", "stop", "setSpeed")
            speed: Motor speed 0-100 (None if not specified)
        """

    def shutdown(self) -> None:
        """Graceful shutdown: stop MQTT, cleanup hardware."""
```

**Initialization Sequence:**

```python
# 1. Load configurations
service_config, runtime_config = self.config_manager.initialize()

# 2. If no runtime config, enter wait state
if runtime_config is None:
    logger.info("Waiting for administrator to assign trains")
    # Periodically check for config updates
    return

# 3. Initialize MQTT client
self.mqtt_client = MQTTClient(
    broker_host=runtime_config["mqtt_broker"]["host"],
    broker_port=runtime_config["mqtt_broker"]["port"],
    train_id=runtime_config["train_id"],
    status_topic=runtime_config["status_topic"],
    commands_topic=runtime_config["commands_topic"],
    command_handler=self._handle_command
)
self.mqtt_client.start()

# 4. Initialize hardware controller
if HARDWARE_AVAILABLE:
    self.hardware = StepperMotorHatController()
else:
    self.hardware = StepperMotorSimulator()

# 5. Enter main loop
self.run()
```

**Command Routing Logic:**

```python
def _handle_command(self, command: dict[str, Any]) -> None:
    action = command.get("action")
    speed = command.get("speed")

    if action == "start":
        self._execute_hardware_command("start", speed or 50)
    elif action == "stop":
        self._execute_hardware_command("stop", None)
    elif action == "setSpeed" and speed is not None:
        self._execute_hardware_command("setSpeed", speed)
    else:
        logger.warning(f"Unknown command: {command}")
```

---

### config/manager.py - ConfigManager

**Purpose:** Configuration state machine with registration and download logic.

**State Machine:**

```text
[INIT] -> load_service_config() -> [SERVICE_LOADED]
[SERVICE_LOADED] -> check_api_accessible() -> [API_UP | API_DOWN]

[API_UP] + [HAS_CACHED_UUID] -> download_runtime_config() -> [CONFIG_FRESH]
[API_UP] + [NO_CACHED_UUID] -> register_controller() -> download_runtime_config() -> [CONFIG_FRESH | CONFIG_MISSING]

[API_DOWN] + [HAS_CACHED_CONFIG] -> load_cached_runtime_config() -> [CONFIG_STALE]
[API_DOWN] + [NO_CACHED_CONFIG] -> FAIL (ConfigurationError)
```

**Key Methods:**

```python
class ConfigManager:
    def initialize(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Main entry point - orchestrates config loading."""

    def _use_cached_config_fallback(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Fallback when API is unavailable."""

    def _refresh_existing_controller(self, cached_config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Download fresh config for existing UUID."""

    def _register_new_controller(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Register new controller and download config."""

    def _is_runtime_config_complete(self, config: dict[str, Any]) -> bool:
        """Validate config has required fields (train_id, mqtt_broker)."""
```

**Required Config Fields:**

```python
# Service Config (edge-controller.conf)
{
    "central_api_host": str,  # Required
    "central_api_port": int,  # Required
    "logging_level": str      # Optional, default "INFO"
}

# Runtime Config (edge-controller.yaml)
{
    "uuid": str,              # Required (assigned by API)
    "train_id": str,          # Required for operation
    "mqtt_broker": {          # Required for operation
        "host": str,
        "port": int,
        "username": str | None,
        "password": str | None
    },
    "status_topic": str,      # Required
    "commands_topic": str     # Required
}
```

---

### config/loader.py - ConfigLoader

**Purpose:** Pure file I/O for YAML configuration files.

**Design:** Stateless utility class with no side effects beyond disk I/O.

```python
class ConfigLoader:
    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize loader with file paths."""

    def load_service_config(self) -> dict[str, Any]:
        """Load service config from edge-controller.conf.

        Raises:
            ConfigLoadError: If file missing or invalid YAML
        """

    def load_cached_runtime_config(self) -> dict[str, Any] | None:
        """Load cached runtime config from edge-controller.yaml.

        Returns:
            Parsed config dict or None if file doesn't exist
        """

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        """Save runtime config to edge-controller.yaml.

        Side Effects:
            Creates parent directories if they don't exist
        """
```

**Error Handling:**

```python
# ✅ CORRECT - Raise on service config error (critical)
def load_service_config(self) -> dict[str, Any]:
    if not self.config_path.exists():
        raise ConfigLoadError(f"Service config not found: {self.config_path}")

    try:
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML: {exc}") from exc

# ✅ CORRECT - Return None on cached config error (non-critical)
def load_cached_runtime_config(self) -> dict[str, Any] | None:
    if not self.cached_config_path.exists():
        return None

    try:
        with open(self.cached_config_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        logger.error(f"Invalid cached config: {exc}")
        return None
```

---

### api/client.py - CentralAPIClient

**Purpose:** HTTP client for Central API communication.

**Retry Strategy:**

```python
class CentralAPIClient:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 5,
        retry_delay: int = 2,
        max_retries: int = 5
    ) -> None:
        """Initialize API client with retry configuration."""
```

**Endpoints:**

| Method | Endpoint | Purpose | Retries | Raises |
|--------|----------|---------|---------|--------|
| `check_accessibility()` | `GET /api/ping` | Health check | Yes (5x) | Never (returns bool) |
| `register_controller()` | `POST /api/controllers/register` | Register and get UUID | No | `APIRegistrationError` |
| `download_runtime_config()` | `GET /api/controllers/{uuid}/config` | Download config | No | Never (returns None on error) |

**HTTP Request Pattern:**

```python
# ✅ CORRECT - Check accessibility with retries
def check_accessibility(self) -> bool:
    for attempt in range(self.max_retries):
        try:
            url = f"{self.base_url}/api/ping"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return True
        except (RequestException, Timeout) as exc:
            logger.warning(f"API not accessible (attempt {attempt + 1}/{self.max_retries}): {exc}")

        if attempt < self.max_retries - 1:
            time.sleep(self.retry_delay)

    return False

# ✅ CORRECT - Registration raises on failure
def register_controller(self) -> str:
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        url = f"{self.base_url}/api/controllers/register"
        payload = {"name": hostname, "address": ip_address}
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        uuid = response.json().get("uuid")
        if not uuid:
            raise APIRegistrationError("API response missing UUID")

        return uuid
    except RequestException as exc:
        raise APIRegistrationError(f"Registration failed: {exc}") from exc

# ✅ CORRECT - Config download returns None on 404
def download_runtime_config(self, controller_uuid: str) -> dict[str, Any] | None:
    try:
        url = f"{self.base_url}/api/controllers/{controller_uuid}/config"
        response = requests.get(url, timeout=self.timeout)

        if response.status_code == 404:
            logger.info(f"No runtime config for UUID {controller_uuid}")
            return None

        response.raise_for_status()
        config = response.json()
        config["uuid"] = controller_uuid  # Preserve UUID
        return config
    except RequestException as exc:
        logger.error(f"Failed to download config: {exc}")
        return None
```

---

### mqtt_client.py - MQTTClient

**Purpose:** MQTT publish/subscribe for real-time command and status communication.

**Initialization:**

```python
class MQTTClient:
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        train_id: str,
        status_topic: str,
        commands_topic: str,
        command_handler: Callable[[dict[str, Any]], None],
        username: str | None = None,
        password: str | None = None,
        central_api_url: str | None = None
    ) -> None:
        """Initialize MQTT client.

        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port (1883 for plain, 8883 for TLS)
            train_id: Train identifier
            status_topic: Full topic for status publishing
            commands_topic: Full topic for command subscription
            command_handler: Callback function(dict) for processing commands
            username: Optional MQTT username
            password: Optional MQTT password
            central_api_url: Optional HTTP fallback URL
        """
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        if username and password:
            self.client.username_pw_set(username, password)
```

**Callback Pattern:**

```python
def _on_connect(
    self,
    client: mqtt.Client,
    userdata: Any,
    flags: dict[str, int],
    return_code: int
) -> None:
    """Callback on connection established.

    Automatically subscribes to commands_topic on successful connection.
    """
    if return_code == 0:
        logger.info(f"Connected to MQTT broker")
        client.subscribe(self.commands_topic)
        logger.info(f"Subscribed to {self.commands_topic}")
    else:
        logger.error(f"MQTT connection failed: code {return_code}")

def _on_message(
    self,
    client: mqtt.Client,
    userdata: Any,
    msg: mqtt.MQTTMessage
) -> None:
    """Callback on message received.

    Parses JSON, validates, and invokes command_handler.
    All exceptions are caught to prevent MQTT loop crash.
    """
    try:
        payload = msg.payload.decode("utf-8")
        command = json.loads(payload)

        if not isinstance(command, dict):
            logger.error("Command is not a JSON object")
            return

        self.command_handler(command)
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid JSON: {exc}")
    except Exception as exc:
        logger.error(f"Error handling command: {exc}")

def _on_disconnect(
    self,
    client: mqtt.Client,
    userdata: Any,
    return_code: int
) -> None:
    """Callback on disconnection.

    paho-mqtt automatically reconnects, this is for logging only.
    """
    if return_code != 0:
        logger.warning(f"Unexpected disconnect: code {return_code}")
```

**Publishing:**

```python
def publish_status(self, status: dict[str, Any]) -> None:
    """Publish status to MQTT and optionally HTTP.

    Dual publishing:
        1. MQTT (primary): Real-time pub/sub
        2. HTTP (fallback): Ensures API receives updates

    Raises:
        MQTTPublishError: If MQTT publish fails
    """
    # MQTT publish
    payload = json.dumps(status)
    result = self.client.publish(self.status_topic, payload)

    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        raise MQTTPublishError(f"Failed to publish: rc={result.rc}")

    logger.info(f"Published status to {self.status_topic}")

    # HTTP fallback (optional)
    if self.central_api_url:
        self._push_to_http(status)
```

**Topic Conventions:**

```python
# Commands (subscribe)
commands_topic = f"trains/{train_id}/commands"

# Status (publish)
status_topic = f"trains/{train_id}/status"

# Example payloads
command_payload = {
    "action": "setSpeed",  # "start" | "stop" | "setSpeed"
    "speed": 75            # 0-100 (optional)
}

status_payload = {
    "train_id": "train-1",
    "speed": 75,
    "voltage": 12.3,
    "current": 0.8,
    "position": "section_A",
    "timestamp": "2025-11-21T12:34:56Z"
}
```

---

### hardware.py - HardwareController

**Purpose:** Generic GPIO control for motors, lights, sensors.

**Use Case:** Simple DC motors with PWM speed control.

```python
class HardwareController:
    def __init__(
        self,
        motor_pins: list[int],
        light_pins: list[int],
        sensor_pins: list[int]
    ) -> None:
        """Initialize hardware with GPIO pin numbers (BCM numbering)."""
        self.motors = [PWMOutputDevice(pin) for pin in motor_pins]
        self.lights = [LED(pin) for pin in light_pins]
        self.sensors = [DigitalInputDevice(pin) for pin in sensor_pins]

    def set_motor_speed(self, motor_index: int, speed: float) -> bool:
        """Set motor speed (0-100) using PWM.

        Args:
            motor_index: Index in motors list (0-based)
            speed: Speed percentage 0-100

        Returns:
            True if successful, False if invalid index
        """
        if 0 <= motor_index < len(self.motors):
            self.motors[motor_index].value = speed / 100.0  # Convert to 0.0-1.0
            return True
        return False
```

**GPIO Pin Mapping:**

```python
# BCM numbering (GPIO pin numbers, not physical pin numbers)
motor_pins = [18, 19]       # PWM-capable pins (GPIO18, GPIO19)
light_pins = [23, 24, 25]   # Any GPIO pins
sensor_pins = [26, 27]      # Digital input pins
```

---

### stepper_hat.py - StepperMotorHatController

**Purpose:** Waveshare Stepper Motor HAT control via I2C.

**Singleton Pattern:**

```python
class StepperMotorHatController:
    _instance: "StepperMotorHatController" = None

    def __new__(cls) -> "StepperMotorHatController":
        """Singleton: only one instance can exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize GPIO pins (runs once due to singleton)."""
        if getattr(self, "_initialized", False):
            return

        self.dir = OutputDevice(13)   # Direction pin
        self.step = OutputDevice(19)  # Step pulse pin
        self.enable = OutputDevice(12)  # Enable pin
        self.mode_pins = [OutputDevice(16), OutputDevice(17), OutputDevice(20)]
        self._initialized = True
```

**Stepper Control:**

```python
def run_steps(self, speed: int, steps: int = 200) -> None:
    """Execute N steps at specified speed.

    Args:
        speed: Speed 1-100 (maps to pulse delay)
        steps: Number of steps (200 = one revolution in full step mode)
    """
    delay = max(0.001, 0.02 - (speed / 5000.0))
    for _ in range(steps):
        self.step.on()
        time.sleep(delay)
        self.step.off()
        time.sleep(delay)
```

**Microstepping Modes:**

```python
def set_full_step(self) -> None:
    """Full step: MODE pins all LOW (highest torque)."""
    for pin in self.mode_pins:
        pin.off()

def set_half_step(self) -> None:
    """1/2 step: MODE0 HIGH."""
    self.mode_pins[0].on()
    self.mode_pins[1].off()
    self.mode_pins[2].off()

# Additional modes: 1/4, 1/8, 1/16, 1/32 step
```

---

## Testing Patterns

### Unit Tests

**Philosophy:** Fast, isolated, no external dependencies.

```python
# tests/unit/test_config_loader.py
def test_load_service_config_success(tmp_path: Path) -> None:
    """Test loading valid service config."""
    config_file = tmp_path / "edge-controller.conf"
    config_file.write_text("central_api_host: localhost\ncentral_api_port: 8000")

    loader = ConfigLoader(config_path=config_file, cached_config_path=tmp_path / "cache.yaml")
    config = loader.load_service_config()

    assert config["central_api_host"] == "localhost"
    assert config["central_api_port"] == 8000

def test_load_service_config_missing_file(tmp_path: Path) -> None:
    """Test error when service config is missing."""
    loader = ConfigLoader(config_path=tmp_path / "missing.conf", cached_config_path=tmp_path / "cache.yaml")

    with pytest.raises(ConfigLoadError, match="Service config not found"):
        loader.load_service_config()
```

**Mocking External Dependencies:**

```python
# tests/unit/test_api_client.py
@patch("api.client.requests.get")
def test_check_accessibility_success(mock_get: MagicMock) -> None:
    """Test API accessibility check succeeds."""
    mock_get.return_value.status_code = 200

    client = CentralAPIClient(host="localhost", port=8000)
    assert client.check_accessibility() is True

    mock_get.assert_called_once_with("http://localhost:8000/api/ping", timeout=5)

@patch("api.client.requests.get")
def test_check_accessibility_retries(mock_get: MagicMock) -> None:
    """Test API accessibility retries on failure."""
    mock_get.side_effect = [
        RequestException("Connection refused"),
        RequestException("Timeout"),
        MagicMock(status_code=200)
    ]

    client = CentralAPIClient(host="localhost", port=8000, max_retries=3, retry_delay=0)
    assert client.check_accessibility() is True
    assert mock_get.call_count == 3
```

### Integration Tests

**Philosophy:** Test multi-component interactions with minimal mocking.

```python
# tests/integration/test_config_flow.py
def test_full_config_initialization_new_controller(tmp_path: Path, mock_api_server: str) -> None:
    """Test complete config flow for new controller."""
    config_path = tmp_path / "edge-controller.conf"
    cached_path = tmp_path / "edge-controller.yaml"

    config_path.write_text(f"central_api_host: {mock_api_server}\ncentral_api_port: 8000")

    manager = ConfigManager(config_path=config_path, cached_config_path=cached_path)
    service_config, runtime_config = manager.initialize()

    # Verify service config
    assert service_config["central_api_host"] == mock_api_server

    # Verify runtime config was downloaded
    assert runtime_config is not None
    assert "uuid" in runtime_config
    assert "train_id" in runtime_config

    # Verify config was cached
    assert cached_path.exists()
    cached = yaml.safe_load(cached_path.read_text())
    assert cached["uuid"] == runtime_config["uuid"]
```

### E2E Tests

**Philosophy:** Test full lifecycle with simulated hardware.

```python
# tests/e2e/test_controller_lifecycle.py
def test_complete_controller_lifecycle(tmp_path: Path, mock_mqtt_broker: str) -> None:
    """Test controller from startup to shutdown."""
    # Setup configs
    config_path = tmp_path / "edge-controller.conf"
    cached_path = tmp_path / "edge-controller.yaml"

    # Create service config
    config_path.write_text("central_api_host: localhost\ncentral_api_port: 8000")

    # Pre-populate cached config (simulate existing controller)
    cached_config = {
        "uuid": "test-uuid-123",
        "train_id": "train-1",
        "mqtt_broker": {"host": mock_mqtt_broker, "port": 1883},
        "status_topic": "trains/train-1/status",
        "commands_topic": "trains/train-1/commands"
    }
    cached_path.write_text(yaml.dump(cached_config))

    # Initialize app (simulation mode)
    app = EdgeControllerApp(config_path=config_path, cached_config_path=cached_path)

    # Verify MQTT connected
    assert app.mqtt_client.client.is_connected()

    # Send test command
    test_command = {"action": "start", "speed": 50}
    app._handle_command(test_command)

    # Verify hardware received command
    assert app.hardware.last_command == ("start", 50)

    # Shutdown
    app.shutdown()
```

---

## Security Specifications

### Input Validation

**MQTT Command Validation:**

```python
# ✅ CORRECT - Validate all fields
def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        command = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        logger.error("Invalid JSON in MQTT message")
        return

    if not isinstance(command, dict):
        logger.error("Command must be a JSON object")
        return

    action = command.get("action")
    if action not in ["start", "stop", "setSpeed"]:
        logger.warning(f"Unknown action: {action}")
        return

    if action == "setSpeed":
        speed = command.get("speed")
        if not isinstance(speed, int) or not (0 <= speed <= 100):
            logger.error(f"Invalid speed: {speed}")
            return

    self.command_handler(command)
```

### Secrets Management

**Environment Variables for Secrets:**

```python
# ✅ CORRECT - Load from environment
mqtt_password = os.getenv("MQTT_PASSWORD")
if mqtt_password:
    client.username_pw_set(username="edge-controller", password=mqtt_password)

# ❌ INCORRECT - Hardcoded secret
client.username_pw_set(username="edge-controller", password="hardcoded-password")
```

**Docker Secrets:**

```python
# ✅ CORRECT - Read from Docker secret file
def load_mqtt_password() -> str | None:
    secret_path = Path("/run/secrets/mqtt_password")
    if secret_path.exists():
        return secret_path.read_text().strip()
    return os.getenv("MQTT_PASSWORD")
```

### Code Scanning

**Pre-commit Hooks:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: bandit
        name: Bandit Security Scan
        entry: bandit
        args: ["-r", "app/", "-ll"]
        language: system
        pass_filenames: false

      - id: safety
        name: Safety Dependency Check
        entry: safety
        args: ["check", "--file", "requirements.txt"]
        language: system
        pass_filenames: false
```

**CI Pipeline:**

```yaml
# .github/workflows/ci-security.yml
- name: Run Bandit
  run: bandit -r app/ -ll -f json -o bandit-report.json

- name: Run Safety
  run: safety check --file requirements.txt --json > safety-report.json

- name: Fail on High Severity
  run: |
    if jq '.results[] | select(.issue_severity == "HIGH")' bandit-report.json | grep -q .; then
      echo "High severity issues found"
      exit 1
    fi
```

---

## Deployment Specifications

### Docker

**Multi-stage Build:**

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Non-root user
RUN useradd -m -u 1000 edgeuser
USER edgeuser

WORKDIR /app
COPY --from=builder /root/.local /home/edgeuser/.local
COPY app/ ./

ENV PATH=/home/edgeuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

**Environment Variables:**

```bash
# Required
CENTRAL_API_HOST=api.example.com
CENTRAL_API_PORT=8000

# Optional
LOCAL_DEV=true              # Enable simulator mode
MQTT_BROKER=mqtt.local      # Override MQTT broker
MQTT_PORT=1883              # Override MQTT port
MQTT_PASSWORD=secret        # MQTT password (use Docker secrets)
LOG_LEVEL=INFO              # Logging level
```

### Kubernetes

**Deployment Manifest:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: edge-controller
spec:
  replicas: 1  # One per train
  selector:
    matchLabels:
      app: edge-controller
  template:
    metadata:
      labels:
        app: edge-controller
    spec:
      containers:
      - name: edge-controller
        image: edge-controller:latest
        env:
        - name: CENTRAL_API_HOST
          valueFrom:
            configMapKeyRef:
              name: edge-controller-config
              key: central_api_host
        - name: MQTT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mqtt-credentials
              key: password
        volumeMounts:
        - name: config-cache
          mountPath: /app/edge-controller.yaml
          subPath: edge-controller.yaml
      volumes:
      - name: config-cache
        persistentVolumeClaim:
          claimName: edge-controller-cache
```

### Raspberry Pi (Systemd)

**Service File:**

```ini
[Unit]
Description=Edge Controller for Model Train
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/edge-controllers/pi-template/app
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10s
Environment="PYTHONUNBUFFERED=1"
Environment="CENTRAL_API_HOST=api.local"
EnvironmentFile=-/etc/edge-controller/env

[Install]
WantedBy=multi-user.target
```

**Installation:**

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-gpiozero

# Install Python packages
pip3 install -r requirements-pi.txt

# Install service
sudo cp edge-controller.service /etc/systemd/system/
sudo systemctl enable edge-controller
sudo systemctl start edge-controller

# Check status
sudo systemctl status edge-controller
sudo journalctl -u edge-controller -f
```

---

## Performance Specifications

### Latency Requirements

| Operation | Target | Acceptable | Failure |
|-----------|--------|------------|---------|
| MQTT command to hardware | <50ms | <100ms | >200ms |
| Status publish | <20ms | <50ms | >100ms |
| API registration | <2s | <5s | >10s |
| Config download | <1s | <2s | >5s |

### Resource Limits

**Raspberry Pi 3:**

```yaml
# Resource usage targets
memory_idle: 40MB
memory_active: 50MB
memory_peak: 60MB

cpu_idle: <1%
cpu_active: <5%
cpu_peak: <20%

network_idle: <1KB/s
network_active: <5KB/s
network_peak: <10KB/s
```

**Optimization Guidelines:**

1. **Minimize Memory Allocations:** Reuse objects where possible
2. **Avoid Blocking Operations:** Use async/await for I/O-bound tasks (future enhancement)
3. **Batch Status Updates:** Don't publish on every sensor read (rate limit to 1Hz)
4. **GPIO Efficiency:** Minimize pin state changes

---

## Common Code Modification Patterns

### Adding a New MQTT Command

**1. Update command validation in `mqtt_client.py`:**

```python
def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    command = json.loads(msg.payload.decode())
    action = command.get("action")

    # Add new action
    if action not in ["start", "stop", "setSpeed", "emergencyStop"]:  # NEW
        logger.warning(f"Unknown action: {action}")
        return
```

**2. Update command handler in `main.py`:**

```python
def _handle_command(self, command: dict[str, Any]) -> None:
    action = command.get("action")

    if action == "emergencyStop":  # NEW
        self._execute_hardware_command("emergencyStop", None)
    elif action == "start":
        # ... existing code
```

**3. Implement hardware action:**

```python
def _execute_hardware_command(self, action: str, speed: int | None) -> None:
    if action == "emergencyStop":  # NEW
        self.hardware_controller.stop()
        logger.info("Emergency stop executed")
        self.publish_status({"speed": 0, "status": "emergency_stop"})
    elif action == "start":
        # ... existing code
```

**4. Add tests:**

```python
def test_emergency_stop_command(app: EdgeControllerApp) -> None:
    """Test emergency stop command."""
    command = {"action": "emergencyStop"}
    app._handle_command(command)

    assert app.hardware_controller.current_speed == 0
    # Verify status was published
```

### Adding a New Configuration Field

**1. Update runtime config schema in `config/manager.py`:**

```python
def _is_runtime_config_complete(self, config: dict[str, Any]) -> bool:
    """Validate runtime config has required fields."""
    required_fields = [
        "train_id",
        "mqtt_broker",
        "status_topic",
        "commands_topic",
        "max_speed"  # NEW
    ]
    return all(field in config for field in required_fields)
```

**2. Use new field in `main.py`:**

```python
def __init__(self, config_path: Path, cached_config_path: Path) -> None:
    service_config, runtime_config = self.config_manager.initialize()

    self.max_speed = runtime_config.get("max_speed", 100)  # NEW
```

**3. Update documentation:**

```python
# In docstrings, update expected config format
"""
Expected Runtime Config:
    {
        "uuid": str,
        "train_id": str,
        "mqtt_broker": {...},
        "status_topic": str,
        "commands_topic": str,
        "max_speed": int  # NEW: Maximum allowed speed (0-100)
    }
"""
```

### Adding a New Hardware Controller

**1. Create new module `my_controller.py`:**

```python
"""Custom hardware controller for XYZ motor driver."""

from typing import Any
import logging

logger = logging.getLogger(__name__)


class MyHardwareController:
    """Controller for XYZ motor driver.

    Implements the hardware controller interface for compatibility
    with EdgeControllerApp.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize controller with hardware-specific config."""
        self.config = config
        # Initialize hardware connection

    def start(self, speed: int = 50) -> None:
        """Start motor at specified speed."""
        logger.info(f"Starting motor at speed {speed}")
        # Hardware-specific implementation

    def stop(self) -> None:
        """Stop motor immediately."""
        logger.info("Stopping motor")
        # Hardware-specific implementation

    def set_speed(self, speed: int) -> None:
        """Change motor speed without stopping."""
        logger.info(f"Setting speed to {speed}")
        # Hardware-specific implementation

    def cleanup(self) -> None:
        """Release hardware resources."""
        logger.info("Cleaning up hardware")
        # Hardware-specific cleanup
```

**2. Update `main.py` to use new controller:**

```python
from my_controller import MyHardwareController

def __init__(self, config_path: Path, cached_config_path: Path) -> None:
    # ... config initialization ...

    if HARDWARE_AVAILABLE:
        hardware_type = runtime_config.get("hardware_type", "stepper_hat")

        if hardware_type == "my_controller":  # NEW
            self.hardware_controller = MyHardwareController(runtime_config.get("hardware_config", {}))
        elif hardware_type == "stepper_hat":
            self.hardware_controller = StepperMotorHatController()
        else:
            self.hardware_controller = HardwareController(
                motor_pins=[18], light_pins=[], sensor_pins=[]
            )
    else:
        self.hardware_controller = StepperMotorSimulator()
```

---

## AI Agent Guidelines

### When Modifying Code

1. **Preserve Type Hints:** All function signatures must maintain complete type annotations
2. **Update Docstrings:** Modify Google-style docstrings to reflect changes
3. **Add Tests:** Include unit tests for new functionality (minimum 80% coverage)
4. **Follow Error Patterns:** Use existing exception classes, raise on critical errors, return None on transient errors
5. **Maintain Logging:** Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
6. **Update This Document:** Modify AI_SPECS.md when adding new patterns or changing architecture

### When Adding Features

1. **Check Compatibility:** Ensure changes work with Python 3.9+
2. **Hardware Abstraction:** New hardware should implement the controller interface
3. **Configuration Management:** Add new config fields to validation logic
4. **MQTT Messages:** Follow existing topic patterns (`trains/{train_id}/...`)
5. **Security:** Validate all external inputs, use environment variables for secrets

### When Debugging

1. **Check Logs:** Review journalctl or Docker logs for ERROR/WARNING messages
2. **Verify Config:** Ensure both service and runtime configs are valid YAML
3. **Test MQTT:** Use `mosquitto_pub`/`mosquitto_sub` to isolate MQTT issues
4. **Mock Hardware:** Use `LOCAL_DEV=true` to test without physical devices
5. **Run Tests:** Execute `pytest tests/` to verify functionality

### Code Quality Checklist

Before committing code changes:

- [ ] All functions have type hints
- [ ] All public functions have Google-style docstrings
- [ ] Unit tests added for new functionality
- [ ] Tests pass (`pytest tests/`)
- [ ] Linting passes (`ruff check app/`)
- [ ] Type checking passes (`mypy app/`)
- [ ] Security scan passes (`bandit -r app/ -ll`)
- [ ] No hardcoded secrets in code
- [ ] Logging uses appropriate levels
- [ ] Error handling follows established patterns

---

## Reference Implementation Examples

### Complete Minimal Controller

```python
"""Minimal edge controller implementation."""

import logging
from pathlib import Path
from config.manager import ConfigManager
from mqtt_client import MQTTClient
from hardware import HardwareController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinimalController:
    """Minimal edge controller for demonstration."""

    def __init__(self) -> None:
        """Initialize controller with default paths."""
        config_path = Path("edge-controller.conf")
        cached_path = Path("edge-controller.yaml")

        # Load configs
        manager = ConfigManager(config_path, cached_path)
        service_config, runtime_config = manager.initialize()

        if runtime_config is None:
            logger.info("Waiting for train assignment")
            return

        # Initialize MQTT
        self.mqtt = MQTTClient(
            broker_host=runtime_config["mqtt_broker"]["host"],
            broker_port=runtime_config["mqtt_broker"]["port"],
            train_id=runtime_config["train_id"],
            status_topic=runtime_config["status_topic"],
            commands_topic=runtime_config["commands_topic"],
            command_handler=self.handle_command
        )
        self.mqtt.start()

        # Initialize hardware
        self.hardware = HardwareController(
            motor_pins=[18],
            light_pins=[],
            sensor_pins=[]
        )

        logger.info("Controller initialized")

    def handle_command(self, command: dict[str, Any]) -> None:
        """Process MQTT command."""
        action = command.get("action")
        speed = command.get("speed", 50)

        if action == "start":
            self.hardware.set_motor_speed(0, speed)
            self.mqtt.publish_status({"speed": speed, "status": "running"})
        elif action == "stop":
            self.hardware.set_motor_speed(0, 0)
            self.mqtt.publish_status({"speed": 0, "status": "stopped"})

    def shutdown(self) -> None:
        """Cleanup resources."""
        self.mqtt.stop()
        self.hardware.cleanup()


if __name__ == "__main__":
    controller = MinimalController()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.shutdown()
```

### Complete Test Suite Structure

```python
# tests/unit/test_minimal_controller.py
"""Unit tests for MinimalController."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


@pytest.fixture
def mock_config_manager() -> MagicMock:
    """Mock ConfigManager for testing."""
    manager = MagicMock()
    manager.initialize.return_value = (
        {"central_api_host": "localhost"},  # service_config
        {  # runtime_config
            "train_id": "train-1",
            "mqtt_broker": {"host": "mqtt", "port": 1883},
            "status_topic": "trains/train-1/status",
            "commands_topic": "trains/train-1/commands"
        }
    )
    return manager


@pytest.fixture
def mock_mqtt_client() -> MagicMock:
    """Mock MQTTClient for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_hardware() -> MagicMock:
    """Mock HardwareController for testing."""
    hardware = MagicMock()
    return hardware


def test_controller_initialization(
    mock_config_manager: MagicMock,
    mock_mqtt_client: MagicMock,
    mock_hardware: MagicMock
) -> None:
    """Test controller initializes correctly."""
    with patch("minimal_controller.ConfigManager", return_value=mock_config_manager):
        with patch("minimal_controller.MQTTClient", return_value=mock_mqtt_client):
            with patch("minimal_controller.HardwareController", return_value=mock_hardware):
                controller = MinimalController()

                # Verify initialization
                mock_config_manager.initialize.assert_called_once()
                mock_mqtt_client.start.assert_called_once()
                assert controller.mqtt == mock_mqtt_client
                assert controller.hardware == mock_hardware


def test_handle_start_command(mock_hardware: MagicMock, mock_mqtt_client: MagicMock) -> None:
    """Test handling start command."""
    controller = MinimalController()
    controller.hardware = mock_hardware
    controller.mqtt = mock_mqtt_client

    command = {"action": "start", "speed": 75}
    controller.handle_command(command)

    mock_hardware.set_motor_speed.assert_called_once_with(0, 75)
    mock_mqtt_client.publish_status.assert_called_once()

    # Verify status payload
    status = mock_mqtt_client.publish_status.call_args[0][0]
    assert status["speed"] == 75
    assert status["status"] == "running"
```

---

**Document Version:** 1.0  
**Last Updated:** November 21, 2025  
**Maintained By:** Development Team  

**Related Documents:**

- [Architecture Guide](ARCHITECTURE.md) - Human-facing architecture documentation
- [Quick Start](../pi-template/README.md) - Setup and deployment guide
- [Security Policy](../../SECURITY.md) - Security best practices

---

**AI Agent Certification:**

This document provides complete specifications for autonomous code modification of the edge controller subsystem. An AI agent following these specifications should be able to:

✅ Generate new Python modules with correct structure and style  
✅ Modify existing code while maintaining type safety and patterns  
✅ Add new hardware controllers following the plugin pattern  
✅ Extend MQTT command handling with new actions  
✅ Write comprehensive unit and integration tests  
✅ Debug common configuration and runtime issues  
✅ Deploy code to Raspberry Pi, Docker, or Kubernetes  

**Feedback Loop:** If AI agents encounter ambiguities or missing specifications, update this document with clarifications and additional examples.
