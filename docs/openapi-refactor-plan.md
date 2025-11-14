# OpenAPI Alignment & Refactor Plan

This file tracks the plan for aligning the central_api implementation with openapi.yaml and adding missing features.

## Current Status
- openapi.yaml is now the canonical OpenAPI spec for the project.
- openapi.json has been removed.

## Plan Steps

### 1. Add missing models to central_api/app/models/schemas.py
- TrainConfig
- FullConfig
- EdgeControllerConfig

### 2. Add missing endpoints to central_api/app/routers/
- /api/plugins (GET)
- /api/config (GET)
- /api/config/trains (GET)
- /api/config/trains/{train_id} (GET)
- /api/edge-controllers (GET)
- /api/config/edge-controllers/{edge_controller_id} (GET)

### 3. Create new routers for config and plugin endpoints
- config.py (for config endpoints)
- plugins.py (for plugins endpoint)

### 4. Register new routers in central_api/app/main.py

### 5. Implement mock handlers for new endpoints
- Return mock/config data for now

### 6. Test all endpoints for OpenAPI spec compliance

## Progress Tracking
 - [x] Step 1: Add missing models (complete)
 - [~] Step 2: Add missing endpoints (in progress)
- [ ] Step 3: Create new routers
- [ ] Step 4: Register routers
- [ ] Step 5: Implement mock handlers
- [ ] Step 6: Test endpoints

---
Update this file as steps are completed or requirements change.
