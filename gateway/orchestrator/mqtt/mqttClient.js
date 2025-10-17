const mqtt = require('mqtt');

class MqttClient {
    constructor(brokerUrl, options) {
        this.brokerUrl = brokerUrl;
        this.options = options;
        this.client = null;
    }

    connect() {
        this.client = mqtt.connect(this.brokerUrl, this.options);

        this.client.on('connect', () => {
            console.log('Connected to MQTT broker');
        });

        this.client.on('error', (err) => {
            console.error('Connection error: ', err);
        });
    }

    subscribe(topic, callback) {
        if (this.client) {
            this.client.subscribe(topic, (err) => {
                if (err) {
                    console.error('Subscription error: ', err);
                } else {
                    console.log(`Subscribed to topic: ${topic}`);
                }
            });

            this.client.on('message', (topic, message) => {
                callback(topic, message.toString());
            });
        }
    }

    publish(topic, message) {
        if (this.client) {
            this.client.publish(topic, message, (err) => {
                if (err) {
                    console.error('Publish error: ', err);
                } else {
                    console.log(`Message published to topic: ${topic}`);
                }
            });
        }
    }

    disconnect() {
        if (this.client) {
            this.client.end(() => {
                console.log('Disconnected from MQTT broker');
            });
        }
    }
}

module.exports = MqttClient;