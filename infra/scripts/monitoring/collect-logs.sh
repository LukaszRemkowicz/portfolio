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
LOG_SINCE="${LOG_SINCE:-24h}"
ARCHIVE_RETENTION_DAYS="${ARCHIVE_RETENTION_DAYS:-30}"

# Infer ENVIRONMENT from COMPOSE_FILE name (e.g., docker-compose.prod.yml -> prod)
if [[ -z "${ENVIRONMENT:-}" ]]; then
    ENVIRONMENT=$(echo "$COMPOSE_FILE" | grep -oE "docker-compose\.(.+)\.yml" | cut -d'.' -f2 || echo "prod")
fi
export ENVIRONMENT

# ---------------------------------------------------------------------------
# Helpers & Context
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
LOG_SOURCES_MANIFEST="${LOG_SOURCES_MANIFEST:-${REPO_ROOT}/backend/monitoring/log_sources.json}"
# Source utils for get_project_name
if [[ -f "${SCRIPT_DIR}/../utils.sh" ]]; then
    source "${SCRIPT_DIR}/../utils.sh"
else
    # Fallback if utils.sh is missing or structure differs
    get_project_name() { echo "${COMPOSE_PROJECT_NAME:-portfolio}"; }
fi

PROJECT_NAME=$(get_project_name)
ARCHIVE_ROOT="${DOCKER_LOGS_DIR}/archive"
CURRENT_SNAPSHOT_FILES=(
    "backend.log"
    "frontend.log"
    "nginx_access.log"
    "nginx_runtime.log"
    "traefik_access.log"
    "traefik_runtime.log"
    "collected_at.txt"
)

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

archive_existing_snapshots() {
    local archive_timestamp archive_dir
    local found_snapshot=0
    archive_timestamp="$(date -u +"%Y-%m-%d_%H%M%S")"
    archive_dir="${ARCHIVE_ROOT}/${archive_timestamp}"

    for filename in "${CURRENT_SNAPSHOT_FILES[@]}"; do
        if [[ -e "${DOCKER_LOGS_DIR}/${filename}" ]]; then
            found_snapshot=1
            break
        fi
    done

    if [[ "${found_snapshot}" -eq 0 ]]; then
        log "No existing snapshot set found to archive."
        return 0
    fi

    mkdir -p "${archive_dir}"
    log "Archiving current snapshot set to ${archive_dir}"

    for filename in "${CURRENT_SNAPSHOT_FILES[@]}"; do
        if [[ -e "${DOCKER_LOGS_DIR}/${filename}" ]]; then
            mv "${DOCKER_LOGS_DIR}/${filename}" "${archive_dir}/${filename}"
        fi
    done
}

prune_old_archives() {
    mkdir -p "${ARCHIVE_ROOT}"
    log "Pruning archive snapshot directories older than ${ARCHIVE_RETENTION_DAYS} days..."
    find "${ARCHIVE_ROOT}" -mindepth 1 -maxdepth 1 -type d -mtime +"${ARCHIVE_RETENTION_DAYS}" -exec rm -rf {} +
}

# ---------------------------------------------------------------------------
# 1. Ensure log directory exists and is writable
# ---------------------------------------------------------------------------
log "Using log directory: ${DOCKER_LOGS_DIR}"
log "Resolved project name: ${PROJECT_NAME}"
mkdir -p "${DOCKER_LOGS_DIR}"

# ---------------------------------------------------------------------------
# 2. Archive previous snapshot set and prune retention
# ---------------------------------------------------------------------------
archive_existing_snapshots
prune_old_archives

# ---------------------------------------------------------------------------
# 3. Collection Function
# ---------------------------------------------------------------------------
# Track byte counts globally since return codes are limited to 0-255
TOTAL_BYTES=0
DOCKER_TOOL_LOG="${DOCKER_TOOL_LOG:-${DOCKER_LOGS_DIR}/docker-tool-errors.log}"

run_quiet_docker() {
    local stderr_file
    stderr_file=$(mktemp)

    if "$@" 2>"${stderr_file}"; then
        rm -f "${stderr_file}"
        return 0
    fi

    local stderr_output=""
    if [[ -s "${stderr_file}" ]]; then
        stderr_output=$(tr '\n' ' ' < "${stderr_file}" | sed 's/[[:space:]]\+/ /g; s/^ //; s/ $//')
        printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "${stderr_output}" >> "${DOCKER_TOOL_LOG}"
    fi
    rm -f "${stderr_file}"

    return 1
}

resolve_container_by_project_service() {
    local project="$1"
    local service="$2"

    run_quiet_docker docker ps \
        --filter "label=com.docker.compose.project=${project}" \
        --filter "label=com.docker.compose.service=${service}" \
        --format '{{.Names}}\t{{.CreatedAt}}' | sort -k2,3r | awk 'NR==1 {print $1}' || true
}

