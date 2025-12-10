echo "All required files exist. Running Docker Compose..."
docker compose -f infra/docker/docker-compose.e2e.yaml up --remove-orphans
