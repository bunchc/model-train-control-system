#!/bin/bash

# Update the package list and upgrade installed packages
sudo apt-get update
sudo apt-get upgrade -y

# Install necessary packages
sudo apt-get install -y python3 python3-pip python3-dev python3-venv git

# Clone the Raspberry Pi controller template
git clone https://github.com/your-repo/pi-template.git /home/pi/pi-controller

# Navigate to the cloned directory
cd /home/pi/pi-controller

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt

# Start the application (this can be modified to run as a service)
python3 app/main.py &

echo "Raspberry Pi provisioning complete. The controller is now running."
