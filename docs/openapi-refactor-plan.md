# OpenAPI Alignment & Refactor Plan

This file tracks the plan for aligning the central_api implementation with openapi.yaml and adding missing features.

## Current Status (as of Nov 14, 2025)
- `openapi.yaml` is the canonical OpenAPI spec.
- All major config and plugin endpoints are implemented in `central_api/app/routers/config.py`.
- The config router is registered in `main.py` with `app.include_router(config.router, prefix="/api")`.
- Endpoints for `/api/config`, `/api/plugins`, `/api/edge-controllers`, `/api/config/edge-controllers/{edge_controller_id}`, and related train queries are present.
- Models for config, train, and edge controller are implemented.


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
	⚠️ Partial: Handlers exist, but some may still return mock data or need real integration.

6. **Test all endpoints for OpenAPI spec compliance**  
	⏳ In progress/not started

---

## Next Steps

1. **Review and replace mock handlers with real data sources**
	- Integrate with actual config and plugin data where possible.

2. **Add/expand unit and integration tests for new endpoints**
	- Ensure coverage for all config, plugin, and edge controller endpoints.

3. **Validate OpenAPI spec compliance**
	- Use tools like Swagger UI or `openapi-generator` to verify endpoint responses match the spec.

4. **Document any remaining gaps or mismatches between code and OpenAPI spec**
	- Update the plan and code as needed.

5. **Refactor or split routers if config and plugin logic grows**
	- Consider a dedicated `plugins.py` router if plugin logic expands.

---
Update this file as steps are completed or requirements change.
