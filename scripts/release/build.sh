#!/usr/bin/env bash
# =============================================================================
# build.sh — build-only (prod targets) for frontend + backend
# =============================================================================
# Builds Docker images using:
#   docker-compose.yml + docker-compose.prod.yml
#
# It ONLY builds images (no migrations, no container restarts).
#
# Default behavior is SAFE:
# - It will NOT switch branches.
# - It will only pull if you explicitly pass --pull.
#
# Usage:
#   ./build.sh                 # build both (no git pull)
#   ./build.sh --pull          # pull current branch, then build
#   ./build.sh --no-cache      # build without cache
#   ./build.sh --frontend-only # build FE only
#   ./build.sh --backend-only  # build BE only
#   ./build.sh --main          # switch to main (refuse if dirty), then build
#
# Env:
#   TAG=<tag>                  # override tag (default: git short sha)
#   PROJECT_DIR=<path>         # repo root (auto-detected via git)
#   LOG_FILE=<path>            # log path (auto)
#   COMPOSE_BASE, COMPOSE_PROD # compose file overrides
# =============================================================================

set -euo pipefail

# -------- Paths / defaults --------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Robust project root detection:
# Prefer user override, else ask git for repo root (works no matter where the script lives).
if [[ -z "${PROJECT_DIR:-}" ]]; then
  if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    PROJECT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
  else
    echo "[ERROR] PROJECT_DIR not set and script is not inside a git repo."
    echo "Set PROJECT_DIR explicitly, e.g.:"
    echo "  PROJECT_DIR=/path/to/repo ./build.sh"
    exit 1
  fi
fi

COMPOSE_BASE="${COMPOSE_BASE:-$PROJECT_DIR/docker-compose.yml}"
COMPOSE_PROD="${COMPOSE_PROD:-$PROJECT_DIR/docker-compose.prod.yml}"

# Prefer /var/log if writable, else fallback to project-local, else /tmp
DEFAULT_LOG_FILE="/var/log/portfolio-build.log"
LOG_FILE="${LOG_FILE:-$DEFAULT_LOG_FILE}"

if ! (touch "$LOG_FILE" >/dev/null 2>&1); then
  LOG_FILE="$PROJECT_DIR/portfolio-build.log"
  if ! (touch "$LOG_FILE" >/dev/null 2>&1); then
    LOG_FILE="/tmp/portfolio-build.log"
    touch "$LOG_FILE" >/dev/null 2>&1 || true
  fi
fi

# -------- Flags --------
DO_PULL=false
FRONTEND_ONLY=false
BACKEND_ONLY=false
NO_CACHE=false
FORCE_MAIN=false
MAIN_BRANCH="${MAIN_BRANCH:-main}"

# -------- Colors --------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# -------- Logging --------
log()     { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE" >/dev/null; echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
info()    { echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE" >/dev/null; echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"; }
success() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE" >/dev/null; echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"; }
warning() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE" >/dev/null; echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"; }
error()   { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE" >/dev/null; echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2; }

usage() {
  cat <<EOF
build.sh (build-only)

Usage:
  $0 [options]

Options:
  --pull              git pull --ff-only on current branch, then build
  --frontend-only     build only portfolio-fe
  --backend-only      build only portfolio-be
  --no-cache          pass --no-cache to docker build
  -h, --help          show help

Env:
  TAG=<tag>           override image tag (default: git short sha)
  PROJECT_DIR         repo root (auto via git if possible)
  LOG_FILE            optional log path
  COMPOSE_BASE, COMPOSE_PROD

Notes:
- Does NOT switch branches.
- Uses: docker compose -f docker-compose.yml -f docker-compose.prod.yml build
EOF
}

# -------- Parse args --------
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull) DO_PULL=true; shift ;;
    --frontend-only) FRONTEND_ONLY=true; shift ;;
    --backend-only) BACKEND_ONLY=true; shift ;;
    --no-cache) NO_CACHE=true; shift ;;
    --main) FORCE_MAIN=true; shift ;;
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

[[ -f "$COMPOSE_BASE" ]] || { error "Missing compose file: $COMPOSE_BASE"; exit 1; }
[[ -f "$COMPOSE_PROD" ]] || { error "Missing compose file: $COMPOSE_PROD"; exit 1; }
[[ -d ".git" ]] || { error "Not a git repository: $PROJECT_DIR"; exit 1; }

command -v docker >/dev/null 2>&1 || { error "Docker is not installed/available"; exit 1; }

export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"

log "🏗️  Starting build-only..."
info "Project: $PROJECT_DIR"
info "Compose: $COMPOSE_BASE + $COMPOSE_PROD"
info "Log: $LOG_FILE"

CURRENT_BRANCH="$(git branch --show-current || true)"
log "📋 Current branch: ${CURRENT_BRANCH:-unknown}"

if [[ "$FORCE_MAIN" == true ]]; then
  # refuse if dirty (protect your work)
  if [[ -n "$(git status --porcelain)" ]]; then
    error "Refusing to switch to '$MAIN_BRANCH': working tree is dirty."
    error "Commit or stash changes, then retry."
    git status --porcelain | tee -a "$LOG_FILE" >/dev/null || true
    exit 1
  fi

  if [[ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]]; then
    log "🔄 Switching to branch $MAIN_BRANCH (because --main)..."
    git checkout "$MAIN_BRANCH"
    CURRENT_BRANCH="$MAIN_BRANCH"
    log "📋 Current branch: $CURRENT_BRANCH"
  fi
fi

if [[ "$DO_PULL" == true ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    error "Working tree is not clean. Commit/stash changes before pulling."
    git status --porcelain | tee -a "$LOG_FILE" >/dev/null || true
    exit 1
  fi
  log "📥 Pulling latest code (current branch)..."
  if [[ "$FORCE_MAIN" == true ]]; then
    git pull --ff-only origin "$MAIN_BRANCH"
  else
    git pull --ff-only
  fi
  success "✅ Code updated"
else
  info "⏭️  Skipping git pull (use --pull to enable)"
fi


BRANCH_NAME="$(git branch --show-current || echo detached)"
COMMIT_FULL="$(git rev-parse HEAD)"
COMMIT_SUBJECT="$(git log -1 --pretty=%s)"
COMMIT_DATE="$(git log -1 --pretty=%ci)"

log "🌿 Branch: $BRANCH_NAME"
log "🔗 Commit: $COMMIT_FULL"
log "📝 Commit msg: $COMMIT_SUBJECT"
log "🕒 Commit date: $COMMIT_DATE"

TAG="${TAG:-$(git rev-parse --short HEAD)}"
export TAG
log "📌 TAG (commit): $TAG"

CACHE_FLAG=""
if [[ "$NO_CACHE" == true ]]; then
  CACHE_FLAG="--no-cache"
fi

log "🔨 Building images..."

if [[ "$FRONTEND_ONLY" == true ]]; then
  log "➡️  Building frontend only (portfolio-fe)"
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" build $CACHE_FLAG portfolio-fe
elif [[ "$BACKEND_ONLY" == true ]]; then
  log "➡️  Building backend only (portfolio-be)"
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" build $CACHE_FLAG portfolio-be
else
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" build $CACHE_FLAG
fi

success "✅ Build complete"

log "📋 Built images (filtered):"
docker images | awk 'NR==1 || $1 ~ /^portfolio-(frontend|backend)$/ {print}' | tee -a "$LOG_FILE" >/dev/null || true
docker images | awk 'NR==1 || $1 ~ /^portfolio-(frontend|backend)$/ {print}' || true

log "✅ Done. Images tagged with: $TAG"
