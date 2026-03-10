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
LOG_TAIL="${LOG_TAIL:-5000}"
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
log "Collecting backend logs (portfolio-portfolio-be-1, --tail=${LOG_TAIL}, --since=120h)..."
# Use 'docker logs' directly to avoid 'docker compose' warnings about missing env vars
docker logs --tail="${LOG_TAIL}" --since="120h" "portfolio-portfolio-be-1" \
    > "${DOCKER_LOGS_DIR}/backend.log" 2>/dev/null || true
BACKEND_SIZE=$(wc -c < "${DOCKER_LOGS_DIR}/backend.log" 2>/dev/null || echo 0)
log "Backend log: ${BACKEND_SIZE} bytes"

# ---------------------------------------------------------------------------
# 4. Collect frontend logs
# ---------------------------------------------------------------------------
log "Collecting frontend logs (portfolio-portfolio-fe-1, --tail=${LOG_TAIL}, --since=120h)..."
docker logs --tail="${LOG_TAIL}" --since="120h" "portfolio-portfolio-fe-1" \
    > "${DOCKER_LOGS_DIR}/frontend.log" 2>/dev/null || true
FRONTEND_SIZE=$(wc -c < "${DOCKER_LOGS_DIR}/frontend.log" 2>/dev/null || echo 0)
log "Frontend log: ${FRONTEND_SIZE} bytes"

# ---------------------------------------------------------------------------
# 5. Collect nginx logs
# ---------------------------------------------------------------------------
log "Collecting nginx logs (portfolio-portfolio-nginx-1, --tail=${LOG_TAIL}, --since=120h)..."
docker logs --tail="${LOG_TAIL}" --since="120h" "portfolio-portfolio-nginx-1" \
    > "${DOCKER_LOGS_DIR}/nginx.log" 2>/dev/null || true
NGINX_SIZE=$(wc -c < "${DOCKER_LOGS_DIR}/nginx.log" 2>/dev/null || echo 0)
log "Nginx log: ${NGINX_SIZE} bytes"

# ---------------------------------------------------------------------------
# 6. Write metadata timestamp (Celery uses this to detect stale data)
# ---------------------------------------------------------------------------
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DOCKER_LOGS_DIR}/collected_at.txt"

log "Done. Total collected: $((BACKEND_SIZE + FRONTEND_SIZE + NGINX_SIZE)) bytes"
