# Model Train Control System

This project is a distributed control system for model trains, designed to provide modular, scalable, and resilient control over multiple trains using Raspberry Pi devices. The architecture consists of several layers, including edge controllers, a central API, a gateway, a frontend interface, and optional persistence and cloud layers.

## Project Structure

- **edge-controllers**: Contains the Raspberry Pi controllers for each train or track segment.
  - **pi-template**: A template for creating Raspberry Pi applications.
  - **examples**: Example configuration files for the Raspberry Pi controllers.

- **central-api**: The central API that coordinates commands and telemetry data between the frontend and the edge controllers.

- **gateway**: Acts as a bridge between the frontend and the central API, handling command processing and MQTT communication.

- **frontend**: The web interface for controlling the trains and visualizing telemetry data.

- **infra**: Infrastructure-related files, including Docker configurations, Kubernetes manifests, and Terraform scripts.

- **persistence**: Scripts for initializing databases for telemetry data storage.

- **scripts**: Utility scripts for provisioning and deploying the application.

- **tests**: Contains unit and integration tests for the system.

- **docs**: Documentation for the architecture, MQTT topics, and onboarding new developers.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.x
- Node.js and npm
- Raspberry Pi devices (for edge controllers)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd model-train-control-system
   ```

2. Set up the edge controllers:
   - Navigate to `edge-controllers/pi-template` and follow the instructions in the README.md file.

3. Set up the central API:
   - Navigate to `central-api` and follow the instructions in the README.md file.

4. Set up the gateway:
   - Navigate to `gateway/orchestrator` and follow the instructions in the README.md file.

5. Set up the frontend:
   - Navigate to `frontend/web` and follow the instructions in the README.md file.

6. (Optional) Set up persistence:
   - Follow the instructions in the `persistence` directory to initialize the databases.

### Running the Application

- Use Docker Compose to start the entire application:
  ```
  cd infra/docker
  docker-compose up
  ```

- Access the frontend at `http://localhost:3000`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.