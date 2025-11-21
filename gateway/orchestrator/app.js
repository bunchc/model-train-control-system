const express = require('express');
const bodyParser = require('body-parser');

const commandsRouter = require('./controllers/commands');
const mqttClient = require('./mqtt/mqttClient');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());

// Use the commands router for train commands and status
app.use('/api/trains', commandsRouter);

// Start the MQTT client
mqttClient.connect();

// Start the Express server
app.listen(PORT, () => {
    console.log(`Gateway server is running on http://localhost:${PORT}`);
});
