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
BACKEND_SERVICE="${BACKEND_SERVICE:-be}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-fe}"
NGINX_SERVICE="${NGINX_SERVICE:-nginx}"

# ---------------------------------------------------------------------------
# Helpers & Context
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Source utils for get_project_name
if [[ -f "${SCRIPT_DIR}/../release/utils.sh" ]]; then
    source "${SCRIPT_DIR}/../release/utils.sh"
else
    # Fallback if utils.sh is missing or structure differs
    get_project_name() { echo "${COMPOSE_PROJECT_NAME:-portfolio}"; }
fi

PROJECT_NAME=$(get_project_name)

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

# ---------------------------------------------------------------------------
# 1. Ensure log directory exists and is writable
# ---------------------------------------------------------------------------
log "Using log directory: ${DOCKER_LOGS_DIR}"
log "Resolved project name: ${PROJECT_NAME}"
mkdir -p "${DOCKER_LOGS_DIR}"

# ---------------------------------------------------------------------------
# 2. Clear old logs (no stale data)
# ---------------------------------------------------------------------------
log "Clearing existing logs..."
rm -f "${DOCKER_LOGS_DIR}"/*.log "${DOCKER_LOGS_DIR}/collected_at.txt" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 3. Collection Function
# ---------------------------------------------------------------------------
# Track byte counts globally since return codes are limited to 0-255
TOTAL_BYTES=0

collect_service_logs() {
    local service="$1"
    local output_file="$2"
    local container_name="${PROJECT_NAME}-${service}-1"

    log "Collecting ${service} logs (${container_name}, --tail=${LOG_TAIL}, --since=120h)..."

    if ! docker inspect "${container_name}" >/dev/null 2>&1; then
        log "⚠️ WARNING: Container ${container_name} not found. Skipping."
        echo "" > "${output_file}"
        return 0
    fi

    # Capture logs and update total
    docker logs --tail="${LOG_TAIL}" --since="120h" "${container_name}" > "${output_file}"
    local size=$(wc -c < "${output_file}" 2>/dev/null || echo 0)
    log "${service} log: ${size} bytes"
    TOTAL_BYTES=$((TOTAL_BYTES + size))
}

# ---------------------------------------------------------------------------
# 4. Collect logs for each service
# ---------------------------------------------------------------------------
collect_service_logs "${BACKEND_SERVICE}" "${DOCKER_LOGS_DIR}/backend.log"
collect_service_logs "${FRONTEND_SERVICE}" "${DOCKER_LOGS_DIR}/frontend.log"
collect_service_logs "${NGINX_SERVICE}" "${DOCKER_LOGS_DIR}/nginx.log"

# ---------------------------------------------------------------------------
# 5. Write metadata timestamp (Celery uses this to detect stale data)
# ---------------------------------------------------------------------------
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DOCKER_LOGS_DIR}/collected_at.txt"

log "Done. Total collected: ${TOTAL_BYTES} bytes"
