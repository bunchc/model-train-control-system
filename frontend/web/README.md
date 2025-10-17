# Frontend Web Application for Model Train Control System

This directory contains the frontend web application for the Model Train Control System. The application is built using React and TypeScript, providing a responsive user interface for controlling and monitoring model trains.

## Getting Started

To get started with the frontend application, follow these steps:

1. **Install Dependencies**: Make sure you have Node.js installed. Then, navigate to this directory and run:
   ```
   npm install
   ```

2. **Run the Application**: After installing the dependencies, you can start the development server with:
   ```
   npm start
   ```

3. **Access the Application**: Open your web browser and go to `http://localhost:3000` to access the application.

## Project Structure

- `src/`: Contains the source code for the application.
  - `App.tsx`: The main component that sets up routing and renders the dashboard.
  - `components/`: Contains reusable components for the application.
    - `Dashboard.tsx`: Displays real-time telemetry data and controls for the trains.
  - `services/`: Contains service files for handling business logic.
    - `mqtt.ts`: Manages the MQTT client for the frontend, handling subscriptions and publishing commands.

## Features

- Real-time dashboard displaying train telemetry data.
- Controls for starting, stopping, and adjusting the speed of trains.
- Responsive design for use on various devices.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.