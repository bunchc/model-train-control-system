#!/bin/bash
# test_api_endpoints.sh

# Multi-suite test orchestration script for model train control system
#
# Supports TEST_SUITE env var: playwright (default), pytest, insomnia, all, none
# - Captures logs from all containers (mqtt, central_api, gateway, edge-controller)
# - Displays logs on failure for immediate debugging
# - Saves logs to timestamped files for post-mortem analysis
# - Monitors container health and startup
# - Runs selected test suite(s) with robust error handling

set -euo pipefail

# --------------------
# Constants & Defaults
# --------------------
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly LOG_DIR="${PROJECT_ROOT}/test-logs/${TIMESTAMP}"
readonly EDGE_CONF_TMP="${PROJECT_ROOT}/.tmp/edge-controller.conf"
readonly COMPOSE_FILE="${PROJECT_ROOT}/infra/docker/docker-compose.e2e.yaml"
readonly COMPOSE_PROJECT_NAME="test_env"
readonly API_URL="http://localhost:8100/api"
readonly INSOMNIA_FILE="${PROJECT_ROOT}/Model Train Control System API 0.1.0-wrk_8d50ef17b2464ceca69ec80fb936efc1.yaml"
readonly ENVIRONMENT="OpenAPI env localhost:8000"
readonly LOG_LEVEL="${LOG_LEVEL:-info}"
readonly CLEANUP_ON_SUCCESS="${CLEANUP_ON_SUCCESS:-no}"
readonly TEST_FRONTEND_HOST="${TEST_FRONTEND_HOST:-localhost}"
readonly TEST_FRONTEND_PORT="${TEST_FRONTEND_PORT:-5174}"
readonly TEST_API_HOST="${TEST_API_HOST:-localhost}"
readonly TEST_API_PORT="${TEST_API_PORT:-8100}"
readonly TEST_MQTT_HOST="${TEST_MQTT_HOST:-localhost}"
readonly TEST_MQTT_PORT="${TEST_MQTT_PORT:-18884}"
readonly REBUILD="${REBUILD:-yes}"
readonly KEEP_RUNNING="${KEEP_RUNNING:-no}"
readonly TEST_SUITE="${TEST_SUITE:-playwright}"
readonly HEALTH_RETRY_COUNT="${HEALTH_RETRY_COUNT:-5}"
readonly TRAIN_RETRY_COUNT="${TRAIN_RETRY_COUNT:-10}"

# Ansible provisioning defaults
USE_ANSIBLE="${USE_ANSIBLE:-1}"
CLEANUP="${CLEANUP:-1}"
ANSIBLE_PLAYBOOK_PATH="${PROJECT_ROOT}/infra/ansible/playbooks/deploy_edge_test.yml"
ANSIBLE_INVENTORY_PATH="${PROJECT_ROOT}/infra/ansible/inventory/test/hosts.yml"

# --------------------
# Helper Functions
# --------------------

# Prints error message to STDERR
err() {
  echo "[ERROR] $*" >&2
}

# Logging function with levels
log_msg() {
  local level="$1"; shift
  local msg="$*"
  case "${level}" in
    error) [[ "${LOG_LEVEL}" =~ error|warn|info|debug ]] && echo "[ERROR] ${msg}" >&2 ;;
    warn)  [[ "${LOG_LEVEL}" =~ warn|info|debug ]] && echo "[WARN] ${msg}" ;;
    info)  [[ "${LOG_LEVEL}" =~ info|debug ]] && echo "[INFO] ${msg}" ;;
    debug) [[ "${LOG_LEVEL}" == debug ]] && echo "[DEBUG] ${msg}" ;;
  esac
  echo "[$(date +%H:%M:%S)] [${level}] ${msg}" >> "${LOG_DIR}/run.log"
}

# Checks for required files and exits if any are missing
check_required_files() {
  local required_files=(
    "${PROJECT_ROOT}/config.test.yaml"
    "${PROJECT_ROOT}/.tmp/edge-controller.conf"
    "${PROJECT_ROOT}/infra/docker/mosquitto/mosquitto.conf"
  )
  local missing=0
  for file in "${required_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
      err "Required file '${file}' does not exist!"
      missing=1
    fi
  done
  if (( missing == 1 )); then
    err "Aborting: One or more required files are missing."
    exit 1
  fi
}

