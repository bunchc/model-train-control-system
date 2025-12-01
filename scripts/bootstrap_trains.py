#!/usr/bin/env python3
"""Bootstrap script to register edge controllers and create trains in Central API.

This script:
1. Registers edge controllers with the Central API
2. Creates train records in the database
3. Links trains to their respective controllers

Usage:
    python scripts/bootstrap_trains.py
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Central API configuration
CENTRAL_API_HOST = "192.168.1.199"
CENTRAL_API_PORT = 8000
CENTRAL_API_URL = f"http://{CENTRAL_API_HOST}:{CENTRAL_API_PORT}"

# Edge controller configuration (from Ansible inventory)
EDGE_CONTROLLERS = [
    {
        "name": "edge-controller-m1",
        "address": "192.168.2.214",
        "trains": [
            {
                "id": "9bf2f703-5ba2-5032-a749-01cce962bcf6",
                "name": "Express Line Engine",
                "description": "DC Motor on M1 port",
                "model": "DC Motor",
                "motor_port": 1,
                "plugin": {
                    "name": "dc_motor",
                    "config": {"motor_port": 1},
                },
            }
        ],
    },
    {
        "name": "edge-controller-m3",
        "address": "192.168.2.214",
        "trains": [
            {
                "id": "7cd3e891-4ab3-6143-b850-12ddf073ce87",
                "name": "Freight Line Engine",
                "description": "DC Motor on M3 port",
                "model": "DC Motor",
                "motor_port": 3,
                "plugin": {
                    "name": "dc_motor",
                    "config": {"motor_port": 3},
                },
            }
        ],
    },
]


def register_controller(name: str, address: str) -> str:
    """Register an edge controller and return its UUID.

    Args:
        name: Controller hostname/name
        address: Controller IP address

    Returns:
        UUID of the registered controller
    """
    logger.info(f"Registering controller: {name} at {address}")

    response = requests.post(
        f"{CENTRAL_API_URL}/api/controllers/register",
        json={"name": name, "address": address},
        timeout=5,
    )

    if response.status_code != 200:
        logger.error(f"Failed to register controller {name}: {response.text}")
        sys.exit(1)

    data = response.json()
    uuid = data["uuid"]
    status = data["status"]

    logger.info(f"✓ Controller {name} {status} with UUID: {uuid}")
    return uuid


def add_train_to_database(controller_uuid: str, train_data: dict) -> None:
    """Add a train to the database via direct SQLite access.

    Since there's no API endpoint for adding trains yet, we'll add them
    directly to the database using the config manager.

    Args:
        controller_uuid: UUID of the edge controller
        train_data: Train configuration dict
    """
    # Database path (same as Central API uses)
    db_path = Path.home() / ".config" / "train-control" / "config.db"

    # Insert train into database
    conn = sqlite3.connect(str(db_path))
    try:
        # Check if train already exists
        cursor = conn.execute("SELECT id FROM trains WHERE id = ?", (train_data["id"],))
        if cursor.fetchone():
            logger.info(f"  Train {train_data['name']} already exists, skipping")
            return

        # Insert train
        plugin_config_json = json.dumps(train_data["plugin"]["config"])
        conn.execute(
            """
            INSERT INTO trains (id, name, description, model, plugin_name, plugin_config, edge_controller_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                train_data["id"],
                train_data["name"],
                train_data.get("description", ""),
                train_data.get("model", ""),
                train_data["plugin"]["name"],
                plugin_config_json,
                controller_uuid,
            ),
        )
        conn.commit()
        logger.info(f"  ✓ Added train: {train_data['name']} ({train_data['id']})")
    finally:
        conn.close()


def main():
    """Bootstrap the train control system."""
    logger.info("=" * 60)
    logger.info("Train Control System Bootstrap")
    logger.info("=" * 60)

    # Check if Central API is accessible
    try:
        response = requests.get(f"{CENTRAL_API_URL}/api/ping", timeout=5)
        if response.status_code != 200:
            logger.error("Central API is not accessible")
            sys.exit(1)
        logger.info(f"✓ Central API accessible at {CENTRAL_API_URL}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Cannot connect to Central API: {e}")
        sys.exit(1)

    # Register controllers and add trains
    for controller_config in EDGE_CONTROLLERS:
        logger.info("")
        controller_uuid = register_controller(
            controller_config["name"], controller_config["address"]
        )

        # Add trains for this controller
        for train_data in controller_config["trains"]:
            add_train_to_database(controller_uuid, train_data)

    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Bootstrap complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Restart edge controllers to fetch their runtime configs")
    logger.info("2. Verify trains appear in GET /api/trains")
    logger.info("3. Send test commands via MQTT")


if __name__ == "__main__":
    main()
