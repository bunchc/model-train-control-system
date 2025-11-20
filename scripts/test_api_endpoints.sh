#!/bin/bash
# test_api_endpoints.sh
# Script to validate central_api endpoints and check FastAPI server status

REBUILD=${1:-yes}
API_URL="http://localhost:8000/api"
COMPOSE_FILE="infra/docker/docker-compose.yml"
# Option to run all requests as a collection or individually
RUN_ALL=${RUN_ALL:-no}

if [ "$REBUILD" == "yes" ]; then
    echo "Rebuilding and restarting Docker containers..."
    docker compose -f ${COMPOSE_FILE} down || exit 1
    docker compose -f ${COMPOSE_FILE} build --no-cache || exit 1
    docker compose -f ${COMPOSE_FILE} up -d  || exit 1
    echo "Waiting for FastAPI server to start..."
    sleep 5
fi

function check_server {
  "req_d23d9496dcb24bb6a1642eabdc9fb39b" # Read Root
  echo "Checking if FastAPI server is running on port 8000..."
  if nc -z localhost 8000; then
    echo "FastAPI server is running."
  else
    echo "FastAPI server is NOT running on port 8000."
    echo -e "\nFetching central_api server logs (docker-central_api-1):"
    docker logs docker-central_api-1
    exit 1
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
    inso run collection wrk_faf1be --env env_7c7a2f7957 --reporter min --bail || return 1
  else
    echo -e "\nRunning Insomnia requests one at a time..."
    for req_id in "${INSO_REQUESTS[@]}"; do
      echo -e "\nRunning Insomnia request: $req_id"
      if ! inso run collection wrk_faf1be --env env_7c7a2f7957 --item "$req_id" --reporter min; then
        echo -e "\nInsomnia run failed. Collecting server logs."
        return 1
      fi
    done
  fi
  return 0
}

function run_tests {
  echo -e "\nRunning pytest integration test (test_end_to_end.py):"
  PYTHONPATH=. pytest tests/integration/test_end_to_end.py
  if [ $? -ne 0 ]; then
    echo -e "\nPytest integration test failed. Collecting server logs."
    docker logs docker-central_api-1
    exit 1
  fi

  echo -e "\nPytest passed. Running Insomnia tests..."
  run_insomnia_tests
  if [ $? -ne 0 ]; then
    echo -e "\nInsomnia tests failed. Collecting server logs."
    docker logs docker-central_api-1
    exit 1
  fi

  echo -e "\nAll tests passed."
}

run_tests
if [ "$RUN_ALL" == "yes" ]; then
  echo -e "\nRunning full Insomnia collection..."
  inso run collection wrk_faf1be --env env_7c7a2f7957 --reporter min --bail || break
else
  echo -e "\nRunning Insomnia requests one at a time..."
  for req_id in "${INSO_REQUESTS[@]}"; do
    echo -e "\nRunning Insomnia request: $req_id"
    # Run the request and break for server output on fail
    if ! inso run collection wrk_faf1be --env env_7c7a2f7957 --item "$req_id" --reporter min; then
      echo -e "\nInsomnia run failed. Collecting server logs."
      break
    fi
  done
fi


# Run pytest integration test for end-to-end API validation
echo -e "\nRunning pytest integration test (test_end_to_end.py):"
PYTHONPATH=. pytest tests/integration/test_end_to_end.py

echo -e "\nCollecting central_api server logs (docker-central_api-1):"
docker logs docker-central_api-1