# Dependency check for Python 3 and Jinja2
check_dependencies() {
  if ! command -v python3 &>/dev/null; then
    err "Python 3 is required but not found. Aborting."
    exit 1
  fi
  if ! python3 -c "import jinja2" &>/dev/null; then
    err "Python package 'jinja2' is required but not found. Aborting."
    exit 1
  fi
}

# Create edge-controller.conf from Jinja template
render_edge_controller_conf() {
  log_msg info "Rendering edge-controller.conf from Jinja template..."
  python3 - <<EOF
import yaml
from jinja2 import Template
from pathlib import Path
import os
config_path = os.path.join('${PROJECT_ROOT}', 'config.test.yaml')
template_path = os.path.join('${PROJECT_ROOT}', 'infra', 'edge-controller.conf.j2')
output_path = Path('${EDGE_CONF_TMP}').expanduser()
with open(config_path) as f:
  config = yaml.safe_load(f)
controller = config['edge_controllers'][0]
train = controller['trains'][0]
context = {
  'central_api_host': 'central_api',
  'central_api_port': 8000,
}
with open(template_path) as f:
  template = Template(f.read())
rendered = template.render(**context)
output_path.write_text(rendered)
EOF
  log_msg info "edge-controller.conf rendered to ${EDGE_CONF_TMP}"
}

