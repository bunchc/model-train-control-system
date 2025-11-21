### Issue

Verify MQTT topic and schema alignment between API, edge controller, and gateway.

- Background/context: MQTT topics and payloads must match across all components for reliable communication. Discrepancies can cause command/status failures.
- Expected outcome: All MQTT topics and payloads are consistent and match docs/mqtt-topics.md and OpenAPI schemas.

### Definition of Done

- [ ] Code implemented and reviewed
- [ ] Tests written/passed
- [ ] Documentation updated
- [ ] Stakeholder approval received

### Verification

- Steps to test or validate:
  - Review MQTT topic usage in API, edge controller, gateway, and frontend.
  - Confirm payload shapes match OpenAPI and docs/mqtt-topics.md.
- Acceptance criteria:
  - [ ] Confirm feature behaves as expected in staging
  - [ ] Verify no regressions in related components

### Notes (optional)

- Reference docs/mqtt-topics.md and central_api/app/models/schemas.py.
