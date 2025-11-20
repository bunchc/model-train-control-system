"""Central API client for edge controller communication."""

import logging
import socket
import time
from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""


class APIConnectionError(APIClientError):
    """Raised when API connection fails."""


class APIRegistrationError(APIClientError):
    """Raised when controller registration fails."""


class CentralAPIClient:
    """Client for communicating with the central API."""

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
            host: API server hostname
            port: API server port
            timeout: Request timeout in seconds
            retry_delay: Delay between retries in seconds
            max_retries: Maximum number of retry attempts
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.base_url = f"http://{host}:{port}"

    def check_accessibility(self) -> bool:
        """Check if the central API is accessible.

        Returns:
            True if API responds to ping, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}/api/ping"
                response = requests.get(url, timeout=self.timeout)

                if response.status_code == 200:
                    logger.info("Central API is accessible")
                    return True

            except (RequestException, Timeout, RequestsConnectionError) as exc:
                logger.warning(
                    f"Central API not accessible (attempt {attempt + 1}/{self.max_retries}): {exc}"
                )

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)

        return False

    def check_controller_exists(self, controller_uuid: str) -> bool:
        """Check if a controller is registered with the central API.

        Args:
            controller_uuid: UUID of the controller

        Returns:
            True if controller exists, False otherwise
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

        Returns:
            UUID assigned by the central API

        Raises:
            APIRegistrationError: If registration fails
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

        Args:
            controller_uuid: UUID of the controller

        Returns:
            Runtime configuration dict if successful, None otherwise
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
