"""Database operations for configuration storage.

This module implements the Repository pattern, separating data access
from business logic. All SQLite interactions are contained here.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger(__name__)


class ConfigRepository:
    """Database repository for configuration persistence.

    Handles all SQLite database operations for storing and retrieving
    configuration data. Implements the Repository pattern.
    """

    def __init__(self, db_path: Path, schema_path: Path) -> None:
        """Initialize repository with database connection.

        Args:
            db_path: Path to SQLite database file
            schema_path: Path to SQL schema file for initialization

        Raises:
            sqlite3.Error: If database connection fails
        """
        self.db_path = db_path
        self.schema_path = schema_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist.

        Executes schema SQL script to initialize database structure.
        Safe to call multiple times - CREATE TABLE IF NOT EXISTS.
        """
        if not self.db_path.exists():
            logger.info(f"Creating new database at {self.db_path}")

        conn = sqlite3.connect(str(self.db_path))
        try:
            if self.schema_path.exists():
                with self.schema_path.open("r") as schema_file:
                    conn.executescript(schema_file.read())
                conn.commit()
                logger.info("Database schema initialized")
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
        finally:
            conn.close()

    def get_edge_controller(self, controller_id: str) -> Optional[dict[str, Any]]:
        """Retrieve edge controller by ID.

        Args:
            controller_id: Edge controller identifier

        Returns:
            Dictionary with controller data or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM edge_controllers WHERE id = ?", (controller_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_edge_controllers(self) -> list[dict[str, Any]]:
        """Retrieve all edge controllers.

        Returns:
            List of controller configuration dicts
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM edge_controllers")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_edge_controller(self, controller_id: str, name: str, address: str) -> None:
        """Add new edge controller to database.

        Args:
            controller_id: Unique UUID for controller
            name: Human-readable name
            address: Network address (IP or hostname)

        Raises:
            sqlite3.IntegrityError: If controller_id already exists
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT INTO edge_controllers
                    (id, name, address, enabled, first_seen, last_seen, status)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'online')
                """,
                (controller_id, name, address),
            )
            conn.commit()
            logger.info(f"Added edge controller: {name} ({controller_id})")
        finally:
            conn.close()

    def update_controller_heartbeat(
        self,
        controller_id: str,
        config_hash: Optional[str] = None,
        version: Optional[str] = None,
        platform: Optional[str] = None,
        python_version: Optional[str] = None,
        memory_mb: Optional[int] = None,
        cpu_count: Optional[int] = None,
    ) -> bool:
        """Update edge controller heartbeat and telemetry data.

        Always updates last_seen and status. Optionally updates other
        telemetry fields if provided.

        Args:
            controller_id: UUID of controller
            config_hash: MD5 hash of current configuration
            version: Controller software version
            platform: OS platform string
            python_version: Python interpreter version
            memory_mb: Total system memory in MB
            cpu_count: Number of CPU cores

        Returns:
            True if update successful, False if controller not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            # Always update last_seen and status
            updates = ["last_seen = CURRENT_TIMESTAMP", "status = 'online'"]
            params: list[Any] = []

            # Add optional telemetry fields
            if config_hash is not None:
                updates.append("config_hash = ?")
                params.append(config_hash)
            if version is not None:
                updates.append("version = ?")
                params.append(version)
            if platform is not None:
                updates.append("platform = ?")
                params.append(platform)
            if python_version is not None:
                updates.append("python_version = ?")
                params.append(python_version)
            if memory_mb is not None:
                updates.append("memory_mb = ?")
                params.append(memory_mb)
            if cpu_count is not None:
                updates.append("cpu_count = ?")
                params.append(cpu_count)

            # Whitelist allowed columns for heartbeat/telemetry updates
            allowed_columns = {
                "last_seen",
                "status",
                "config_hash",
                "version",
                "platform",
                "python_version",
                "memory_mb",
                "cpu_count",
            }
            safe_updates = [u for u in updates if u.split("=")[0].strip() in allowed_columns]
            if len(safe_updates) != len(updates):
                msg = "Invalid column in update_fields for edge_controllers"
                raise ValueError(msg)
            params.append(controller_id)
            set_clause = ", ".join(safe_updates)
            # Safe: set_clause is built only from whitelisted columns, values are parameterized
            query = f"UPDATE edge_controllers SET {set_clause} WHERE id = ?"  # nosec
            cursor = conn.execute(query, params)
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"Heartbeat for unknown controller: {controller_id}")
                return False
            logger.debug(f"Heartbeat received from controller: {controller_id}")
            return True

        except sqlite3.Error:
            logger.exception(f"Failed to update heartbeat for controller {controller_id}")
            return False
        finally:
            conn.close()

    def update_edge_controller(
        self,
        controller_id: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """Update edge controller fields.

        Args:
            controller_id: UUID of controller to update
            name: New name (optional)
            address: New address (optional)
            enabled: New enabled state (optional)
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if address is not None:
                updates.append("address = ?")
                params.append(address)
            if enabled is not None:
                updates.append("enabled = ?")
                params.append(int(enabled))

            if updates:
                params.append(controller_id)
                allowed_columns = {
                    "name",
                    "address",
                    "enabled",
                    "status",
                    "last_heartbeat",
                    "platform",
                    "python_version",
                }
                safe_updates = [u for u in updates if u.split("=")[0].strip() in allowed_columns]
                if len(safe_updates) != len(updates):
                    msg = "Invalid column in update_fields for edge_controllers"
                    raise ValueError(msg)
                set_clause = ", ".join(safe_updates)
                # Safe: set_clause is built only from whitelisted columns, values are parameterized
                query = f"UPDATE edge_controllers SET {set_clause} WHERE id = ?"  # nosec
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Updated edge controller: {controller_id}")
        finally:
            conn.close()

    def update_train_controller(self, train_id: str, new_controller_id: str) -> bool:
        """Update the controller assignment for a train.

        Args:
            train_id: UUID of train to reassign
            new_controller_id: UUID of new controller

        Returns:
            True if update successful
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "UPDATE trains SET edge_controller_id = ? WHERE id = ?",
                (new_controller_id, train_id),
            )
            conn.commit()
            logger.info(f"Reassigned train {train_id} to controller {new_controller_id}")
        except sqlite3.Error:
            logger.exception(f"Failed to reassign train {train_id}")
            return False
        else:
            return True
        finally:
            conn.close()

    def update_train(
        self,
        train_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        model: Optional[str] = None,
        plugin_name: Optional[str] = None,
        plugin_config: Optional[str] = None,
        invert_directions: Optional[bool] = None,
    ) -> bool:
        """Update train fields.

        Args:
            train_id: UUID of train to update
            name: New name (optional)
            description: New description (optional)
            model: New model (optional)
            plugin_name: New plugin name (optional)
            plugin_config: New plugin config JSON (optional)
            invert_directions: Invert motor direction (optional)

        Returns:
            True if update successful
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if model is not None:
                updates.append("model = ?")
                params.append(model)
            if plugin_name is not None:
                updates.append("plugin_name = ?")
                params.append(plugin_name)
            if plugin_config is not None:
                updates.append("plugin_config = ?")
                params.append(plugin_config)
            if invert_directions is not None:
                updates.append("invert_directions = ?")
                params.append(1 if invert_directions else 0)

            if updates:
                allowed_columns = {
                    "name",
                    "description",
                    "model",
                    "status",
                    "controller_id",
                    "last_updated",
                    "invert_directions",
                }
                safe_updates = [u for u in updates if u.split("=")[0].strip() in allowed_columns]
                if len(safe_updates) != len(updates):
                    msg = "Invalid column in update_fields for trains"
                    raise ValueError(msg)
                params.append(train_id)
                set_clause = ", ".join(safe_updates)
                # Safe: set_clause is built only from whitelisted columns, values are parameterized
                query = f"UPDATE trains SET {set_clause} WHERE id = ?"  # nosec
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Updated train: {train_id}")
        except sqlite3.Error:
            logger.exception(f"Failed to update train {train_id}")
            return False
        else:
            return bool(updates)
        finally:
            conn.close()

    def get_trains_for_controller(self, controller_id: str) -> list[dict[str, Any]]:
        """Get all trains assigned to a controller.

        Args:
            controller_id: UUID of the edge controller

            return True
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT * FROM trains WHERE edge_controller_id = ?", (controller_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_train(self, train_id: str) -> Optional[dict[str, Any]]:
        """Retrieve train configuration.

        Args:
            train_id: Train identifier

        Returns:
            Dictionary with train config or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM trains WHERE id = ?", (train_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_trains(self) -> list[dict[str, Any]]:
        """Retrieve all trains.

        Returns:
            List of train configuration dicts
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM trains")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_train(
        self,
        train_id: str,
        name: str,
        controller_id: str,
        description: str = "",
        model: str = "",
        plugin_name: str = "dc_motor",
        plugin_config: str = "{}",
    ) -> None:
        """Add a new train to the database.

        Args:
            train_id: Unique UUID for the train
            name: Human-readable train name
            controller_id: UUID of the edge controller managing this train
            description: Optional description of the train
            model: Optional model name/number
            plugin_name: Hardware plugin name (default: dc_motor)
            plugin_config: JSON string of plugin configuration

        Raises:
            sqlite3.IntegrityError: If train_id already exists or controller_id invalid
            sqlite3.Error: For other database errors

        Example:
            >>> repo.add_train(
            ...     train_id="abc-123",
            ...     name="Express Line",
            ...     controller_id="ctrl-456",
            ...     plugin_config='{"motor_port": 1}'
            ... )
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT INTO trains
                (id, name, description, model, plugin_name, plugin_config, edge_controller_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (train_id, name, description, model, plugin_name, plugin_config, controller_id),
            )
            conn.commit()
            logger.info(f"Added train: {name} ({train_id}) to controller {controller_id}")
        except sqlite3.IntegrityError:
            logger.exception(f"Failed to add train {train_id}")
            raise
        finally:
            conn.close()

    def get_plugin(self, plugin_name: str) -> Optional[dict[str, Any]]:
        """Retrieve plugin by name.

        Args:
            plugin_name: Plugin name

        Returns:
            Dictionary with plugin data or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM plugins WHERE name = ?", (plugin_name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_plugins(self) -> list[dict[str, Any]]:
        """Retrieve all plugins.

        Returns:
            List of plugin configuration dicts
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM plugins")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_train_status(
        self, train_id: str, speed: int, voltage: float, current: float, position: str
    ) -> None:
        """Update the status of a train in the train_status table.

        Args:
            train_id: UUID of the train
            speed: Current speed (0-100)
            voltage: Current voltage reading
            current: Current amperage reading
            position: Current track position/section
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO train_status
                (train_id, speed, voltage, current, position, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (train_id, speed, voltage, current, position),
            )
            conn.commit()
            logger.info(
                f"Updated train status for {train_id}: speed={speed}, "
                f"voltage={voltage}, current={current}, position={position}"
            )
        finally:
            conn.close()

    def get_train_status(self, train_id: str) -> Optional[dict[str, Any]]:
        """Retrieve the latest status for a train from the train_status table.

        Args:
            train_id: UUID of the train

        Returns:
            Train status dict or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT train_id, speed, voltage, current, position "
                "FROM train_status WHERE train_id = ?",
                (train_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_metadata(self, key: str) -> Optional[str]:
        """Retrieve metadata value.

        Args:
            key: Metadata key

        Returns:
            Value or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute("SELECT value FROM config_metadata WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def set_metadata(self, key: str, value: str) -> None:
        """Set metadata key-value pair.

        Args:
            key: Metadata key
            value: Metadata value
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config_metadata (key, value) VALUES (?, ?)", (key, value)
            )
            conn.commit()
            logger.info(f"Set metadata {key} = {value}")
        finally:
            conn.close()

    def insert_plugin(self, name: str, description: str, config: dict[str, Any]) -> None:
        """Insert plugin into database.

        Args:
            name: Plugin name
            description: Plugin description
            config: Plugin configuration dict
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT OR REPLACE INTO plugins (name, description, config) VALUES (?, ?, ?)",
                (name, description, json.dumps(config)),
            )
            conn.commit()
            logger.info(f"Inserted plugin: {name}")
        finally:
            conn.close()

    def insert_edge_controller_with_details(
        self, controller_id: str, name: str, description: str, address: str, enabled: bool
    ) -> None:
        """Insert edge controller with full details.

        Args:
            controller_id: Unique UUID
            name: Controller name
            description: Controller description
            address: Network address
            enabled: Whether controller is enabled
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO edge_controllers
                (id, name, description, address, enabled)
                VALUES (?, ?, ?, ?, ?)
                """,
                (controller_id, name, description, address, int(enabled)),
            )
            conn.commit()
            logger.info(f"Inserted edge controller: {name} ({controller_id})")
        finally:
            conn.close()

    def insert_train(
        self,
        train_id: str,
        name: str,
        description: str,
        model: str,
        plugin_name: str,
        plugin_config: str,
        edge_controller_id: str,
    ) -> None:
        """Insert train into database.

        Args:
            train_id: Unique UUID
            name: Train name
            description: Train description
            model: Train model
            plugin_name: Associated plugin name
            plugin_config: Plugin configuration as YAML string
            edge_controller_id: Associated controller UUID
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO trains
                (id, name, description, model, plugin_name, plugin_config, edge_controller_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    train_id,
                    name,
                    description,
                    model,
                    plugin_name,
                    plugin_config,
                    edge_controller_id,
                ),
            )
            conn.commit()
            logger.info(f"Inserted train: {name} ({train_id})")
        finally:
            conn.close()
