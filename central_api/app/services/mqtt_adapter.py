from paho.mqtt import client as mqtt
import json

class MQTTAdapter:
    def __init__(self, broker_address, train_id):
        self.broker_address = broker_address
        self.train_id = train_id
        self.client = mqtt.Client()

    def connect(self):
        self.client.connect(self.broker_address)

    def subscribe(self, topic, on_message):
        self.client.subscribe(topic)
        self.client.on_message = on_message

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

# Example publish_command and get_train_status functions
def publish_command(train_id, command):
    # This is a stub. Replace with real MQTT publish logic as needed.
    try:
        adapter = MQTTAdapter(broker_address="mqtt", train_id=train_id)
        adapter.connect()
        topic = f"trains/{train_id}/commands"
        # Serialize command to JSON for compatibility
        if hasattr(command, 'dict'):
            payload = json.dumps(command.dict())
        else:
            payload = json.dumps(command)
        adapter.publish(topic, payload)
        return True
    except Exception as e:
        print(f"MQTT publish error: {e}")
        return False

def get_train_status(train_id, local_testing=True):
    from models.schemas import TrainStatus
    if local_testing:
        return TrainStatus(
            train_id=train_id,
            speed=50,
            voltage=12.3,
            current=0.8,
            position="section_A"
        )
    else:
        # Fetch real status from MQTT
        status_topic = f"trains/{train_id}/status"
        result = {}
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                result.update(payload)
            except Exception as e:
                print(f"Error decoding MQTT status: {e}")
        adapter = MQTTAdapter(broker_address="mqtt", train_id=train_id)
        adapter.connect()
        adapter.client.on_message = on_message
        adapter.client.subscribe(status_topic)
        adapter.client.loop_start()
        import time
        timeout = 2  # seconds
        start = time.time()
        while not result and time.time() - start < timeout:
            time.sleep(0.1)
        adapter.client.loop_stop()
        if result:
            return TrainStatus(**result)
        else:
            return None