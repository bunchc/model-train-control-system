import { Client, connect } from 'mqtt';

const MQTT_BROKER_URL = 'ws://your-mqtt-broker-url:port'; // Replace with your MQTT broker URL
const client = connect(MQTT_BROKER_URL);

const MQTT_TOPICS = {
    COMMANDS: 'trains/+/commands',
    STATUS: 'trains/+/status',
};

client.on('connect', () => {
    console.log('Connected to MQTT broker');
    client.subscribe(MQTT_TOPICS.STATUS, (err) => {
        if (err) {
            console.error('Failed to subscribe to status topic:', err);
        }
    });
});

client.on('message', (topic, message) => {
    const payload = JSON.parse(message.toString());
    console.log(`Received message on topic ${topic}:`, payload);
    // Handle incoming messages based on topic
});

export const sendCommand = (trainId, command) => {
    const topic = `trains/${trainId}/commands`;
    client.publish(topic, JSON.stringify(command), { qos: 1 }, (err) => {
        if (err) {
            console.error('Failed to send command:', err);
        } else {
            console.log(`Command sent to ${topic}:`, command);
        }
    });
};