#!/usr/bin/env bash
# scripts/collect-logs.sh
# Collects Docker container logs to a shared directory for the AgentLog Celery worker.
# Runs as a daily cron job on the Ubuntu host.
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment)
# ---------------------------------------------------------------------------
DOCKER_LOGS_DIR="${DOCKER_LOGS_DIR:?ERROR: DOCKER_LOGS_DIR env var must be set}"
COMPOSE_FILE="${COMPOSE_FILE:?ERROR: COMPOSE_FILE env var must be set}"
LOG_TAIL="${LOG_TAIL:-2000}"
BACKEND_SERVICE="${BACKEND_SERVICE:-portfolio-be}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-portfolio-fe}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

# ---------------------------------------------------------------------------
# 1. Ensure log directory exists and is writable
# ---------------------------------------------------------------------------
log "Using log directory: ${DOCKER_LOGS_DIR}"
mkdir -p "${DOCKER_LOGS_DIR}"

# ---------------------------------------------------------------------------
# 2. Clear old logs (no stale data)
# ---------------------------------------------------------------------------
log "Clearing existing logs..."
rm -f "${DOCKER_LOGS_DIR}"/*.log "${DOCKER_LOGS_DIR}/collected_at.txt" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 3. Collect backend logs
# ---------------------------------------------------------------------------
log "Collecting backend logs (${BACKEND_SERVICE}, --tail=${LOG_TAIL})..."
docker compose -f "${COMPOSE_FILE}" logs --no-color --tail="${LOG_TAIL}" "${BACKEND_SERVICE}" \
    > "${DOCKER_LOGS_DIR}/backend.log"
BACKEND_SIZE=$(wc -c < "${DOCKER_LOGS_DIR}/backend.log")
log "Backend log: ${BACKEND_SIZE} bytes"

# ---------------------------------------------------------------------------
# 4. Collect frontend logs
# ---------------------------------------------------------------------------
log "Collecting frontend logs (${FRONTEND_SERVICE}, --tail=${LOG_TAIL})..."
docker compose -f "${COMPOSE_FILE}" logs --no-color --tail="${LOG_TAIL}" "${FRONTEND_SERVICE}" \
    > "${DOCKER_LOGS_DIR}/frontend.log"
FRONTEND_SIZE=$(wc -c < "${DOCKER_LOGS_DIR}/frontend.log")
log "Frontend log: ${FRONTEND_SIZE} bytes"

# ---------------------------------------------------------------------------
# 5. Write metadata timestamp (Celery uses this to detect stale data)
# ---------------------------------------------------------------------------
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DOCKER_LOGS_DIR}/collected_at.txt"

log "Done. Total collected: $((BACKEND_SIZE + FRONTEND_SIZE)) bytes"
