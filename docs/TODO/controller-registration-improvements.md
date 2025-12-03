# Edge Controller Registration Process - Improvement Analysis

**Date:** December 2, 2025  
**Status:** Analysis & Recommendations  
**Context:** Review of current registration flow and potential enhancements

---

## Current Strengths

1. **Retry logic** on API accessibility checks (5 attempts, 2s delays)
2. **Graceful degradation** to cached config when API unavailable
3. **Database reset detection** via UUID ping before using cached UUID
4. **Auto-registration** of trains via environment variables
5. **Idempotent operations** - registration returns existing UUID if name matches

---

## Potential Improvements to Consider

### 1. **UUID-First Matching (The Issue You Identified)**

**Current Problem:** Hostname-based matching fails for containers (dynamic hostnames)

**Current Behavior:**

```python
# Central API matches on hostname first
for ec in all_controllers:
    if ec.name == name:  # Container hostname changes on rebuild!
        return {"uuid": ec.id, "status": "existing"}
```

**Solutions:**

**Option A: Send Cached UUID in Registration**

- Edge controller sends cached UUID in registration payload
- API matches UUID first, falls back to hostname
- Most straightforward fix

**Option B: Persistent Hardware Identifier**

- Use MAC address, serial number, or deployment ID
- Independent of container lifecycle
- Won't work in simulation mode

**Option C: Volume-Persisted UUID**

- UUID stored in persistent volume, survives container rebuilds
- Requires careful volume management in Ansible/Docker

**Trade-offs:**

- Option A: Simplest, requires API + edge changes
- Option B: Most robust, hardware-dependent
- Option C: Works but adds deployment complexity

---

### 2. **Controller Metadata Staleness**

**Current Problem:** If a controller's IP changes, the database has stale `address`

**Potential Fix:**

```python
# Update controller metadata on every registration
def register_controller(name, address, uuid=None):
    if uuid and exists(uuid):
        # Update name and address even if controller exists
        update_controller_metadata(uuid, name, address)
        return {"uuid": uuid, "status": "reactivated"}
```

**Additional Fields to Track:**

- `last_seen` timestamp (track controller heartbeats)
- `status` field (online/offline/error based on last contact)
- `version` (software version running on controller)

**Benefit:** Admins can see which controllers are active and where they are

---

### 3. **Train Assignment Race Condition**

**Current Problem:** Auto-registration happens during controller boot, but what if:

- Controller registers with TRAIN_ID="train-123"
- Admin manually assigns different train via API
- Controller reboots and tries to re-register original train

**Current Mitigation:**

```python
# You already have reassign flag!
def register_train_for_controller(controller_uuid, train_id, reassign=False):
    if train_exists and not reassign:
        raise HTTPException(409, "Train already exists")
```

**Potential Enhancement:**

- Add controller "intent" vs "actual" assignment tracking
- Log warning if train assignment conflicts
- Add `desired_controller_id` and `actual_controller_id` columns

---

### 4. **Cached Config Validation**

**Current Problem:** Cached config might be incomplete or corrupted

**Current Validation:**

```python
def _is_runtime_config_complete(self, config: dict) -> bool:
    return "train_id" in config and "mqtt_broker" in config
```

**Additional Validations:**

- **Schema validation** - Use pydantic models for structure
- **Reachability checks** - Ping MQTT broker before trusting cached config
- **Version/timestamp** - Detect stale caches (e.g., >24 hours old)
- **Checksum/signature** - Detect file corruption

**Example:**

```python
def validate_cached_config(config: dict) -> bool:
    # Structure validation
    if not all(k in config for k in ["uuid", "train_id", "mqtt_broker"]):
        return False

    # Staleness check
    cached_at = config.get("cached_at")
    if cached_at and (now() - cached_at) > timedelta(days=7):
        logger.warning("Cached config is >7 days old")
        return False

    # MQTT broker reachability
    broker = config["mqtt_broker"]
    if not can_reach_mqtt(broker["host"], broker["port"]):
        logger.warning("Cached MQTT broker unreachable")
        return False

    return True
```

---

### 5. **Polling for Config Updates**

**Current Gap:** If controller registers but no train assigned, it just waits forever

**Current Code:**

```python
if runtime_config is None:
    logger.warning("Edge controller registered but no train configuration available.")
    logger.warning("Waiting for administrator to assign trains...")
    return True  # Valid state - waiting for config
```

**Potential Solutions:**

**Option A: Periodic Polling**

```python
async def poll_for_config():
    while not has_config:
        await asyncio.sleep(30)  # Check every 30 seconds
        config = api_client.download_runtime_config(uuid)
        if config:
            reinitialize_with_config(config)
            break
```

