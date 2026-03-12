#!/usr/bin/env bash
###############################################################################
# deploy.sh
#
# Purpose:
#   Deploy a tagged release to production on the VPS in a safe, repeatable way.
#
# High-level behavior:
#   - Refuses to deploy untagged commits (tag == release)
#   - Ensures the tagged Docker images exist locally (never builds)
#   - Runs release tasks (migrations/collectstatic/etc) via release.sh
#   - Switches running services to the new TAG using docker compose up -d
#   - Performs a basic post-deploy health check (frontend + backend)
#   - Updates /var/lib/portfolio/{current_tag,prev_tag} for rollback tracking
#
# What this script DOES:
#   - Deploys images:
#       portfolio-backend:<TAG>
#       portfolio-frontend:<TAG>
#   - Starts/updates long-running services with docker compose
#   - Writes deployment state files for rollback tooling:
#       /var/lib/portfolio/current_tag
#       /var/lib/portfolio/prev_tag
#
# What this script DOES NOT DO:
#   - Does not build images (build.sh does that)
#   - Does not tag git commits (CI does that)
#   - Does not implement automatic rollback (manual rollback uses prev_tag)
#
# Typical usage:
#   TAG=v1.2.3 doppler run -- ./deploy.sh
#
# Optional:
#   --dry-run   Print what would happen without making changes
#
###############################################################################

set -euo pipefail

# ------------------------------------------------------------------
# Parse command-line arguments
# ------------------------------------------------------------------
DRY_RUN=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=true; echo "🧪 Dry-run mode enabled" ;;
    *)
      echo "❌ ERROR: Unknown argument: ${arg}"
      echo "✅ Usage: TAG=vX.Y.Z ENVIRONMENT=stg|prod doppler run -- ./deploy.sh [--dry-run]"
      exit 1
      ;;
  esac
done

: "${ENVIRONMENT:?ENVIRONMENT is required (inject via: doppler run -- ./deploy.sh)}"

# ------------------------------------------------------------------
# Setup & Context
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

PROJECT_DIR="$(get_project_dir)"

# Dynamic validation: If the config file exists, the environment is valid.
# This avoids hardcoding environment names and allows easy scaling (stage, prod, qa, etc).
if [[ ! -f "${PROJECT_DIR}/docker-compose.${ENVIRONMENT}.yml" ]]; then
  echo "❌ ERROR: Configuration for environment '$ENVIRONMENT' not found." >&2
  echo "� Expected: docker-compose.${ENVIRONMENT}.yml" >&2
  exit 1
fi

echo "⚙️  Environment: ${ENVIRONMENT}"

# ------------------------------------------------------------------
# Deploy lock (prevents concurrent deploys)
# ------------------------------------------------------------------
LOCK_DIR="/tmp/portfolio-deploy-${ENVIRONMENT}.lock"

if command -v flock >/dev/null 2>&1; then
  # Preferred method: flock provides robust, kernel-level locking.
  LOCK_FILE="${LOCK_DIR}.file"
  exec 9>"$LOCK_FILE"
  # Terminate early if another deployment process is already holding the lock.
  if ! flock -n 9; then
    echo "❌ ERROR: Another deploy appears to be running (lock: $LOCK_FILE)" >&2
    exit 1
  fi
  # Automatically remove the lock file when the script exits.
  cleanup() {
    local exit_code=$?
    rm -f "$LOCK_FILE"
    exit $exit_code
  }
  trap cleanup EXIT SIGINT SIGTERM
  echo "🔒 Deploy lock acquired (flock)"
else
  # Fallback: Directory-based locking for environments where flock is missing (e.g., macOS/CI).
  # mkdir is atomic in shell scripts. We add a small retry loop for robustness.
  MAX_LOCK_RETRIES=5
  for ((i=1; i<=MAX_LOCK_RETRIES; i++)); do
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      cleanup() { rm -rf "$LOCK_DIR"; }
      trap cleanup EXIT SIGINT SIGTERM
      echo "🔒 Deploy lock acquired (mkdir fallback)"
      break
    fi
    if [[ "$i" -eq "$MAX_LOCK_RETRIES" ]]; then
      echo "❌ ERROR: Another deploy appears to be running (lock: $LOCK_DIR)" >&2
      exit 1
    fi
    echo "⏳ Waiting for lock... ($i/$MAX_LOCK_RETRIES)"
    sleep 1
  done
fi

cd "$PROJECT_DIR"

# ------------------------------------------------------------------
# Resolve docker-compose production file
# ------------------------------------------------------------------
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_DIR/docker-compose.prod.yml}"
[[ -f "$COMPOSE_FILE" ]] || { echo "❌ ERROR: Missing compose file: $COMPOSE_FILE" >&2; exit 1; }
echo "🧾 Using compose file: $COMPOSE_FILE"

