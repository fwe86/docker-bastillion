#!/usr/bin/env bash

set -euo pipefail

IMAGE="${1:-docker-bastillion:ci}"
CONTAINER_NAME="${CONTAINER_NAME:-bastillion-smoke-test}"
HOST_PORT="${SMOKE_TEST_PORT:-18080}"

cleanup() {
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

cleanup

echo "Starting smoke-test container from ${IMAGE}..."

docker run \
    --detach \
    --name "${CONTAINER_NAME}" \
    --env TLS_ENABLED=false \
    --env PORT=8080 \
    --publish "127.0.0.1:${HOST_PORT}:8080" \
    "${IMAGE}" \
    >/dev/null

echo "Waiting for Bastillion to respond..."

for attempt in $(seq 1 60); do
    state="$(
        docker inspect \
            --format '{{.State.Status}}' \
            "${CONTAINER_NAME}" \
            2>/dev/null || true
    )"

    if [[ "${state}" == "exited" || "${state}" == "dead" ]]; then
        echo "ERROR: Bastillion container stopped unexpectedly." >&2
        docker logs "${CONTAINER_NAME}" >&2 || true
        exit 1
    fi

    http_code="$(
        curl \
            --silent \
            --output /dev/null \
            --max-time 2 \
            --write-out '%{http_code}' \
            "http://127.0.0.1:${HOST_PORT}/" \
            2>/dev/null || true
    )"

    if [[ "${http_code}" =~ ^[234][0-9][0-9]$ ]]; then
        echo "Bastillion responded with HTTP ${http_code}."
        echo "Smoke test successful."
        exit 0
    fi

    sleep 2
done

echo "ERROR: Bastillion did not become ready." >&2
docker logs "${CONTAINER_NAME}" >&2 || true
exit 1
