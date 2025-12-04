# Consolidated TODO List

**Date:** December 4, 2025
**Status:** Active Planning Document
**Context:** Consolidated from previous TODO files after Train Config feature completion

---

## Summary of Completed Work

### ✅ Train Configuration Feature (COMPLETED)

**Source:** `TRAIN_CONFIG_IMPLEMENTATION_PLAN.md`, `TRAIN_CONFIG_TODAY.md`

All core functionality implemented:

- Database schema with `invert_directions` column
- Pydantic models with `TrainUpdateRequest`
- `PUT /api/trains/{train_id}` endpoint
- TypeScript types and React Query mutation hooks
- `TrainConfigModal` component with validation
- Gear icon integration in `TrainDetail` page
- Toast notifications and loading states
- Accessibility audit completed
- Direction change safety with gradual ramping (stop before reverse)

**Deferred items (low priority):**

- [ ] Audit logging for config changes
- [ ] Undo/redo functionality
- [ ] Bulk edit for multiple trains

---

## Outstanding Work

### 1. Web UI Testing Strategy (Phase 2 Priority)

**Source:** `WEB_UI_TESTING_STRATEGY.md`
**Status:** ✅ Setup Complete, Tests Implemented
**Current Coverage:** 12 RTL unit tests + 4 Playwright E2E tests

#### Implemented

- `frontend/web/vitest.config.ts` - Unit test configuration
- `frontend/web/playwright.config.ts` - E2E test configuration
- `frontend/web/tests/setup.ts` - Test setup with jest-dom matchers
- `frontend/web/tests/utils/test-utils.tsx` - Shared test providers
- `frontend/web/tests/components/TrainConfigModal.test.tsx` - 12 unit tests
- `frontend/web/tests/e2e/train-config.spec.ts` - 4 E2E tests

#### Remaining Test Coverage

| Priority | Component | Status |
|----------|-----------|--------|
| High | TrainControlPanel | Not started |
| High | TrainDetail page | Not started |
| Medium | TrainList | Not started |
| Medium | ControllerList | Not started |
| Low | Dashboard | Not started |
| Low | Navigation | Not started |

#### Commands

```bash
cd frontend/web
npm run test          # RTL unit tests
npm run test:e2e      # Playwright E2E tests
```

#### Success Metrics

- 70%+ code coverage on frontend
- All critical paths tested in E2E
- Tests run in <2 min (RTL) + <5 min (E2E)
- No flaky tests

---

### 2. Controller Registration Improvements (Production Hardening)

**Source:** `controller-registration-improvements.md`
**Status:** ⏸️ Deferred (system working, improvements optional)
**Effort:** Variable per improvement

#### High Priority (If Issues Arise)

| Improvement | Effort | Risk | Description |
|-------------|--------|------|-------------|
| Retry with Backoff | Low | Low | Exponential backoff for API/MQTT failures |
| Health Endpoint | Medium | Low | `/health` endpoint on edge controllers |
| Graceful Degradation | Medium | Low | Fail-safe behavior when Central API unavailable |

#### Medium Priority (Next Phase)

| Improvement | Effort | Risk | Description |
|-------------|--------|------|-------------|
| Cached Config Validation | Low | Low | Timestamp, schema validation for cached configs |
| Registration Rate Limiting | Low | Very Low | 5 registrations/min per IP |
| Metrics & Observability | Medium | Low | Prometheus metrics for controller health |

#### Low Priority (Future)

| Improvement | Effort | Risk | Description |
|-------------|--------|------|-------------|
| mTLS Authentication | High | Medium | Mutual TLS for controller auth |
| Database Schema Evolution | Medium | Medium | Add `last_seen`, `status`, `version` to controllers table |
| Fleet Dashboard | High | Low | Real-time controller status visualization |

#### Recommended Implementation Order

1. **If registration fails frequently:** Add retry with exponential backoff
2. **If debugging is difficult:** Add health endpoints and metrics
3. **If security audit required:** Add rate limiting, then mTLS

---

## Phase 2 Roadmap

### Production Enhancements

- [ ] Set up monitoring/alerting (Prometheus/Grafana)
- [ ] Implement log aggregation (Loki stack)
- [ ] Frontend integration (connect React UI to live system)

### Cleanup Tasks

- [ ] Remove `controllers.py` (dead code in edge-controllers)
- [ ] Remove FastAPI/uvicorn from edge-controller requirements
- [ ] Document I2C troubleshooting in runbook
- [ ] Add build time metrics to deployment logs

### Testing

- [ ] Performance testing (rapid speed changes, sustained operation)
- [ ] Multi-motor configuration (M1, M3, M4)

---

## Quick Reference

### Commands

```bash
# Run frontend tests
cd frontend/web
npm run test           # RTL unit/integration tests
npm run test:e2e       # Playwright E2E tests

# Deploy
./scripts/tear-down.sh # Rebuild and deploy to edge controllers

# Check system status
curl http://localhost:8000/api/ping
curl http://localhost:8000/api/trains
```

### Key Files

| Area | File |
|------|------|
| Train Config Modal | `frontend/web/src/components/trains/TrainConfigModal.tsx` |
| Train API Types | `frontend/web/src/api/types.ts` |
| Backend Train Endpoint | `central_api/app/routers/trains.py` |
| Edge Controller Main | `edge-controllers/pi-template/app/main.py` |
| Direction Safety | `edge-controllers/pi-template/app/main.py` (`_ramp_speed`) |
| Deployment | `scripts/tear-down.sh` |

---

## Document History

| Date | Action |
|------|--------|
| 2025-12-04 | Consolidated from 4 TODO files after Train Config completion |
| — | Archived: `TRAIN_CONFIG_IMPLEMENTATION_PLAN.md` |
| — | Archived: `TRAIN_CONFIG_TODAY.md` |
| — | Archived: `controller-registration-improvements.md` |
| — | Archived: `WEB_UI_TESTING_STRATEGY.md` |

---

**Next Action:** Choose between:

1. **Expand frontend test coverage** (TrainControlPanel, TrainDetail)
2. **Connect React UI** to live deployment
3. **Add monitoring** (Prometheus + Grafana)
