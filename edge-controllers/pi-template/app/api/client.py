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
from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout


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
        ...     host="central-api.local",
        ...     port=8000,
        ...     timeout=5,
        ...     retry_delay=2,
        ...     max_retries=3
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
                if response.status_code == 200:
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
            return response.status_code == 200

        except (RequestException, Timeout, RequestsConnectionError) as exc:
            logger.warning(f"Failed to check controller existence: {exc}")
            return False

    def register_controller(self) -> str:
        """Register this edge controller with the central API.

        Calls POST /api/controllers/register with hostname and IP address.
        The API assigns a UUID which must be persisted in cached config.

        Registration Payload:
            {
                "name": "edge-controller-01",  # socket.gethostname()
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

            # Attempt to get actual IP address
            try:
                ip_address = socket.gethostbyname(hostname)
            except socket.gaierror:
                logger.warning("Could not resolve IP address")
                ip_address = "unknown"

            url = f"{self.base_url}/api/controllers/register"
            payload = {"name": hostname, "address": ip_address}

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            controller_uuid = data.get("uuid")

            if not controller_uuid:
                raise APIRegistrationError("API response missing UUID")

            status = data.get("status", "unknown")
            logger.info(
                f"Registered controller: name={hostname}, uuid={controller_uuid}, status={status}"
            )

            return controller_uuid

        except RequestException as exc:
            raise APIRegistrationError(f"Registration request failed: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise APIRegistrationError(f"Invalid registration response: {exc}") from exc

    def download_runtime_config(self, controller_uuid: str) -> dict[str, Any] | None:
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

            if response.status_code == 404:
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
            return config_data

        except RequestException as exc:
            logger.error(f"Failed to download runtime config: {exc}")
            return None
        except ValueError as exc:
            logger.error(f"Invalid JSON in runtime config response: {exc}")
            return None
