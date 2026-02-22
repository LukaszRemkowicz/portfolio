#!/bin/sh
set -e

# Fix permissions for media (runtime-safe)
# Check if SKIP_PERMISSION_FIX is set (useful for local dev with large media folders)
if [ "$SKIP_PERMISSION_FIX" != "true" ] && [ -d /app/media ]; then
    echo "[entrypoint] fixing media permissions..."
    chown -R appuser:appuser /app/media || true
    chmod -R u+rwX /app/media || true
else
    echo "[entrypoint] skipping media permissions fix (SKIP_PERMISSION_FIX=$SKIP_PERMISSION_FIX)"
fi

exec "$@"
