#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$PROJECT_DIR" ]]; then
  echo "❌ ERROR: build.sh must be run inside a Git repository."
  exit 1
fi
cd "$PROJECT_DIR"

# Require an explicit release tag
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
if [[ -z "$TAG" ]]; then
  echo "🛑 ERROR: No Git tag on HEAD."
  echo "👉 Fix: git tag vX.Y.Z && git push origin vX.Y.Z"
  exit 1
fi
export TAG

# Enforce deterministic build
if [[ -n "$(git status --porcelain)" ]]; then
  echo "🛑 ERROR: Working tree is dirty. Commit or stash changes first."
  git status --porcelain
  exit 1
fi

export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"

echo "🏷️  Release tag: $TAG"
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
  --build-arg "SITE_DOMAIN=${SITE_DOMAIN:-portfolio.local}" \
  --build-arg "API_URL=https://${API_DOMAIN:-api.portfolio.local}" \
  --build-arg "SSL_KEY_PATH=${SSL_KEY_PATH:-/etc/nginx/ssl/portfolio.local.key}" \
  --build-arg "SSL_CRT_PATH=${SSL_CRT_PATH:-/etc/nginx/ssl/portfolio.local.crt}" \
  -t "portfolio-frontend:$TAG" \
  .
echo "✅ Frontend image built"

# ---------------- Summary ----------------
echo "📦 Built images:"
docker images | awk 'NR==1 || $1 ~ /^portfolio-(frontend|backend)$/ {print}'

# ---------------- Cleanup ----------------
STATE_DIR="${STATE_DIR:-/var/lib/portfolio}"
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

docker image prune -f >/dev/null 2>&1 || true

echo "🎉 Build completed successfully for tag: $TAG"
