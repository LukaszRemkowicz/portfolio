#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# release.sh
#
# Purpose:
#   Run a safe, repeatable "release job" for production.
#
# What this script DOES:
#   - Ensures it is run from a clean, tagged git state
#   - Prevents concurrent releases (lock file)
#   - Ensures required dependencies (db, redis) are running
#   - Waits for the database to become healthy
#   - Runs the Docker Compose "release" service exactly once
#
# What this script DOES NOT DO:
#   - Build images (handled by build.sh)
#   - Start application services (handled by deploy.sh)
#   - Update current_tag / prev_tag (deploy responsibility)
#
# When to use:
#   After images for a given TAG already exist.
#
# Typical usage:
#   TAG=v1.2.3 doppler run -- ./release.sh
#
###############################################################################

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-portfolio}"
export COMPOSE_PROJECT_NAME

echo "📦 Compose project: ${COMPOSE_PROJECT_NAME}"


# ------------------------------------------------------------------
# Resolve project root directory
#
# We require running this script from inside a git repository.
# git rev-parse --show-toplevel returns the absolute path to the repo root.
#
# This ensures:
# - paths are stable
# - docker-compose file is found correctly
# - scripts behave the same no matter where invoked from
# ------------------------------------------------------------------
PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${PROJECT_DIR}" ]]; then
  echo "❌ ERROR: release.sh must be run inside a Git repository."
  exit 1
fi
cd "${PROJECT_DIR}"

echo "📁 Project root: ${PROJECT_DIR}"


# ------------------------------------------------------------------
# Ensure 'flock' is available
#
# flock provides a filesystem-based lock to prevent
# two release scripts from running at the same time.
#
# Without this, concurrent releases could:
# - run migrations twice
# - corrupt shared volumes
# - race on database state
# ------------------------------------------------------------------
command -v flock >/dev/null 2>&1 || {
  echo "❌ ERROR: 'flock' is required but not installed (usually in util-linux)." >&2
  exit 1
}


# ------------------------------------------------------------------
# Acquire exclusive release lock
#
# We open a file descriptor (9) on a lock file and try to lock it.
# If another release is running, this will fail immediately.
#
# This is critical safety for production.
# ------------------------------------------------------------------
LOCK_FILE="/var/lock/portfolio-release.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "❌ ERROR: Another release appears to be running (lock: $LOCK_FILE)" >&2
  exit 1
fi


# ------------------------------------------------------------------
# Resolve docker-compose production file
#
# Allows overriding via COMPOSE_PROD env,
# but defaults to docker-compose.prod.yml in repo root.
#
# We explicitly fail if the file does not exist
# to avoid running against the wrong stack.
# ------------------------------------------------------------------
COMPOSE_PROD="${COMPOSE_PROD:-${PROJECT_DIR}/docker-compose.prod.yml}"
[[ -f "$COMPOSE_PROD" ]] || { echo "❌ ERROR: Missing compose file: $COMPOSE_PROD" >&2; exit 1; }


# Build reusable docker compose command array
COMPOSE=(docker compose -f "${COMPOSE_PROD}")
echo "🧾 Using compose file: ${COMPOSE_PROD}"


# ------------------------------------------------------------------
# Check whether required dependencies are already running
#
# We inspect currently running compose services.
# If either db or redis is missing, we mark that dependencies
# need to be started.
#
# This makes release repeatable after server reboot.
# ------------------------------------------------------------------
need_deps=false
"${COMPOSE[@]}" ps --services --status running 2>/dev/null | grep -q '^db$' || need_deps=true
"${COMPOSE[@]}" ps --services --status running 2>/dev/null | grep -q '^redis$' || need_deps=true

if [[ "$need_deps" == true ]]; then
  echo "🧩 Starting dependencies (db, redis)..."
  "${COMPOSE[@]}" up -d db redis
else
  echo "✅ Dependencies already running"
fi