# Capture logs from all services
capture_all_logs() {
  local prefix="$1"
  log_msg info "Capturing logs from all containers in compose file..."
  local services
  services=$(docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" config --services)
  for svc in ${services}; do
    docker logs "${COMPOSE_PROJECT_NAME}-${svc}-1" > "${LOG_DIR}/${prefix}_${svc}.log" 2>&1 || log_msg warn "$svc container not running"
  done
}

# Display logs on failure
# Args: component name
# Side effect: prints logs to stdout
# Exits: does not exit
show_logs_on_failure() {
  local component="$1"
  log_msg error "FAILURE DETECTED - Displaying Container Logs"
  echo "--- MQTT Broker Logs ---"
  docker logs ${COMPOSE_PROJECT_NAME}-mqtt-1 2>&1 | tail -n 50
  echo "--- Central API Logs ---"
  docker logs ${COMPOSE_PROJECT_NAME}-central_api-1 2>&1 | tail -n 50
  echo "Full logs saved to: ${LOG_DIR}"
}

# Cleanup function for trap
cleanup() {
  log_msg info "Capturing final logs..."
  capture_all_logs "final"
  if [[ "${KEEP_RUNNING}" == "yes" ]]; then
    log_msg info "Containers left running for development"
    echo "API: http://${TEST_API_HOST}:${TEST_API_PORT}"
    echo "Web UI: http://${TEST_FRONTEND_HOST}:${TEST_FRONTEND_PORT}"
    echo "To stop all containers, run:"
    echo "  docker compose --project-name ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} down"
  elif [[ "${REBUILD}" == "yes" ]]; then
    log_msg info "Stopping containers..."
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down || log_msg warn "No existing containers to stop"
  fi
  if [[ "${CLEANUP_ON_SUCCESS}" == "yes" ]]; then
    log_msg info "Cleaning up logs and configs..."
    rm -rf "${LOG_DIR}" "${EDGE_CONF_TMP}"
  else
    echo
    echo "===================="
    echo "Test logs and captured container logs are available at: ${LOG_DIR}"
    echo "If a test or container failed, check the logs above for details."
    echo "===================="
  fi
}

# Stops and removes existing containers
stop_containers() {
  log_msg info "Stopping and removing existing containers..."
  docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down || log_msg warn "No existing containers to stop"
}

# Builds and starts containers
start_containers() {
  log_msg info "Starting services..."
  if [[ "${REBUILD}" == "yes" ]]; then
    log_msg info "Building containers..."
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" build --no-cache
    log_msg info "Starting containers..."
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d
  else
    log_msg info "Starting containers (no rebuild)..."
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d
  fi
}

# Checks if FastAPI server is running and /api/ping is reachable
check_server() {
  log_msg info "Checking if FastAPI server is running on port ${TEST_API_PORT} and /api/ping is reachable..."
  if ! nc -z "${TEST_API_HOST}" "${TEST_API_PORT}"; then
    err "FastAPI server is NOT running on ${TEST_API_HOST} port ${TEST_API_PORT}."
    show_logs_on_failure "central_api_port_check"
    return 1
  fi
  local retry_count=0
  while (( retry_count < HEALTH_RETRY_COUNT )); do
    if curl -sSf "http://${TEST_API_HOST}:${TEST_API_PORT}/api/ping" > /dev/null 2>&1; then
      log_msg info "✓ FastAPI server is running and /api/ping is reachable."
      return 0
    fi
    (( retry_count++ ))
    log_msg warn "Retry ${retry_count}/${HEALTH_RETRY_COUNT} - waiting for /api/ping..."
    sleep 2
  done
  err "FastAPI server is running, but /api/ping is NOT reachable after ${HEALTH_RETRY_COUNT} attempts."
  show_logs_on_failure "central_api_ping_check"
  return 1
}

# Checks if MQTT server is running
check_mqtt() {
  log_msg info "Checking if MQTT server is running..."
  local status
  status=$(docker ps --filter "name=${COMPOSE_PROJECT_NAME}-mqtt-1" --format '{{.Status}}' 2>/dev/null || echo "")
  if [[ "${status}" == Up* ]]; then
    log_msg info "✓ MQTT server is running."
    # First, wait for any process to be listening on the port (host-side)
    local lsof_retry_count=0
    local lsof_found=1
    while (( lsof_retry_count < HEALTH_RETRY_COUNT )); do
      if lsof -iTCP:"${TEST_MQTT_PORT}" -sTCP:LISTEN &>/dev/null; then
        lsof_found=0
        break
      fi
      (( lsof_retry_count++ ))
      log_msg warn "Retry ${lsof_retry_count}/${HEALTH_RETRY_COUNT} - waiting for a process to listen on port ${TEST_MQTT_PORT} (lsof)..."
      sleep 2
    done
    if (( lsof_found != 0 )); then
      log_msg warn "No process found listening on port ${TEST_MQTT_PORT} after ${HEALTH_RETRY_COUNT} attempts"
    fi
    # Now check actual connectivity with netcat
    local mqtt_retry_count=0
    local mqtt_port_open=1
    while (( mqtt_retry_count < HEALTH_RETRY_COUNT )); do
      if nc -z "${TEST_MQTT_HOST}" "${TEST_MQTT_PORT}" 2>/dev/null; then
        log_msg info "✓ MQTT server is accepting connections on port ${TEST_MQTT_PORT}."
        mqtt_port_open=0
        break
      fi
      (( mqtt_retry_count++ ))
      log_msg warn "Retry ${mqtt_retry_count}/${HEALTH_RETRY_COUNT} - waiting for MQTT port ${TEST_MQTT_PORT} (nc)..."
      sleep 2
    done
    if (( mqtt_port_open != 0 )); then
      log_msg warn "MQTT container running but port ${TEST_MQTT_PORT} not accessible after ${HEALTH_RETRY_COUNT} attempts"
    fi
    return 0
  else
    err "MQTT server is NOT healthy. Status: ${status:-not found}"
    show_logs_on_failure "mqtt_check"
    return 1
  fi
}

# Checks if edge-controller is running
check_edge_controller() {
  log_msg info "Checking if edge-controller is running..."
  local status
  status=$(docker ps --filter "name=${COMPOSE_PROJECT_NAME}-edge-controller-1" --format '{{.Status}}' 2>/dev/null || echo "")
  if [[ "${status}" == Up* ]]; then
    log_msg info "✓ Edge controller is running."
    if docker logs ${COMPOSE_PROJECT_NAME}-edge-controller-1 2>&1 | grep -q "Edge controller running\|Subscribed to topic"; then
      log_msg info "✓ Edge controller appears to have initialized successfully."
    else
      log_msg warn "Edge controller running but initialization status unclear"
      docker logs --tail 10 ${COMPOSE_PROJECT_NAME}-edge-controller-1 2>&1 | sed 's/^/  /'
    fi
    return 0
  else
    err "Edge controller is NOT healthy. Status: ${status:-not found}"
    show_logs_on_failure "edge_controller_check"
    return 1
  fi
}


# --- Test Suite Functions ---

# Playwright E2E tests
run_playwright_tests() {
  log_msg info "=== Starting Playwright E2E tests ==="
  echo "\n========== Playwright E2E tests =========="
  pushd "${PROJECT_ROOT}/frontend/web" > /dev/null
  if ! npm install 2>&1 | tee "${LOG_DIR}/playwright_npm_install.log"; then
    err "npm install failed in frontend/web"
    show_logs_on_failure "playwright"
    popd > /dev/null
    return 1
  fi
  if ! npm run test:e2e -- --reporter=dot 2>&1 | tee "${LOG_DIR}/playwright_e2e.log"; then
    err "Playwright E2E tests failed."
    show_logs_on_failure "playwright"
    popd > /dev/null
    return 1
  fi
  popd > /dev/null
  log_msg info "✓ Playwright E2E tests passed."
  echo "========== Playwright E2E tests complete =========="
}

# Pytest integration tests
run_pytest_tests() {
  log_msg info "=== Starting pytest integration tests ==="
  echo "\n========== Pytest integration tests =========="
  if ! API_PORT="${TEST_API_PORT}" MQTT_PORT="18884" PYTHONPATH=. pytest tests/integration/ -v --tb=short 2>&1 | tee "${LOG_DIR}/pytest_integration.log"; then
    err "Pytest integration test failed."
    show_logs_on_failure "pytest"
    return 1
  fi
  log_msg info "✓ Pytest tests passed."
  echo "========== Pytest integration tests complete =========="
}

# Insomnia API tests
run_insomnia_tests() {
  log_msg info "=== Starting Insomnia API tests ==="
  echo "\n========== Insomnia API tests =========="
  if command -v inso &> /dev/null; then
    log_msg info "Running Insomnia API tests..."
    # TODO: Replace with actual Insomnia test command
    # Example: inso run test "${INSOMNIA_FILE}" --env "${ENVIRONMENT}" 2>&1 | tee "${LOG_DIR}/insomnia_api.log"
    log_msg info "Insomnia test command placeholder"
    echo "Insomnia test command placeholder" | tee "${LOG_DIR}/insomnia_api.log"
  else
    log_msg info "Skipping Insomnia tests (inso not installed)"
    log_msg info "Install with: npm install -g insomnia-inso"
    echo "Skipping Insomnia tests (inso not installed)" | tee "${LOG_DIR}/insomnia_api.log"
  fi
  echo "========== Insomnia API tests complete =========="
}

# Run all test suites
run_all_tests() {
  log_msg info "=== Running all test suites (pytest, playwright, insomnia) ==="
  run_pytest_tests || return 1
  run_playwright_tests || return 1
  run_insomnia_tests || return 1
  log_msg info "✓ All test suites passed."
}

# Dispatcher for selected test suite
run_selected_tests() {
  log_msg info "Selected test suite: ${TEST_SUITE}"
  echo "\n===================="
  echo "Selected test suite: ${TEST_SUITE}"
  echo "====================\n"
  case "${TEST_SUITE}" in
    playwright)
      run_playwright_tests
      ;;
    pytest)
      run_pytest_tests
      ;;
    insomnia)
      run_insomnia_tests
      ;;
    all)
      run_all_tests
      ;;
    none)
      log_msg info "TEST_SUITE=none: Skipping all test suites."
      ;;
    *)
      err "Unknown TEST_SUITE: '${TEST_SUITE}'. Must be one of: playwright, pytest, insomnia, all, none."
      exit 1
      ;;
  esac
}