COMPOSE=(docker compose -f "$COMPOSE_FILE")

# Standardize project name by environment to ensure total isolation.
COMPOSE_PROJECT_NAME="landingpage-${ENVIRONMENT}"
export COMPOSE_PROJECT_NAME
echo "📦 Compose project: ${COMPOSE_PROJECT_NAME}"

# ------------------------------------------------------------------
# Resolve pre-deploy state (for rollback)
# ------------------------------------------------------------------
STATE_DIR="$(get_state_dir "${ENVIRONMENT}")"
CURRENT_FILE="$STATE_DIR/current_tag"
SAFE_TAG_BEFORE_DEPLOY="$(cat "$CURRENT_FILE" 2>/dev/null || true)"
SWITCHED_CONTAINERS=false

error_handler() {
  local exit_code=$?
  if [[ "${SWITCHED_CONTAINERS}" == "true" && -n "${SAFE_TAG_BEFORE_DEPLOY}" && "${SAFE_TAG_BEFORE_DEPLOY}" != "${TAG}" ]]; then
    echo "🚨 ERROR detected (exit code: $exit_code). Initiating automatic rollback to ${SAFE_TAG_BEFORE_DEPLOY}..."
    TAG="${SAFE_TAG_BEFORE_DEPLOY}" "${COMPOSE[@]}" up -d --remove-orphans
    echo "↩️  Rollback complete. System restored to ${SAFE_TAG_BEFORE_DEPLOY}."
  else
    echo "❌ ERROR detected (exit code: $exit_code). No rollback needed/possible."
  fi
  exit $exit_code
}
trap error_handler ERR

# ------------------------------------------------------------------
# Resolve release TAG
# ------------------------------------------------------------------
git fetch --tags >/dev/null 2>&1 || true
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
validate_tag "$TAG"
export TAG

# [DEPLOY] [1/6] Image preflight
# ------------------------------------------------------------------
echo "🔍 [DEPLOY] [1/6] Image preflight (verifying TAG=$TAG)"
# Verify each service image for TAG=${TAG}
# Implementation note: We check 'be', 'fe', 'celery-worker', 'nginx' and 'release'.
# We dynamically resolve the image from compose config for each service.
for svc in "be" "fe" "celery-worker" "nginx" "release"; do
  image_to_check=$(get_compose_image "$svc" "${COMPOSE[@]}")

  # Fallback to standard naming convention if config resolution fails.
  if [[ "${image_to_check}" =~ ^[[:space:]]*$ ]]; then
    echo "ℹ️  NOTE: Using naming fallback for '${svc}' (config resolution skipped)."
    image_to_check="${ENVIRONMENT}-${svc}"
    if [[ "$svc" == "release" ]]; then image_to_check="${ENVIRONMENT}-be"; fi
    if [[ "$svc" == "celery-worker" ]]; then image_to_check="${ENVIRONMENT}-worker"; fi
    image_to_check="${image_to_check}:$TAG"
  fi

  if ! docker image inspect "${image_to_check}" >/dev/null 2>&1; then
    echo "❌ Error: Missing image ${image_to_check}"
    echo "Please run build.sh first or ensure the image exists."
    exit 1
  fi
done

echo "✅ Images found. Proceeding with deployment."

echo "🧪 [DEPLOY] [2/6] Running release tasks (migrate/compilemessages/collectstatic/seeds)"

# ------------------------------------------------------------------
# Release tasks
# ------------------------------------------------------------------
echo "🧪 Running release tasks via release.sh..."
if [[ "${DRY_RUN}" == true ]]; then
  echo "🧾 DRY RUN: would execute: TAG=${TAG} ENVIRONMENT=${ENVIRONMENT} $SCRIPT_DIR/release.sh"
else
  ENVIRONMENT="${ENVIRONMENT}" TAG="${TAG}" "$SCRIPT_DIR/release.sh"
fi

# ------------------------------------------------------------------
# Switch running services to the new TAG
# ------------------------------------------------------------------
echo "🚀 [DEPLOY] [3/6] Switching containers to new images (TAG=$TAG)"
if [[ "${DRY_RUN}" == true ]]; then
  echo "🧾 DRY RUN: would execute: ${COMPOSE[*]} up -d --remove-orphans"
else
  "${COMPOSE[@]}" up -d --remove-orphans
  SWITCHED_CONTAINERS=true
fi

# ------------------------------------------------------------------
# Reload Nginx configuration
# ------------------------------------------------------------------
if [[ "${DRY_RUN}" == true ]]; then
  echo "🧾 DRY RUN: would reload Nginx config"
else
  echo "🔄 [DEPLOY] [4/6] Reloading Nginx configuration..."
  if "${COMPOSE[@]}" exec -T "nginx" nginx -s reload 2>/dev/null; then
    echo "✅ Nginx config reloaded successfully"
  else
    echo "⚠️  Nginx reload skipped (container may not be running)"
  fi
