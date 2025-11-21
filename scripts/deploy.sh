#!/bin/bash

# This script deploys the model train control system components.

# Deploy the edge controllers
echo "Deploying edge controllers..."
cd edge-controllers/pi-template
docker build -t model-train-controller .
docker run -d --name train-controller model-train-controller

# Deploy the central API
echo "Deploying central API..."
cd ../../central_api
docker build -t central_api .
docker run -d --name central_api -p 8000:8000 central_api

# Deploy the gateway
echo "Deploying gateway..."
cd ../gateway/orchestrator
docker build -t train-gateway .
docker run -d --name train-gateway -p 3000:3000 train-gateway

# Notify completion
echo "Deployment completed successfully!"