# Runs health checks and test suites
run_tests() {
  log_msg info "Starting Health Checks"
  check_mqtt || exit 1
  check_server || exit 1
  check_edge_controller || exit 1
  log_msg info "All Health Checks Passed - Verifying train registration..."
  local train_retry_count=0
  local train_count=0
  local train_api_response=""
  echo "Polling Central API for train registration..."
  while (( train_retry_count < TRAIN_RETRY_COUNT )); do
    echo -n "[Train Check] Attempt $((train_retry_count+1))/${TRAIN_RETRY_COUNT}... "
    train_api_response=$(curl -sSf "http://${TEST_API_HOST}:${TEST_API_PORT}/api/trains" || echo "CURL_ERROR")
    if [[ "$train_api_response" == "CURL_ERROR" ]]; then
      echo "Central API unreachable."
      log_msg warn "Central API unreachable on train registration check."
    else
      train_count=$(echo "$train_api_response" | grep -o '"id"' | wc -l || true)
      echo "Found $train_count trains."
      if (( train_count > 0 )); then
        log_msg info "✓ At least one train registered in Central API."
        echo "Train registration detected. Proceeding with tests."
        break
      fi
    fi
    (( train_retry_count++ ))
    log_msg warn "Retry ${train_retry_count}/${TRAIN_RETRY_COUNT} - waiting for train registration..."
    sleep 2
  done
  if (( train_count == 0 )); then
    echo "[ERROR] No trains registered in Central API after ${TRAIN_RETRY_COUNT} attempts."
    echo "Last response from /api/trains: $train_api_response"
    err "No trains registered in Central API after ${TRAIN_RETRY_COUNT} attempts. Check config and edge controller startup."
    show_logs_on_failure "train_registration_check"
    exit 1
  fi
  run_selected_tests || {
    err "Test suite(s) failed."
    exit 1
  }
  log_msg info "✓ All selected test suites passed."
  capture_all_logs "success"
  return 0
}