resolve_container_by_name() {
    local container_name="$1"

    run_quiet_docker docker ps \
        --filter "name=^/${container_name}$" \
        --format '{{.Names}}\t{{.CreatedAt}}' | sort -k2,3r | awk 'NR==1 {print $1}' || true
}

collect_service_logs() {
    local source_key="$1"
    local service="$2"
    local output_file="$3"
    local compose_project="${4:-${PROJECT_NAME}}"
    local explicit_container_name="${5:-}"
    local newest_container=""
    local resolution_hint="project=${compose_project}, service=${service}"

    if [[ -n "${explicit_container_name}" ]]; then
        newest_container=$(resolve_container_by_name "${explicit_container_name}")
        if [[ -n "${newest_container}" ]]; then
            resolution_hint="container=${explicit_container_name}"
        fi
    fi

    if [[ -z "${newest_container}" ]]; then
        newest_container=$(resolve_container_by_project_service "${compose_project}" "${service}")
    fi

    log "Collecting ${source_key} logs (${resolution_hint}, --tail=${LOG_TAIL}, --since=${LOG_SINCE}, --timestamps)..."

    if [[ -z "${newest_container}" ]]; then
        log "⚠️ WARNING: No running container found for source=${source_key} (${resolution_hint}). Skipping."
        : > "${output_file}"
        return 0
    fi

    log "Resolved ${source_key} container: ${newest_container}"

    # Capture logs and update total
    if ! run_quiet_docker docker logs --timestamps --tail="${LOG_TAIL}" --since="${LOG_SINCE}" "${newest_container}" > "${output_file}"; then
        log "⚠️ WARNING: Failed to collect logs for source=${source_key}. See ${DOCKER_TOOL_LOG}."
        : > "${output_file}"
        return 0
    fi
    local size=$(wc -c < "${output_file}" 2>/dev/null || echo 0)
    log "${source_key} log: ${size} bytes"
    TOTAL_BYTES=$((TOTAL_BYTES + size))
}

collect_file_logs() {
    local source_key="$1"
    local source_path="$2"
    local output_file="$3"

    log "Collecting ${source_key} file logs from ${source_path} (tail=${LOG_TAIL} lines)..."

    if [[ ! -f "${source_path}" ]]; then
        log "⚠️ WARNING: Log file not found for source=${source_key}: ${source_path}. Skipping."
        : > "${output_file}"
        return 0
    fi

    if ! tail -n "${LOG_TAIL}" "${source_path}" > "${output_file}"; then
        log "⚠️ WARNING: Failed to read file logs for source=${source_key}."
        : > "${output_file}"
        return 0
    fi

    local size=$(wc -c < "${output_file}" 2>/dev/null || echo 0)
    log "${source_key} log: ${size} bytes"
    TOTAL_BYTES=$((TOTAL_BYTES + size))
}

iterate_log_sources() {
    python3 -c '
import json
import sys

manifest_path = sys.argv[1]
with open(manifest_path, encoding="utf-8") as manifest_file:
    sources = json.load(manifest_file)

for source in sources:
    print("\t".join([
        source["key"],
        source["filename"],
        source.get("source_type", "docker"),
        source["service_env"],
        source["service_default"],
        source.get("compose_project_env", ""),
        source.get("compose_project_default", ""),
        source.get("container_name_env", ""),
        source.get("container_name_default", ""),
        source.get("file_path_env", ""),
        source.get("file_path_default", ""),
    ]))
' "${LOG_SOURCES_MANIFEST}"
}

# ---------------------------------------------------------------------------
# 4. Collect logs for each service
# ---------------------------------------------------------------------------
while IFS=$'\t' read -r source_key filename source_type service_env service_default compose_project_env compose_project_default container_env container_default file_path_env file_path_default; do
    service_name="${!service_env:-${service_default}}"
    compose_project="${PROJECT_NAME}"
    if [[ -n "${compose_project_env}" ]]; then
        compose_project="${!compose_project_env:-${compose_project_default}}"
    fi
    explicit_container_name=""
    if [[ -n "${container_env}" ]]; then
        explicit_container_name="${!container_env:-${container_default}}"
    fi

    if [[ "${source_type}" == "file" ]]; then
        source_path="${!file_path_env:-${file_path_default}}"
        collect_file_logs \
            "${source_key}" \
            "${source_path}" \
            "${DOCKER_LOGS_DIR}/${filename}"
    else
        collect_service_logs \
            "${source_key}" \
            "${service_name}" \
            "${DOCKER_LOGS_DIR}/${filename}" \
            "${compose_project}" \
            "${explicit_container_name}"
    fi
done < <(iterate_log_sources)

# ---------------------------------------------------------------------------
# 5. Write metadata timestamp (Celery uses this to detect stale data)
# ---------------------------------------------------------------------------
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${DOCKER_LOGS_DIR}/collected_at.txt"

log "Done. Total collected: ${TOTAL_BYTES} bytes"
