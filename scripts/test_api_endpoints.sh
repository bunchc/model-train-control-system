#!/bin/bash
# test_api_endpoints.sh
# Script to validate central_api endpoints and check FastAPI server status
#
# This script provides comprehensive testing with integrated log monitoring:
# - Captures logs from all containers (mqtt, central_api, gateway, edge-controller)
# - Displays logs on failure for immediate debugging
# - Saves logs to timestamped files for post-mortem analysis
# - Monitors container health and startup

set -euo pipefail  # Exit on error, undefined var, or pipe failure

# Option to rebuild and restart Docker containers (default: yes)
REBUILD=${1:-yes}

export API_URL="http://localhost:8000/api"
export COMPOSE_FILE="infra/docker/docker-compose.yml"
export LOCAL_DEV=true
export COMPOSE_PROFILE="local-dev"
export EDGE_CONTROLLER_DOCKERFILE="Dockerfile-local"

# Insomnia test configuration
INSOMNIA_FILE="Model Train Control System API 0.1.0-wrk_8d50ef17b2464ceca69ec80fb936efc1.yaml"
ENVIRONMENT="OpenAPI env localhost:8000"

# Create logs directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="test-logs/${TIMESTAMP}"
mkdir -p "${LOG_DIR}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Test run: ${TIMESTAMP}"
echo "Logs will be saved to: ${LOG_DIR}"
echo ""

# Function to capture logs from all containers
capture_all_logs() {
  local prefix=$1
  echo "Capturing logs from all containers..."

  docker logs docker-mqtt-1 > "${LOG_DIR}/${prefix}_mqtt.log" 2>&1 || echo "mqtt container not running"
  docker logs docker-central_api-1 > "${LOG_DIR}/${prefix}_central_api.log" 2>&1 || echo "central_api container not running"
  docker logs docker-gateway-1 > "${LOG_DIR}/${prefix}_gateway.log" 2>&1 || echo "gateway container not running"
  docker logs docker-edge-controller-1 > "${LOG_DIR}/${prefix}_edge_controller.log" 2>&1 || echo "edge-controller container not running"
}

# Function to display logs on failure
display_logs_on_failure() {
  local component=$1
  echo ""
  echo "========================================"
  echo "FAILURE DETECTED - Displaying Container Logs"
  echo "========================================"
  echo ""

  echo "--- MQTT Broker Logs ---"
  docker logs docker-mqtt-1 2>&1 | tail -n 50

  echo ""
  echo "--- Central API Logs ---"
  docker logs docker-central_api-1 2>&1 | tail -n 50

  echo ""
  echo "Full logs saved to: ${LOG_DIR}"
  echo "========================================"
}

