#!/bin/sh
set -e

# Fix permissions for media (runtime-safe)
if [ -d /app/media ]; then
    echo "[entrypoint] fixing media permissions..."
    chown -R appuser:appuser /app/media || true
    chmod -R u+rwX /app/media || true
fi

exec "$@"
