#!/usr/bin/env bash
###############################################################################
# build.sh
#
# Purpose:
#   Build versioned Docker images for production in a deterministic,
#   reproducible, and rollback-safe way.
#
# High-level behavior:
#   - Refuses to run outside a git repository
#   - Refuses to run if the working tree is dirty
#   - Requires an exact git tag on HEAD (tag == release)
#   - Builds backend and frontend Docker images for that tag
#   - Does NOT deploy anything
#   - Does NOT run migrations or collect static files
#
# What this script DOES:
#   - Builds:
#       portfolio-backend:<TAG>
#       portfolio-frontend:<TAG>
#       portfolio-nginx:<TAG>
#   - Uses Docker BuildKit for consistent builds
#   - Injects runtime configuration via environment variables
#   - Cleans up old images while keeping:
#       - the tag just built
#       - the currently deployed tag
#       - the previous (rollback) tag
#
# What this script DOES NOT DO:
#   - Does not start containers
#   - Does not modify docker-compose state
#   - Does not update current_tag / prev_tag
#   - Does not touch the database
#
# Typical usage:
#   TAG=v1.2.3 doppler run -- ./build.sh
#
###############################################################################

set -euo pipefail

# ------------------------------------------------------------------
# Setup & Context
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

PROJECT_DIR="$(get_project_dir)"

echo "DEBUG: API_DOMAIN=${API_DOMAIN:-unset}"

# ------------------------------------------------------------------
# Emergency flag: --emergency or EMERGENCY=1
# Bypasses the dirty working-tree guard for urgent hotfix deploys.
# Usage: EMERGENCY=1 doppler run -- ./build.sh
#   or:  doppler run -- ./build.sh --emergency
# ------------------------------------------------------------------
ENVIRONMENT="${ENVIRONMENT:-}"
EMERGENCY="${EMERGENCY:-0}"
CACHE_FLAG=""
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env=*)    ENVIRONMENT="${1#*=}"; shift ;;
    --env)      ENVIRONMENT="$2"; shift 2 ;;
    --emergency) EMERGENCY=1; shift ;;
    --no-cache)  CACHE_FLAG="--no-cache"; echo "♻️  No-cache mode enabled (fresh build)"; shift ;;
    *)           ARGS+=("$1"); shift ;;
  esac
done

