#!/usr/bin/env bash
set -euo pipefail

# Define constants for paths and filenames
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
CENTRAL_API_DIR="${PROJECT_ROOT}/central_api"
CONFIG_DB="central_api_config.db"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/infra/docker/docker-compose.yml"
VOLUME_NAME="docker_central_api_data"

# Display status of local and remote Docker services before tear-down
echo "=== Local Services ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo -e "\n=== Pi Edge Controllers ==="
ssh pi@192.168.2.214 "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Begin tear-down process
echo "=== Cleanup Local Services ==="

# Remove configuration database files if they exist
rm -f "${CONFIG_DB}" "${CENTRAL_API_DIR}/${CONFIG_DB}" || echo "No local db files to remove."

# Stop and remove Docker containers using the local-dev profile
docker compose -f "${DOCKER_COMPOSE_FILE}" --profile local-dev down || {
    echo "Error: Failed to stop and remove Docker containers."
    exit 1
}

# Remove Docker volume if it exists
if docker volume inspect "${VOLUME_NAME}" > /dev/null 2>&1; then
    docker volume rm "${VOLUME_NAME}" || {
        echo "Error: Failed to remove Docker volume ${VOLUME_NAME}."
        exit 1
    }
else
    echo "Docker volume ${VOLUME_NAME} does not exist. Skipping removal."
fi

ssh pi@192.168.2.214 'docker stop edge-controller-m1 edge-controller-m3' || {
    echo "Error: Failed to stop edge controllers on remote Pi."
    exit 1
} && {
    echo "Successfully stopped edge controllers on remote Pi."
    ssh pi@192.168.2.214 'docker rm edge-controller-m1 edge-controller-m3' || {
        echo "Error: Failed to remove edge controllers on remote Pi."
        exit 1
    }
}

# Post tear-down status
echo "=== Local Services ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo -e "\n=== Pi Edge Controllers ==="
ssh pi@192.168.2.214 "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Stand things back up
docker compose -f "${DOCKER_COMPOSE_FILE}" --profile local-dev build || {
    echo "Error: Failed to build Docker images."
    exit 1
} && echo "Successfully built Docker images."

docker compose -f "${DOCKER_COMPOSE_FILE}" --profile local-dev up -d || {
    echo "Error: Failed to start Docker containers."
    exit 1
} && echo "Successfully started Docker containers."

ansible-playbook -i ${PROJECT_ROOT}/infra/ansible/inventory/production/hosts.yml \
    ${PROJECT_ROOT}/infra/ansible/playbooks/deploy_edge_multi_motor.yml \
    --vault-password-file ${PROJECT_ROOT}/infra/ansible/.vault_pass || {
    echo "Error: Failed to deploy edge controllers via Ansible."
    exit 1
} && echo "Successfully deployed edge controllers via Ansible."
