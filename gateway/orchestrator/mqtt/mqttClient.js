const mqtt = require('mqtt');

let client = null;

function connect(brokerUrl = 'mqtt://mqtt:1883', options = {}) {
    client = mqtt.connect(brokerUrl, options);
    client.on('connect', () => {
        console.log('Connected to MQTT broker');
    });
    client.on('error', (err) => {
        console.error('Connection error: ', err);
    });
}

function subscribe(topic, callback) {
    if (client) {
        client.subscribe(topic, (err) => {
            if (err) {
                console.error('Subscription error: ', err);
            } else {
                console.log(`Subscribed to topic: ${topic}`);
            }
        });
        client.on('message', (topic, message) => {
            callback(topic, message.toString());
        });
    }
}

function publish(topic, message) {
    if (client) {
        client.publish(topic, message, (err) => {
            if (err) {
                console.error('Publish error: ', err);
            } else {
                console.log(`Message published to topic: ${topic}`);
            }
        });
    }
}

module.exports = {
    connect,
    subscribe,
    publish
};
