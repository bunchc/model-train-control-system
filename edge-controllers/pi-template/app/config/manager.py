"""Configuration manager orchestrating config loading and API interaction."""

import logging
from pathlib import Path
from typing import Any

from api.client import APIRegistrationError, CentralAPIClient
from config.loader import ConfigLoader, ConfigLoadError


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration cannot be initialized."""


class ConfigManager:
    """Manages configuration lifecycle for edge controller."""

    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to service configuration file
            cached_config_path: Path to cached runtime configuration file
        """
        self.loader = ConfigLoader(config_path, cached_config_path)
        self.api_client: CentralAPIClient | None = None
        self._service_config: dict[str, Any] | None = None
        self._runtime_config: dict[str, Any] | None = None

    def initialize(self) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Initialize and load both service and runtime configurations.

        Returns:
            Tuple of (service_config, runtime_config).
            runtime_config may be None if waiting for admin to assign trains.

        Raises:
            ConfigurationError: If initialization fails critically
        """
        # Load service config
        try:
            self._service_config = self.loader.load_service_config()
        except ConfigLoadError as exc:
            raise ConfigurationError(f"Failed to load service config: {exc}") from exc

        # Initialize API client
        api_host = self._service_config.get("central_api_host", "localhost")
        api_port = self._service_config.get("central_api_port", 8000)
        self.api_client = CentralAPIClient(host=api_host, port=api_port)

        # Check API accessibility
        if not self.api_client.check_accessibility():
            logger.warning("Central API not accessible, attempting to use cached config")
            return self._use_cached_config_fallback()

        # Try to load and use existing config
        cached_config = self.loader.load_cached_runtime_config()

        if cached_config and "uuid" in cached_config:
            return self._refresh_existing_controller(cached_config)

        # No cached config - register as new controller
        return self._register_new_controller()

    def _use_cached_config_fallback(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Fallback to cached config when API is unavailable.

        Returns:
            Tuple of (service_config, runtime_config)

        Raises:
            ConfigurationError: If no cached config exists
        """
        runtime_config = self.loader.load_cached_runtime_config()

        if runtime_config:
            logger.warning("Using cached runtime config (API unavailable)")
            return self._service_config, runtime_config

        raise ConfigurationError(
            "Central API is not accessible and no cached runtime config exists"
        )

    def _refresh_existing_controller(
        self, cached_config: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Refresh configuration for existing controller.

        Args:
            cached_config: Previously cached configuration

        Returns:
            Tuple of (service_config, runtime_config)
        """
        controller_uuid = cached_config["uuid"]
        logger.info(f"Found cached config with UUID {controller_uuid}")

        # Try to download fresh config
        fresh_config = self.api_client.download_runtime_config(controller_uuid)

        if fresh_config:
            try:
                self.loader.save_runtime_config(fresh_config)
                logger.info("Runtime config updated from central API")
                return self._service_config, fresh_config
            except ConfigLoadError as exc:
                logger.error(f"Failed to save fresh config: {exc}")

        # Download failed - use cached if it has required fields
        if self._is_runtime_config_complete(cached_config):
            logger.warning("Using cached runtime config (download failed)")
            return self._service_config, cached_config

        logger.warning("Cached config incomplete, running without train config")
        return self._service_config, None

    def _register_new_controller(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Register as new controller with central API.

        Returns:
            Tuple of (service_config, runtime_config)

        Raises:
            ConfigurationError: If registration fails
        """
        logger.info("No cached UUID found, registering with central API")

        try:
            controller_uuid = self.api_client.register_controller()
        except APIRegistrationError as exc:
            raise ConfigurationError(f"Failed to register with central API: {exc}") from exc

        # Try to download runtime config
        runtime_config = self.api_client.download_runtime_config(controller_uuid)

        if runtime_config:
            try:
                self.loader.save_runtime_config(runtime_config)
                logger.info("Downloaded runtime config after registration")
                return self._service_config, runtime_config
            except ConfigLoadError as exc:
                logger.error(f"Failed to save runtime config: {exc}")

        # Normal case: registered but admin hasn't assigned trains yet
        logger.info(
            "Registered successfully but no runtime config available yet. "
            "Waiting for administrator to assign trains to this controller."
        )
        return self._service_config, None

    @staticmethod
    def _is_runtime_config_complete(config: dict[str, Any]) -> bool:
        """Check if runtime config has all required fields.

        Args:
            config: Runtime configuration to validate

        Returns:
            True if config is complete, False otherwise
        """
        required_fields = ["train_id", "mqtt_broker"]
        return all(field in config for field in required_fields)

    @property
    def service_config(self) -> dict[str, Any]:
        """Get service configuration.

        Raises:
            ConfigurationError: If configuration not initialized
        """
        if self._service_config is None:
            raise ConfigurationError("Configuration not initialized")
        return self._service_config

    @property
    def runtime_config(self) -> dict[str, Any] | None:
        """Get runtime configuration."""
        return self._runtime_config
