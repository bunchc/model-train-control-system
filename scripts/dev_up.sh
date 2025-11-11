#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
COMPOSE_DIR="$ROOT_DIR/infra/docker"

echo "Starting development stack from $COMPOSE_DIR"
 # Only cd if not already in infra/docker
 if [ "$(basename "$PWD")" != "docker" ]; then
   cd "$COMPOSE_DIR"
 fi

docker compose up --build -d

wait_http() {
  local url=$1
  local timeout=${2:-60}
  local interval=2
  local elapsed=0
  echo "Waiting for HTTP $url (timeout ${timeout}s)"
  while true; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "OK: $url"
      return 0
    fi
    sleep $interval
    elapsed=$((elapsed+interval))
    if [ $elapsed -ge $timeout ]; then
      echo "TIMEOUT: $url didn't respond within ${timeout}s"
      return 1
    fi
  done
}

wait_tcp() {
  local host=$1; local port=$2; local timeout=${3:-60}
  local interval=2; local elapsed=0
  echo "Waiting for TCP $host:$port (timeout ${timeout}s)"
  while true; do
    if command -v nc >/dev/null 2>&1; then
      if nc -z "$host" "$port" >/dev/null 2>&1; then
        echo "OK: $host:$port"
        return 0
      fi
    else
      # Fallback to bash /dev/tcp
      if (echo > "/dev/tcp/$host/$port") >/dev/null 2>&1; then
        echo "OK: $host:$port"
        return 0
      fi
    fi
    sleep $interval
    elapsed=$((elapsed+interval))
    if [ $elapsed -ge $timeout ]; then
      echo "TIMEOUT: $host:$port didn't accept connections within ${timeout}s"
      return 1
    fi
  done
}

failed=0

if ! wait_http "http://localhost:8000/" 60; then failed=1; fi
if ! wait_http "http://localhost:3000/" 60; then failed=1; fi
if ! wait_tcp "localhost" 1883 60; then failed=1; fi

if [ $failed -ne 0 ]; then
  echo "One or more services failed to become healthy. Showing compose ps and recent logs:"
  docker compose ps
  echo "---- recent logs (central-api, gateway, mqtt, edge-controller) ----"
  docker compose logs --no-color --tail 200 central-api gateway mqtt edge-controller || true
  exit 1
fi

echo "All services are healthy. Frontend: http://localhost:3000 | API: http://localhost:8000"
