"""Unit tests for configuration loader."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.config.loader import ConfigLoader, ConfigLoadError


@pytest.mark.unit()
class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_service_config_success(self, temp_config_dir: Path) -> None:
        """Test successful service config loading."""
        config_data = {"central_api_host": "api.example.com", "central_api_port": 9000}

        config_file = temp_config_dir / "service.conf"
        with config_file.open("w") as file_handle:
            yaml.safe_dump(config_data, file_handle)

        cached_file = temp_config_dir / "cached.yaml"

        loader = ConfigLoader(config_file, cached_file)
        result = loader.load_service_config()

        assert result == config_data
        assert result["central_api_host"] == "api.example.com"
        assert result["central_api_port"] == 9000

    def test_load_service_config_file_not_found(self, temp_config_dir: Path) -> None:
        """Test error when config file doesn't exist."""
        config_file = temp_config_dir / "nonexistent.conf"
        cached_file = temp_config_dir / "cached.yaml"

        loader = ConfigLoader(config_file, cached_file)

        with pytest.raises(ConfigLoadError, match="Config file not found"):
            loader.load_service_config()

    def test_load_service_config_invalid_yaml(self, temp_config_dir: Path) -> None:
        """Test error with invalid YAML syntax."""
        config_file = temp_config_dir / "invalid.conf"
        with config_file.open("w") as file_handle:
            file_handle.write("invalid: yaml: syntax:\n  - broken")

        cached_file = temp_config_dir / "cached.yaml"
        loader = ConfigLoader(config_file, cached_file)

        with pytest.raises(ConfigLoadError, match="Invalid YAML"):
            loader.load_service_config()

    def test_load_cached_runtime_config_success(self, temp_config_dir: Path) -> None:
        """Test successful cached config loading."""
        cached_data = {"uuid": "abc-123", "train_id": "train-1"}

        config_file = temp_config_dir / "service.conf"
        cached_file = temp_config_dir / "cached.yaml"

        with cached_file.open("w") as file_handle:
            yaml.safe_dump(cached_data, file_handle)

        loader = ConfigLoader(config_file, cached_file)
        result = loader.load_cached_runtime_config()

        assert result == cached_data
        assert result["uuid"] == "abc-123"

    def test_load_cached_runtime_config_no_file(self, temp_config_dir: Path) -> None:
        """Test cached config returns None when file doesn't exist."""
        config_file = temp_config_dir / "service.conf"
        cached_file = temp_config_dir / "nonexistent.yaml"

        loader = ConfigLoader(config_file, cached_file)
        result = loader.load_cached_runtime_config()

        assert result is None

    def test_save_runtime_config_success(
        self, temp_config_dir: Path, mock_runtime_config: dict[str, Any]
    ) -> None:
        """Test successful config saving."""
        config_file = temp_config_dir / "service.conf"
        cached_file = temp_config_dir / "cached.yaml"

        loader = ConfigLoader(config_file, cached_file)
        loader.save_runtime_config(mock_runtime_config)

        assert cached_file.exists()

        with cached_file.open("r") as file_handle:
            saved_data = yaml.safe_load(file_handle)

        assert saved_data == mock_runtime_config
        assert saved_data["uuid"] == "test-uuid-1234"

    def test_save_runtime_config_creates_directory(
        self, temp_config_dir: Path, mock_runtime_config: dict[str, Any]
    ) -> None:
        """Test that save creates parent directories."""
        config_file = temp_config_dir / "service.conf"
        cached_file = temp_config_dir / "subdir" / "cached.yaml"

        loader = ConfigLoader(config_file, cached_file)
        loader.save_runtime_config(mock_runtime_config)

        assert cached_file.parent.exists()
        assert cached_file.exists()
