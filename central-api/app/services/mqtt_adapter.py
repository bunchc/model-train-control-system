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