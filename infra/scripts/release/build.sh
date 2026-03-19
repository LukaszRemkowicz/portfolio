#!/usr/bin/env bash
###############################################################################
# build.sh
#
# Purpose:
#   Build versioned Docker images for production in a deterministic,
#   reproducible, and rollback-safe way.
#
# Usage:
#   [ENVIRONMENT=prod] [TAG=v1.2.3] doppler run -- ./build.sh [ARGS]
#
# Parameters (Environment Variables):
#   ENVIRONMENT   - Target environment (required: 'production', 'dev', etc.)
#   TAG           - Release tag (vX.Y.Z). If omitted, uses 'git describe'.
#   COMPOSE_FILE  - Path to the docker-compose file. Defaults to docker-compose.${ENVIRONMENT}.yml.
#   EMERGENCY     - Set to '1' to bypass dirty git status check.
#
#   Domain & Analytics (Required via Doppler):
#     API_DOMAIN, SITE_DOMAIN, GA_TRACKING_ID, SENTRY_DSN_FE,
#     ALLOWED_HOSTS, PROJECT_OWNER
#
#   Optional:
#     FRONTEND_PORT - Port for frontend service (default: 8080)
#
# Arguments (CLI):
#   --emergency   - Bypass dirty git status check (same as EMERGENCY=1).
#   --no-cache    - Force a fresh build without using Docker layer cache.
#
# High-level behavior:
#   - Refuses to run outside a git repository
#   - Refuses to run if the working tree is dirty (unless --emergency is used)
#   - Requires an exact git tag on HEAD (tag == release)
#   - Builds backend and frontend Docker images for that tag
#   - Does NOT deploy anything
#   - Does NOT run migrations or collect static files
#
# What this script DOES:
#   - Builds:
#       portfolio-backend:<TAG>
#       portfolio-frontend:<TAG>
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
source "${SCRIPT_DIR}/../utils.sh"

PROJECT_DIR="$(get_project_dir)"

echo "DEBUG: API_DOMAIN=${API_DOMAIN:-unset}"

# ------------------------------------------------------------------
# Emergency flag: --emergency or EMERGENCY=1
# Bypasses the dirty working-tree guard for urgent hotfix deploys.
# Usage: EMERGENCY=1 doppler run -- ./build.sh
#   or:  doppler run -- ./build.sh --emergency
# ------------------------------------------------------------------
EMERGENCY="${EMERGENCY:-0}"
CACHE_FLAG=""
for arg in "$@"; do
  case "${arg}" in
    --emergency) EMERGENCY=1 ;;
    --no-cache)  CACHE_FLAG="--no-cache"; echo "♻️  No-cache mode enabled (fresh build)" ;;
  esac
done



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
: "${ENVIRONMENT:?ENVIRONMENT is required (inject via: doppler run -- ./build.sh)}"
: "${PROJECT_OWNER:?PROJECT_OWNER is required (inject via: doppler run -- ./build.sh)}"
: "${FRONTEND_PORT:=8080}"

# Resolve Compose File
ENV_SUFFIX=$(get_env_suffix "${ENVIRONMENT}")
COMPOSE_FILE="${COMPOSE_FILE:-${PROJECT_DIR}/docker-compose.${ENV_SUFFIX}.yml}"

# Dynamic validation: If the config file exists, the environment is valid.
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "❌ ERROR: Configuration file not found: $COMPOSE_FILE" >&2
  echo "👉 Check environment naming and compose selection in infra/scripts/README.md" >&2
  exit 1
fi

echo "⚙️  Target ENVIRONMENT: ${ENVIRONMENT}"
echo "⚙️  Target API_DOMAIN: ${API_DOMAIN}"
echo "⚙️  Compose File: ${COMPOSE_FILE}"


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
  echo "👉 See release tagging guidance in infra/scripts/README.md"
  exit 1
fi
validate_tag "$TAG"
export TAG

echo "🏷️  Release tag: $TAG"

# Standardize project name for tagging/logging
COMPOSE_PROJECT_NAME="$(get_project_name)"
export COMPOSE_PROJECT_NAME
echo "📦 Compose project: ${COMPOSE_PROJECT_NAME}"

# Enforce deterministic build
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "${EMERGENCY}" == "1" ]]; then
    echo "⚠️  WARNING: Working tree is dirty — EMERGENCY bypass active. Proceeding anyway."
    git status --porcelain
  else
    echo "🛑 ERROR: Working tree is dirty. Commit or stash changes first."
    echo "👉 To bypass in an emergency: EMERGENCY=1 doppler run -- ./build.sh"
    echo "   or: doppler run -- ./build.sh --emergency"
    echo "👉 See emergency build guidance in infra/scripts/README.md"
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
  -t "${ENVIRONMENT}-be:${TAG}" \
  -t "${ENVIRONMENT}-worker:${TAG}" \
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
  -t "${ENVIRONMENT}-fe:${TAG}" \
  .
echo "✅ Frontend image built"

# ---------------- Nginx ----------------
echo "🌍 Building nginx release image..."
docker build \
  ${CACHE_FLAG} \
  --pull \
  -f docker/nginx/Dockerfile \
  -t "${ENVIRONMENT}-nginx:${TAG}" \
  .
echo "✅ Nginx image built"

# ------------------------------------------------------------------
# Verify Built Images
# ------------------------------------------------------------------
echo "📦 Built images:"
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -E "^${ENVIRONMENT}-(be|fe|worker|nginx):${TAG}"; then
  echo "❌ ERROR: Expected built images were not found after build."
  echo "👉 Check image naming in infra/scripts/README.md"
  exit 1
fi


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
REPOS=("${ENVIRONMENT}-be" "${ENVIRONMENT}-fe" "${ENVIRONMENT}-worker" "${ENVIRONMENT}-nginx")

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
  # Sort by CreatedAt (newest first) to accurately identify "last versions"
  tags=()
  while IFS=$'\t' read -r _ tag; do
    if [[ -n "$tag" && "$tag" != "<none>" ]]; then
      # Only include tags matching our SemVer pattern
      if [[ "$tag" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+ ]]; then
        tags+=("$tag")
      fi
    fi
  done < <(
    docker images "$repo" --format '{{.CreatedAt}}\t{{.Tag}}' | sort -r
  )
  # -----------------------------------------------

  # Check if we have more tags than our retention window allows.
  if (( ${#tags[@]} > KEEP_IMAGES )); then
    # Since tags are sorted newest-first, we keep the first KEEP_IMAGES (0..4)
    # and remove everything from index 5 onwards.
    for ((i=KEEP_IMAGES; i<${#tags[@]}; i++)); do
      t="${tags[$i]}"

      # NEVER remove the tag we just built, or the ones currently/previously live.
      if [[ "$t" == "$TAG" ]] || [[ -n "$CURRENT_TAG" && "$t" == "$CURRENT_TAG" ]] || [[ -n "$PREV_TAG" && "$t" == "$PREV_TAG" ]]; then
        echo "📌 Skipping protective tag: $repo:$t"
        continue
      fi

      echo "🗑️ Removing old image: $repo:$t"
      docker image rm -f "$repo:$t" >/dev/null 2>&1 || true
    done
  else
    echo "✔️ Nothing to clean for $repo"
  fi
done

echo "🎉 Build completed successfully for tag: $TAG"
