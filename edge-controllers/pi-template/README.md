# Raspberry Pi Train Controller

This directory contains the implementation for the Raspberry Pi controller that manages a model train. The controller interfaces with the train's hardware components and communicates with a central API via MQTT.

## Directory Structure

- **app/**: Contains the main application code.
  - **main.py**: Entry point for the Raspberry Pi controller.
  - **controllers.py**: Logic for handling train commands (start, stop, set speed).
  - **hardware.py**: Interfaces with the train's hardware (motors, lights, sensors).
  - **mqtt_client.py**: Manages the MQTT client for communication with the central API.

- **requirements.txt**: Lists the Python dependencies required for the Raspberry Pi controller.

- **Dockerfile**: Instructions for building a Docker image for the Raspberry Pi controller.

## Setup Instructions

1. **Clone the Repository**: 
   ```bash
   git clone <repository-url>
   cd model-train-control-system/edge-controllers/pi-template
   ```

2. **Install Dependencies**: 
   You can install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**: 
   Execute the main application script:
   ```bash
   python app/main.py
   ```

4. **Docker Setup** (Optional): 
   If you prefer to run the application in a Docker container, build the Docker image:
   ```bash
   docker build -t pi-controller .
   ```
   Then run the container:
   ```bash
   docker run --rm pi-controller
   ```

## Run locally with Docker Compose (recommended for development)

The repository includes a local Compose stack that runs an MQTT broker, central API, gateway and a sample edge-controller. From the project root run:

```bash
cd infra/docker
docker compose up --build
```

Notes:
- The compose file uses Eclipse Mosquitto as the MQTT broker (ports 1883 and 9001 exposed).
- The `edge-controller` service in Compose builds the `edge-controllers/pi-template` Dockerfile and sets `MQTT_BROKER=mqtt` and `MQTT_PORT=1883` in its environment.
- Use the frontend at `http://localhost:3000` and the API at `http://localhost:8000` by default.


## Configuration

You can customize the behavior of the Raspberry Pi controller by modifying the configuration settings in the `examples/pi-config.yaml` file.

## Usage

Once the controller is running, it will listen for commands from the central API and publish telemetry data about the train's status. You can control the train using the provided API endpoints.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.