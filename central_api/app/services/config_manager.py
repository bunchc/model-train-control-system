"""Configuration management business logic.

Orchestrates configuration loading, validation, and database synchronization.
Implements the Facade pattern over ConfigLoader and ConfigRepository.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, Union

from ..models.schemas import EdgeController, FullConfig, Plugin, Train, TrainStatus
from .config_loader import ConfigLoader, ConfigLoadError
from .config_repository import ConfigRepository


logger = logging.getLogger(__name__)

# UUID validation pattern (RFC 4122)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


class ConfigurationError(Exception):
    """Raised when configuration initialization fails.

    This is a terminal error - the application cannot start without
    valid configuration.
    """


class ConfigManager:
    """Orchestrates configuration management across YAML files and database.

    Responsibilities:
    - Load configuration from YAML
    - Synchronize configuration to database
    - Provide unified access to configuration data
    - Handle controller registration
    """

    def __init__(
        self,
        yaml_path: Union[str, Path, None] = None,
        db_path: Union[str, Path, None] = None,
        schema_path: Union[str, Path, None] = None,
    ) -> None:
        """Initialize configuration manager.

        Args:
            yaml_path: Path to config.yaml (defaults to ./config.yaml)
            db_path: Path to SQLite database (defaults to ./central_api_config.db)
            schema_path: Path to SQL schema file (defaults to ./config_schema.sql)

        Raises:
            ConfigurationError: If paths are invalid or initialization fails
        """
        # Use pathlib for modern path handling
        self.yaml_path = Path(yaml_path) if yaml_path else Path("config.yaml")
        self.db_path = Path(db_path) if db_path else Path("central_api_config.db")

        # Schema path is relative to this file
        default_schema = Path(__file__).parent / "config_schema.sql"
        self.schema_path = Path(schema_path) if schema_path else default_schema

        try:
            self.loader = ConfigLoader(self.yaml_path)
            self.repository = ConfigRepository(self.db_path, self.schema_path)
        except (ConfigLoadError, OSError) as initialization_error:
            msg = f"Failed to initialize ConfigManager: {initialization_error}"
            raise ConfigurationError(msg) from initialization_error

        # Load and sync configuration on initialization
        self._initialize_configuration()

    def _initialize_configuration(self) -> None:
        """Load YAML configuration and sync to database.

        Raises:
            ConfigurationError: If configuration cannot be loaded or synced
        """
        try:
            config = self.loader.load_config()
            self.loader.validate_config_structure(config)
            self._bootstrap_from_yaml(config)
        except ConfigLoadError as load_error:
            logger.exception("Configuration initialization failed")
            msg = f"Cannot load configuration: {load_error}"
            raise ConfigurationError(msg) from load_error

    def _bootstrap_from_yaml(self, config: dict[str, Any]) -> None:
        """Bootstrap database from YAML configuration.

        This is an idempotent operation - safe to run multiple times.
        Validates UUIDs and creates missing entries.

        Args:
            config: Parsed YAML configuration
        """
        logger.info("Bootstrapping configuration from YAML")

        # Bootstrap plugins
        for plugin_data in config.get("plugins", []):
            plugin_name = plugin_data["name"]
            existing_plugin = self.repository.get_plugin(plugin_name)

            if not existing_plugin:
                logger.info(f"Would insert plugin: {plugin_name} (not implemented)")

        # Bootstrap edge controllers
        for controller_data in config.get("edge_controllers", []):
            controller_id = self._ensure_valid_uuid(controller_data["id"], controller_data["name"])
            controller_name = controller_data["name"]
            controller_address = controller_data.get("address", "unknown")

            existing_controller = self.repository.get_edge_controller(controller_id)

            if not existing_controller:
                try:
                    self.repository.add_edge_controller(
                        controller_id, controller_name, controller_address
                    )
                except Exception:
                    logger.exception(f"Failed to add controller {controller_name}")

        logger.info("Configuration bootstrap complete")

    def _ensure_valid_uuid(self, id_value: Any, name: str) -> str:
        """Validate and normalize UUID value, generating one if needed.

        Args:
            id_value: Value to validate as UUID (or placeholder like "${UUID}")
            name: Name for error messages

        Returns:
            Validated UUID string in lowercase

        Raises:
            ConfigurationError: If UUID is invalid
        """
        if not isinstance(id_value, str):
            msg = f"Controller '{name}' has non-string ID: {type(id_value)}"
            raise ConfigurationError(msg)

        uuid_str = id_value.lower().strip()

        # Generate new UUID for placeholders or missing values
        if uuid_str in ("${uuid}", "", "none", "null"):
            import uuid

            uuid_str = str(uuid.uuid4())
            logger.info(f"Generated UUID for '{name}': {uuid_str}")
            return uuid_str

        if not UUID_PATTERN.match(uuid_str):
            msg = f"Controller '{name}' has invalid UUID format: {id_value}"
            raise ConfigurationError(msg)

        return uuid_str

    # Public API methods

    def add_edge_controller(self, controller_uuid: str, name: str, address: str) -> str:
        """Register a new edge controller.

        Args:
            controller_uuid: UUID for the controller (generated by caller)
            name: Human-readable controller name
            address: Network address (IP or hostname)

        Returns:
            UUID assigned to the new controller

        Raises:
            ConfigurationError: If registration fails
        """
        try:
            self.repository.add_edge_controller(controller_uuid, name, address)
        except Exception as registration_error:
            msg = f"Failed to register controller: {registration_error}"
            raise ConfigurationError(msg) from registration_error
        else:
            logger.info(f"Registered controller: {name} -> {controller_uuid}")
            return controller_uuid

    def add_train(
        self,
        controller_uuid: str,
        train_id: str,
        name: str,
        description: str = "",
        model: str = "",
        plugin_name: str = "dc_motor",
        plugin_config: Optional[dict] = None,
        reassign: bool = False,
    ) -> Train:
        """Register a new train for a controller.

        Args:
            controller_uuid: UUID of the edge controller managing this train
            train_id: Unique UUID for the train
            name: Human-readable train name
            description: Optional train description
            model: Optional model name/number
            plugin_name: Hardware plugin name (default: dc_motor)
            plugin_config: Plugin configuration dict
            reassign: If true, reassign train from existing controller

        Returns:
            Train model object representing the created train

        Raises:
            ConfigurationError: If controller doesn't exist or train creation fails

        Example:
            >>> train = manager.add_train(
            ...     controller_uuid="ctrl-123",
            ...     train_id="train-456",
            ...     name="Express Line",
            ...     plugin_config={"motor_port": 1}
            ... )
        """
        import json

        # Validate controller exists
        controller = self.repository.get_edge_controller(controller_uuid)
        if not controller:
            msg = f"Controller {controller_uuid} not found"
            raise ConfigurationError(msg)

        # Convert plugin config dict to JSON string
        if plugin_config is None:
            plugin_config = {}
        plugin_config_json = json.dumps(plugin_config)

        # Check if train already exists
        existing_train = self.repository.get_train(train_id)
        if existing_train and not reassign:
            msg = f"Train {train_id} already exists"
            raise ConfigurationError(msg)

        # Add train to database (or reassign if exists)
        try:
            if existing_train and reassign:
                # Reassign train to new controller
                logger.info(f"Reassigning train {train_id} to controller {controller_uuid}")
                self.repository.update_train_controller(train_id, controller_uuid)
                # Update other train details if provided
                self.repository.update_train(
                    train_id=train_id,
                    name=name,
                    description=description,
                    model=model,
                    plugin_name=plugin_name,
                    plugin_config=plugin_config_json,
                )
            else:
                # Add new train
                self.repository.add_train(
                    train_id=train_id,
                    name=name,
                    controller_id=controller_uuid,
                    description=description,
                    model=model,
                    plugin_name=plugin_name,
                    plugin_config=plugin_config_json,
                )
        except Exception as add_error:
            msg = f"Failed to add train {train_id}: {add_error}"
            raise ConfigurationError(msg) from add_error

        action = "Reassigned" if (existing_train and reassign) else "Registered"
        logger.info(f"{action} train: {name} ({train_id}) for controller {controller_uuid}")

        # Return Train model
        from app.models.schemas import TrainPlugin

        return Train(
            id=train_id,
            name=name,
            description=description,
            model=model,
            plugin=TrainPlugin(name=plugin_name, config=plugin_config),
        )

    def get_full_config(self) -> FullConfig:
        """Retrieve complete system configuration.

        Returns:
            FullConfig model with all plugins and edge controllers
        """
        # Load plugins from database
        plugin_rows = self.repository.get_all_plugins()
        plugins = [
            Plugin(
                name=row["name"],
                description=row.get("description"),
                config={},  # TODO: Parse JSON config from DB
            )
            for row in plugin_rows
        ]

        # Load edge controllers with their trains
        controller_rows = self.repository.get_all_edge_controllers()
        edge_controllers = []

        for controller_row in controller_rows:
            train_rows = self.repository.get_trains_for_controller(controller_row["id"])
            trains = [
                Train(
                    id=train_row["id"],
                    name=train_row["name"],
                    description=train_row.get("description"),
                    model=train_row.get("model"),
                    plugin={"name": train_row.get("plugin_name", "unknown"), "config": {}},
                )
                for train_row in train_rows
            ]

            edge_controllers.append(
                EdgeController(
                    id=controller_row["id"],
                    name=controller_row["name"],
                    description=controller_row.get("description"),
                    address=controller_row.get("address"),
                    enabled=bool(controller_row["enabled"]),
                    trains=trains,
                )
            )

        return FullConfig(plugins=plugins, edge_controllers=edge_controllers)

    def get_plugins(self) -> list[Plugin]:
        """Retrieve all plugins.

        Returns:
            List of Plugin models
        """
        plugin_rows = self.repository.get_all_plugins()
        return [
            Plugin(name=row["name"], description=row.get("description"), config={})
            for row in plugin_rows
        ]

    def get_edge_controllers(self) -> list[EdgeController]:
        """Retrieve all edge controllers.

        Returns:
            List of EdgeController models
        """
        controller_rows = self.repository.get_all_edge_controllers()
        edge_controllers = []

        for controller_row in controller_rows:
            train_rows = self.repository.get_trains_for_controller(controller_row["id"])
            trains = [
                Train(
                    id=train_row["id"],
                    name=train_row["name"],
                    description=train_row.get("description"),
                    model=train_row.get("model"),
                    plugin={"name": train_row.get("plugin_name", "unknown"), "config": {}},
                )
                for train_row in train_rows
            ]

            edge_controllers.append(
                EdgeController(
                    id=controller_row["id"],
                    name=controller_row["name"],
                    description=controller_row.get("description"),
                    address=controller_row.get("address"),
                    enabled=bool(controller_row["enabled"]),
                    trains=trains,
                )
            )

        return edge_controllers

    def get_edge_controller(self, edge_controller_id: str) -> Optional[EdgeController]:
        """Retrieve an edge controller by ID.

        Args:
            edge_controller_id: Edge controller identifier

        Returns:
            EdgeController model or None if not found
        """
        row = self.repository.get_edge_controller(edge_controller_id)
        if not row:
            return None

        train_rows = self.repository.get_trains_for_controller(row["id"])
        trains = [
            Train(
                id=train["id"],
                name=train["name"],
                description=train.get("description"),
                model=train.get("model"),
                plugin={
                    "name": train.get("plugin_name", "unknown"),
                    "config": json.loads(train.get("plugin_config", "{}")),
                },
            )
            for train in train_rows
        ]

        return EdgeController(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            address=row.get("address"),
            enabled=bool(row["enabled"]),
            trains=trains,
        )

    def get_trains(self) -> list[Train]:
        """Get all trains from database.

        Returns:
            List of Train models
        """
        train_rows = self.repository.get_all_trains()
        return [
            Train(
                id=train["id"],
                name=train["name"],
                description=train.get("description"),
                model=train.get("model"),
                plugin={
                    "name": train.get("plugin_name", "unknown"),
                    "config": json.loads(train.get("plugin_config", "{}")),
                },
            )
            for train in train_rows
        ]

    def get_train(self, train_id: str) -> Optional[Train]:
        """Retrieve a train by ID.

        Args:
            train_id: Train identifier

        Returns:
            Train model or None if not found
        """
        row = self.repository.get_train(train_id)
        if not row:
            return None

        return Train(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            model=row.get("model"),
            plugin={
                "name": row.get("plugin_name", "unknown"),
                "config": json.loads(row.get("plugin_config", "{}")),
            },
        )

    def update_train_status(
        self, train_id: str, speed: int, voltage: float, current: float, position: str
    ) -> None:
        """Update the status of a train.

        Args:
            train_id: UUID of the train
            speed: Current speed (0-100)
            voltage: Current voltage reading
            current: Current amperage reading
            position: Current track position/section
        """
        self.repository.update_train_status(train_id, speed, voltage, current, position)

    def get_train_status(self, train_id: str) -> Optional[TrainStatus]:
        """Retrieve current train status.

        Args:
            train_id: Train identifier

        Returns:
            TrainStatus model or None if not found
        """
        row = self.repository.get_train_status(train_id)
        if not row:
            logger.warning(f"No status found for train {train_id}")
            return None

        return TrainStatus(
            train_id=row["train_id"],
            speed=row["speed"],
            voltage=row["voltage"],
            current=row["current"],
            position=row["position"],
        )

    def get_last_updated(self) -> str:
        """Get last configuration update timestamp.

        Returns:
            Epoch timestamp as string, or empty string if not set
        """
        value = self.repository.get_metadata("last_updated")
        return value if value else ""

    def get_controller_for_train(self, train_id: str) -> Optional[EdgeController]:
        """Get the controller that manages a specific train.

        Args:
            train_id: UUID of the train

        Returns:
            EdgeController model or None if train not found

        Example:
            >>> controller = manager.get_controller_for_train("train-123")
            >>> print(f"Train managed by: {controller.name}")
        """
        train_data = self.repository.get_train(train_id)
        if not train_data:
            return None

        controller_id = train_data.get("edge_controller_id")
        if not controller_id:
            return None

        controller_data = self.repository.get_edge_controller(controller_id)
        if not controller_data:
            return None

        # Convert to EdgeController model
        from app.models.schemas import EdgeController

        return EdgeController(
            id=controller_data["id"],
            name=controller_data["name"],
            description=controller_data.get("description"),
            address=controller_data["address"],
            enabled=bool(controller_data.get("enabled", True)),
            trains=[],  # We don't need to populate trains for this use case
        )
