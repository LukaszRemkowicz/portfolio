#!/usr/bin/env bash
###############################################################################
# release.sh
#
# Purpose:
#   Run a safe, repeatable "release job" (migrations, seeds, etc) for production.
#
# High-level behavior:
#   - Prevents concurrent releases via flock
#   - Dynamically resolves release image from docker-compose config
#   - Ensures required dependencies (db, redis) are running and healthy
#   - Captures release logs for long-term auditing
#
# Typical usage:
#   TAG=v1.2.3 ENVIRONMENT=stage doppler run -- ./release.sh
#
# Parameters (Environment Variables):
#   ENVIRONMENT   - Target environment (required: 'production', 'dev', etc.)
#   TAG           - Release tag (vX.Y.Z). Defaults to 'git describe'.
#   COMPOSE_FILE  - Path to the docker-compose file. Defaults to docker-compose.${ENVIRONMENT}.yml.
###############################################################################

set -euo pipefail

: "${ENVIRONMENT:?ENVIRONMENT is required (inject via: doppler run -- ./release.sh)}"

# ------------------------------------------------------------------
# Setup & Context
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils.sh"

PROJECT_DIR="$(get_project_dir)"
COMMON_COMPOSE_FILE="${PROJECT_DIR}/docker-compose.common.yml"

# Resolve Compose File
ENV_SUFFIX=$(get_env_suffix "${ENVIRONMENT}")
COMPOSE_FILE="${COMPOSE_FILE:-${PROJECT_DIR}/docker-compose.${ENV_SUFFIX}.yml}"

# Dynamic validation: If the config file exists, the environment is valid.
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "❌ ERROR: Configuration file not found: $COMPOSE_FILE" >&2
  echo "👉 Check environment naming and compose selection in infra/scripts/README.md" >&2
  exit 1
fi
if [[ ! -f "$COMMON_COMPOSE_FILE" ]]; then
  echo "❌ ERROR: Common compose file not found: $COMMON_COMPOSE_FILE" >&2
  echo "👉 Check repository layout and deploy docs in infra/scripts/README.md" >&2
  exit 1
fi

echo "⚙️  Environment: ${ENVIRONMENT}"
echo "🧾 Using compose file: $COMPOSE_FILE"
echo "🧾 Using common compose file: $COMMON_COMPOSE_FILE"

cd "${PROJECT_DIR}"
COMPOSE_PROJECT_NAME="$(get_project_name)"
export COMPOSE_PROJECT_NAME

# ------------------------------------------------------------------
# Parse arguments
# ------------------------------------------------------------------
DRY_RUN=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=true; echo "🧪 Dry-run mode enabled" ;;
    *)
      echo "❌ ERROR: Unknown argument: ${arg}"
      echo "👉 Supported usage is documented in infra/scripts/README.md"
      exit 1
      ;;
  esac
done

# ------------------------------------------------------------------
# Concurrency Lock
# ------------------------------------------------------------------
if command -v flock >/dev/null 2>&1; then
  LOCK_FILE="/tmp/portfolio-release-${ENVIRONMENT}.lock"
  exec 9>"$LOCK_FILE"
  if ! flock -n -w 300 9; then
    echo "❌ ERROR: Another release is running (lock: $LOCK_FILE). Timed out." >&2
    echo "👉 Check release troubleshooting in infra/scripts/README.md" >&2
    exit 1
  fi
  # Automatically remove the lock file when the script exits.
  cleanup() {
    local exit_code=$?
    rm -f "${LOCK_FILE:-}"
    exit $exit_code
  }
  trap cleanup EXIT SIGINT SIGTERM
  echo "🔒 Release lock acquired"
else
  echo "⚠️  'flock' not found; skipping concurrency lock"
fi

# ------------------------------------------------------------------
# Resolve TAG & Compose
# ------------------------------------------------------------------
git fetch --tags >/dev/null 2>&1 || true
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
validate_tag "$TAG"
export TAG

