### Issue
Integrate real train command endpoint with actual MQTT and hardware responses.
- Background/context: The current `/api/trains/{train_id}/command` endpoint sends mock commands. It should publish to the correct MQTT topic and confirm delivery.
- Expected outcome: The endpoint reliably sends commands to the train and receives confirmation.

### Definition of Done
- [ ] Code implemented and reviewed
- [ ] Tests written/passed
- [ ] Documentation updated
- [ ] Stakeholder approval received

### Verification
- Steps to test or validate:
  - Send command to `/api/trains/{train_id}/command`.
  - Confirm command is published to MQTT and train acts accordingly.
- Acceptance criteria:
  - [ ] Confirm feature behaves as expected in staging
  - [ ] Verify no regressions in related components

### Notes (optional)
- See docs/mqtt-topics.md for command payloads.
- Reference edge-controllers/pi-template/app/mqtt_client.py for command handling.