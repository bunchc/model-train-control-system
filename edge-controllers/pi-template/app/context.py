"""context.py

Configuration and runtime context management for the edge-controller service.

This module handles:
    - Loading service configuration from edge-controller.conf
    - Determining controller identity from environment or config
    - Building central API URLs from config
    - Checking central API and controller accessibility
    - Registering with central API and downloading runtime config
    - Loading cached runtime config from edge-controller.yaml
    - Providing train and MQTT context for hardware control

Constants:
    CONFIG_FILE: Path to edge-controller.conf (service config)
    CACHED_CONFIG_FILE: Path to edge-controller.yaml (runtime config)

Usage:
    service_config, runtime_config = initialize_configs()
    TRAIN_ID = runtime_config.get('train_id', 'train_1')
    MQTT_BROKER = runtime_config.get('mqtt_broker', {}).get('host', 'localhost')
    MQTT_PORT = runtime_config.get('mqtt_broker', {}).get('port', 1883)
    MQTT_USER = runtime_config.get('mqtt_broker', {}).get('username', None)
    MQTT_PASS = runtime_config.get('mqtt_broker', {}).get('password', None)
    STATUS_TOPIC = runtime_config.get('status_topic', f'trains/{TRAIN_ID}/status')
    COMMANDS_TOPIC = runtime_config.get('commands_topic', f'trains/{TRAIN_ID}/commands')
"""

import logging
import os
import time

import requests
import yaml


def is_central_api_accessible(service_config, retries=5, delay=2):
    """Check if the central API is accessible by calling its /ping endpoint.

    Implements retry logic with configurable attempts and delay. This is used
    during initialization to determine whether to download fresh config or
    fall back to cached config.

    Retry Strategy:
        - Makes up to 'retries' attempts
        - Waits 'delay' seconds between attempts
        - Returns True on first successful response
        - Returns False if all retries exhausted

    Args:
        service_config (dict): Service config dict containing:
            - central_api_host: API hostname
            - central_api_port: API port
        retries (int): Number of retry attempts (default: 5)
        delay (int): Delay in seconds between retries (default: 2)

    Returns:
        bool: True if API responds with 200 OK, False otherwise

    Note:
        All exceptions are caught and logged. Method never raises.
    """
    # Retry loop: attempt up to 'retries' times with delays between attempts
    for attempt in range(retries):
        try:
            # Construct ping endpoint URL from service config
            base_url = get_central_api_url(service_config)
            url = f"{base_url}/api/ping"

            # Send GET request with short timeout (2 seconds)
            resp = requests.get(url, timeout=2)

            # Success: API responded with 200 OK
            if resp.status_code == 200:
                return True  # Exit immediately on first success
            # Non-200 status: retry (might be temporary API issue)

        except Exception as e:
            # Network error: timeout, connection refused, DNS failure, etc.
            # Log attempt number for debugging
            logging.warning(f"Central API not accessible (attempt {attempt + 1}/{retries}): {e}")

        # Delay before next retry (unless this was the last attempt)
        if attempt < retries - 1:
            time.sleep(delay)

    # All retries exhausted - API is unreachable
    return False


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "./edge-controller.conf")
"""
Absolute path to the edge-controller service configuration file.
"""

CACHED_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "./edge-controller.yaml")
"""
Absolute path to the cached runtime configuration file.
"""


