### Issue

Integrate real train status endpoint with actual MQTT and hardware responses.

- Background/context: The current `/api/trains/{train_id}/status` endpoint returns mock data. It should query the edge controller via MQTT and return live telemetry.
- Expected outcome: The endpoint returns real-time status for any train, matching the OpenAPI schema.

### Definition of Done

- [ ] Code implemented and reviewed
- [ ] Tests written/passed
- [ ] Documentation updated
- [ ] Stakeholder approval received

### Verification

- Steps to test or validate:
  - Deploy edge controller and central API locally.
  - Send status request to `/api/trains/{train_id}/status`.
  - Confirm response matches live train telemetry.
- Acceptance criteria:
  - [ ] Confirm feature behaves as expected in staging
  - [ ] Verify no regressions in related components

### Notes (optional)

- See docs/mqtt-topics.md for topic conventions.
- Reference edge-controllers/pi-template/app/mqtt_client.py for status publishing.

- Integration with edge controller: ensure it calls /status/update to push status.
- Update central API and gateway logic to use DB for status, not MQTT.
- Expand integration tests to cover new status flow.
- Update documentation (OpenAPI spec, onboarding, etc.) to reflect new status endpoint and flow.
