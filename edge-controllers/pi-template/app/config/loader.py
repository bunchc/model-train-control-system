"""Configuration loading and management."""

import logging
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded."""


class ConfigLoader:
    """Handles loading and parsing of configuration files."""

    def __init__(self, config_path: Path, cached_config_path: Path) -> None:
        """Initialize config loader.

        Args:
            config_path: Path to service configuration file
            cached_config_path: Path to cached runtime configuration file
        """
        self.config_path = config_path
        self.cached_config_path = cached_config_path

    def load_service_config(self) -> dict[str, Any]:
        """Load the edge-controller service configuration.

        Returns:
            Parsed YAML configuration

        Raises:
            ConfigLoadError: If config file cannot be read or parsed
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

    def load_cached_runtime_config(self) -> dict[str, Any] | None:
        """Load cached runtime configuration.

        Returns:
            Parsed runtime config if available, None otherwise
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

        except yaml.YAMLError as exc:
            logger.error(f"Invalid YAML in cached config: {exc}")
            return None
        except OSError as exc:
            logger.error(f"Failed to read cached config: {exc}")
            return None

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        """Save runtime configuration to cache file.

        Args:
            config: Configuration to save

        Raises:
            ConfigLoadError: If config cannot be saved
        """
        try:
            # Ensure directory exists
            self.cached_config_path.parent.mkdir(parents=True, exist_ok=True)

            with self.cached_config_path.open("w") as file_handle:
                yaml.safe_dump(config, file_handle)

            logger.info(f"Saved runtime config to {self.cached_config_path}")

        except OSError as exc:
            raise ConfigLoadError(f"Failed to save config: {exc}") from exc