# ------------------------------------------------------------------
# Parse command-line arguments
#
# Supported flags:
#   --dry-run  : show what would be executed without doing it
#
# Any unknown argument is treated as an error to avoid ambiguity.
# ------------------------------------------------------------------
DRY_RUN=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=true; echo "🧪 Dry-run mode enabled";;
    *)
      echo "❌ ERROR: Unknown argument: ${arg}"
      echo "✅ Usage: TAG=vX.Y.Z doppler run -- ./release.sh [--dry-run]"
      exit 1
      ;;
  esac
done


# ------------------------------------------------------------------
# Resolve release TAG
#
# Priority:
#   1. Explicit TAG environment variable
#   2. Exact git tag on HEAD
#
# We require an exact tag to guarantee reproducible releases.
# ------------------------------------------------------------------
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
if [[ -z "${TAG}" ]]; then
  echo "🛑❌ ERROR: TAG is required (or HEAD must be exactly tagged)."
  echo "👉 Example: TAG=vX.Y.Z doppler run -- ./release.sh"
  exit 1
fi
export TAG

if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([\-+].+)?$ ]]; then
  echo "❌ ERROR: Tag '$TAG' is not SemVer-like (expected vX.Y.Z or vX.Y.Z-suffix)" >&2
  exit 1
fi


echo "🏷️  Release tag: ${TAG}"
echo "🔎 Preflight checks..."

# Determinism: ensure compose sees TAG (helpful debug)
if [[ -z "${TAG}" ]]; then
  echo "❌ ERROR: TAG resolved to empty (unexpected)."
  exit 1
fi

# Ensure the exact backend image exists locally (release never builds).
if ! docker image inspect "portfolio-backend:${TAG}" >/dev/null 2>&1; then
  echo "❌ ERROR: Missing image portfolio-backend:${TAG}"
  echo "👉 Build it first: TAG=${TAG} doppler run -- ./build.sh"
  exit 1
fi

echo "📦 Backend image found: portfolio-backend:${TAG}"

# Optional: ensure DB is up (so release doesn't fail mid-way with confusing errors)
# This doesn't start anything; it just checks the current state.
# Ensure dependencies are up (release should be repeatable after reboot)
if ! "${COMPOSE[@]}" ps --services --status running 2>/dev/null | grep -q '^db$'; then
  echo "🧩 Starting dependencies (db, redis)..."
  "${COMPOSE[@]}" up -d db redis
fi

# ------------------------------------------------------------------
# Wait for database to become healthy
#
# We rely on Docker healthchecks defined in docker-compose.
# This prevents running migrations against a database
# that is still starting.
# ------------------------------------------------------------------
echo "⏳ Waiting for db to become healthy..."
DB_CID="$("${COMPOSE[@]}" ps -q db)"
if [[ -z "$DB_CID" ]]; then
  echo "❌ ERROR: Could not get db container id" >&2
  exit 1
fi

has_health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$DB_CID" 2>/dev/null || true)"
if [[ -z "$has_health" ]]; then
  echo "❌ ERROR: db container has no healthcheck configured; cannot wait for health." >&2
  exit 1
fi


for i in {1..60}; do
  status="$(docker inspect -f '{{.State.Health.Status}}' "$DB_CID" 2>/dev/null || true)"
  if [[ "$status" == "healthy" ]]; then
    echo "✅ db is healthy"
    break
  fi
  echo "⏳ Waiting for db… (${i}/60)"
  sleep 1
  if [[ "$i" -eq 60 ]]; then
    echo "❌ ERROR: db did not become healthy in time (last status: ${status:-unknown})" >&2
    exit 1
  fi
done



echo "✅ Preflight OK"
echo "🧪 Running release job (migrations/static/messages/seeds)..."


# ------------------------------------------------------------------
# Execute release job
#
# This runs the one-shot "release" service defined in docker-compose:
# - database migrations
# - seed data
# - compile messages
# - collect static files
#
# IMPORTANT:
# - No images are built here
# - Image must already exist locally
# ------------------------------------------------------------------
if [[ "${DRY_RUN}" == true ]]; then
  echo "🧾 DRY RUN: would execute:"
  echo "   TAG=${TAG} ${COMPOSE[*]} run --rm release"
  exit 0
fi

echo "🚀 Executing release container"
"${COMPOSE[@]}" run --rm release

echo "🎉 Release completed successfully for tag: ${TAG}"
