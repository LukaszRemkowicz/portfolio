#!/bin/sh
set -e

# Fix permissions for media (runtime-safe)
# Check if SKIP_PERMISSION_FIX is set (useful for local dev with large media folders)
if [ "$SKIP_PERMISSION_FIX" != "true" ] && [ -d /app/media ]; then
    echo "[entrypoint] fixing media permissions (owned files only)..."
    CURRENT_UID="$(id -u)"
    # Only touch files owned by root or the current user — skip host-created files
    find /app/media \( -user 0 -o -user "$CURRENT_UID" \) -exec chown appuser:appuser {} + 2>/dev/null || true
    find /app/media -user appuser -exec chmod u+rwX {} + 2>/dev/null || true
else
    echo "[entrypoint] skipping media permissions fix (SKIP_PERMISSION_FIX=$SKIP_PERMISSION_FIX)"
fi

# Fix celerybeat schedule file permissions (named volume initialised as root)
if [ -d /app/celerybeat ]; then
    echo "[entrypoint] fixing celerybeat permissions..."
    chown -R appuser:appuser /app/celerybeat 2>/dev/null || true
fi

# Fix staticfiles permissions (named volume initialised as root on production)
if [ "$SKIP_PERMISSION_FIX" != "true" ] && [ -d /app/staticfiles ]; then
    echo "[entrypoint] fixing staticfiles permissions..."
    CURRENT_UID="$(id -u)"
    find /app/staticfiles \( -user 0 -o -user "$CURRENT_UID" \) -exec chown appuser:appuser {} + 2>/dev/null || true
fi

exec "$@"
