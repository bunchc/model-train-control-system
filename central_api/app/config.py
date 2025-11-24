"""Application configuration with environment variable validation.

Uses Pydantic Settings for type-safe environment variable parsing
and validation. All configuration errors are caught at startup.
"""

import logging
from pathlib import Path

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All paths are validated and converted to Path objects.
    Missing required variables will raise ValidationError on startup.
    """

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")  # nosec B104  # noqa: S104
    api_port: int = Field(default=8000, env="API_PORT", ge=1, le=65535)

    # Configuration Paths
    config_yaml_path: Path = Field(default=Path("/app/config.yaml"), env="CENTRAL_API_CONFIG_YAML")
    config_db_path: Path = Field(
        default=Path("/app/data/central_api_config.db"), env="CENTRAL_API_CONFIG_DB"
    )

    # MQTT Configuration
    mqtt_broker_host: str = Field(default="mqtt-broker", env="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, env="MQTT_BROKER_PORT", ge=1, le=65535)

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get validated application settings.

    Returns:
        Validated Settings instance

    Raises:
        ValidationError: If environment variables are invalid
    """
    try:
        return Settings()
    except ValidationError:
        logger.exception("Configuration validation failed")
        raise


# Singleton settings instance
settings = get_settings()
