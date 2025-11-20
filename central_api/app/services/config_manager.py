import os
import sqlite3
import yaml
import logging
import uuid
from typing import List
try:
    from central_api.app.models.schemas import Plugin, EdgeController, Train, FullConfig
except ModuleNotFoundError:
    from models.schemas import Plugin, EdgeController, Train, FullConfig

DB_PATH = os.getenv("CENTRAL_API_CONFIG_DB", "central_api_config.db")
YAML_PATH = os.getenv("CENTRAL_API_CONFIG_YAML", "config.yaml")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "config_schema.sql")

class ConfigManager:
    def update_train_status(self, train_id: str, speed: int, voltage: float, current: float, position: str):
        """
        Update the status of a train in the train_status table.
        """
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO train_status (train_id, speed, voltage, current, position, updated_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (train_id, speed, voltage, current, position)
        )
        self.conn.commit()
        self.logger.info(f"Updated train status for {train_id}: speed={speed}, voltage={voltage}, current={current}, position={position}")

    def get_train_status(self, train_id: str):
        """
        Retrieve the latest status for a train from the train_status table.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT train_id, speed, voltage, current, position FROM train_status WHERE train_id=?", (train_id,))
        row = cur.fetchone()
        if row:
            from central_api.app.models.schemas import TrainStatus
            return TrainStatus(
                train_id=row[0],
                speed=row[1],
                voltage=row[2],
                current=row[3],
                position=row[4]
            )
        else:
            self.logger.warning(f"No status found for train {train_id}")
            return None

    def get_plugins(self):
        """Return a list of Plugin objects from the plugins table."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute("SELECT name, description, config FROM plugins")
        rows = cur.fetchall()
        plugins = []
        for name, description, config_json in rows:
            import json
            config = json.loads(config_json) if config_json else {}
            plugins.append(Plugin(name=name, description=description, config=config))
        conn.close()
        return plugins
    def __init__(self, db_path=DB_PATH, yaml_path=YAML_PATH):
        self.db_path = db_path
        self.yaml_path = yaml_path
        self.conn = None
        self.logger = logging.getLogger("central_api.config_manager")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)
        self.logger.info(f"Initializing ConfigManager with db_path={db_path}, yaml_path={yaml_path}")
        self._ensure_db()

    def _ensure_db(self):
        db_exists = os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()
        self.conn.executescript(schema_sql)
        self.conn.commit()
        self.logger.info("Database schema ensured.")
        if not db_exists:
            self.logger.info("Database did not exist, bootstrapping from YAML.")
            self._bootstrap_from_yaml()
        else:
            if not self.get_last_updated():
                self.logger.info("No last_updated found in DB, bootstrapping from YAML.")
                self._bootstrap_from_yaml()
    def set_last_updated(self):
        import time
        epoch_time = int(time.time())
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO config_metadata (key, value) VALUES (?, ?)",
                ("last_updated", str(epoch_time))
            )
            self.conn.commit()
            self.logger.info(f"Set last_updated in config_metadata to {epoch_time}")
        except Exception as e:
            self.logger.error(f"Failed to set last_updated in config_metadata: {e}")




    def get_trains(self) -> List[Train]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, description, model, plugin_name, plugin_config FROM trains")
        train_rows = cur.fetchall()
        trains = [Train(
            id=tr[0],
            name=tr[1],
            description=tr[2],
            model=tr[3],
            plugin={
                "name": tr[4],
                "config": yaml.safe_load(tr[5]) if tr[5] else {}
            }
        ) for tr in train_rows]
        return trains

    def get_train(self, train_id: str) -> Train:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, description, model, plugin_name, plugin_config FROM trains WHERE id=?", (train_id,))
        tr = cur.fetchone()
        if not tr:
            return None
        return Train(
            id=tr[0],
            name=tr[1],
            description=tr[2],
            model=tr[3],
            plugin={
                "name": tr[4],
                "config": yaml.safe_load(tr[5]) if tr[5] else {}
            }
        )

    def _bootstrap_from_yaml(self):
        # import uuid (already imported at top)
        if not os.path.exists(self.yaml_path):
            self.logger.warning(f"YAML file not found: {self.yaml_path}. DB will be empty.")
            return
        self.logger.info("YAML file found, loading...")
        with open(self.yaml_path, "r") as f:
            config = yaml.safe_load(f)
        import json
        self.logger.debug(f"Loaded config: {json.dumps(config)[:500]}{'...' if len(json.dumps(config)) > 500 else ''}")
        self.logger.info("Populating plugins...")
        for plugin in config.get("plugins", []):
            self.logger.info(f"Plugin: {plugin.get('name')} | Description: {plugin.get('description', '')}")
            try:
                self.conn.execute(
                    "INSERT OR REPLACE INTO plugins (name, description, config) VALUES (?, ?, ?)",
                    (
                        plugin["name"],
                        plugin.get("description", ""),
                        json.dumps(plugin.get("config", {}))
                    )
                )
                self.set_last_updated()
                self.logger.info(f"Plugin '{plugin.get('name')}' inserted successfully.")
            except Exception as e:
                self.logger.error(f"Plugin '{plugin.get('name')}' insert FAILED: {e}")
        self.logger.info("Populating edge controllers and trains...")
        for ec in config.get("edge_controllers", []):
            raw_id = ec.get("id")
            id_str = str(raw_id) if raw_id is not None else ""
            import re
            uuid_regex = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
            needs_uuid = False
            if not id_str or "{UUID}" in id_str:
                needs_uuid = True
            elif not uuid_regex.match(id_str):
                needs_uuid = True
            if needs_uuid:
                new_uuid = str(uuid.uuid4())
                self.logger.info(f"Edge controller '{ec.get('name')}' id '{id_str}' is not a valid UUID, assigning new UUID: {new_uuid}")
                ec_id = new_uuid
            else:
                ec_id = id_str
            name = str(ec["name"])
            description = str(ec.get("description", ""))
            address = ec.get("address", None)
            if address is not None:
                address = str(address)
            enabled = bool(ec.get("enabled", True))
            self.logger.debug(f"About to insert edge_controller with id: {ec_id}")
            try:
                self.conn.execute(
                    "INSERT OR REPLACE INTO edge_controllers (id, name, description, address, enabled) VALUES (?, ?, ?, ?, ?)",
                    (
                        ec_id,
                        name,
                        description,
                        address,
                        enabled
                    )
                )
                self.set_last_updated()
                self.logger.info(f"Edge controller '{name}' inserted with id: {ec_id}")
            except Exception as e:
                self.logger.error(f"Failed to insert edge_controller '{name}' with id '{ec_id}': {e}")
                raise
            for train in ec.get("trains", []):
                plugin = train.get("plugin", {})
                import json
                import re
                def safe_str(val):
                    if val is None:
                        return None
                    if isinstance(val, (dict, list)):
                        return json.dumps(val)
                    return str(val)
                raw_id = train.get("id")
                id_str = str(raw_id) if raw_id is not None else ""
                uuid_regex = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
                needs_uuid = False
                if not id_str or "{UUID}" in id_str:
                    needs_uuid = True
                elif not uuid_regex.match(id_str):
                    needs_uuid = True
                if needs_uuid:
                    new_uuid = str(uuid.uuid4())
                    self.logger.info(f"Train '{train.get('name')}' id '{id_str}' is not a valid UUID, assigning new UUID: {new_uuid}")
                    train_id = new_uuid
                else:
                    train_id = id_str
                train_name = safe_str(train.get("name"))
                train_desc = safe_str(train.get("description", ""))
                train_model = safe_str(train.get("model", None))
                plugin_name = safe_str(plugin.get("name", None))
                plugin_config = safe_str(json.dumps(plugin.get("config", {})))
                edge_controller_id = safe_str(ec_id)
                self.logger.debug(f"Inserting train: id={train_id}, name={train_name}, description={train_desc}, model={train_model}, plugin_name={plugin_name}, plugin_config={plugin_config}, edge_controller_id={edge_controller_id}")
                try:
                    self.conn.execute(
                        "INSERT OR REPLACE INTO trains (id, name, description, model, plugin_name, plugin_config, edge_controller_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            train_id,
                            train_name,
                            train_desc,
                            train_model,
                            plugin_name,
                            plugin_config,
                            edge_controller_id
                        )
                    )
                    self.set_last_updated()
                    self.logger.info(f"Train '{train_name}' inserted with id: {train_id}")
                except Exception as e:
                    self.logger.error(f"Failed to insert train '{train_name}' with id '{train_id}': {e}")
                    raise
        # ...existing code...

    def get_edge_controllers(self) -> List[EdgeController]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, description, address, enabled FROM edge_controllers")
        ec_rows = cur.fetchall()
        ecs = []
        for ec_row in ec_rows:
            cur.execute("SELECT id, name, description, model, plugin_name, plugin_config FROM trains WHERE edge_controller_id=?", (ec_row[0],))
            train_rows = cur.fetchall()
            trains = [Train(
                id=tr[0],
                name=tr[1],
                description=tr[2],
                model=tr[3],
                plugin={
                    "name": tr[4],
                    "config": yaml.safe_load(tr[5]) if tr[5] else {}
                }
            ) for tr in train_rows]
            ecs.append(EdgeController(
                id=ec_row[0],
                name=ec_row[1],
                description=ec_row[2],
                address=ec_row[3],
                enabled=bool(ec_row[4]),
                trains=trains
            ))
        return ecs

    def get_edge_controller(self, edge_controller_id: str) -> EdgeController:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, description, address, enabled FROM edge_controllers WHERE id=?", (edge_controller_id,))
        ec_row = cur.fetchone()
        if not ec_row:
            return None
        cur.execute("SELECT id, name, description, model, plugin_name, plugin_config FROM trains WHERE edge_controller_id=?", (ec_row[0],))
        train_rows = cur.fetchall()
        trains = [Train(
            id=tr[0],
            name=tr[1],
            description=tr[2],
            model=tr[3],
            plugin={
                "name": tr[4],
                "config": yaml.safe_load(tr[5]) if tr[5] else {}
            }
        ) for tr in train_rows]
        return EdgeController(
            id=ec_row[0],
            name=ec_row[1],
            description=ec_row[2],
            address=ec_row[3],
            enabled=bool(ec_row[4]),
            trains=trains
        )

    def get_full_config(self) -> FullConfig:
        return FullConfig(
            plugins=self.get_plugins(),
            edge_controllers=[ec.dict() for ec in self.get_edge_controllers()]
        )

    def get_last_updated(self) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM config_metadata WHERE key='last_updated'")
        row = cur.fetchone()
        return row[0] if row else None
