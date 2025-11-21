# OpenAPI Alignment & Refactor Plan

This file tracks the plan for aligning the central_api implementation with openapi.yaml and adding missing features.

## Current Status (as of Nov 20, 2025)

- `openapi.yaml` is the canonical OpenAPI spec.
- All major config and plugin endpoints are implemented in `central_api/app/routers/config.py`.
- The config router is registered in `main.py` with `app.include_router(config.router, prefix="/api")`.
- Endpoints for `/api/config`, `/api/plugins`, `/api/edge-controllers`, `/api/config/edge-controllers/{edge_controller_id}`, `/api/trains`, `/api/config/trains`, `/api/trains/{train_id}`, `/api/config/trains/{train_id}` are present.
- Models for config, train, edge controller, and plugin are implemented and mostly match OpenAPI.
- MQTT integration is present in API, edge controller, and gateway.
- Frontend and gateway use REST and MQTT for control and telemetry.

## Plan Steps & Progress

1. **Add missing models to `schemas.py`**  
 ✅ Complete

2. **Add missing endpoints to routers**  
 ✅ Complete (all listed endpoints exist in `config.py`)

3. **Create new routers for config and plugin endpoints**  
 ✅ Complete (`config.py` covers both config and plugin endpoints)

4. **Register new routers in `main.py`**  
 ✅ Complete (config router registered)

5. **Implement mock handlers for new endpoints**  
 ⚠️ Partial: Some endpoints (e.g., train status, command) still return mock data or need deeper integration with MQTT and hardware.

6. **Test all endpoints for OpenAPI spec compliance**  
 ⏳ In progress: Insomnia CLI and integration tests cover most endpoints, but some edge cases and error handling need more coverage.

---

## Next Steps

1. **Replace mock handlers with real data sources**
   - Integrate train status and command endpoints with actual MQTT and hardware responses.
   - Ensure all config endpoints return real DB-backed data.

2. **Expand unit and integration tests**
   - Add tests for train status, command, and error cases.
   - Mock MQTT and hardware interactions for reliable CI.

3. **Validate OpenAPI spec compliance**
   - Use Swagger UI and openapi-generator to verify endpoint responses and schemas.
   - Fix any mismatches in response shapes or error handling.

4. **Document gaps and update plan**
   - Note any missing endpoints, fields, or error codes.
   - Update OpenAPI spec and code as needed.

5. **Refactor routers and service layers**
   - Split config, plugin, and train logic into dedicated routers/services if code grows.
   - Improve separation of concerns and maintainability.

6. **Frontend and gateway integration**
   - Ensure frontend and gateway use correct REST/MQTT topics and payloads.
   - Add tests for frontend command/status flows.

7. **DevOps and deployment**
   - Review Docker Compose, K8s, and Terraform manifests for completeness.
   - Add health checks and readiness probes.

---
Update this file as steps are completed or requirements change.
