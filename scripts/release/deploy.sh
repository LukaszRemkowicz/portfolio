#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  PROJECT_DIR="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
else
  echo "ERROR: deploy.sh must be inside a git repository"
  exit 1
fi

cd "$PROJECT_DIR"

COMPOSE_PROD="$PROJECT_DIR/docker-compose.prod.yml"

COMPOSE=(docker compose -f "$COMPOSE_PROD")

TAG="${TAG:-$(git -C "$PROJECT_DIR" describe --tags --exact-match 2>/dev/null || git -C "$PROJECT_DIR" rev-parse --short HEAD)}"
export TAG

echo "[1/3] Checking images for TAG=$TAG"

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

echo "[2/3] Release tasks (migrate / compilemessages / collectstatic)"
"${COMPOSE[@]}" run --rm release

echo "[3/3] Switch containers to new images (TAG=$TAG)"
"${COMPOSE[@]}" up -d --remove-orphans

echo "✅ Done. Deployed TAG=$TAG"

echo "[4/4] Cleanup old images"
docker image prune -f --filter "until=168h"
