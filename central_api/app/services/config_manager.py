import os
import sqlite3
import yaml
from datetime import datetime
from typing import List, Dict, Any
try:
    from central_api.app.models.schemas import Plugin, EdgeController, Train, FullConfig
except ModuleNotFoundError:
    from models.schemas import Plugin, EdgeController, Train, FullConfig

DB_PATH = os.getenv("CENTRAL_API_CONFIG_DB", "central_api_config.db")
YAML_PATH = os.getenv("CENTRAL_API_CONFIG_YAML", "config.yaml")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "config_schema.sql")

class ConfigManager:
    def __init__(self, db_path=DB_PATH, yaml_path=YAML_PATH):
        self.db_path = db_path
        self.yaml_path = yaml_path
        self.conn = None
        self._ensure_db()

    def _ensure_db(self):
        db_exists = os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()
        self.conn.executescript(schema_sql)
        self.conn.commit()
        if not db_exists:
            self._bootstrap_from_yaml()
        else:
            if not self._has_last_updated():
                self._bootstrap_from_yaml()

    def _has_last_updated(self):
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM config_metadata WHERE key='last_updated'")
        return cur.fetchone() is not None

    def _bootstrap_from_yaml(self):
        import uuid
        import sys
        import sqlite3
        import json
        print(f"[BOOTSTRAP] Python version: {sys.version}")
        print(f"[BOOTSTRAP] SQLite version: {sqlite3.sqlite_version}")
        print(f"[BOOTSTRAP] Using YAML path: {self.yaml_path}")
        if not os.path.exists(self.yaml_path):
            print(f"[BOOTSTRAP] YAML file not found: {self.yaml_path}")
            # No YAML, just leave DB empty
            return
        print(f"[BOOTSTRAP] YAML file found, loading...")
        with open(self.yaml_path, "r") as f:
            config = yaml.safe_load(f)
        print(f"[BOOTSTRAP] Loaded config: {json.dumps(config)[:500]}{'...' if len(json.dumps(config)) > 500 else ''}")
        # Populate plugins
        print(f"[BOOTSTRAP] Populating plugins...")
        for plugin in config.get("plugins", []):
            print(f"[BOOTSTRAP] Plugin: {plugin.get('name')} | Description: {plugin.get('description', '')}")
            try:
                self.conn.execute(
                    "INSERT OR REPLACE INTO plugins (name, description, config) VALUES (?, ?, ?)",
                    (
                        plugin["name"],
                        plugin.get("description", ""),
                        json.dumps(plugin.get("config", {}))
                    )
                )
                print(f"[BOOTSTRAP] Plugin '{plugin.get('name')}' inserted successfully.")
            except Exception as e:
                print(f"[BOOTSTRAP] Plugin '{plugin.get('name')}' insert FAILED: {e}")
        print(f"[BOOTSTRAP] Populating edge controllers and trains...")
        # Populate edge controllers and trains
        for ec in config.get("edge_controllers", []):
            # Validate and assign UUID for id
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
                print(f"[BOOTSTRAP] Edge controller '{ec.get('name')}' id '{id_str}' is not a valid UUID, assigning new UUID: {new_uuid}")
                ec_id = new_uuid
            else:
                ec_id = id_str
            name = str(ec["name"])
            description = str(ec.get("description", ""))
            address = ec.get("address", None)
            if address is not None:
                address = str(address)
            enabled = bool(ec.get("enabled", True))
            print(f"[DEBUG] About to insert edge_controller with id: {ec_id}")
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
                print(f"[BOOTSTRAP] Edge controller '{name}' inserted with id: {ec_id}")
            except Exception as e:
                print(f"[ERROR] Failed to insert edge_controller '{name}' with id '{ec_id}': {e}")
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
                # Validate and assign UUID for train id
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
                    print(f"[BOOTSTRAP] Train '{train.get('name')}' id '{id_str}' is not a valid UUID, assigning new UUID: {new_uuid}")
                    train_id = new_uuid
                else:
                    train_id = id_str
                train_name = safe_str(train.get("name"))
                train_desc = safe_str(train.get("description", ""))
                train_model = safe_str(train.get("model", None))
                plugin_name = safe_str(plugin.get("name", None))
                plugin_config = safe_str(json.dumps(plugin.get("config", {})))
                edge_controller_id = safe_str(ec_id)
                print("[DEBUG] Inserting train:")
                print(f"  id: {train_id} ({type(train_id)})")
                print(f"  name: {train_name} ({type(train_name)})")
                print(f"  description: {train_desc} ({type(train_desc)})")
                print(f"  model: {train_model} ({type(train_model)})")
                print(f"  plugin_name: {plugin_name} ({type(plugin_name)})")
                print(f"  plugin_config: {plugin_config} ({type(plugin_config)})")
                print(f"  edge_controller_id: {edge_controller_id} ({type(edge_controller_id)})")
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
                    print(f"[BOOTSTRAP] Train '{train_name}' inserted with id: {train_id}")
                except Exception as e:
                    print(f"[ERROR] Failed to insert train '{train_name}' with id '{train_id}': {e}")
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
            edge_controllers=self.get_edge_controllers()
        )

    def get_last_updated(self) -> str:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM config_metadata WHERE key='last_updated'")
        row = cur.fetchone()
        return row[0] if row else None
