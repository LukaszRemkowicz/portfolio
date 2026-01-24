#!/usr/bin/env bash
# =============================================================================
# BUILD.SH — PRODUCTION IMAGE BUILD SCRIPT
# =============================================================================
#
# PURPOSE
# -------
# This script builds Docker images for the project (frontend + backend)
# in a safe and repeatable way.
#
# It ONLY builds images.
# It does NOT:
#   - run migrations
#   - start or stop containers
#   - deploy anything
#
# The goal is to always produce tagged images that can later be deployed
# without downtime.
#
#
# HOW IT WORKS
# ------------
# - Uses docker-compose.yml + docker-compose.prod.yml
# - Builds images from production targets:
#     * frontend  -> target: prod
#     * backend   -> target: production
# - Images are tagged with the current git commit hash (TAG)
#
# Example produced images:
#   - portfolio-frontend:<git_sha>
#   - portfolio-backend:<git_sha>
#
#
# DEFAULT FLOW
# ------------
# 1. Ensure working tree is clean
# 2. (Optional) Pull latest code from the main branch
# 3. Build Docker images using docker compose
# 4. Exit (no containers are started or restarted)
#
#
# USAGE
# -----
# Full build (frontend + backend):
#   ./build.sh
#
# Build without pulling code:
#   ./build.sh --no-pull
#
# Build only frontend:
#   ./build.sh --frontend-only
#
# Build only backend:
#   ./build.sh --backend-only
#
# Build without Docker cache:
#   ./build.sh --no-cache
#
#
# ENVIRONMENT VARIABLES
# ---------------------
# TAG
#   Override image tag manually.
#   Default: short git commit hash.
#
# PROJECT_DIR
#   Root directory of the project.
#   Default: auto-detected.
#
# BRANCH
#   Git branch used for pulling code.
#   Default: "main".
#
#
# RELATION TO DEPLOY
# ------------------
# Typical production flow:
#
#   ./build.sh
#   ./deploy.sh
#
# Where:
#   - build.sh  -> builds images only
#   - deploy.sh -> runs release tasks and switches containers
#
#
# SAFETY NOTES
# ------------
# - The script refuses to pull if the git working tree is dirty.
# - This prevents accidental builds from uncommitted changes.
# - Images from previous builds are NOT deleted (rollback-friendly).
#
# =============================================================================

set -euo pipefail

# -------- Paths / defaults --------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

COMPOSE_BASE="${COMPOSE_BASE:-$PROJECT_DIR/docker-compose.yml}"
COMPOSE_PROD="${COMPOSE_PROD:-$PROJECT_DIR/docker-compose.prod.yml}"

BRANCH="${BRANCH:-main}"

# Prefer /var/log if writable, else fallback to project-local
DEFAULT_LOG_FILE="/var/log/portfolio-build.log"
LOG_FILE="${LOG_FILE:-$DEFAULT_LOG_FILE}"
if ! (touch "$LOG_FILE" >/dev/null 2>&1); then
  LOG_FILE="$PROJECT_DIR/portfolio-build.log"
  touch "$LOG_FILE" >/dev/null 2>&1 || true
fi

# -------- Flags --------
NO_PULL=false
FRONTEND_ONLY=false
BACKEND_ONLY=false
NO_CACHE=false

# -------- Colors --------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# -------- Logging --------
log()     { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
info()    { echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"; }
error()   { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE" >&2; }

usage() {
  cat <<EOF
Portfolio build.sh (build-only)

Usage:
  $0 [options]

Options:
  --no-pull           Skip git pull
  --frontend-only     Build only frontend image
  --backend-only      Build only backend image
  --no-cache          Disable Docker build cache
  -h, --help          Show help

Environment overrides:
  PROJECT_DIR, BRANCH, LOG_FILE
  COMPOSE_BASE, COMPOSE_PROD

Notes:
- Uses: docker compose -f docker-compose.yml -f docker-compose.prod.yml build
- Tags images using TAG=<git short sha> (exported for compose)
EOF
}

# -------- Parse args --------
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-pull) NO_PULL=true; shift ;;
    --frontend-only) FRONTEND_ONLY=true; shift ;;
    --backend-only) BACKEND_ONLY=true; shift ;;
    --no-cache) NO_CACHE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) error "Unknown argument: $1"; echo "Use --help"; exit 1 ;;
  esac
done

if [[ "$FRONTEND_ONLY" == true && "$BACKEND_ONLY" == true ]]; then
  error "Cannot use --frontend-only and --backend-only together"
  exit 1
fi

# -------- Preconditions --------
cd "$PROJECT_DIR" || { error "Cannot cd to PROJECT_DIR=$PROJECT_DIR"; exit 1; }

if [[ ! -f "$COMPOSE_BASE" ]]; then
  error "Missing compose file: $COMPOSE_BASE"
  exit 1
fi
if [[ ! -f "$COMPOSE_PROD" ]]; then
  error "Missing compose file: $COMPOSE_PROD"
  exit 1
fi

if [[ ! -d ".git" ]]; then
  error "Not a git repository: $PROJECT_DIR"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  error "Docker is not installed/available"
  exit 1
fi

# Use BuildKit if available
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"

log "🏗️  Starting build-only..."
info "Project: $PROJECT_DIR"
info "Compose: $COMPOSE_BASE + $COMPOSE_PROD"
info "Log: $LOG_FILE"

CURRENT_BRANCH="$(git branch --show-current || true)"
log "📋 Current branch: ${CURRENT_BRANCH:-unknown}"

# Refuse to pull if working tree dirty (prevents mystery builds)
if [[ "$NO_PULL" == false ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    error "Working tree is not clean. Commit/stash changes or run with --no-pull intentionally."
    git status --porcelain | tee -a "$LOG_FILE"
    exit 1
  fi

  log "📥 Pulling latest code from branch $BRANCH..."
  if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    log "🔄 Switching to branch $BRANCH..."
    git checkout "$BRANCH"
  fi

  git pull --ff-only origin "$BRANCH"
  success "✅ Code updated"
else
  info "⏭️  Skipping git pull (--no-pull)"
fi

TAG="${TAG:-$(git rev-parse --short HEAD)}"
export TAG
log "📌 TAG (commit): $TAG"

# Compose command as an array (safe with spaces, no eval)
COMPOSE=(docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD")

# Build args as an array (safe with set -u)
BUILD_ARGS=()
if [[ "$NO_CACHE" == true ]]; then
  BUILD_ARGS+=(--no-cache)
fi

# -------- Build --------
log "🔨 Building images..."

if [[ "$FRONTEND_ONLY" == true ]]; then
  log "➡️  Building frontend only (portfolio-fe)"
  "${COMPOSE[@]}" build "${BUILD_ARGS[@]}" portfolio-fe
elif [[ "$BACKEND_ONLY" == true ]]; then
  log "➡️  Building backend only (portfolio-be)"
  "${COMPOSE[@]}" build "${BUILD_ARGS[@]}" portfolio-be
else
  "${COMPOSE[@]}" build "${BUILD_ARGS[@]}"
fi

success "✅ Build complete"

# Optional: show built images
log "📋 Built images (filtered):"
docker images | awk 'NR==1 || $1 ~ /^portfolio-(frontend|backend)$/ {print}' | tee -a "$LOG_FILE" || true

log "✅ Done. Images tagged with: $TAG"
