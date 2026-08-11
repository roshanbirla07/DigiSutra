#!/usr/bin/env bash
set -euo pipefail

POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:18.3-alpine}"
API_IMAGE="${API_IMAGE:-digisutra-api-smoke}"
CONTAINER_NAME="${CONTAINER_NAME:-digisutra-migration-smoke-postgres}"
NETWORK_NAME="${NETWORK_NAME:-digisutra-migration-smoke}"
POSTGRES_DB="${POSTGRES_DB:-digisutra}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB_URI="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${CONTAINER_NAME}:5432/${POSTGRES_DB}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker network rm "${NETWORK_NAME}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

cleanup
docker network create "${NETWORK_NAME}" >/dev/null
docker run \
  -d \
  --name "${CONTAINER_NAME}" \
  --network "${NETWORK_NAME}" \
  -e POSTGRES_DB="${POSTGRES_DB}" \
  -e POSTGRES_USER="${POSTGRES_USER}" \
  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  "${POSTGRES_IMAGE}" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "${CONTAINER_NAME}" pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "${CONTAINER_NAME}" pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null
docker build -t "${API_IMAGE}" .

docker run \
  --rm \
  --network "${NETWORK_NAME}" \
  -v "${PWD}:/app" \
  -w /app \
  -e PYTHONPATH=/app/apps/api/src \
  -e POSTGRES_DB_URI="${POSTGRES_DB_URI}" \
  "${API_IMAGE}" \
  alembic upgrade head

docker run \
  --rm \
  --network "${NETWORK_NAME}" \
  -v "${PWD}:/app" \
  -w /app \
  -e PYTHONPATH=/app/apps/api/src \
  -e POSTGRES_DB_URI="${POSTGRES_DB_URI}" \
  "${API_IMAGE}" \
  python -m unittest discover apps/api/tests