**Option B: MQTT Notification**

```python
# Central API publishes when admin assigns trains
mqtt.publish(f"controllers/{uuid}/config/update", {"action": "reload"})

# Controller subscribes and reloads
def on_config_update(message):
    fresh_config = api_client.download_runtime_config(uuid)
    reinitialize_with_config(fresh_config)
```

**Option C: Long-Polling**

```python
# API endpoint blocks until config available or timeout
GET /api/controllers/{uuid}/config?wait=60
```

**Trade-offs:**

- Polling: Simple but adds network overhead
- MQTT: Clean but requires MQTT setup before config
- Long-polling: Efficient but complex server-side

---

### 6. **Multi-Train Support per Controller**

**Current Limitation:** One controller = one train (single `train_id` in config)

**Your Deployment:** Multiple motors per Pi (M1, M3) = separate containers = separate "controllers"

**Alternative Architecture:**

```yaml
# Runtime config with multiple trains
uuid: "controller-abc"
trains:
  - train_id: "train-m1"
    motor_port: 1
    mqtt_topics:
      commands: "trains/train-m1/commands"
      status: "trains/train-m1/status"
  - train_id: "train-m3"
    motor_port: 3
    mqtt_topics:
      commands: "trains/train-m3/commands"
      status: "trains/train-m3/status"
mqtt_broker:
  host: "192.168.1.199"
  port: 1883
```

**Implementation:**

- One controller per Pi
- Controller spawns thread/task per train
- Each train gets own hardware interface

**Trade-offs:**

- ✅ Simpler deployment (one container per Pi)
- ✅ Shared MQTT connection
- ❌ More complex controller logic
- ❌ Harder to isolate train failures
- ❌ One crash takes down all trains

**Current approach (1 container per train) is probably better for:**

- Fault isolation
- Independent scaling
- Simpler code

---

### 7. **Registration Security**

**Current Gap:** No authentication on `/api/controllers/register`

**Risks:**

- Rogue device could register and consume resources
- Malicious actor could spam registrations (DoS)
- No way to verify device identity

**Potential Fixes:**

**Option A: Pre-Shared Key**

```python
# Edge controller
headers = {"X-Registration-Token": os.getenv("REGISTRATION_TOKEN")}
response = requests.post(url, json=payload, headers=headers)

# Central API
@router.post("/controllers/register")
def register_controller(request: Request, ...):
    token = request.headers.get("X-Registration-Token")
    if token != EXPECTED_TOKEN:
        raise HTTPException(401, "Invalid registration token")
```

**Option B: Certificate-Based (mTLS)**

```python
# Mutual TLS - both client and server verify certificates
response = requests.post(url, json=payload,
                        cert=("/path/to/client.crt", "/path/to/client.key"),
                        verify="/path/to/ca.crt")
```

**Option C: MAC Address Allowlist**

```python
# Central API maintains allowlist of authorized MAC addresses
ALLOWED_MACS = ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"]

if mac_address not in ALLOWED_MACS:
    raise HTTPException(403, "MAC address not authorized")
```

**Option D: Rate Limiting**

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")  # Max 5 registrations per minute per IP
@router.post("/controllers/register")
def register_controller(...):
    ...
```

**Trade-off:** All add deployment complexity vs running on trusted network

---

### 8. **Config Refresh Strategy**

**Current:** Download config on boot, cache it, use cache if API down

**Potential Improvements:**

**A. Periodic Config Refresh**

```python
async def refresh_config_loop():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        fresh_config = api_client.download_runtime_config(uuid)
        if fresh_config and fresh_config != current_config:
            logger.info("Config changed, reloading")
            apply_config_changes(fresh_config)
```

**B. MQTT-Based Push Updates**

```python
# Admin updates train assignment -> API publishes event
mqtt.publish(f"controllers/{uuid}/config/update", {
    "version": 2,
    "changes": ["train_id", "mqtt_broker"]
})

# Controller receives and reloads
def on_config_update(message):
    if message["version"] > current_config_version:
        reload_config()
```

**C. Version-Based Config with Rollback**

```yaml
# Config includes version and checksum
version: 5
checksum: "sha256:abc123..."
trains:
  - train_id: "train-m1"
    ...
```

```python
def apply_config(new_config):
    backup = current_config
    try:
        validate_config(new_config)
        apply_config_changes(new_config)
        if not health_check():
            raise ConfigError("Health check failed")
    except Exception as e:
        logger.error(f"Config application failed: {e}")
        rollback_config(backup)
