# MQTT Topics Documentation

This document outlines the MQTT topics used in the model train control system, detailing their purpose and structure.

## Topic Structure

The MQTT topics follow a hierarchical structure to facilitate organization and clarity. The general format is:

```
trains/{train_id}/{action}
```

### Topics

1. **Train Commands**
   - **Topic:** `trains/{train_id}/commands`
   - **Description:** This topic is used to send control commands to a specific train. Commands can include actions such as starting, stopping, and setting speed.
   - **Example Payload:**
     ```json
     {
       "action": "start"
     }
     ```

2. **Train Status**
   - **Topic:** `trains/{train_id}/status`
   - **Description:** This topic is used to publish the current status and telemetry data of a specific train. It includes information such as speed, voltage, and position.
   - **Example Payload:**
     ```json
     {
       "speed": 50,
       "voltage": 12,
       "position": "section_3"
     }
     ```

3. **Train Discovery**
   - **Topic:** `trains/discovery`
   - **Description:** This topic is used for broadcasting the presence of a new train in the system. When a new train connects, it publishes its information to this topic.
   - **Example Payload:**
     ```json
     {
       "train_id": "1",
       "model": "Steam Engine"
     }
     ```

4. **Configuration Updates**
   - **Topic:** `trains/{train_id}/config`
   - **Description:** This topic is used to send configuration updates to a specific train. This can include changes to operational parameters or settings.
   - **Example Payload:**
     ```json
     {
       "max_speed": 100,
       "light_enabled": true
     }
     ```

## Notes

- Replace `{train_id}` with the actual identifier of the train when using the topics.
- Ensure that all commands and status updates are published in a timely manner to maintain synchronization between the central API and the edge controllers.