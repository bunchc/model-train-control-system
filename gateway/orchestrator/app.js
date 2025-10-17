const express = require('express');
const bodyParser = require('body-parser');
const commandsController = require('./controllers/commands');
const mqttClient = require('./mqtt/mqttClient');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());

// Routes
app.post('/api/trains/:id/command', commandsController.handleCommand);
app.get('/api/trains/:id/status', commandsController.getStatus);

// Start the MQTT client
mqttClient.connect();

// Start the Express server
app.listen(PORT, () => {
    console.log(`Gateway server is running on http://localhost:${PORT}`);
});