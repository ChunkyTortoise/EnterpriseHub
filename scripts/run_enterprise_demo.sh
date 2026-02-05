#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.enterprise.yml"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Missing docker-compose.enterprise.yml in ${ROOT_DIR}"
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    echo "Starting EnterpriseHub demo with Docker Compose..."
    docker compose -f "${COMPOSE_FILE}" up
    exit 0
  fi
fi

if command -v docker-compose >/dev/null 2>&1; then
  echo "Starting EnterpriseHub demo with docker-compose..."
  docker-compose -f "${COMPOSE_FILE}" up
  exit 0
fi

echo "Docker Compose not found. Please install Docker Desktop or run services manually."
exit 1
