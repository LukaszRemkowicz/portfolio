#!/bin/sh
set -e

# Fix permissions for media (runtime-safe)
# Only run if we are root (UID 0) to avoid PermissionError in production
if [ "$(id -u)" = "0" ]; then
    if [ "$SKIP_PERMISSION_FIX" != "true" ] && [ -d /app/media ]; then
        echo "[entrypoint] fixing media permissions (owned files only)..."
        # Only touch files owned by root or the current user — skip host-created files
        find /app/media \( -user 0 -o -user "$(id -u)" \) -exec chown appuser:appuser {} + 2>/dev/null || true
        find /app/media -user appuser -exec chmod u+rwX {} + 2>/dev/null || true
    fi

    # Fix celerybeat schedule file permissions
    if [ -d /app/celerybeat ]; then
        echo "[entrypoint] fixing celerybeat permissions..."
        chown -R appuser:appuser /app/celerybeat 2>/dev/null || true
    fi

    # Fix staticfiles permissions
    if [ "$SKIP_PERMISSION_FIX" != "true" ] && [ -d /app/staticfiles ]; then
        echo "[entrypoint] fixing staticfiles permissions..."
        find /app/staticfiles \( -user 0 -o -user "$(id -u)" \) -exec chown appuser:appuser {} + 2>/dev/null || true
    fi
else
    echo "[entrypoint] running as non-root ($(id -u)), skipping permission fixes"
fi

echo "[entrypoint] dropping privileges to appuser and executing command..."
exec gosu appuser "$@"