```

**D. Blue/Green Config Deployments**

- Test new config in "blue" slot before switching from "green"
- Requires duplicate hardware or simulation

---

### 9. **Error Recovery & Observability**

**Current:** Good logging, but limited metrics

**Additions:**

**Metrics to Track:**

```python
from prometheus_client import Counter, Histogram

registration_attempts = Counter("controller_registration_attempts_total")
registration_failures = Counter("controller_registration_failures_total", ["reason"])
config_cache_hits = Counter("controller_config_cache_hits_total")
config_download_duration = Histogram("controller_config_download_seconds")

# Usage
registration_attempts.inc()
config_cache_hits.inc()
with config_download_duration.time():
    config = api_client.download_runtime_config(uuid)
```

**Health Endpoint:**

```python
# HTTP health endpoint on edge controller
@app.get("/health")
def health():
    return {
        "status": "healthy" if has_config else "degraded",
        "controller_uuid": uuid,
        "train_id": train_id,
        "mqtt_connected": mqtt_client.is_connected(),
        "last_command": last_command_timestamp,
        "uptime_seconds": time.time() - start_time
    }
```

**Structured Logging:**

```python
import structlog

logger = structlog.get_logger()
logger.info("controller_registered",
           controller_uuid=uuid,
           train_id=train_id,
           registration_status="existing",
           duration_ms=elapsed)
```

**Distributed Tracing:**

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("controller_registration"):
    uuid = api_client.register_controller()
    with tracer.start_as_current_span("config_download"):
        config = api_client.download_runtime_config(uuid)
```

---

### 10. **Database Schema Evolution**

**Future-Proofing:**

**Edge Controllers Table:**

```sql
CREATE TABLE edge_controllers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT,
    enabled BOOLEAN NOT NULL,

    -- NEW FIELDS
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'offline',  -- online/offline/error
    version TEXT,                    -- Software version running on controller
    metadata TEXT,                   -- JSON for extensibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Trains Table:**

```sql
CREATE TABLE trains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    model TEXT,
    plugin_name TEXT NOT NULL,
    plugin_config TEXT,
    edge_controller_id TEXT NOT NULL,

    -- NEW FIELDS
    desired_controller_id TEXT,      -- Admin intent
    actual_controller_id TEXT,       -- Where train actually is running
    reassignment_status TEXT,        -- pending/in_progress/complete
    last_telemetry_at TIMESTAMP,     -- Track active trains

    FOREIGN KEY(edge_controller_id) REFERENCES edge_controllers(id)
);
```

**Benefits:**

- Track controller heartbeats (`last_seen`)
- Monitor which trains are active (`last_telemetry_at`)
- Support controller reassignment workflows
- Store arbitrary metadata without schema changes

---

## Recommendations (Priority Order)

### **High Priority (Fix Now):**

1. **UUID-First Matching** ⭐⭐⭐
   - **Why:** Fixes your immediate container rebuild issue
   - **Effort:** Medium (requires changes to edge + API)
   - **Risk:** Low (backward compatible if done right)
   - **Implementation:** Option A (send cached UUID in registration payload)

2. **Controller Metadata Updates** ⭐⭐
   - **Why:** Track active controllers, detect IP changes
   - **Effort:** Low (add `last_seen`, update on registration)
   - **Risk:** Very low
   - **Implementation:** Add fields to DB, update on every registration

3. **Periodic Config Refresh** ⭐⭐
   - **Why:** Controllers pick up admin changes without reboot
   - **Effort:** Medium (add polling loop to edge controller)
   - **Risk:** Low (just adds network calls)
   - **Implementation:** Simple polling every 5 minutes

### **Medium Priority (Next Phase):**

4. **Cached Config Validation** ⭐
   - **Why:** Prevent boot failures from corrupt/stale cache
   - **Effort:** Low (add validation checks)
   - **Risk:** Low
   - **Implementation:** Add timestamp, schema validation

5. **Registration Rate Limiting** ⭐
   - **Why:** Basic security hygiene
   - **Effort:** Low (use slowapi or nginx)
   - **Risk:** Very low
   - **Implementation:** 5 registrations per minute per IP

6. **Metrics & Health Endpoints** ⭐
   - **Why:** Better observability for debugging
   - **Effort:** Medium
   - **Risk:** Low
   - **Implementation:** Prometheus metrics, /health endpoint

### **Low Priority (Future Enhancements):**

7. Multi-train support per controller (probably not needed)
8. Advanced security (mTLS) - only if internet-facing
9. Distributed tracing - only if you have many controllers
10. Blue/green config deployments - overkill for current scale

---

## Questions for You

**Please answer these to help prioritize:**

1. **Do you want controllers to survive database resets gracefully?**
   - If yes → UUID-first matching is essential
   - Current behavior: Re-register with new UUID (creates duplicates?)

   Yes

2. **Should controllers auto-update when admin changes train assignments via web UI?**
   - If yes → Need polling or MQTT notifications
   - Current behavior: Requires controller reboot

   Yes

3. **Do you plan to run multiple trains per physical Pi in the future?**
   - If yes → Consider multi-train architecture
   - Current design (1 container = 1 train) works well for fault isolation

   Maybe, put this one on the back burner

4. **How important is security for this deployment?**
   - Trusted home network → Skip auth for now
   - Internet-facing → Add pre-shared key or mTLS

   Right now: not very, put this one on the back burner

5. **Do you want the tear-down script to preserve controller UUIDs?**
   - Option A: Don't delete the database (just clear trains/status)
   - Option B: Export/import controller registrations
   - Option C: Use volume persistence for database

   I would like this to be optional, but let's not worry about this at the moment, put your thoughts around this into a file in `docs/TODO/features/`

6. **What's your typical deployment workflow?**
   - Frequent rebuilds during development → UUID-first is critical
   - Rare production updates → Current hostname matching might be OK

   You've hit the nail on the head, and right now we're in a heavy development phase, so UUID first.

---

## Proposed Implementation Plan

**If you want to proceed with high-priority fixes:**

### Phase 1: UUID-First Matching (Week 1)

**Edge Controller Changes:**

```python
# app/api/client.py
def register_controller(self, cached_uuid: Optional[str] = None) -> str:
    payload = {"name": hostname, "address": ip_address}
    if cached_uuid:
        payload["uuid"] = cached_uuid
    # ... rest of registration