def load_local_config():
    """Load the edge-controller service configuration from edge-controller.conf.

    The service config contains static configuration:
    - central_api_host: Central API hostname
    - central_api_port: Central API port
    - logging configuration

    Expected Format:
        central_api_host: "192.168.1.100"
        central_api_port: 8000

    Returns:
        dict: Parsed YAML config if file exists, else None

    Side Effects:
        Reads from disk (CONFIG_FILE path)
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return None


def get_controller_id():
    """Determine the controller ID for this edge-controller.

    Checks two sources in priority order:
    1. CONTROLLER_ID environment variable (highest priority)
    2. controller_id field in edge-controller.conf

    This function is currently unused but may be needed for future
    multi-controller deployments.

    Returns:
        str: Controller ID if found, else None

    Example:
        >>> os.environ["CONTROLLER_ID"] = "edge-01"
        >>> get_controller_id()
        "edge-01"
    """
    controller_id = os.getenv("CONTROLLER_ID")
    if controller_id:
        return controller_id
    config = load_local_config()
    if config and "controller_id" in config:
        return config["controller_id"]
    return None


def get_central_api_url(service_config):
    """Build the base URL for the central API from service config.

    Constructs HTTP URL from host and port in service config.
    Provides defaults if fields missing.

    Args:
        service_config (dict): Service config dict containing:
            - central_api_host: API hostname (default: "localhost")
            - central_api_port: API port (default: 8000)

    Returns:
        str: Base URL for central API (e.g., "http://central-api:8000")

    Example:
        >>> config = {"central_api_host": "192.168.1.100", "central_api_port": 8000}
        >>> get_central_api_url(config)
        "http://192.168.1.100:8000"
    """
    host = service_config.get("central_api_host", "localhost")
    port = service_config.get("central_api_port", 8000)
    return f"http://{host}:{port}"


def is_controller_accessible(controller_id, service_config):
    """Check if the controller is accessible via the central API.

    Calls GET /api/controllers/{id}/ping to verify the controller is registered
    and recognized by the Central API.

    This function is currently unused but may be needed for validation logic.

    Args:
        controller_id (str): Controller ID to check
        service_config (dict): Service config dict

    Returns:
        bool: True if API returns 200 OK, False otherwise

    Side Effects:
        Performs HTTP GET request to central API

    Note:
        All exceptions are caught and logged. Method never raises.
    """
    try:
        base_url = get_central_api_url(service_config)
        url = f"{base_url}/api/controllers/{controller_id}/ping"
        resp = requests.get(url, timeout=2)
        return resp.status_code == 200
    except Exception as e:
        logging.warning(f"Controller {controller_id} not accessible: {e}")
        return False


def read_uuid_from_cached_config():
    """Read the UUID from the cached runtime config (edge-controller.yaml).

    The UUID is assigned during registration and persisted in the cached
    config. It uniquely identifies this controller in the Central API.

    Returns:
        str: UUID if present in cached config, else None

    Side Effects:
        Reads from disk (CACHED_CONFIG_FILE path)

    Example:
        >>> # After registration, cached config contains:
        >>> # uuid: "550e8400-e29b-41d4-a716-446655440000"
        >>> # train_id: "1"
        >>> read_uuid_from_cached_config()
        "550e8400-e29b-41d4-a716-446655440000"
    """
    if os.path.exists(CACHED_CONFIG_FILE):
        with open(CACHED_CONFIG_FILE) as f:
            cached = yaml.safe_load(f)
            return cached.get("uuid")
    return None


def download_runtime_config(uuid, service_config):
    """Download the latest runtime config for this controller from the central API.

    Retrieves runtime configuration (train assignment, MQTT broker details)
    from Central API and saves to edge-controller.yaml. Preserves UUID in
    the saved config.

    Expected API Response:
        {
            "train_id": "1",
            "mqtt_broker": {
                "host": "192.168.1.10",
                "port": 1883,
                "username": null,
                "password": null
            },
            "status_topic": "trains/1/status",
            "commands_topic": "trains/1/commands"
        }

    Args:
        uuid (str): Controller UUID (assigned during registration)
        service_config (dict): Service config dict

    Returns:
        bool: True if download succeeded and config saved, False otherwise

    Side Effects:
        - Performs HTTP GET request to central API
        - Writes to disk (CACHED_CONFIG_FILE)

    Note:
        If API returns 404, this means controller is registered but not
        assigned to a train yet. Returns False in this case.
    """
    try:
        base_url = get_central_api_url(service_config)
        url = f"{base_url}/api/controllers/{uuid}/config"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            # Parse the downloaded config and ensure uuid is included
            config_data = resp.json()
            if config_data is None:
                config_data = {}
            config_data["uuid"] = uuid

            with open(CACHED_CONFIG_FILE, "w") as f:
                yaml.safe_dump(config_data, f)
            logging.info(f"Downloaded runtime config for UUID {uuid}")
            return True
    except Exception as e:
        logging.exception(f"Failed to download runtime config: {e}")
    return False


def register_with_central_api(service_config):
    """Register this edge-controller with the central API and obtain a UUID.

    Sends controller hostname and IP address to Central API. API assigns
    a UUID which uniquely identifies this controller.

    Registration Payload:
        {
            "name": "edge-controller-01",  # socket.gethostname()
            "address": "192.168.1.50"       # socket.gethostbyname()
        }

    Expected API Response:
        {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "status": "registered"
        }

    Args:
        service_config (dict): Service config dict

    Returns:
        str: UUID if registration succeeded, else None

    Side Effects:
        Performs HTTP POST request to central API

    Note:
        UUID is NOT saved to disk by this function. Caller should use
        download_runtime_config() which saves UUID to cached config.
    """
    import socket

    try:
        # Get hostname and IP address
        hostname = socket.gethostname()
        try:
            # Try to get the actual IP address
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            ip_address = "unknown"

        base_url = get_central_api_url(service_config)
        url = f"{base_url}/api/controllers/register"
        payload = {"name": hostname, "address": ip_address}
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            uuid = data.get("uuid")
            if uuid:
                logging.info(
                    f"Registered controller name={hostname}, address={ip_address}, uuid={uuid}, status={data.get('status')}"
                )
                return uuid
    except Exception as e:
        logging.exception(f"Failed to register: {e}")
    return None


def load_cached_runtime_config():
    """Load the cached runtime config from edge-controller.yaml.

    Runtime config contains:
    - uuid: Controller identifier
    - train_id: Assigned train identifier
    - mqtt_broker: MQTT connection details
    - status_topic: MQTT topic for status publishing
    - commands_topic: MQTT topic for command subscription

    Returns:
        dict: Parsed YAML config if file exists, else None

    Side Effects:
        Reads from disk (CACHED_CONFIG_FILE path)

    Example:
        >>> config = load_cached_runtime_config()
        >>> if config:
        ...     train_id = config["train_id"]
    """
    if os.path.exists(CACHED_CONFIG_FILE):
        with open(CACHED_CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return None


def initialize_configs():
    """Initialize and load both service and runtime configs for the edge-controller.

    This is the main entry point for configuration initialization. Orchestrates
    the complex workflow of registration, config download, and fallback logic.

    Workflow:
        1. Load service config from edge-controller.conf
        2. Check if Central API is accessible
        3. If API accessible:
           a. Check for cached UUID
           b. If UUID exists, download fresh runtime config
           c. If no UUID, register and download runtime config
        4. If API not accessible:
           a. Load cached runtime config
           b. Raise RuntimeError if no cache exists

    Scenarios:
        - First boot, API online:
          Registers, downloads config, returns complete configs

        - First boot, API offline:
          Raises RuntimeError (cannot proceed without config)

        - Subsequent boot, API online:
          Downloads fresh config using cached UUID

        - Subsequent boot, API offline:
          Uses cached config (may be stale)

        - Registered but not assigned:
          Returns (service_config, None) - waiting for admin

    Returns:
        tuple: (service_config, runtime_config)
        - service_config: Always present (from edge-controller.conf)
        - runtime_config: May be None if waiting for train assignment

    Raises:
        RuntimeError: If Central API is not accessible and no cached config exists

    Side Effects:
        - May perform HTTP requests (registration, config download)
        - May read/write disk (config files)
        - Logs extensively
    """
    service_config = load_local_config()

    # Check if central API is accessible
    if not is_central_api_accessible(service_config):
        # Central API not accessible, try to use cached config
        runtime_config = load_cached_runtime_config()
        if runtime_config:
            logging.warning("Central API not accessible, using cached runtime config.")
            return service_config, runtime_config
        logging.error(
            "Central API is not accessible and no cached runtime config. Failing to start."
        )
        raise RuntimeError("Central API is not accessible.")

    # Check for existing cached config with UUID
    cached_config = load_cached_runtime_config()
    if cached_config and "uuid" in cached_config:
        uuid = cached_config["uuid"]
        logging.info(f"Found cached config with uuid={uuid}")

        # Try to download fresh runtime config
        if download_runtime_config(uuid, service_config):
            runtime_config = load_cached_runtime_config()
            logging.info("Runtime config updated from central API.")
            return service_config, runtime_config
        # Download failed, use cached config if it has required fields
        if "train_id" in cached_config and "mqtt_broker" in cached_config:
            logging.warning("Failed to download fresh config, using cached runtime config.")
            return service_config, cached_config
        logging.warning(
            "Failed to download config and cached config is incomplete. Will run without train config."
        )
        return service_config, None

    # No cached UUID - need to register
    logging.info("No cached UUID found. Registering with central API...")
    uuid = register_with_central_api(service_config)

    if not uuid:
        logging.error("Failed to register with central API.")
        raise RuntimeError("Failed to register with central API.")

    logging.info(f"Successfully registered with UUID: {uuid}")

    # Try to download runtime config
    if download_runtime_config(uuid, service_config):
        runtime_config = load_cached_runtime_config()
        logging.info("Downloaded runtime config after registration.")
        return service_config, runtime_config
    # We just registered but config isn't available yet
    # This is normal - admin needs to assign trains to this controller
    logging.info(
        "Registered successfully but no runtime config available yet. Starting without train config."
    )
    logging.info("Waiting for administrator to assign trains to this controller...")
    return service_config, None


# Usage variables (documented):
service_config, runtime_config = initialize_configs()
"""
service_config (dict): Service configuration loaded from edge-controller.conf.
runtime_config (dict): Runtime configuration loaded from edge-controller.yaml.
                       May be None if just registered and waiting for admin to assign trains.