fi

# ------------------------------------------------------------------
# Health checks
# ------------------------------------------------------------------
if [[ "${DRY_RUN}" == true ]]; then
  echo "🩺 DRY RUN: skipping health checks."
else
  CURL_OPTS="-fsS -o /dev/null"

  echo "🩺 [DEPLOY] [5/6] Health check (Frontend)..."
  HEALTH_SITE_DOMAIN="${SITE_DOMAIN}"

  # Only bypass SSL validation in DEBUG environments (local development).
  if [[ "${DEBUG:-false}" == "true" || "${DEBUG:-}" == "1" ]]; then
    CURL_OPTS="${CURL_OPTS} -k"
  fi

  # Retry loop for frontend accessibility (accounts for slow Nginx or SSL generation).
  MAX_RETRIES_FE=20 # Extended to 60s (20 * 3s) for certificates and warmup.
  for ((i=1; i<=MAX_RETRIES_FE; i++)); do
    if curl ${CURL_OPTS} "https://${HEALTH_SITE_DOMAIN}/" 2>/dev/null; then
      echo "✅ Frontend is reachable at https://${HEALTH_SITE_DOMAIN}/"
      break
    fi
    echo "⏳ Waiting for frontend to become reachable… ($i/$MAX_RETRIES_FE)"
    sleep 3
    if [[ "$i" -eq "$MAX_RETRIES_FE" ]]; then
      echo "❌ Health check failed: frontend not reachable at https://${HEALTH_SITE_DOMAIN}/"
      false
    fi
  done

  # [DEPLOY] [6/6] Health check (Backend)
  # ------------------------------------------------------------------
  run_backend_health_checks() {
    echo "🩺 [DEPLOY] [6/6] Health check (Backend)..."
    # Implementation note: We use label-based resolution to find all active backend
    # containers. We iterate over each to ensure the whole cluster is healthy.
    # Progressive backoff sleep reduces log noise during slow warmups.
    local be_containers
    be_containers=$(docker ps --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" --filter "label=com.docker.compose.service=be" --format '{{.Names}}')

    if [[ -z "${be_containers}" ]]; then
      echo "⚠️  WARNING: No active backend containers found via labels; falling back to default naming."
      be_containers="${COMPOSE_PROJECT_NAME}-be-1"
    fi

    for container in ${be_containers}; do
      echo "🩺 Checking backend instance: ${container}"
      local MAX_RETRIES_BE=60
      for ((i=1; i<=MAX_RETRIES_BE; i++)); do
        # Use python as curl/wget may be missing in production images.
        # We connect to 127.0.0.1 and pass X-Forwarded-Proto: https to bypass Django's SSL redirect.
        # timeout=5 ensures the script doesn't hang if gunicorn is stuck.
        local python_health_cmd="import urllib.request; req = urllib.request.Request('http://127.0.0.1:8000/v1/health', headers={'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(req, timeout=5)"
        if docker exec "${container}" python3 -c "${python_health_cmd}" >/dev/null 2>&1; then
          echo "✅ Backend ${container} is healthy (/health)"
          break
        fi
        local sleep_time=$(( i < 10 ? 1 : i / 10 ))
        echo "⏳ Waiting for ${container}... ($i/$MAX_RETRIES_BE, sleep ${sleep_time}s)"
        sleep "${sleep_time}"
        if [[ "$i" -eq "$MAX_RETRIES_BE" ]]; then
          echo "❌ Health check failed: ${container} not reachable after ${MAX_RETRIES_BE} attempts"
          false
        fi
      done
    done
    echo "✅ All backend instances are healthy"
  }

  run_backend_health_checks
fi

# ------------------------------------------------------------------
# Update deployment state for rollback tracking
# ------------------------------------------------------------------
if [[ "${DRY_RUN}" == true ]]; then
  echo "📌 DRY RUN: skipping state file updates."
else
  STATE_DIR="$(get_state_dir "${ENVIRONMENT}")"
  CURRENT_FILE="$STATE_DIR/current_tag"
  PREV_FILE="$STATE_DIR/prev_tag"
  mkdir -p "$STATE_DIR"

  CURRENT_TAG="$(cat "$CURRENT_FILE" 2>/dev/null || true)"

  # Rotate deployment state files: prev_tag becomes rollback target.
  if [[ -n "$CURRENT_TAG" && "$CURRENT_TAG" != "$TAG" ]]; then
    echo "$CURRENT_TAG" > "$PREV_FILE"
    echo "↩️  prev_tag set to: $CURRENT_TAG"
  fi

  echo "$TAG" > "$CURRENT_FILE"
  echo "📌 current_tag set to: $TAG"
  echo "✅ Done. Deployed TAG=$TAG"
fi
