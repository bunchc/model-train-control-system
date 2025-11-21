"""Configuration file loading and validation.

This module handles all file I/O for edge controller configuration, including:
- Loading service configuration from YAML files
- Caching runtime configuration locally
- Validating configuration structure

The loader is stateless and does not perform any network operations.
All network communication is delegated to the ConfigManager and APIClient.

Architecture Decision:
    File I/O is separated from network I/O to enable:
    - Testing without mocking the filesystem
    - Configuration loading from different sources (files, env vars, secrets)
    - Clear separation of concerns (SRP)

Typical usage:
    loader = ConfigLoader(
        config_path=Path("edge-controller.conf"),
        cached_config_path=Path("edge-controller.yaml")
    )
    service_config = loader.load_service_config()
    runtime_config = loader.load_cached_runtime_config()
"""

import logging
from pathlib import Path
from typing import Any, Optional

import yaml


logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded or parsed.

    This exception is raised for:
    - Missing configuration files
    - Invalid YAML syntax
    - I/O errors during file operations
    - Configuration validation failures

    Example:
        >>> if not config_path.exists():
        ...     raise ConfigLoadError(f"Config file not found: {config_path}")
    """


class ConfigLoader:
    """Handles loading and parsing of configuration files.

    This class is responsible for all file-based configuration operations.
    It maintains no state beyond the file paths and performs no network I/O.

    Architecture Decision:
        We separated file I/O from network I/O to enable testing without
        mocking the filesystem and to allow configuration to be loaded from
        different sources in the future (environment variables, secrets managers).

    Attributes:
        config_path: Path to service configuration file (edge-controller.conf)
        cached_config_path: Path to cached runtime config (edge-controller.yaml)

    Example:
        >>> loader = ConfigLoader(
        ...     config_path=Path("edge-controller.conf"),
        ...     cached_config_path=Path("edge-controller.yaml"),
        ... )
        >>> service_config = loader.load_service_config()
        >>> print(service_config["central_api_host"])
        'localhost'
    """

    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize configuration loader.

        Args:
            config_path: Path to service configuration file. This file contains
                static configuration like API endpoints and should be versioned.
            cached_config_path: Path to cached runtime configuration. This file
                is dynamically generated and should NOT be versioned.

        Note:
            Neither file is required to exist at initialization time.
            Existence checks happen during load operations.
        """
        self.config_path = config_path
        self.cached_config_path = cached_config_path

    def load_service_config(self) -> dict[str, Any]:
        """Load the edge-controller service configuration.

        This loads the static, version-controlled configuration that defines
        how the edge controller connects to the central API and other services.

        The service config typically contains:
        - central_api_host: Hostname or IP of central API
        - central_api_port: Port number for central API
        - logging_level: Log verbosity (DEBUG|INFO|WARNING|ERROR)

        Returns:
            Parsed YAML configuration as a dictionary

        Raises:
            ConfigLoadError: If config file is missing, unreadable, or contains
                invalid YAML syntax, or is not a valid dictionary

        Example:
            >>> loader.load_service_config()
            {'central_api_host': 'localhost', 'central_api_port': 8000}
        """
        try:
            if not self.config_path.exists():
                raise ConfigLoadError(f"Config file not found: {self.config_path}")

            with self.config_path.open("r") as file_handle:
                config = yaml.safe_load(file_handle)

            if not isinstance(config, dict):
                raise ConfigLoadError("Config file must contain a YAML dictionary")

            return config

        except yaml.YAMLError as exc:
            raise ConfigLoadError(f"Invalid YAML in config file: {exc}") from exc
        except OSError as exc:
            raise ConfigLoadError(f"Failed to read config file: {exc}") from exc

    def load_cached_runtime_config(self) -> Optional[dict[str, Any]]:
        """Load cached runtime configuration.

        Runtime configuration is downloaded from the central API and cached
        locally. This allows the controller to start even if the API is
        temporarily unavailable.

        The runtime config typically contains:
        - uuid: Controller's unique identifier
        - train_id: ID of the train this controller manages
        - mqtt_broker: MQTT connection details (host, port, credentials)
        - status_topic: MQTT topic for publishing status
        - commands_topic: MQTT topic for receiving commands

        Returns:
            Parsed runtime config if available, None if file doesn't exist.
            Returns None rather than raising to allow graceful degradation.

        Note:
            This method logs warnings but does not raise exceptions for
            missing files, as missing cache is a valid state (first boot).
            Invalid YAML or I/O errors are logged but return None.

        Example:
            >>> config = loader.load_cached_runtime_config()
            >>> if config:
            ...     print(f"Train ID: {config['train_id']}")
            ... else:
            ...     print("No cached config, need to register")
        """
        if not self.cached_config_path.exists():
            logger.info(f"No cached config found at {self.cached_config_path}")
            return None

        try:
            with self.cached_config_path.open("r") as file_handle:
                config = yaml.safe_load(file_handle)

            if not isinstance(config, dict):
                logger.warning("Cached config is not a valid dictionary")
                return None

            return config

        except yaml.YAMLError:
            logger.exception("Invalid YAML in cached config")
            return None
        except OSError:
            logger.exception("Failed to read cached config")
            return None

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        """Save runtime configuration to cache file.

        This is called after successfully downloading configuration from the
        central API. The cached config allows offline operation and faster
        startup on subsequent boots.

        Args:
            config: Configuration dictionary to save. Must include 'uuid' key
                at minimum. Typically contains all runtime configuration fields.

        Raises:
            ConfigLoadError: If config cannot be saved to disk due to:
                - Insufficient permissions
                - Disk full
                - Invalid path
                - Other I/O errors

        Side Effects:
            - Creates parent directories if they don't exist
            - Overwrites existing cached config file
            - File is written with safe YAML dumper (no Python objects)

        Example:
            >>> loader.save_runtime_config(
            ...     {
            ...         "uuid": "abc-123",
            ...         "train_id": "train-1",
            ...         "mqtt_broker": {"host": "mqtt", "port": 1883},
            ...     }
            ... )
        """
        try:
            # Ensure directory exists
            self.cached_config_path.parent.mkdir(parents=True, exist_ok=True)

            with self.cached_config_path.open("w") as file_handle:
                yaml.safe_dump(config, file_handle)

            logger.info(f"Saved runtime config to {self.cached_config_path}")

        except OSError as exc:
            raise ConfigLoadError(f"Failed to save config: {exc}") from exc
