# Central API for Model Train Control System

This directory contains the implementation of the central API for the model train control system. The central API serves as the orchestrator for managing train commands and telemetry data.

## Overview

The central API is built using FastAPI and provides a RESTful interface for controlling and monitoring the model trains. It communicates with the edge controllers via MQTT to send commands and receive telemetry data.

## Directory Structure

- **app/**: Contains the main application code.
  - **main.py**: Entry point for the FastAPI application.
  - **routers/**: Contains API route definitions.
    - **trains.py**: API endpoints related to train control.
  - **services/**: Contains business logic and service layers.
    - **mqtt_adapter.py**: Logic for interacting with the MQTT broker.
  - **models/**: Contains data models and schemas.
    - **schemas.py**: Defines request and response formats.

- **requirements.txt**: Lists the Python dependencies required for the central API.

- **Dockerfile**: Instructions for building a Docker image for the central API.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Docker (optional, for containerization)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
  cd model-train-control-system/central_api
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the API

To run the API locally, execute the following command:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

To build and run the Docker container, use the following commands:
```
docker build -t central_api .
docker run -p 8000:8000 central_api
```

### API Endpoints

- **GET /api/trains**: List available trains.
- **POST /api/trains/{id}/command**: Send a control command to a specific train.
- **GET /api/trains/{id}/status**: Get the current telemetry of a specific train.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.