TRAIN_ID (str): Train identifier for this controller.
MQTT_BROKER (str): MQTT broker hostname.
MQTT_PORT (int): MQTT broker port.
MQTT_USER (str): MQTT broker username.
MQTT_PASS (str): MQTT broker password.
STATUS_TOPIC (str): MQTT topic for train status updates.
COMMANDS_TOPIC (str): MQTT topic for train commands.
"""

if runtime_config:
    TRAIN_ID = runtime_config.get("train_id", "train_1")
    MQTT_BROKER = runtime_config.get("mqtt_broker", {}).get("host", "localhost")
    MQTT_PORT = runtime_config.get("mqtt_broker", {}).get("port", 1883)
    MQTT_USER = runtime_config.get("mqtt_broker", {}).get("username", None)
    MQTT_PASS = runtime_config.get("mqtt_broker", {}).get("password", None)
    STATUS_TOPIC = runtime_config.get("status_topic", f"trains/{TRAIN_ID}/status")
    COMMANDS_TOPIC = runtime_config.get("commands_topic", f"trains/{TRAIN_ID}/commands")
else:
    # No runtime config yet - set defaults
    logging.warning("No runtime config available. Using default values.")
    TRAIN_ID = None
    MQTT_BROKER = "mqtt"
    MQTT_PORT = 1883
    MQTT_USER = None
    MQTT_PASS = None
    STATUS_TOPIC = None
    COMMANDS_TOPIC = None
