"""Central API application package.

This package contains the FastAPI application for the model train control system.
It provides REST API endpoints for train control, configuration management, and
MQTT integration with edge controllers.

Modules:
    main: FastAPI application entry point with lifespan events
    config: Pydantic Settings for environment variable validation

Subpackages:
    models: Pydantic data models for request/response validation
    routers: FastAPI router modules for API endpoints
    services: Business logic and external service adapters
"""
