#!/usr/bin/env bash
# infra/scripts/monitoring/collect-logs.sh
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
TRAEFIK_SERVICE="${TRAEFIK_SERVICE:-traefik}"

# Infer ENVIRONMENT from COMPOSE_FILE name (e.g., docker-compose.prod.yml -> prod)
if [[ -z "${ENVIRONMENT:-}" ]]; then
    ENVIRONMENT=$(echo "$COMPOSE_FILE" | grep -oE "docker-compose\.(.+)\.yml" | cut -d'.' -f2 || echo "prod")
fi
export ENVIRONMENT

# ---------------------------------------------------------------------------
# Helpers & Context
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Source utils for get_project_name
if [[ -f "${SCRIPT_DIR}/../utils.sh" ]]; then
    source "${SCRIPT_DIR}/../utils.sh"
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
    local container_names
    local newest_container

    container_names=$(docker ps \
        --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
        --filter "label=com.docker.compose.service=${service}" \
        --format '{{.Names}}\t{{.CreatedAt}}' | sort -k2,3r || true)

    newest_container=$(printf '%s\n' "${container_names}" | awk 'NR==1 {print $1}')

    log "Collecting ${service} logs (project=${PROJECT_NAME}, --tail=${LOG_TAIL}, --since=120h)..."

    if [[ -z "${newest_container}" ]]; then
        log "⚠️ WARNING: No running container found for service=${service} in project=${PROJECT_NAME}. Skipping."
        echo "" > "${output_file}"
        return 0
    fi

    log "Resolved ${service} container: ${newest_container}"

    # Capture logs and update total
    docker logs --tail="${LOG_TAIL}" --since="120h" "${newest_container}" > "${output_file}"
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
collect_service_logs "${TRAEFIK_SERVICE}" "${DOCKER_LOGS_DIR}/traefik.log"

# ---------------------------------------------------------------------------
# 5. Write metadata timestamp (Celery uses this to detect stale data)
# ---------------------------------------------------------------------------
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DOCKER_LOGS_DIR}/collected_at.txt"

log "Done. Total collected: ${TOTAL_BYTES} bytes"
