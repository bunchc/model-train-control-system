### Issue

Ensure all config endpoints return real DB-backed data.

- Background/context: Some config endpoints may still return mock or static data. They should query the SQLite DB via ConfigManager.
- Expected outcome: All config endpoints return up-to-date, persistent configuration data.

### Definition of Done

- [ ] Code implemented and reviewed
- [ ] Tests written/passed
- [ ] Documentation updated
- [ ] Stakeholder approval received

### Verification

- Steps to test or validate:
  - Query config endpoints and confirm data matches DB state.
- Acceptance criteria:
  - [ ] Confirm feature behaves as expected in staging
  - [ ] Verify no regressions in related components

### Notes (optional)

- Reference central_api/app/services/config_manager.py for DB logic.
