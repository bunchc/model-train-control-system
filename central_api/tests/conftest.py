"""Shared test fixtures and configuration for central_api tests.

This module provides pytest fixtures used across all test modules.
"""

import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def temp_db_path() -> Generator[Path, None, None]:
    """Provide a temporary database path for testing.

    Yields:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = Path(temp_file.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def temp_yaml_path() -> Generator[Path, None, None]:
    """Provide a temporary YAML file path for testing.

    Yields:
        Path to temporary YAML file
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        yaml_path = Path(temp_file.name)

    yield yaml_path

    # Cleanup
    if yaml_path.exists():
        yaml_path.unlink()


@pytest.fixture()
def sample_config() -> dict:
    """Provide sample configuration dictionary.

    Returns:
        Valid configuration dictionary for testing
    """
    return {
        "plugins": [
            {
                "name": "test-plugin",
                "description": "Test plugin for unit tests",
                "config": {"enabled": True, "port": 8080},
            }
        ],
        "edge_controllers": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test-controller",
                "description": "Test edge controller",
                "address": "192.168.1.100",
                "enabled": True,
                "trains": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440001",
                        "name": "test-train",
                        "description": "Test train",
                        "model": "Test Model",
                        "plugin": {"name": "test-plugin", "config": {"speed": 50}},
                    }
                ],
            }
        ],
    }


@pytest.fixture()
def schema_sql() -> str:
    """Provide test database schema SQL.

    Returns:
        SQL schema string for testing
    """
    return """
    CREATE TABLE IF NOT EXISTS plugins (
        name TEXT PRIMARY KEY,
        description TEXT,
        config TEXT
    );

    CREATE TABLE IF NOT EXISTS edge_controllers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        address TEXT,
        enabled INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS trains (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        model TEXT,
        plugin_name TEXT,
        plugin_config TEXT,
        edge_controller_id TEXT,
        invert_directions BOOLEAN DEFAULT 0,
        FOREIGN KEY (edge_controller_id) REFERENCES edge_controllers(id)
    );

    CREATE TABLE IF NOT EXISTS train_status (
        train_id TEXT PRIMARY KEY,
        speed INTEGER,
        voltage REAL,
        current REAL,
        position TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (train_id) REFERENCES trains(id)
    );

    CREATE TABLE IF NOT EXISTS config_metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """


@pytest.fixture()
def temp_schema_path(schema_sql: str) -> Generator[Path, None, None]:
    """Provide a temporary schema file for testing.

    Args:
        schema_sql: SQL schema content

    Yields:
        Path to temporary schema file
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as temp_file:
        temp_file.write(schema_sql)
        schema_path = Path(temp_file.name)

    yield schema_path

    # Cleanup
    if schema_path.exists():
        schema_path.unlink()


@pytest.fixture()
def populated_db(temp_db_path: Path, temp_schema_path: Path, sample_config: dict) -> Path:
    """Provide a populated test database.

    Args:
        temp_db_path: Temporary database path
        temp_schema_path: Temporary schema file path
        sample_config: Sample configuration data

    Returns:
        Path to populated database
    """
    # Create and populate database
    conn = sqlite3.connect(str(temp_db_path))

    # Initialize schema
    with temp_schema_path.open("r") as schema_file:
        conn.executescript(schema_file.read())

    # Insert test data
    conn.execute(
        "INSERT INTO plugins (name, description, config) VALUES (?, ?, ?)",
        ("test-plugin", "Test plugin", '{"enabled": true}'),
    )

    conn.execute(
        "INSERT INTO edge_controllers (id, name, address, enabled) VALUES (?, ?, ?, ?)",
        ("550e8400-e29b-41d4-a716-446655440000", "test-controller", "192.168.1.100", 1),
    )

    conn.commit()
    conn.close()

    return temp_db_path


@pytest.fixture()
def sample_yaml_file(temp_yaml_path: Path, sample_config: dict) -> Path:
    """Create a sample YAML configuration file.

    Args:
        temp_yaml_path: Temporary YAML file path
        sample_config: Sample configuration dictionary

    Returns:
        Path to YAML file with sample configuration
    """
    with temp_yaml_path.open("w") as yaml_file:
        yaml.dump(sample_config, yaml_file)

    return temp_yaml_path
