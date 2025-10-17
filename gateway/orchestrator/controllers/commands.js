const express = require('express');
const router = express.Router();
const mqttClient = require('../mqtt/mqttClient');

// Start a train
router.post('/:id/start', (req, res) => {
    const trainId = req.params.id;
    mqttClient.publish(`trains/${trainId}/commands`, JSON.stringify({ command: 'start' }));
    res.status(200).send({ message: `Train ${trainId} started` });
});

// Stop a train
router.post('/:id/stop', (req, res) => {
    const trainId = req.params.id;
    mqttClient.publish(`trains/${trainId}/commands`, JSON.stringify({ command: 'stop' }));
    res.status(200).send({ message: `Train ${trainId} stopped` });
});

// Set speed of a train
router.post('/:id/setSpeed', (req, res) => {
    const trainId = req.params.id;
    const { speed } = req.body;
    mqttClient.publish(`trains/${trainId}/commands`, JSON.stringify({ command: 'setSpeed', speed }));
    res.status(200).send({ message: `Train ${trainId} speed set to ${speed}` });
});

// Get status of a train
router.get('/:id/status', (req, res) => {
    const trainId = req.params.id;
    // Here you would typically retrieve the status from a database or another service
    res.status(200).send({ message: `Status for train ${trainId}` });
});

module.exports = router;