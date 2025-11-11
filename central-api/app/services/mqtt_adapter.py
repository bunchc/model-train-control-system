from paho.mqtt import client as mqtt

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
        adapter.publish(topic, str(command))
        return True
    except Exception as e:
        print(f"MQTT publish error: {e}")
        return False

def get_train_status(train_id):
    # This is a stub. Replace with real MQTT subscribe logic as needed.
    # For now, just return a dummy status.
    return {
        "train_id": train_id,
        "speed": 50,
        "voltage": 12.3,
        "current": 0.8,
        "position": "section_A"
    }