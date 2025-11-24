"""FastAPI application entry point with lifespan management.

This module initializes the FastAPI application, configures middleware,
and sets up routers. Configuration is loaded and validated at startup
using the lifespan context manager pattern.

The application exposes REST API endpoints for:
- Train control (commands, status)
- Configuration management (edge controllers, plugins)
- Health monitoring (ping endpoint)

Example:
    Run the application with uvicorn:

        $ uvicorn app.main:app --host 0.0.0.0 --port 8000

    Access the interactive API docs:

        http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import config, trains
from app.services.config_manager import ConfigManager, ConfigurationError


# Configure logging
logging.basicConfig(
    level=settings.log_level, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# Application state
config_manager: Optional[ConfigManager] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager for startup/shutdown.

    Handles configuration initialization and cleanup using async context manager.
    This is the recommended FastAPI pattern for managing application lifecycle.

    Args:
        app_instance: FastAPI application instance

    Yields:
        None - Application runs while context is active

    Raises:
        RuntimeError: If configuration initialization fails (terminal error)

    Example:
        The lifespan is automatically managed by FastAPI:

        ```python
        app = FastAPI(lifespan=lifespan)
        # On startup: config_manager initialized
        # Application serves requests
        # On shutdown: cleanup performed
        ```
    """
    global config_manager  # noqa: PLW0603

    # Startup: Validate configuration exists and is readable
    try:
        if not settings.config_yaml_path.exists():
            msg = (
                f"Config file not found: {settings.config_yaml_path}. "
                "Please mount config.yaml at the expected location."
            )
            raise ConfigurationError(msg)  # noqa: TRY301

        logger.info(f"Loading configuration from {settings.config_yaml_path}")
        config_manager = ConfigManager(
            yaml_path=str(settings.config_yaml_path),
            db_path=str(settings.config_db_path),
        )
        # Store in app.state so routes can access it
        app.state.config_manager = config_manager
        logger.info("Configuration manager initialized successfully")

    except ConfigurationError as startup_error:
        logger.exception("Startup failed")
        msg = f"Cannot start API: {startup_error}"
        raise RuntimeError(msg) from startup_error

    yield

    # Shutdown: Cleanup (if needed in future)
    logger.info("Shutting down Central API")


app = FastAPI(title="Model Train Control System API", version="0.1.0", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper prefix
app.include_router(config.router, prefix="/api")
app.include_router(trains.router, prefix="/api/trains")


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns basic metadata about the API including version and documentation URL.

    Returns:
        Dictionary containing:
            - message: API name
            - version: API version string
            - docs: URL path to interactive API documentation

    Example:
        ```bash
        curl http://localhost:8000/
        ```

        Response:
        ```json
        {
          "message": "Model Train Control System API",
          "version": "0.1.0",
          "docs": "/docs"
        }
        ```
    """
    return {"message": "Model Train Control System API", "version": "0.1.0", "docs": "/docs"}


@app.get("/api/ping")
def ping():
    """Health check endpoint.

    Returns 200 if service is running and configuration is loaded.
    Returns 503 if configuration is not initialized (startup failure).

    Returns:
        Dictionary containing:
            - status: "ok" if healthy, "error" if unhealthy
            - message: Error description (only present if status="error")

        HTTP status code: 200 (healthy) or 503 (unhealthy)

    Example:
        ```bash
        # Healthy response
        curl http://localhost:8000/api/ping
        ```

        Response (200):
        ```json
        {"status": "ok"}
        ```

        Unhealthy response (503):
        ```json
        {
          "status": "error",
          "message": "Configuration not initialized"
        }
        ```
    """
    if config_manager is None:
        return {"status": "error", "message": "Configuration not initialized"}, 503

    return {"status": "ok"}
