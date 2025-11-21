"""YAML configuration file loading and validation.

This module handles file I/O for configuration, separated from business
logic and database operations following Single Responsibility Principle.
"""

import logging
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)

# Configuration validation constants
REQUIRED_TOP_LEVEL_KEYS = {"plugins", "edge_controllers"}
REQUIRED_PLUGIN_FIELDS = {"name"}
REQUIRED_CONTROLLER_FIELDS = {"id", "name"}


class ConfigLoadError(Exception):
    """Raised when configuration file cannot be loaded or parsed.

    This exception indicates a critical error during configuration
    initialization. The application cannot start without valid config.
    """


class ConfigLoader:
    """Handles loading and parsing of YAML configuration files.

    Separates file I/O from business logic and database operations.
    Provides validation of configuration structure.
    """

    def __init__(self, yaml_path: Path) -> None:
        """Initialize loader with YAML file path.

        Args:
            yaml_path: Path to config.yaml file
        """
        self.yaml_path = yaml_path

    def load_config(self) -> dict[str, Any]:
        """Load and parse YAML configuration file.

        Returns:
            Parsed configuration dictionary

        Raises:
            ConfigLoadError: If file doesn't exist, is unreadable, or invalid
        """
        if not self.yaml_path.exists():
            msg = f"Config file not found: {self.yaml_path}"
            raise ConfigLoadError(msg)

        try:
            with self.yaml_path.open("r") as config_file:
                config = yaml.safe_load(config_file)

            if not isinstance(config, dict):
                msg = "Config file must contain a YAML dictionary"
                raise ConfigLoadError(msg)

        except yaml.YAMLError as yaml_error:
            msg = f"Invalid YAML syntax: {yaml_error}"
            raise ConfigLoadError(msg) from yaml_error
        except OSError as io_error:
            msg = f"Cannot read config file: {io_error}"
            raise ConfigLoadError(msg) from io_error
        else:
            logger.info(f"Loaded configuration from {self.yaml_path}")
            return config

    def validate_config_structure(self, config: dict[str, Any]) -> None:
        """Validate configuration has required top-level keys and structure.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigLoadError: If required keys are missing or types invalid
        """
        # Check top-level keys
        missing_keys = REQUIRED_TOP_LEVEL_KEYS - config.keys()
        if missing_keys:
            msg = f"Configuration missing required keys: {missing_keys}"
            raise ConfigLoadError(msg)

        # Validate plugins structure
        if not isinstance(config["plugins"], list):
            msg = "'plugins' must be a list"
            raise ConfigLoadError(msg)

        for index, plugin in enumerate(config["plugins"]):
            if not isinstance(plugin, dict):
                msg = f"Plugin at index {index} must be a dict"
                raise ConfigLoadError(msg)
            missing_plugin_fields = REQUIRED_PLUGIN_FIELDS - plugin.keys()
            if missing_plugin_fields:
                msg = f"Plugin at index {index} missing fields: {missing_plugin_fields}"
                raise ConfigLoadError(msg)

        # Validate edge_controllers structure
        if not isinstance(config["edge_controllers"], list):
            msg = "'edge_controllers' must be a list"
            raise ConfigLoadError(msg)

        for index, controller in enumerate(config["edge_controllers"]):
            if not isinstance(controller, dict):
                msg = f"Controller at index {index} must be a dict"
                raise ConfigLoadError(msg)
            missing_controller_fields = REQUIRED_CONTROLLER_FIELDS - controller.keys()
            if missing_controller_fields:
                msg = f"Controller at index {index} missing fields: {missing_controller_fields}"
                raise ConfigLoadError(msg)
