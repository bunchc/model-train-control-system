"""Central API client for edge controller communication.

This module provides HTTP client for interacting with the Central API,
handling registration, configuration download, and health checks.

The CentralAPIClient implements:
- Retry logic with exponential backoff
- Connection error handling
- JSON response validation
- UUID-based controller identification

Network Topology:
    Edge Controller -> HTTP/REST -> Central API

    The Central API is the authoritative source for:
    - Controller registration and UUID assignment
    - Runtime configuration (train assignment, MQTT broker)
    - Health monitoring

Error Handling:
    - APIConnectionError: Network-level failures (DNS, timeout, refused)
    - APIRegistrationError: Registration-specific failures
    - APIClientError: Base class for all API errors

Typical usage:
    client = CentralAPIClient(host="192.168.1.100", port=8000)
    if client.check_accessibility():
        uuid = client.register_controller()
        config = client.download_runtime_config(uuid)
"""

import logging
import socket
import time
from typing import Any, Optional

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout


# HTTP status code constants for readability
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_CONFLICT = 409
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404


logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors.

    All exceptions raised by CentralAPIClient inherit from this class,
    allowing callers to catch all API-related errors with a single handler.

    Example:
        >>> try:
        ...     client.register_controller()
        ... except APIClientError as e:
        ...     logger.error(f"API error: {e}")
    """


class APIConnectionError(APIClientError):
    """Raised when API connection fails.

    Indicates network-level failures such as:
    - DNS resolution failure (hostname not found)
    - Connection refused (API not running)
    - Timeout (network congestion or API overload)
    - Network unreachable (routing issues)

    This error suggests the API is completely unreachable. The caller
    should fall back to cached configuration if available.
    """


class APIRegistrationError(APIClientError):
    """Raised when controller registration fails.

    Indicates registration-specific failures:
    - API returned error status (400, 500)
    - Response missing required fields (no UUID)
    - Invalid JSON in response
    - Duplicate registration rejected

    Unlike APIConnectionError, this indicates the API is reachable but
    rejected the registration. This is a terminal error requiring operator
    intervention.
    """


class CentralAPIClient:
    """Client for communicating with the central API.

    This client provides methods for all edge-controller-to-API interactions:
    - Health checks (check_accessibility, check_controller_exists)
    - Registration (register_controller)
    - Configuration download (download_runtime_config)

    The client implements automatic retry logic for transient failures and
    graceful degradation when the API is unreachable.

    Attributes:
        host: API server hostname or IP address
        port: API server port (typically 8000)
        timeout: HTTP request timeout in seconds
        retry_delay: Delay between retry attempts in seconds
        max_retries: Maximum number of retry attempts for health checks
        base_url: Constructed base URL (http://host:port)

    Example:
        >>> client = CentralAPIClient(
        ...     host="central-api.local", port=8000, timeout=5, retry_delay=2, max_retries=3
        ... )
        >>> if client.check_accessibility():
        ...     uuid = client.register_controller()
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 5,
        retry_delay: int = 2,
        max_retries: int = 5,
    ) -> None:
        """Initialize API client.

        Args:
            host: API server hostname or IP address (e.g., "192.168.1.100")
            port: API server port (typically 8000 for Central API)
            timeout: Request timeout in seconds. Operations exceeding this
                will raise Timeout exception.
            retry_delay: Delay between retry attempts in seconds. Used for
                health checks and transient failures.
            max_retries: Maximum number of retry attempts for health checks.
                Registration and config downloads do not retry automatically.

        Note:
            This constructor does not perform network operations. Call
            check_accessibility() to verify the API is reachable.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.base_url = f"http://{host}:{port}"

    def check_accessibility(self) -> bool:
        """Check if the central API is accessible.

        Performs health check by calling GET /api/ping with automatic retries.
        This method is used during initialization to determine whether to
        download fresh config or fall back to cached config.

        Retry Logic:
            - Makes up to max_retries attempts
            - Waits retry_delay seconds between attempts
            - Logs each failed attempt
            - Returns True on first successful response

        Returns:
            True if API responds with 200 OK, False if all retries exhausted

        Note:
            This method never raises exceptions. All errors are caught, logged,
            and result in False return value.

        Example:
            >>> client = CentralAPIClient(host="api.local", port=8000)
            >>> if client.check_accessibility():
            ...     print("API is online")
            ... else:
            ...     print("API is offline, using cached config")
        """
        # Retry loop: attempt up to max_retries times with delays
        for attempt in range(self.max_retries):
            try:
                # Send HTTP GET to ping endpoint
                url = f"{self.base_url}/api/ping"
                response = requests.get(url, timeout=self.timeout)
                # Success: API responded with 200 OK
                if response.status_code == HTTP_OK:
                    logger.info("Central API is accessible")
                    return True  # Exit immediately on success
                # Non-200 response: log but retry (might be temporary API issue)
            except (RequestException, Timeout, RequestsConnectionError) as exc:
                # Network error: DNS failure, connection refused, timeout, etc.
                # Log attempt number and error for debugging
                logger.warning(
                    f"Central API not accessible (attempt {attempt + 1}/{self.max_retries}): {exc}"
                )
            # Delay before next retry (unless this was the last attempt)
            # Implements simple retry with fixed delay (not exponential backoff)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        # All retries exhausted - API is unreachable
        return False

    def check_controller_exists(self, controller_uuid: str) -> bool:
        """Check if a controller is registered with the central API.

        Calls GET /api/controllers/{uuid}/ping to verify the controller's
        UUID is recognized by the API. Used to validate cached UUIDs.

        Args:
            controller_uuid: UUID to check (typically from cached config)

        Returns:
            True if API recognizes the UUID (200 OK), False otherwise

        Note:
            This method does NOT retry. It performs a single check and returns.
            All exceptions are caught and logged, resulting in False.

        Example:
            >>> uuid = cached_config.get("uuid")
            >>> if uuid and client.check_controller_exists(uuid):
            ...     print(f"Controller {uuid} is registered")
        """
        try:
            url = f"{self.base_url}/api/controllers/{controller_uuid}/ping"
            response = requests.get(url, timeout=self.timeout)
        except (RequestException, Timeout, RequestsConnectionError) as exc:
            logger.warning(f"Failed to check controller existence: {exc}")
            return False
        else:
            return response.status_code == HTTP_OK

    def register_controller(self, config: Optional[dict[str, Any]] = None) -> str:
        """Register this edge controller with the central API.

        Calls POST /api/controllers/register with hostname and IP address.
        The API assigns a UUID which must be persisted in cached config.

        Registration Payload:
            {
                "name": controller_name from config or socket.gethostname(),
                "address": "192.168.1.50"       # socket.gethostbyname()
            }

        Expected Response:
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "status": "registered"
            }

        Returns:
            UUID string assigned by the central API

        Raises:
            APIRegistrationError: If registration fails:
                - Network error (API unreachable)
                - API returned error status (400, 500)
                - Response missing UUID field
                - Invalid JSON in response

        Example:
            >>> try:
            ...     uuid = client.register_controller()
            ...     cache_config["uuid"] = uuid
            ... except APIRegistrationError as e:
            ...     logger.error(f"Registration failed: {e}")
            ...     sys.exit(1)
        """
        try:
            hostname = socket.gethostname()
            name = None
            if config is not None:
                name = config.get("controller_name")
            if not name:
                name = hostname

            # Attempt to get actual IP address
            try:
                ip_address = socket.gethostbyname(hostname)
            except socket.gaierror:
                logger.warning("Could not resolve IP address")
                ip_address = "unknown"

            url = f"{self.base_url}/api/controllers/register"
            payload = {"name": name, "address": ip_address}

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            controller_uuid = data.get("uuid")

            if not controller_uuid:
                raise APIRegistrationError("API response missing UUID")

            status = data.get("status", "unknown")
            logger.info(
                f"Registered controller: name={name}, uuid={controller_uuid}, status={status}"
            )

        except RequestException:
            logger.exception("Registration request failed")
            raise APIRegistrationError("Registration request failed") from None
        except (KeyError, ValueError):
            logger.exception("Invalid registration response")
            raise APIRegistrationError("Invalid registration response") from None
        else:
            return controller_uuid

    def register_train(self, controller_uuid: str, train_data: dict[str, Any]) -> bool:
        """Register a train with the central API.

        Calls POST /api/controllers/{controller_uuid}/trains to register a new train
        for this controller. The train data should contain:
        - train_id: Unique train identifier
        - name: Human-readable train name
        - plugin: Dict with 'name' and 'config' keys
        - description: Optional train description
        - model: Optional train model

        Expected Request:
            {
                "train_id": "7cd3e891-fb64-46ff-a3f4-36e4aff6bee0",
                "name": "Train M1",
                "plugin": {
                    "name": "adafruit_dcmotor_hat",
                    "config": {"motor_port": 1}
                },
                "description": "Train on motor port M1",
                "model": "DC Motor"
            }

        Expected Response (201 Created):
            {
                "id": "7cd3e891-fb64-46ff-a3f4-36e4aff6bee0",
                "name": "Train M1",
                "plugin": {"name": "adafruit_dcmotor_hat", "config": {"motor_port": 1}},
                "edge_controller_id": "{controller_uuid}",
                ...
            }

        Args:
            controller_uuid: UUID of the controller owning this train
            train_data: Dictionary containing train configuration

        Returns:
            True if registration successful, False otherwise

        Raises:
            APIRegistrationError: If registration fails:
                - Network error (API unreachable)
                - API returned error status (400, 409, 500)
                - Invalid JSON in response

        Example:
            >>> train_config = {
            ...     "train_id": "train-123",
            ...     "name": "Express Train",
            ...     "plugin": {"name": "adafruit_dcmotor_hat", "config": {"motor_port": 1}},
            ... }
            >>> try:
            ...     success = client.register_train(controller_uuid, train_config)
            ...     if success:
            ...         logger.info("Train registered successfully")
            ... except APIRegistrationError as e:
            ...     logger.error(f"Train registration failed: {e}")
        """
        try:
            url = f"{self.base_url}/api/controllers/{controller_uuid}/trains"

            response = requests.post(url, json=train_data, timeout=self.timeout)

            # Handle expected status codes
            if response.status_code == HTTP_CREATED:
                data = response.json()
                train_id = data.get("id", train_data.get("id", "unknown"))
                logger.info(
                    f"Registered train: id={train_id}, name={train_data.get('name', 'unknown')}"
                )
                return True

            if response.status_code == HTTP_CONFLICT:
                # Train already exists - this is acceptable
                logger.warning(
                    f"Train {train_data.get('id', 'unknown')} already registered (409 Conflict)"
                )
                return True

            if response.status_code == HTTP_BAD_REQUEST:
                error_detail = "unknown"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except Exception:
                    logger.exception("Exception occurred while parsing error detail")
                raise APIRegistrationError(f"Train registration failed (400): {error_detail}")

            # Other error status codes
            raise APIRegistrationError(
                f"Train registration failed with status {response.status_code}"
            )

        except RequestException as exc:
            raise APIRegistrationError(f"Train registration request failed: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise APIRegistrationError(f"Invalid train registration response: {exc}") from exc

    def download_runtime_config(self, controller_uuid: str) -> Optional[dict[str, Any]]:
        """Download runtime configuration for a controller.

        Calls GET /api/controllers/{uuid}/config to retrieve runtime configuration.
        The runtime config contains:
        - train_id: Which train this controller manages
        - mqtt_broker_host: MQTT broker hostname
        - mqtt_broker_port: MQTT broker port

        Expected Response (when configured):
            {
                "train_id": "1",
                "mqtt_broker_host": "192.168.1.10",
                "mqtt_broker_port": 1883
            }

        Args:
            controller_uuid: UUID of the controller (from registration)

        Returns:
            Runtime configuration dict if available, None if:
            - API returns 404 (controller registered but not assigned)
            - Network error occurs
            - Response is invalid JSON
            - Response is not a dictionary

        Note:
            This method adds the UUID to the returned config for consistency.
            The UUID is needed for subsequent API calls and cache validation.

        Example:
            >>> config = client.download_runtime_config(uuid)
            >>> if config:
            ...     print(f"Managing train {config['train_id']}")
            ... else:
            ...     print("Waiting for admin to assign train")
        """
        try:
            url = f"{self.base_url}/api/controllers/{controller_uuid}/config"
            response = requests.get(url, timeout=self.timeout)

            if response.status_code == HTTP_NOT_FOUND:
                logger.info(f"No runtime config available for UUID {controller_uuid}")
                return None

            response.raise_for_status()

            config_data = response.json()

            if not isinstance(config_data, dict):
                logger.error("Runtime config response is not a dictionary")
                return None

            # Ensure UUID is preserved in the config
            config_data["uuid"] = controller_uuid

            logger.info(f"Downloaded runtime config for UUID {controller_uuid}")
        except RequestException:
            logger.exception("Failed to download runtime config")
            return None
        except ValueError:
            logger.exception("Invalid JSON in runtime config response")
            return None
        else:
            return config_data

    def send_heartbeat(
        self,
        controller_uuid: str,
        config_hash: Optional[str] = None,
        version: Optional[str] = None,
        platform: Optional[str] = None,
        python_version: Optional[str] = None,
        memory_mb: Optional[int] = None,
        cpu_count: Optional[int] = None,
    ) -> bool:
        """Send heartbeat telemetry to central API.

        Edge controllers call this periodically to report health and system info.
        The Central API uses heartbeats to determine controller online/offline status.

        Fire-and-Forget Pattern:
            This method never raises exceptions. All errors are caught, logged as
            warnings, and result in False return value. This ensures the main
            application loop is never interrupted by heartbeat failures.

        Args:
            controller_uuid: UUID of this controller (from registration/runtime config)
            config_hash: MD5 hash of current runtime config (optional)
            version: Controller software version string (optional)
            platform: OS platform string, e.g., "Linux-5.15.0-aarch64" (optional)
            python_version: Python interpreter version, e.g., "3.11.2" (optional)
            memory_mb: Total RAM in megabytes (optional)
            cpu_count: Number of CPU cores (optional)

        Returns:
            True if heartbeat was accepted (200 OK), False otherwise

        Note:
            Only non-None fields are included in the request payload.
            The API accepts partial updates - any subset of fields is valid.

        Example:
            >>> success = client.send_heartbeat(
            ...     controller_uuid="550e8400-e29b-41d4-a716-446655440000",
            ...     config_hash="a1b2c3d4e5f6",
            ...     version="1.0.0",
            ...     platform="Linux-6.1.0-rpi4",
            ...     python_version="3.11.5",
            ...     memory_mb=3906,
            ...     cpu_count=4,
            ... )
            >>> if not success:
            ...     logger.warning("Heartbeat failed, will retry next interval")
        """
        try:
            url = f"{self.base_url}/api/controllers/{controller_uuid}/heartbeat"

            # Build payload - only include non-None fields
            payload: dict[str, Any] = {}
            if config_hash is not None:
                payload["config_hash"] = config_hash
            if version is not None:
                payload["version"] = version
            if platform is not None:
                payload["platform"] = platform
            if python_version is not None:
                payload["python_version"] = python_version
            if memory_mb is not None:
                payload["memory_mb"] = memory_mb
            if cpu_count is not None:
                payload["cpu_count"] = cpu_count

            response = requests.post(url, json=payload, timeout=self.timeout)

            if response.status_code == HTTP_OK:
                logger.debug(f"Heartbeat sent successfully for {controller_uuid}")
                return True

            if response.status_code == HTTP_NOT_FOUND:
                logger.warning(f"Heartbeat rejected: controller {controller_uuid} not found")
                return False

            # Other error status codes
            logger.warning(f"Heartbeat failed with status {response.status_code}")
            return False

        except (RequestException, Timeout, RequestsConnectionError) as exc:
            logger.warning(f"Heartbeat request failed: {exc}")
        else:
            return False