# Cleanup function
cleanup() {
  echo ""
  echo "Capturing final logs..."
  capture_all_logs "final"

  if [ "${REBUILD}" = "yes" ]; then
    echo "Stopping containers..."
    docker-compose -f "${COMPOSE_FILE}" down
  fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Stop and remove existing containers if rebuild requested
if [ "${REBUILD}" = "yes" ]; then
  echo "Stopping and removing existing containers..."
  docker-compose -f "${COMPOSE_FILE}" down
  echo ""
fi

# Start services
echo "Starting services..."
if [ "${REBUILD}" = "yes" ]; then
  echo "Building and starting containers..."
  docker-compose -f "${COMPOSE_FILE}" up --build -d mqtt central_api
else
  echo "Starting containers (no rebuild)..."
  docker-compose -f "${COMPOSE_FILE}" up -d mqtt central_api
fi

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Capture startup logs
capture_all_logs "startup"

# Wait for central_api to be healthy
echo "Checking central_api health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
  if curl -s -f "${API_URL}/config" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Central API is running${NC}"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Waiting for API... (${RETRY_COUNT}/${MAX_RETRIES})"
  sleep 2
done

if [ ${RETRY_COUNT} -eq ${MAX_RETRIES} ]; then
  echo -e "${RED}ERROR: Central API failed to start${NC}"
  display_logs_on_failure "central_api"
  exit 1
fi

echo ""
echo "======================================"
echo "Running API Tests with Inso CLI"
echo "======================================"
echo ""

inso run collection "wrk_8d50ef17b2464ceca69ec80fb936efc1" \
    --env "${ENVIRONMENT}" \
    --workingDir "${INSOMNIA_FILE}"

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "======================================"
if [ ${TEST_EXIT_CODE} -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    display_logs_on_failure "tests"
fi
echo "======================================"

exit ${TEST_EXIT_CODE}
  echo ""

  echo "--- MQTT Broker Logs ---"
  docker logs --tail 50 docker-mqtt-1 2>&1 || echo "mqtt container not available"
  echo ""

  echo "--- Central API Logs ---"
  docker logs --tail 50 docker-central_api-1 2>&1 || echo "central_api container not available"
  echo ""

  echo "--- Gateway Logs ---"
  docker logs --tail 50 docker-gateway-1 2>&1 || echo "gateway container not available"
  echo ""

  echo "--- Edge Controller Logs ---"
  docker logs --tail 50 docker-edge-controller-1 2>&1 || echo "edge-controller container not available"
  echo ""

  echo "========================================"
  echo "Full logs saved to: ${LOG_DIR}"
  echo "========================================"

  # Capture full logs
  capture_all_logs "failure"
}

# Trap errors and display logs
trap 'display_logs_on_failure "unknown"' ERR

# Function to tail logs in background (for monitoring during tests)
start_log_monitoring() {
  echo "Starting background log monitoring..."

  # Create named pipes for log streaming
  mkfifo "${LOG_DIR}/mqtt.fifo" 2>/dev/null || true
  mkfifo "${LOG_DIR}/central_api.fifo" 2>/dev/null || true
  mkfifo "${LOG_DIR}/edge_controller.fifo" 2>/dev/null || true

  # Start background log capture
  docker logs -f docker-mqtt-1 > "${LOG_DIR}/mqtt_live.log" 2>&1 &
  MQTT_LOG_PID=$!

  docker logs -f docker-central_api-1 > "${LOG_DIR}/central_api_live.log" 2>&1 &
  API_LOG_PID=$!

  docker logs -f docker-edge-controller-1 > "${LOG_DIR}/edge_controller_live.log" 2>&1 &
  EDGE_LOG_PID=$!

  echo "Log monitoring started (PIDs: mqtt=$MQTT_LOG_PID api=$API_LOG_PID edge=$EDGE_LOG_PID)"
}

# Function to stop log monitoring
stop_log_monitoring() {
  echo "Stopping background log monitoring..."
  kill $MQTT_LOG_PID 2>/dev/null || true
  kill $API_LOG_PID 2>/dev/null || true
  kill $EDGE_LOG_PID 2>/dev/null || true

  # Clean up named pipes
  rm -f "${LOG_DIR}"/*.fifo 2>/dev/null || true
}


if [ "$REBUILD" == "yes" ]; then
  echo "Rebuilding and restarting Docker containers..."
  docker compose --profile ${COMPOSE_PROFILE} -f ${COMPOSE_FILE} down || exit 1
  docker compose --profile ${COMPOSE_PROFILE} -f ${COMPOSE_FILE} build --no-cache || exit 1
  docker compose --profile ${COMPOSE_PROFILE} -f ${COMPOSE_FILE} up -d  || exit 1
else
  echo "Restarting Docker containers without rebuild..."
  docker compose --profile ${COMPOSE_PROFILE} -f ${COMPOSE_FILE} down || exit 1
  docker compose --profile ${COMPOSE_PROFILE} -f ${COMPOSE_FILE} up -d  || exit 1
fi

echo "Waiting for services to start..."
sleep 5

# Start background log monitoring
start_log_monitoring

echo "Waiting additional time for edge controller initialization..."
sleep 10


function check_server {
  echo "Checking if FastAPI server is running on port 8000 and /api/ping is reachable..."

  # Check if port is open
  if ! nc -z localhost 8000; then
    echo "ERROR: FastAPI server is NOT running on port 8000."
    display_logs_on_failure "central_api_port_check"
    return 1
  fi

  # Check /api/ping endpoint with retries
  local max_retries=5
  local retry_count=0

  while [ $retry_count -lt $max_retries ]; do
    if curl -sSf http://localhost:8000/api/ping > /dev/null 2>&1; then
      echo "✓ FastAPI server is running and /api/ping is reachable."
      return 0
    fi

    retry_count=$((retry_count + 1))
    echo "  Retry $retry_count/$max_retries - waiting for /api/ping..."
    sleep 2
  done

  echo "ERROR: FastAPI server is running, but /api/ping is NOT reachable after $max_retries attempts."
  display_logs_on_failure "central_api_ping_check"
  return 1
}


function check_mqtt {
  echo "Checking if MQTT server is running..."
  local status
  status=$(docker ps --filter "name=docker-mqtt-1" --format '{{.Status}}' 2>/dev/null || echo "")

  if [[ "$status" == Up* ]]; then
    echo "✓ MQTT server is running."

    # Additional check: try to connect to MQTT port
    if nc -z localhost 1883 2>/dev/null; then
      echo "✓ MQTT server is accepting connections on port 1883."
    else
      echo "WARNING: MQTT container running but port 1883 not accessible"
    fi
    return 0
  else
    echo "ERROR: MQTT server is NOT healthy. Status: ${status:-not found}"
    display_logs_on_failure "mqtt_check"
    return 1
  fi
}


function check_edge_controller {
  echo "Checking if edge-controller is running..."
  local status
  status=$(docker ps --filter "name=docker-edge-controller-1" --format '{{.Status}}' 2>/dev/null || echo "")

  if [[ "$status" == Up* ]]; then
    echo "✓ Edge controller is running."

    # Check if controller has logged successful initialization
    if docker logs docker-edge-controller-1 2>&1 | grep -q "MQTT client started successfully\|Running in simulation mode"; then
      echo "✓ Edge controller appears to have initialized successfully."
    else
      echo "WARNING: Edge controller running but initialization status unclear"
      echo "  Last 10 lines of edge controller log:"
      docker logs --tail 10 docker-edge-controller-1 2>&1 | sed 's/^/  /'
    fi
    return 0
  else
    echo "ERROR: Edge controller is NOT healthy. Status: ${status:-not found}"
    display_logs_on_failure "edge_controller_check"
    return 1
  fi
}

# List of Insomnia request IDs to run sequentially
INSO_REQUESTS=(
  "req_d23d9496dcb24bb6a1642eabdc9fb39b" # Read Root
  "req_04efebeb40a04d5cbddbd7b7e52c9195" # Get config for edge controller
  "req_4ffd4a0d380640b5a0902f052e3422ec" # List all edge controllers
  "req_11fe132ca9b148769bc7b47b992aa759" # Get config for train
  "req_c3d15f1ed5ef49feb82755ac715dca32" # List all configured trains
  "req_006c87b4839a40bab576ef051f7c7279" # Get entire config
  "req_ed3a7511d0534758b3235e933a342a6f" # List plugins
  "req_4ecbac26047c4b07adf872da0e4d8bdd" # Get Status
  "req_735a0132ecd948b5a5c4024e04ba08d1" # Send Command
  "req_010ca9f3c40049168dedc812020c79d2" # List Trains
)

function run_insomnia_tests {
  if [ "$RUN_ALL" == "yes" ]; then
    echo -e "\nRunning full Insomnia collection..."
    if ! inso run collection wrk_faf1be --env env_7c7a2f7957 --reporter min --bail; then
      display_logs_on_failure "insomnia_collection"
      return 1
    fi
  else
    echo -e "\nRunning Insomnia requests one at a time..."
    for req_id in "${INSO_REQUESTS[@]}"; do
      echo -e "\nRunning Insomnia request: $req_id"
      if ! inso run collection wrk_faf1be --env env_7c7a2f7957 --item "$req_id" --reporter min; then
        echo -e "\nInsomnia run failed."
        display_logs_on_failure "insomnia_${req_id}"
        return 1
      fi
    done
  fi
  echo "✓ All Insomnia tests passed."
  return 0
}

function run_tests {
  echo ""
  echo "========================================"
  echo "Starting Health Checks"
  echo "========================================"

  check_mqtt || exit 1
  check_server || exit 1
  check_edge_controller || exit 1

  echo ""
  echo "========================================"
  echo "All Health Checks Passed - Starting Tests"
  echo "========================================"

  echo -e "\n[1/2] Running pytest integration tests..."
  if ! PYTHONPATH=. pytest tests/integration/ -v --tb=short; then
    echo -e "\nERROR: Pytest integration test failed."
    display_logs_on_failure "pytest"
    return 1
  fi
  echo "✓ Pytest tests passed."

  # Check if inso is installed before running Insomnia tests
  if command -v inso &> /dev/null; then
    echo -e "\n[2/2] Running Insomnia API tests..."
    if ! run_insomnia_tests; then
      return 1
    fi
  else
    echo -e "\n[2/2] Skipping Insomnia tests (inso not installed)"
    echo "  Install with: npm install -g insomnia-inso"
  fi

  echo ""
  echo "========================================"
  echo "✓ All Tests Passed Successfully!"
  echo "========================================"

  # Capture final logs
  capture_all_logs "success"

  return 0
}

# Main execution
run_tests
TEST_RESULT=$?

# Stop log monitoring
stop_log_monitoring

# Clean exit
if [ $TEST_RESULT -eq 0 ]; then
  echo ""
  echo "Test logs saved to: ${LOG_DIR}"
  echo "To view logs: ls -lh ${LOG_DIR}/"
  exit 0
else
  echo ""
  echo "Tests failed. Full logs available at: ${LOG_DIR}"
  exit 1
fi
