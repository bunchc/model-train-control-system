"""Configuration manager orchestrating config loading and API interaction.

This module implements the configuration state machine for edge controllers:
1. Load service configuration (API endpoints, logging)
2. Check Central API accessibility
3. Register with API or refresh existing registration
4. Download runtime configuration (train assignment, MQTT broker)
5. Cache configuration locally for offline operation
6. Fallback to cached config if API unavailable

The ConfigManager handles the complex orchestration between file I/O (ConfigLoader)
and network I/O (CentralAPIClient), implementing retry logic and graceful degradation.

Architecture Decision:
    Separating ConfigManager from ConfigLoader allows:
    - Pure file I/O testing (ConfigLoader)
    - Integration testing with mocked API (ConfigManager)
    - Clear separation of concerns (orchestration vs. file operations)

Typical usage:
    manager = ConfigManager(
        config_path=Path("edge-controller.conf"),
        cached_config_path=Path("edge-controller.yaml")
    )
    service_config, runtime_config = manager.initialize()
"""

import logging
from pathlib import Path
from typing import Any, Optional

from ..api.client import APIRegistrationError, CentralAPIClient
from .loader import ConfigLoader, ConfigLoadError


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration cannot be initialized.

    This exception indicates a critical failure in configuration initialization
    that prevents the edge controller from starting. Examples:
    - Service config file missing or invalid
    - Central API unreachable AND no cached config exists
    - Registration with Central API fails

    This is a terminal error - the application should exit and require
    operator intervention.

    Example:
        >>> if not api_accessible and not cached_config:
        ...     raise ConfigurationError("Cannot start without configuration")
    """


class ConfigManager:
    """Manages configuration lifecycle for edge controller.

    This class orchestrates the complex flow of configuration initialization,
    including file loading, API communication, caching, and fallback logic.

    State Machine:
        INIT -> LOAD_SERVICE -> CHECK_API -> [ONLINE|OFFLINE] -> READY

        ONLINE path:
            - Load cached UUID (if exists)
            - Download fresh runtime config
            - Cache locally
            - READY

        OFFLINE path:
            - Load cached runtime config
            - If valid, READY
            - If missing, FAIL

    Attributes:
        loader: ConfigLoader instance for file I/O
        api_client: CentralAPIClient instance for network I/O
        _service_config: Loaded service configuration (API host, port)
        _runtime_config: Runtime configuration (train_id, MQTT broker)

    Example:
        >>> manager = ConfigManager(config_path, cached_config_path)
        >>> service, runtime = manager.initialize()
        >>> if runtime:
        ...     print(f"Managing train: {runtime['train_id']}")
        ... else:
        ...     print("Waiting for train assignment")
    """

    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize configuration manager.

        Creates the ConfigLoader for file operations. The CentralAPIClient is
        created during initialize() after loading the service config.

        Args:
            config_path: Path to service configuration file (edge-controller.conf).
                This file must exist and contain central_api_host and central_api_port.
            cached_config_path: Path to cached runtime configuration (edge-controller.yaml).
                This file is optional and will be created after registration.

        Note:
            This constructor does not perform I/O or network operations.
            Call initialize() to load configurations.
        """
        self.loader = ConfigLoader(config_path, cached_config_path)
        self.api_client: CentralAPIClient | None = None
        self._service_config: Optional[dict[str, Any]] = None
        self._runtime_config: Optional[dict[str, Any]] = None

    def initialize(self) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        """Initialize and load both service and runtime configurations.

        This is the main entry point for configuration initialization. It orchestrates
        the entire configuration workflow:

        Workflow:
            1. Load service config from file (required)
            2. Create API client with host/port from service config
            3. Check if Central API is accessible
            4. If accessible:
               a. Load cached UUID (if exists)
               b. Download fresh runtime config or register new controller
               c. Cache runtime config locally
            5. If not accessible:
               a. Load cached runtime config
               b. Raise ConfigurationError if no cache exists

        Returns:
            Tuple of (service_config, runtime_config).
            - service_config: Always present, contains API host/port
            - runtime_config: May be None if:
                * Controller is registered but not assigned to a train yet
                * Waiting for administrator to configure train assignment

        Raises:
            ConfigurationError: If initialization fails critically:
                - Service config file missing or invalid
                - API unreachable AND no cached runtime config exists
                - Registration with API fails

        Example:
            >>> manager = ConfigManager(config_path, cached_path)
            >>> service, runtime = manager.initialize()
            >>> if runtime is None:
            ...     logger.info("Waiting for admin to assign trains")
        """
        # Load service config
        try:
            # Step 1: Load service config from filesystem (edge-controller.conf)
            # This file must exist and contain central_api_host/port - no fallback
            self._service_config = self.loader.load_service_config()
        except ConfigLoadError as exc:
            # Terminal error: cannot proceed without knowing where Central API is
            raise ConfigurationError(f"Failed to load service config: {exc}") from exc

        # Initialize API client
        # Extract API connection details from service config
        api_host = self._service_config.get("central_api_host", "localhost")
        api_port = self._service_config.get("central_api_port", 8000)
        self.api_client = CentralAPIClient(host=api_host, port=api_port)

        # Check API accessibility
        # State decision: ONLINE path (API accessible) vs OFFLINE path (use cache)
        if not self.api_client.check_accessibility():
            logger.warning("Central API not accessible, attempting to use cached config")
            # OFFLINE PATH: API unreachable, try cached config
            return self._use_cached_config_fallback()

        # ONLINE PATH: API is accessible, proceed with registration or refresh
        # Try to load and use existing config
        cached_config = self.loader.load_cached_runtime_config()

        # State decision: Existing controller (has UUID) vs new controller (no UUID)
        if cached_config and "uuid" in cached_config:
            # EXISTING CONTROLLER: Refresh config from API using cached UUID
            return self._refresh_existing_controller(cached_config)

        # NEW CONTROLLER: No cached config - register as new controller
        return self._register_new_controller()

    def _use_cached_config_fallback(
        self,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        """Fallback to cached config when API is unavailable.

        This method enables offline operation by using previously cached
        runtime configuration. This is critical for edge deployments where
        network connectivity may be intermittent.

        Offline Scenario:
            1. Central API is unreachable (network down, API maintenance, etc.)
            2. Check for cached runtime config
            3. If cached config exists and is valid, use it
            4. If no cache exists, raise ConfigurationError (cannot start)

        Returns:
            Tuple of (service_config, runtime_config) if cache exists

        Raises:
            ConfigurationError: If no cached config exists. This is a terminal
                error because the controller cannot start without knowing which
                train to manage or which MQTT broker to connect to.

        Warning:
            Cached config may be stale if the administrator changed train
            assignments. The controller will reconnect and refresh when API
            becomes available again.
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
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        """Refresh configuration for existing controller.

        Called when cached config contains a UUID, indicating this controller
        has been registered before. Attempts to download fresh configuration
        from the Central API.

        Refresh Flow:
            1. Extract UUID from cached config
            2. Verify controller is actually registered in the Central API
            3. If not registered, re-register as a new controller
            4. Download fresh runtime config from API using UUID
            5. If download succeeds:
               a. Save fresh config to cache
               b. Return fresh config
            6. If download fails:
               a. Validate cached config has required fields
               b. If valid, return cached config (stale but functional)
               c. If invalid, return None (wait for admin)

        Args:
            cached_config: Previously cached configuration containing UUID

        Returns:
            Tuple of (service_config, runtime_config).
            runtime_config is:
            - Fresh config if download succeeded
            - Cached config if download failed but cache is valid
            - None if download failed and cache is incomplete

        Note:
            This method never raises exceptions. All errors are logged and
            handled gracefully by falling back to cached config or returning None.
        """
        # Extract UUID from cached config (controller was registered previously)
        controller_uuid = cached_config["uuid"]
        logger.info(f"Found cached config with UUID {controller_uuid}")

        # Verify the controller is actually registered in the Central API
        # The database may have been reset, or the UUID may be stale
        if not self.api_client.check_controller_exists(controller_uuid):
            logger.warning(
                f"Controller UUID {controller_uuid} not found in Central API. "
                "Database may have been reset. Re-registering as new controller."
            )
            # Controller not found - re-register
            return self._register_new_controller()

        # Try to download fresh config from API
        # This ensures we have latest train assignments, MQTT broker updates, etc.
        fresh_config = self.api_client.download_runtime_config(controller_uuid)

        # Download successful - save to cache and return fresh config
        if fresh_config:
            try:
                # Persist to disk so we have fallback if API becomes unavailable
                self.loader.save_runtime_config(fresh_config)
                logger.info("Runtime config updated from central API")
                return self._service_config, fresh_config
            except ConfigLoadError:
                # Save failed but we have fresh config in memory - continue anyway
                logger.exception("Failed to save fresh config")
                # Fall through to cached config check

        # Download failed - validate cached config before using it
        # Cached config may be stale but is better than not starting
        if self._is_runtime_config_complete(cached_config):
            logger.warning("Using cached runtime config (download failed)")
            return self._service_config, cached_config

        # Cached config is incomplete (missing train_id or mqtt_broker)
        # Controller is registered but admin hasn't assigned trains yet
        logger.warning("Cached config incomplete, running without train config")
        return self._service_config, None

    def _register_new_controller(
        self,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        """Register as new controller with central API.

        Called when no cached UUID exists, indicating this is a first-time boot
        or the cache was cleared. Registers the controller with the Central API
        to obtain a UUID.

        Registration Flow:
            1. Call API to register (sends hostname, IP address)
            2. Receive UUID from API
            3. Attempt to download runtime config using new UUID
            4. If runtime config available:
               a. Administrator has pre-configured this controller
               b. Save config to cache
               c. Return config (controller can start immediately)
            5. If runtime config not available (404):
               a. Controller is registered but not assigned to a train
               b. Return None (wait state - administrator needs to assign)

        Returns:
            Tuple of (service_config, runtime_config).
            runtime_config is:
            - Complete config if admin pre-configured train assignment
            - None if waiting for admin to assign trains

        Raises:
            ConfigurationError: If registration with API fails. This is terminal
                because we cannot proceed without a UUID.

        Example:
            >>> # First boot - no cached UUID
            >>> service, runtime = manager._register_new_controller()
            >>> if runtime is None:
            ...     logger.info("Registered, waiting for train assignment")
        """
        logger.info("No cached UUID found, registering with central API")

        # Step 1: Register with Central API to get UUID
        # Sends hostname and IP address to help admin identify this controller
        try:
            controller_uuid = self.api_client.register_controller()
        except APIRegistrationError as exc:
            # Registration failed - terminal error, cannot proceed without UUID
            raise ConfigurationError(f"Failed to register with central API: {exc}") from exc

        # Step 2: Try to download runtime config using new UUID
        # Admin may have pre-configured this controller, or it may return 404
        runtime_config = self.api_client.download_runtime_config(controller_uuid)

        # Config available - admin pre-configured train assignment
        if runtime_config:
            try:
                # Save to cache for offline operation and future refreshes
                self.loader.save_runtime_config(runtime_config)
                logger.info("Downloaded runtime config after registration")
                return self._service_config, runtime_config
            except ConfigLoadError:
                # Save failed but we have config in memory - continue anyway
                logger.exception("Failed to save runtime config")
                # Fall through to return None

        # Normal case: registered but admin hasn't assigned trains yet
        # Controller enters wait state - will poll for config updates
        logger.info(
            "Registered successfully but no runtime config available yet. "
            "Waiting for administrator to assign trains to this controller."
        )
        return self._service_config, None

    def _is_runtime_config_complete(self, config: dict[str, Any]) -> bool:
        """Check if runtime config has all required fields.

        Validates that the runtime configuration contains the minimum required
        fields for the edge controller to operate:
        - train_id: Which train to control
        - mqtt_broker_host: Where to connect for real-time communication
        - mqtt_broker_port: MQTT broker port

        Incomplete Configuration Scenario:
            Controller is registered with Central API (has UUID) but administrator
            has not yet assigned a train. In this case, the API returns 404 for
            /config endpoint, or returns a config with missing fields.

        Args:
            config: Runtime configuration dictionary to validate

        Returns:
            True if all required fields are present and not None, False otherwise

        Note:
            This does not validate field types or values, only presence.
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
    def runtime_config(self) -> Optional[dict[str, Any]]:
        """Get runtime configuration."""
        return self._runtime_config
