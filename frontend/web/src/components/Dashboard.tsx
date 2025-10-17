import React, { useEffect, useState } from 'react';
import { mqttClient } from '../services/mqtt';

const Dashboard = () => {
    const [trains, setTrains] = useState([]);
    const [selectedTrain, setSelectedTrain] = useState(null);
    const [telemetry, setTelemetry] = useState({});

    useEffect(() => {
        const fetchTrains = async () => {
            const response = await fetch('/api/trains');
            const data = await response.json();
            setTrains(data);
        };

        fetchTrains();

        const handleTelemetryUpdate = (message) => {
            const data = JSON.parse(message.data);
            setTelemetry((prev) => ({ ...prev, [data.trainId]: data }));
        };

        mqttClient.on('message', handleTelemetryUpdate);

        return () => {
            mqttClient.off('message', handleTelemetryUpdate);
        };
    }, []);

    const sendCommand = async (command) => {
        await fetch(`/api/trains/${selectedTrain}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(command),
        });
    };

    return (
        <div>
            <h1>Train Dashboard</h1>
            <select onChange={(e) => setSelectedTrain(e.target.value)} value={selectedTrain}>
                <option value="">Select a Train</option>
                {trains.map((train) => (
                    <option key={train.id} value={train.id}>
                        {train.name}
                    </option>
                ))}
            </select>
            {selectedTrain && (
                <div>
                    <h2>Telemetry for Train {selectedTrain}</h2>
                    <pre>{JSON.stringify(telemetry[selectedTrain], null, 2)}</pre>
                    <button onClick={() => sendCommand({ action: 'start' })}>Start</button>
                    <button onClick={() => sendCommand({ action: 'stop' })}>Stop</button>
                    <button onClick={() => sendCommand({ action: 'setSpeed', speed: 50 })}>Set Speed to 50</button>
                </div>
            )}
        </div>
    );
};

export default Dashboard;