# Creates log directory
create_log_dir() {
  mkdir -p "${LOG_DIR}" "${PROJECT_ROOT}/.tmp"
}

# --------------------
# Main
# --------------------
main() {
  # Parse CLI args for Ansible and cleanup options
  while [[ $# -gt 0 ]]; do
    case $1 in
      --no-ansible) USE_ANSIBLE=0 ;;
      --no-cleanup) CLEANUP=0 ;;
      --ansible-playbook) ANSIBLE_PLAYBOOK_PATH="$2"; shift ;;
      --ansible-inventory) ANSIBLE_INVENTORY_PATH="$2"; shift ;;
      # ...existing options...
    esac
    shift
  done

  create_log_dir
  log_msg info "==== Starting E2E Test Orchestration ===="
  check_dependencies

  # Cleanup previous artifacts if requested
  if [[ "$CLEANUP" == "1" ]]; then
    log_msg info "Cleaning up previous containers and configs..."
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down -v || log_msg warn "No existing containers to stop"
    rm -rf "${EDGE_CONF_TMP}" "${LOG_DIR}" "${PROJECT_ROOT}/.tmp/edge-controller.secrets"
    mkdir -p "${LOG_DIR}" "${PROJECT_ROOT}/.tmp"
  fi

  # Ansible provisioning (default)
  if [[ "$USE_ANSIBLE" == "1" ]]; then
    log_msg info "Provisioning test environment with Ansible..."
    ansible-playbook -i "$ANSIBLE_INVENTORY_PATH" "$ANSIBLE_PLAYBOOK_PATH" || {
      err "Ansible provisioning failed. Aborting."
      exit 1
    }
    log_msg info "Ansible provisioning complete."
  else
    log_msg info "Skipping Ansible provisioning (USE_ANSIBLE=0)"
    log_msg info "Rendering edge-controller.conf and preparing environment..."
    render_edge_controller_conf
  fi

  # Robust required file check after provisioning
  check_required_files

  stop_containers
  log_msg info "Bringing up containers and building images..."
  start_containers
  log_msg info "Waiting for services to be ready..."
  sleep 5
  capture_all_logs "startup"
  run_tests
  echo
  echo "===================="
  echo "Test run complete."
  echo "Logs and captured output are in: ${LOG_DIR}"
  echo "===================="
}

trap cleanup EXIT

main "$@"
