### Issue

Update and expand integration tests for real train status and command endpoints.

- Background/context: Integration tests should cover real MQTT flows and DB-backed config endpoints. Current tests may only cover mock data.
- Expected outcome: Integration tests validate end-to-end flows for status, command, and config endpoints using real data.

### Definition of Done

- [ ] Code implemented and reviewed
- [ ] Tests written/passed
- [ ] Documentation updated
- [ ] Stakeholder approval received

### Verification

- Steps to test or validate:
  - Run integration tests in tests/integration and scripts/test_api_endpoints.sh.
  - Confirm tests pass with real edge controller and API.
- Acceptance criteria:
  - [ ] Confirm feature behaves as expected in staging
  - [ ] Verify no regressions in related components

### Notes (optional)

- Reference tests/integration/test_end_to_end.py and scripts/test_api_endpoints.sh.
