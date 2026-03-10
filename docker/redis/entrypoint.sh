#!/bin/sh
set -e

# If no password is provided in the environment, start normally (dev fallback if not strict)
# If a password is provided (e.g. via Doppler or .env), start with --requirepass
if [ -n "$REDIS_PASSWORD" ]; then
    echo "Starting Redis with password protection..."
    exec redis-server --requirepass "$REDIS_PASSWORD"
else
    echo "WARNING: Starting Redis WITHOUT password protection..."
    exec redis-server
fi
