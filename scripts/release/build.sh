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
# Preconditions:
#   - Must be run from inside the git repository
#   - HEAD must be exactly tagged (vX.Y.Z)
#   - Required environment variables must be provided
#     (typically via: doppler run -- ./build.sh)
#   - Docker must be available on the host
#
# Typical usage:
#   TAG=v1.2.3 doppler run -- ./build.sh
#
# Relationship to other scripts:
#   - build.sh   → builds images only (this file)
#   - release.sh → runs migrations / collectstatic
#   - deploy.sh  → starts services and handles rollback
#
# Design principles:
#   - Deterministic: same inputs → same images
#   - Explicit: no hidden defaults for production config
#   - Boring: no automation magic, easy to reason about
#
###############################################################################

set -euo pipefail

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

echo "API_DOMAIN=${API_DOMAIN}"


# ------------------------------------------------------------------
# Resolve project root directory
#
# We require running inside the git repository, because:
# - build context paths are relative to repo root
# - tag detection uses git metadata
# - prevents "ran from wrong directory" mistakes
# ------------------------------------------------------------------
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$PROJECT_DIR" ]]; then
  echo "❌ ERROR: build.sh must be run inside a Git repository."
  exit 1
fi
cd "$PROJECT_DIR"
echo "📁 Project root: ${PROJECT_DIR}"



# ------------------------------------------------------------------
# Resolve release TAG
#
# We require an exact git tag on HEAD to make builds reproducible.
# This prevents "I built some random commit and forgot which one".
# ------------------------------------------------------------------
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
if [[ -z "$TAG" ]]; then
  echo "🛑 ERROR: No Git tag on HEAD."
  echo "👉 Fix: git tag vX.Y.Z && git push origin vX.Y.Z"
  exit 1
fi
export TAG

if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([\-+].+)?$ ]]; then
  echo "ERROR: Tag '$TAG' is not SemVer-like (expected vX.Y.Z or vX.Y.Z-suffix)" >&2
  exit 1
fi

echo "🏷️  Release tag: $TAG"


# Enforce deterministic build
if [[ -n "$(git status --porcelain)" ]]; then
  echo "🛑 ERROR: Working tree is dirty. Commit or stash changes first."
  git status --porcelain
  exit 1
fi


# ------------------------------------------------------------------
# Enable Docker BuildKit
#
# BuildKit improves performance and caching and is the modern builder.
# ------------------------------------------------------------------
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"
echo "⚙️  DOCKER_BUILDKIT=${DOCKER_BUILDKIT}"


echo "🏗️  Starting build..."

# ---------------- Backend ----------------
echo "🐍 Building backend image..."
docker build \
  --pull \
  --target production \
  -t "portfolio-backend:$TAG" \
  ./backend
echo "✅ Backend image built"

# ---------------- Frontend ----------------
echo "🌐 Building frontend image..."
docker build \
  --pull \
  -f frontend/Dockerfile \
  --target prod \
  --build-arg "SITE_DOMAIN=${SITE_DOMAIN}" \
  --build-arg "API_URL=https://${API_DOMAIN}" \
  --build-arg "GA_TRACKING_ID=${GA_TRACKING_ID}" \
  -t "portfolio-frontend:$TAG" \
  .
echo "✅ Frontend image built"


# ------------------------------------------------------------------
# Summary
#
# Show resulting images for quick verification.
# ------------------------------------------------------------------

echo "📦 Built images:"
docker images | grep -E '^portfolio-(frontend|backend)'


# ------------------------------------------------------------------
# Cleanup old images
#
# We keep:
# - the tag we just built
# - the "current" tag (currently deployed)
# - the "prev" tag (rollback target)
#
# Everything else for these repos can be removed to save disk space.
# ------------------------------------------------------------------
# We write:
# - current_tag: the tag considered "currently deployed"
# - prev_tag   : the previous value of current_tag (rollback target)
# ------------------------------------------------------------------
# State directory for tag tracking
# We prefer /var/lib/portfolio for multi-user consistency (sudo vs regular),
# but fallback to $HOME if we can't write there.
if [[ -z "${STATE_DIR:-}" ]]; then
  if [[ -w "/var/lib/portfolio" ]] || [[ "$EUID" -eq 0 && -d "/var/lib" ]]; then
    STATE_DIR="/var/lib/portfolio"
  else
    STATE_DIR="$HOME/.portfolio-state"
  fi
fi
CURRENT_FILE="$STATE_DIR/current_tag"
PREV_FILE="$STATE_DIR/prev_tag"
mkdir -p "$STATE_DIR"

CURRENT_TAG="$(cat "$CURRENT_FILE" 2>/dev/null || true)"
PREV_TAG="$(cat "$PREV_FILE" 2>/dev/null || true)"

echo "🧹 Cleaning up old images..."
echo "📌 Keeping tags: build=$TAG current=${CURRENT_TAG:-none} prev=${PREV_TAG:-none}"

should_keep() {
  local t="$1"
  [[ -n "$t" && "$t" != "<none>" ]] || return 1
  [[ "$t" == "$TAG" ]] && return 0
  [[ -n "$CURRENT_TAG" && "$t" == "$CURRENT_TAG" ]] && return 0
  [[ -n "$PREV_TAG" && "$t" == "$PREV_TAG" ]] && return 0
  return 1
}

for repo in portfolio-backend portfolio-frontend; do
  mapfile -t tags < <(docker images "$repo" --format '{{.Tag}}' | sort -u)
  for t in "${tags[@]}"; do
    if should_keep "$t"; then
      continue
    fi
    docker image rm -f "$repo:$t" >/dev/null 2>&1 || true
  done
done

KEEP_TAGS=("$TAG")
[[ -n "$CURRENT_TAG" ]] && KEEP_TAGS+=("$CURRENT_TAG")
[[ -n "$PREV_TAG" ]] && KEEP_TAGS+=("$PREV_TAG")

docker image prune -f >/dev/null 2>&1 || true

echo "🎉 Build completed successfully for tag: $TAG"