# app/config/manager.py
def _register_new_controller(self):
    cached_config = self.loader.load_cached_runtime_config()
    cached_uuid = cached_config.get("uuid") if cached_config else None
    controller_uuid = self.api_client.register_controller(cached_uuid=cached_uuid)
```

**Central API Changes:**

```python
# app/routers/config.py
@router.post("/controllers/register")
def register_controller(
    name: str = Body(...),
    address: str = Body(...),
    uuid: Optional[str] = Body(None)  # NEW: cached UUID
):
    # Priority 1: Match on UUID if provided
    if uuid and controller_exists(uuid):
        update_controller_metadata(uuid, name, address)
        return {"uuid": uuid, "status": "reactivated"}

    # Priority 2: Match on hostname (fallback)
    existing = find_by_name(name)
    if existing:
        return {"uuid": existing.id, "status": "existing"}

    # Priority 3: Create new
    new_uuid = generate_uuid()
    create_controller(new_uuid, name, address)
    return {"uuid": new_uuid, "status": "registered"}
```

**Database Migration:**

```sql
ALTER TABLE edge_controllers ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE edge_controllers ADD COLUMN status TEXT DEFAULT 'offline';
ALTER TABLE edge_controllers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

**Testing:**

1. Deploy controller → Get UUID `abc-123`
2. Tear down container (preserve volume with cached UUID)
3. Redeploy → Should get same UUID `abc-123`
4. Verify no duplicate controllers in database

### Phase 2: Metadata & Refresh (Week 2)

**Add controller heartbeat:**

```python
# Update last_seen on every registration
UPDATE edge_controllers SET last_seen = CURRENT_TIMESTAMP WHERE id = ?

# Periodic status check
UPDATE edge_controllers SET status = 'offline'
WHERE last_seen < datetime('now', '-5 minutes')
```

**Add config polling:**

```python
async def config_refresh_task():
    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            fresh = api_client.download_runtime_config(uuid)
            if fresh != cached_config:
                reload_config(fresh)
        except Exception as e:
            logger.error(f"Config refresh failed: {e}")
```

### Phase 3: Validation & Observability (Week 3)

**Config validation:**

```python
def validate_runtime_config(config: dict) -> bool:
    required = ["uuid", "train_id", "mqtt_broker"]
    if not all(k in config for k in required):
        return False

    # Check staleness
    cached_at = config.get("cached_at")
    if cached_at and is_stale(cached_at, max_age=timedelta(days=7)):
        return False

    return True
```

**Health endpoint:**

```python
@app.get("/health")
def health():
    return {
        "status": "healthy" if mqtt_connected else "degraded",
        "controller_uuid": uuid,
        "config_version": config_version,
        "uptime": uptime_seconds
    }
```

---

## Summary

**Current registration is solid but has container-specific issues.**

**Critical fix:** UUID-first matching to handle container rebuilds

**Nice-to-haves:** Metadata tracking, config refresh, validation

**Answer the questions above, and I can create a focused implementation plan!**
