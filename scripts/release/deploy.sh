#!/usr/bin/env bash
set -euo pipefail

COMPOSE_BASE="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
COMPOSE="docker compose -f $COMPOSE_BASE -f $COMPOSE_PROD"

TAG="${TAG:-$(git rev-parse --short HEAD)}"
export TAG

echo "[1/2] Release tasks (backend only)"
$COMPOSE run --rm release

echo "[2/2] Switch containers to new images (TAG=$TAG)"
$COMPOSE up -d

echo "✅ Done. Deployed TAG=$TAG"
