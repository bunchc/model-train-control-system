"""Unit tests for config_loader module.

Tests YAML loading and validation with mocked file I/O.
"""

from pathlib import Path

import pytest
import yaml

from app.services.config_loader import (
    REQUIRED_CONTROLLER_FIELDS,
    REQUIRED_PLUGIN_FIELDS,
    REQUIRED_TOP_LEVEL_KEYS,
    ConfigLoader,
    ConfigLoadError,
)


@pytest.mark.unit()
class TestConfigLoader:
    """Test suite for ConfigLoader class."""

    def test_init_sets_yaml_path(self, temp_yaml_path: Path) -> None:
        """Test that __init__ sets yaml_path correctly."""
        loader = ConfigLoader(temp_yaml_path)

        assert loader.yaml_path == temp_yaml_path

    def test_load_config_success(self, sample_yaml_file: Path) -> None:
        """Test loading valid YAML configuration."""
        loader = ConfigLoader(sample_yaml_file)

        config = loader.load_config()

        assert isinstance(config, dict)
        assert "plugins" in config
        assert "edge_controllers" in config

    def test_load_config_file_not_found(self, temp_yaml_path: Path) -> None:
        """Test loading config when file doesn't exist."""
        temp_yaml_path.unlink(missing_ok=True)  # Ensure file doesn't exist
        loader = ConfigLoader(temp_yaml_path)

        with pytest.raises(ConfigLoadError, match="Config file not found"):
            loader.load_config()

    def test_load_config_invalid_yaml(self, temp_yaml_path: Path) -> None:
        """Test loading config with invalid YAML syntax."""
        # Write invalid YAML
        with temp_yaml_path.open("w") as yaml_file:
            yaml_file.write("invalid: yaml: content: [")

        loader = ConfigLoader(temp_yaml_path)

        with pytest.raises(ConfigLoadError, match="Invalid YAML syntax"):
            loader.load_config()

    def test_load_config_not_dict(self, temp_yaml_path: Path) -> None:
        """Test loading config that doesn't contain a dictionary."""
        # Write YAML list instead of dict
        with temp_yaml_path.open("w") as yaml_file:
            yaml.dump(["item1", "item2"], yaml_file)

        loader = ConfigLoader(temp_yaml_path)

        with pytest.raises(ConfigLoadError, match="must contain a YAML dictionary"):
            loader.load_config()

    def test_load_config_io_error(self) -> None:
        """Test loading config when file cannot be read."""
        fake_path = Path("/nonexistent/path/config.yaml")
        loader = ConfigLoader(fake_path)

        with pytest.raises(ConfigLoadError, match="Config file not found"):
            loader.load_config()

    def test_validate_config_structure_success(self, sample_config: dict) -> None:
        """Test validating config with correct structure."""
        loader = ConfigLoader(Path("dummy.yaml"))

        # Should not raise
        loader.validate_config_structure(sample_config)

    def test_validate_config_structure_missing_plugins(self) -> None:
        """Test validating config missing 'plugins' key."""
        config = {"edge_controllers": []}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="missing required keys"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_missing_edge_controllers(self) -> None:
        """Test validating config missing 'edge_controllers' key."""
        config = {"plugins": []}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="missing required keys"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_plugins_not_list(self) -> None:
        """Test validating config where 'plugins' is not a list."""
        config = {"plugins": {}, "edge_controllers": []}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="'plugins' must be a list"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_edge_controllers_not_list(self) -> None:
        """Test validating config where 'edge_controllers' is not a list."""
        config = {"plugins": [], "edge_controllers": {}}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="'edge_controllers' must be a list"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_plugin_not_dict(self) -> None:
        """Test validating config where plugin is not a dict."""
        config = {"plugins": ["invalid"], "edge_controllers": []}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="Plugin at index 0 must be a dict"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_plugin_missing_name(self) -> None:
        """Test validating config where plugin is missing 'name' field."""
        config = {"plugins": [{"description": "test"}], "edge_controllers": []}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="Plugin at index 0 missing fields"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_controller_not_dict(self) -> None:
        """Test validating config where controller is not a dict."""
        config = {"plugins": [], "edge_controllers": ["invalid"]}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="Controller at index 0 must be a dict"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_controller_missing_id(self) -> None:
        """Test validating config where controller is missing 'id' field."""
        config = {"plugins": [], "edge_controllers": [{"name": "test"}]}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="Controller at index 0 missing fields"):
            loader.validate_config_structure(config)

    def test_validate_config_structure_controller_missing_name(self) -> None:
        """Test validating config where controller is missing 'name' field."""
        config = {"plugins": [], "edge_controllers": [{"id": "test-id"}]}
        loader = ConfigLoader(Path("dummy.yaml"))

        with pytest.raises(ConfigLoadError, match="Controller at index 0 missing fields"):
            loader.validate_config_structure(config)

    def test_required_fields_constants(self) -> None:
        """Test that required field constants are defined correctly."""
        assert "plugins" in REQUIRED_TOP_LEVEL_KEYS
        assert "edge_controllers" in REQUIRED_TOP_LEVEL_KEYS
        assert "name" in REQUIRED_PLUGIN_FIELDS
        assert "id" in REQUIRED_CONTROLLER_FIELDS
        assert "name" in REQUIRED_CONTROLLER_FIELDS
