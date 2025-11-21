# Onboarding Documentation for Model Train Control System

Welcome to the Model Train Control System! This document serves as an onboarding guide for new developers joining the project. Below are the key steps and resources to help you get started.

## Prerequisites

Before you begin, ensure you have the following installed on your development machine:

- Python 3.7 or higher
- Node.js and npm
- Docker and Docker Compose
- Git

## Project Structure

Familiarize yourself with the project structure:

```text
model-train-control-system/
├── edge-controllers/          # Raspberry Pi controllers for trains
├── central_api/               # Central API for managing train commands
├── gateway/                   # Gateway for communication between frontend and backend
├── frontend/                  # Frontend web application
├── infra/                     # Infrastructure as code (Docker, Kubernetes, Terraform)
├── persistence/               # Database initialization scripts
├── scripts/                   # Utility scripts for provisioning and deployment
├── tests/                     # Test cases for integration and unit testing
└── docs/                      # Documentation
```

## Getting Started

1. **Clone the Repository**

   Start by cloning the repository to your local machine:

   ```bash
   git clone <repository-url>
   cd model-train-control-system
   ```

2. **Set Up Edge Controllers**

   Navigate to the `edge-controllers/pi-template` directory and follow the instructions in the `README.md` file to set up the Raspberry Pi controllers.

3. **Set Up Central API**

   Go to the `central_api` directory and refer to the `README.md` for instructions on setting up the central API.

4. **Set Up Gateway**

   In the `gateway/orchestrator` directory, follow the `README.md` to configure the gateway application.

5. **Set Up Frontend**

   Navigate to the `frontend/web` directory and follow the instructions in the `README.md` to set up the frontend application.

6. **Run the Application**

   Use Docker Compose to run the entire application stack. Navigate to the `infra/docker` directory and execute:

   ```bash
   docker-compose up
   ```

## Development Workflow

- **Branching**: Use feature branches for new developments. Follow the naming convention `feature/<feature-name>`.
- **Code Reviews**: Submit pull requests for code reviews before merging into the main branch.
- **Testing**: Write tests for new features and run existing tests to ensure stability.

## Resources

- **Documentation**: Refer to the `docs` directory for detailed documentation on architecture, MQTT topics, and onboarding.
- **Community**: Join the project’s communication channels (e.g., Slack, Discord) for support and collaboration.

## Conclusion

We are excited to have you on board! If you have any questions or need assistance, feel free to reach out to the team. Happy coding!
