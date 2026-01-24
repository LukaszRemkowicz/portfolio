#!/usr/bin/env bash
set -euo pipefail

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

COMPOSE_BASE="$PROJECT_DIR/docker-compose.yml"
COMPOSE_PROD="$PROJECT_DIR/docker-compose.prod.yml"

COMPOSE="docker compose -f \"$COMPOSE_BASE\" -f \"$COMPOSE_PROD\""

TAG="${TAG:-$(git -C "$PROJECT_DIR" rev-parse --short HEAD)}"
export TAG

echo "[1/3] Checking images for TAG=$TAG"

docker image inspect "portfolio-backend:$TAG" >/dev/null 2>&1 \
  || { echo "Missing image portfolio-backend:$TAG"; exit 1; }

docker image inspect "portfolio-frontend:$TAG" >/dev/null 2>&1 \
  || { echo "Missing image portfolio-frontend:$TAG"; exit 1; }

echo "[2/3] Release tasks (migrate / compilemessages / collectstatic)"
eval $COMPOSE run --rm release

echo "[3/3] Switch containers to new images (TAG=$TAG)"
eval $COMPOSE up -d

echo "✅ Done. Deployed TAG=$TAG"