# Restore positional arguments if needed
[[ ${#ARGS[@]} -gt 0 ]] && set -- "${ARGS[@]}"



# ------------------------------------------------------------------
# Required environment variables (injected by Doppler)
#
# These must be provided at runtime (not hardcoded defaults),
# to avoid accidentally building a production image with "local" config.
#
# Usage example:
#   doppler run -- ./build.sh
# ------------------------------------------------------------------
: "${API_DOMAIN:?API_DOMAIN is required (inject via: doppler run -- ./build.sh)}"
: "${GA_TRACKING_ID:?GA_TRACKING_ID is required (inject via: doppler run -- ./build.sh)}"
: "${SITE_DOMAIN:?SITE_DOMAIN is required (inject via: doppler run -- ./build.sh)}"
: "${SENTRY_DSN_FE:?SENTRY_DSN_FE is required (inject via: doppler run -- ./build.sh)}"
: "${ALLOWED_HOSTS:?ALLOWED_HOSTS is required (inject via: doppler run -- ./build.sh)}"
: "${ENVIRONMENT:?ENVIRONMENT is required (set via --env=production|stage or ENVIRONMENT=...)}"
: "${PROJECT_OWNER:?PROJECT_OWNER is required (inject via: doppler run -- ./build.sh)}"
: "${FRONTEND_PORT:=8080}"

# Map full environment names to internal shorthand
ENV_SHORT="${ENVIRONMENT}"
if [[ "${ENVIRONMENT}" == "production" ]]; then
  ENV_SHORT="prod"
fi

# Dynamic validation: If the config file exists, the environment is valid.
if [[ ! -f "${PROJECT_DIR}/docker-compose.${ENV_SHORT}.yml" ]]; then
  echo "❌ ERROR: Configuration for environment '$ENVIRONMENT' (mapped to '$ENV_SHORT') not found." >&2
  echo "📂 Expected: docker-compose.${ENV_SHORT}.yml" >&2
  exit 1
fi

# Define Image Naming Convention
if [[ "${ENV_SHORT}" == "prod" ]]; then
  IMAGE_PREFIX="portfolio"
else
  IMAGE_PREFIX="portfolio-${ENV_SHORT}"
fi

echo "⚙️  Target ENVIRONMENT: ${ENVIRONMENT} (using: ${ENV_SHORT})"
echo "⚙️  Image Prefix: ${IMAGE_PREFIX}"
echo "⚙️  Target API_DOMAIN: ${API_DOMAIN}"


# ------------------------------------------------------------------
# Set working directory
# ------------------------------------------------------------------
cd "$PROJECT_DIR"
echo "📁 Project root: ${PROJECT_DIR}"


# ------------------------------------------------------------------
# Resolve release TAG
# ------------------------------------------------------------------
git fetch --tags >/dev/null 2>&1 || true
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
if [[ -z "$TAG" ]]; then
  echo "🛑 ERROR: No Git tag on HEAD."
  echo "👉 Fix: git tag vX.Y.Z && git push origin vX.Y.Z"
  exit 1
fi
validate_tag "$TAG"
export TAG

echo "🏷️  Release tag: $TAG"

# Enforce deterministic build
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "${EMERGENCY}" == "1" ]]; then
    echo "⚠️  WARNING: Working tree is dirty — EMERGENCY bypass active. Proceeding anyway."
    git status --porcelain
  else
    echo "🛑 ERROR: Working tree is dirty. Commit or stash changes first."
    echo "👉 To bypass in an emergency: EMERGENCY=1 doppler run -- ./build.sh"
    echo "   or: doppler run -- ./build.sh --emergency"
    git status --porcelain
    exit 1
  fi
fi


# ------------------------------------------------------------------
# Enable Docker BuildKit
# ------------------------------------------------------------------
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"
echo "⚙️  DOCKER_BUILDKIT=${DOCKER_BUILDKIT}"


echo "🏗️  Starting build..."

# ---------------- Backend ----------------
docker build \
  ${CACHE_FLAG} \
  --pull \
  -f docker/backend/Dockerfile \
  --target production \
  -t "${IMAGE_PREFIX}-backend:${TAG}" \
  -t "${IMAGE_PREFIX}-worker:${TAG}" \
  .
echo "✅ Backend & Worker images built"

# ---------------- Frontend ----------------
echo "🌐 Building frontend image..."
docker build \
  ${CACHE_FLAG} \
  --pull \
  -f docker/frontend/Dockerfile \
  --target prod \
  --build-arg "SITE_DOMAIN=${SITE_DOMAIN}" \
  --build-arg "API_URL=https://${API_DOMAIN}" \
  --build-arg "GA_TRACKING_ID=${GA_TRACKING_ID}" \
  --build-arg "SENTRY_DSN_FE=${SENTRY_DSN_FE}" \
  --build-arg "FRONTEND_PORT=${FRONTEND_PORT}" \
  --build-arg "PROJECT_OWNER=${PROJECT_OWNER}" \
  -t "${IMAGE_PREFIX}-frontend:${TAG}" \
  .
echo "✅ Frontend image built"

# ---------------- Nginx ----------------
echo "🛡️  Building Nginx image..."
docker build \
  ${CACHE_FLAG} \
  --pull \
  -f docker/nginx/Dockerfile \
  -t "${IMAGE_PREFIX}-nginx:${TAG}" \
  .
echo "✅ Nginx image built"
# ---------------- Redis ----------------
echo "🔋 Building Redis image..."
docker build \
  ${CACHE_FLAG} \
  --pull \
  -f docker/redis/Dockerfile \
  -t "${IMAGE_PREFIX}-redis:${TAG}" \
  ./docker/redis
echo "✅ Redis image built"


# ------------------------------------------------------------------
# Verify Built Images
# ------------------------------------------------------------------
echo "📦 Built images:"
docker images --format '{{.Repository}}:{{.Tag}}' | grep -E "^${IMAGE_PREFIX}-(backend|frontend|worker|nginx|redis):${TAG}"


# ------------------------------------------------------------------
# Cleanup old images
#
# To prevent the VPS disk from filling up, we remove older images.
# We maintain a "retention window" of the last 5 SemVer-tagged builds.
#
# State Management:
#   We track 'current_tag' (what is live) and 'prev_tag' (rollback target).
#   These are stored in a persistent directory ($STATE_DIR).
#   deploy.sh handles updating these files; build.sh only reads them for auditing.
# ------------------------------------------------------------------
  STATE_DIR="$(get_state_dir "${ENVIRONMENT}")"
CURRENT_FILE="$STATE_DIR/current_tag"
PREV_FILE="$STATE_DIR/prev_tag"
mkdir -p "$STATE_DIR"

CURRENT_TAG="$(cat "$CURRENT_FILE" 2>/dev/null || true)"
PREV_TAG="$(cat "$PREV_FILE" 2>/dev/null || true)"

echo "🧹 Cleaning up old images..."
echo "📌 Keeping tags: build=$TAG current=${CURRENT_TAG:-none} prev=${PREV_TAG:-none}"


# ------------------------------------------------------------------
# Retention Policy - Keep last 5 versions for each service image.
# ------------------------------------------------------------------
KEEP_IMAGES=5
REPOS=("${IMAGE_PREFIX}-backend" "${IMAGE_PREFIX}-frontend" "${IMAGE_PREFIX}-worker" "${IMAGE_PREFIX}-nginx" "${IMAGE_PREFIX}-redis")

echo "🧹 Cleaning up images (keeping last $KEEP_IMAGES versions)..."


# ------------------------------------------------------------------
# Tag Discovery Optimization
# ------------------------------------------------------------------
# Implementation note: We use a 'while read' loop for universal compatibility.
# This works on both macOS (Bash 3.2) and Linux (Bash 4.0+).
#
# PERFORMANCE TIP (PRODUCTION ONLY on Ubuntu):
# If you have thousands of images, you can replace the entire 'while' loop block
# (the 6 lines from 'tags=()' down to ') ') with this one-liner:
#
#   mapfile -t tags < <(docker images "$repo" --format '{{.Tag}}' | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+" | sort -V)
#
# ------------------------------------------------------------------
for repo in "${REPOS[@]}"; do
  echo "➡️ Repo: $repo"

  # --- Universal Tag Discovery (macOS + Linux) ---
  tags=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && tags+=("$line")
  done < <(
    docker images "$repo" --format '{{.Tag}}' \
    | grep -E "^v?[0-9]+\.[0-9]+\.[0-9]+" \
    | sort -V
  )
  # -----------------------------------------------

  # Check if we have more tags than our retention window allows.
  if (( ${#tags[@]} > KEEP_IMAGES )); then
    remove_count=$((${#tags[@]} - KEEP_IMAGES))
    # Remove the oldest tags first (at the start of the sorted list).
    for ((i=0; i<remove_count; i++)); do
      t="${tags[$i]}"
      echo "🗑️ Removing old image: $repo:$t"
      docker image rm -f "$repo:$t" >/dev/null 2>&1 || true
    done
  else
    echo "✔️ Nothing to clean for $repo"
  fi
done

echo "🧹 Removing any remaining dangling images..."
docker image prune -f

echo "🎉 Build completed successfully for tag: $TAG"
