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
# Preconditions:
#   - Must be run inside the git repository on the server
#   - TAG must be provided or HEAD must be exactly tagged (vX.Y.Z…)
#   - build.sh must have been run for that TAG on this server
#   - release.sh must be present and executable
#   - Required runtime env vars must be provided (typically via Doppler)
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
#
# Supported:
#   --dry-run  : show what would be executed without changing anything
#
# We fail on unknown args to avoid ambiguity.
# ------------------------------------------------------------------
DRY_RUN=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=true; echo "🧪 Dry-run mode enabled" ;;
    *)
      echo "❌ ERROR: Unknown argument: ${arg}"
      echo "✅ Usage: TAG=vX.Y.Z doppler run -- ./deploy.sh [--dry-run]"
      exit 1
      ;;
  esac
done


COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-portfolio}"
export COMPOSE_PROJECT_NAME
echo "📦 Compose project: ${COMPOSE_PROJECT_NAME}"

command -v flock >/dev/null 2>&1 || {
  echo "❌ ERROR: 'flock' is required but not installed (usually in util-linux)." >&2
  exit 1
}


# ------------------------------------------------------------------
# Deploy lock (prevents concurrent deploys)
#
# Two deploys at once can race:
# - migrations / collectstatic
# - container restarts
# - state files (current_tag/prev_tag)
#
# flock creates a filesystem lock to serialize deploys.
# ------------------------------------------------------------------
LOCK_FILE="/var/lock/portfolio-deploy.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "❌ ERROR: Another deploy appears to be running (lock: $LOCK_FILE)" >&2
  exit 1
fi
echo "🔒 Deploy lock acquired"


# ------------------------------------------------------------------
# Resolve repository root
#
# We locate the git root so the script works regardless of the
# current working directory.
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  PROJECT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
else
  echo "ERROR: deploy.sh must be inside a git repository"
  exit 1
fi

cd "$PROJECT_DIR"


# ------------------------------------------------------------------
# Resolve docker-compose production file
#
# You may override COMPOSE_PROD, otherwise we default to:
#   <repo>/docker-compose.prod.yml
# ------------------------------------------------------------------
COMPOSE_PROD="${COMPOSE_PROD:-$PROJECT_DIR/docker-compose.prod.yml}"
[[ -f "$COMPOSE_PROD" ]] || { echo "❌ ERROR: Missing compose file: $COMPOSE_PROD" >&2; exit 1; }
echo "🧾 Using compose file: $COMPOSE_PROD"


COMPOSE=(docker compose -f "$COMPOSE_PROD")


# ------------------------------------------------------------------
# Parse command-line arguments
#
# Supported:
#   --dry-run  : show what would be executed without changing anything
#
# We fail on unknown args to avoid ambiguity.
# ------------------------------------------------------------------
TAG="${TAG:-$(git -C "$PROJECT_DIR" describe --tags --exact-match 2>/dev/null || true)}"
if [[ -z "${TAG}" ]]; then
  echo "🛑❌ ERROR: TAG is required (or HEAD must be exactly tagged)."
  echo "👉 Example: TAG=vX.Y.Z doppler run -- ./deploy.sh"
  exit 1
fi
export TAG

if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([\-+].+)?$ ]]; then
  echo "❌ ERROR: Tag '$TAG' is not SemVer-like (expected vX.Y.Z or vX.Y.Z-suffix)" >&2
  exit 1
fi

# ------------------------------------------------------------------
# Image preflight
#
# deploy.sh never builds. Images must already exist locally.
# This prevents accidental "deploy built something else" behavior.
# ------------------------------------------------------------------
echo "🔎 [1/3] Checking images for TAG=$TAG"

# Robust check for image existence
if ! docker image inspect "portfolio-backend:$TAG" >/dev/null 2>&1; then
  echo "❌ Error: Missing image portfolio-backend:$TAG"
  echo "Please run build.sh first or ensure the image exists."
  exit 1
fi

if ! docker image inspect "portfolio-frontend:$TAG" >/dev/null 2>&1; then
  echo "❌ Error: Missing image portfolio-frontend:$TAG"
  echo "Please run build.sh first or ensure the image exists."
  exit 1
fi

echo "✅ Images found. Proceeding with deployment."

echo "🧪 [2/3] Release tasks (migrate/compilemessages/collectstatic/seeds)"

# ------------------------------------------------------------------
# Release tasks
#
# We delegate to release.sh so all safety checks live in one place:
# - dependencies up
# - db health wait
# - pinned backend image
# ------------------------------------------------------------------
echo "🧪 Running release tasks via release.sh..."
if [[ "${DRY_RUN}" == true ]]; then
  echo "🧾 DRY RUN: would execute: TAG=${TAG} doppler run -- $SCRIPT_DIR/release.sh"
else
  TAG="${TAG}" "$SCRIPT_DIR/release.sh"
fi


# ------------------------------------------------------------------
# Switch running services to the new TAG
#
# docker compose up -d updates services in-place using the images
# tagged with $TAG.
# ------------------------------------------------------------------
echo "🚀 [3/3] Switching containers to new images (TAG=$TAG)"
"${COMPOSE[@]}" up -d --remove-orphans

# ------------------------------------------------------------------
# Reload Nginx configuration
#
# If the Nginx config file changed on the host, the container won't
# automatically pick it up since it's mounted read-only. We force a
# reload here to ensure any config updates take effect.
# Also crucial to refresh upstream DNS resolution if container IPs changed.
# ------------------------------------------------------------------
echo "🔄 Reloading Nginx configuration..."
if "${COMPOSE[@]}" exec -T portfolio-nginx nginx -s reload 2>/dev/null; then
  echo "✅ Nginx config reloaded successfully"
else
  echo "⚠️  Nginx reload skipped (container may not be running or nginx not installed)"
fi

echo "🩺 Health check..."

# Frontend (expect 200/304)
if ! curl -fsS -o /dev/null "https://${SITE_DOMAIN}/"; then
  echo "❌ Health check failed: frontend not reachable"
  exit 1
fi

# Backend (retrying for up to 30s to allow Gunicorn to bind)
echo "🩺 Health check (Backend)..."
MAX_RETRIES=30
for ((i=1; i<=MAX_RETRIES; i++)); do
  if curl -fsS -o /dev/null "https://${API_DOMAIN}/health" 2>/dev/null; then
    echo "✅ Backend is healthy"
    break
  fi
  echo "⏳ Waiting for backend to become ready… (${i}/${MAX_RETRIES})"
  sleep 1
  if [[ "$i" -eq "$MAX_RETRIES" ]]; then
    echo "❌ Health check failed: backend not reachable after ${MAX_RETRIES}s"
    exit 1
  fi
done

echo "✅ Health check OK"




# ------------------------------------------------------------------
# Update deployment state for rollback tracking
#
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

# Move current -> prev, new tag -> current (only after successful up)
if [[ -n "$CURRENT_TAG" && "$CURRENT_TAG" != "$TAG" ]]; then
  echo "$CURRENT_TAG" > "$PREV_FILE"
  echo "↩️  prev_tag set to: $CURRENT_TAG"
fi

echo "$TAG" > "$CURRENT_FILE"
echo "📌 current_tag set to: $TAG"


echo "✅ Done. Deployed TAG=$TAG"