export COMPOSE_FILE
COMPOSE=(docker compose -f "${COMMON_COMPOSE_FILE}" -f "${COMPOSE_FILE}")

DB_SVC="db"
REDIS_SVC="redis"
RELEASE_SVC="release"

# ------------------------------------------------------------------
# Dependency & Health Checks
# ------------------------------------------------------------------
check_health() {
  echo "🔍 [RELEASE] [1/4] Checking dependencies..."

  # Ensure containers are at least running
  # STRICT DRY_RUN: In dry-run mode, we do NOT attempt to start services.
  # We only warn if they are missing.
  if ! "${COMPOSE[@]}" ps --services --status running 2>/dev/null | grep -q "^${DB_SVC}$"; then
    if [[ "${DRY_RUN}" == "true" ]]; then
       echo "⚠️  DRY RUN: Database is NOT running (would be started in a real run)."
    else
       echo "🧩 Starting database..."
       "${COMPOSE[@]}" up -d "${DB_SVC}"
    fi
  fi

  if ! "${COMPOSE[@]}" ps --services --status running 2>/dev/null | grep -q "^${REDIS_SVC}$"; then
    if [[ "${DRY_RUN}" == "true" ]]; then
       echo "⚠️  DRY RUN: Redis is NOT running (would be started in a real run)."
    else
       echo "🧩 Starting redis..."
       "${COMPOSE[@]}" up -d "${REDIS_SVC}"
    fi
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then return 0; fi

  # 1. Database Health (Configurable Timeout & Progressive Backoff)
  local db_timeout="${DB_HEALTH_TIMEOUT:-120}"

  # Dynamically resolve ALL active database container names.
  # This handles clusters or scaled instances (e.g. db-1, db-2).
  local db_containers
  db_containers=$(docker ps --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" --filter "label=com.docker.compose.service=${DB_SVC}" --format '{{.Names}}')

  if [[ -z "${db_containers}" ]]; then
     echo "⚠️  WARNING: No active DB containers found via labels; falling back to default naming."
     db_containers="${COMPOSE_PROJECT_NAME}-${DB_SVC}-1"
  fi

  for container in ${db_containers}; do
    echo "🩺 Checking database: ${container}"
    for ((i=1; i<=db_timeout; i++)); do
      if docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null | grep -q "healthy"; then
        echo "✅ Database ${container} is healthy"
        break
      fi
      # Progressive backoff sleep: sleep 1s for first 10 tries, then i/10s.
      # This reduces log spam during long boots or massive migrations.
      local sleep_time=$(( i < 10 ? 1 : i / 10 ))
      echo "⏳ Waiting for ${container}... ($i/$db_timeout, sleep ${sleep_time}s)"
      sleep "${sleep_time}"
      [[ "$i" -eq "$db_timeout" ]] && { echo "❌ ERROR: Database ${container} timeout"; echo "👉 Check release troubleshooting in infra/scripts/README.md" >&2; exit 1; }
    done
  done

  # 2. Redis Health (Multi-instance & Retry Loop)
  local redis_timeout=30
  local redis_containers
  redis_containers=$(docker ps --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" --filter "label=com.docker.compose.service=${REDIS_SVC}" --format '{{.Names}}')

  if [[ -z "${redis_containers}" ]]; then
     echo "⚠️  WARNING: No active Redis containers found via labels; falling back to default naming."
     redis_containers="${COMPOSE_PROJECT_NAME}-${REDIS_SVC}-1"
  fi

  for container in ${redis_containers}; do
    echo "🩺 Checking Redis: ${container}"
    local redis_ok=false
    for ((i=1; i<=redis_timeout; i++)); do
      # Preferred: Live PING
      if docker exec "${container}" redis-cli PING 2>/dev/null | grep -iq "PONG"; then
        echo "✅ Redis ${container} is reachable (PONG)"
        redis_ok=true
        break
      fi
      # Fallback: Docker Health Status
      if docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null | grep -q "healthy"; then
        echo "✅ Redis ${container} is healthy (Docker)"
        redis_ok=true
        break
      fi
      local sleep_time=$(( i < 10 ? 1 : i / 10 ))
      echo "⏳ Waiting for ${container}... ($i/$redis_timeout, sleep ${sleep_time}s)"
      sleep "${sleep_time}"
    done

    if [[ "${redis_ok}" != "true" ]]; then
      echo "❌ ERROR: Redis ${container} not ready after ${redis_timeout}s." >&2
      echo "👉 Check release troubleshooting in infra/scripts/README.md" >&2
      exit 1
    fi
  done
}

check_health

# ------------------------------------------------------------------
# Image Preflight
# ------------------------------------------------------------------
echo "🔎 [RELEASE] [2/4] Checking release image..."

RELEASE_IMAGE=$(get_compose_image "${RELEASE_SVC}" "${COMPOSE[@]}")

if [[ "${RELEASE_IMAGE}" =~ ^[[:space:]]*$ ]]; then
  echo "ℹ️  NOTE: Using naming fallback for release image (config resolution skipped)."
  echo "👉 Fallback image: ${ENVIRONMENT}-be:${TAG}"
  RELEASE_IMAGE="${ENVIRONMENT}-be:${TAG}"
fi

if ! docker image inspect "${RELEASE_IMAGE}" >/dev/null 2>&1; then
  echo "❌ Error: Missing image ${RELEASE_IMAGE}"
  echo "👉 Check image naming and build order in infra/scripts/README.md" >&2
  exit 1
fi
echo "✅ Image found: ${RELEASE_IMAGE}"

# ------------------------------------------------------------------
# Execution
# ------------------------------------------------------------------
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "🧪 DRY RUN: Would execute release job for ${TAG}"
  exit 0
fi

if [[ "${ENV_SUFFIX}" == "prod" ]]; then
  echo "🛡️ [RELEASE] Downloading Nginx bot blocklist..."
  if ! "${COMPOSE[@]}" run --rm "nginx-blocklist-init"; then
    echo "⚠️ WARNING: Blocklist download failed. Nginx will start with an empty list."
  fi

  BACKUP_DIR="${BACKUP_DIR:-/var/backups/portfolio/pre_release/prod}"
  echo "💾 [RELEASE] Creating pre-release database backup in ${BACKUP_DIR}..."
  if ! ENVIRONMENT="${ENVIRONMENT}" \
       COMPOSE_FILE="${COMPOSE_FILE}" \
       BACKUP_DIR="${BACKUP_DIR}" \
       "${PROJECT_DIR}/infra/scripts/db_backup/backup_db.sh"; then
    echo "❌ ERROR: Pre-release database backup failed. Refusing to run migrations." >&2
    echo "👉 Check backup directory ownership and setup in infra/scripts/README.md and infra/docs/traefik_production_deployment.md" >&2
    exit 1
  fi
fi

LOG_DIR="$HOME/.portfolio-logs/${ENVIRONMENT}"
LOG_FILE="${LOG_DIR}/release-${TAG}-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$LOG_DIR" || { echo "❌ ERROR: Cannot create log dir $LOG_DIR"; exit 1; }

# ------------------------------------------------------------------
# Releasing
# ------------------------------------------------------------------
echo "🚀 [RELEASE] [3/3] Running release job..."
echo "📝 Logs: $LOG_FILE"

if "${COMPOSE[@]}" run --rm "${RELEASE_SVC}" 2>&1 | tee "$LOG_FILE"; then
  echo "🎉 Release successful!"
else
  echo "❌ ERROR: Release job failed." >&2
  echo "📁 Log summary (cat $LOG_FILE):" >&2
  echo "------------------------------------------------------------------" >&2
  cat "$LOG_FILE" >&2
  echo "------------------------------------------------------------------" >&2
  exit 1
fi
