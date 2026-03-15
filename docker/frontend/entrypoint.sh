#!/bin/sh
set -e

# This script synchronizes the built frontend assets from the container's
# default Nginx path to the shared volume used by the main Nginx service.
# It runs as a non-root user (nginx).

# Ensure the destination is writable by the 'nginx' user (UID 101)
# We do this as root before dropping privileges.
chown -R nginx:nginx /frontend_dist

echo "Dropping privileges and starting synchronization..."

# Drop privileges and run the sync
exec su-exec nginx sh -c '
  echo "Clearing old assets..."
  rm -rf /frontend_dist/*
  echo "Copying new assets..."
  cp -a /usr/share/nginx/html/. /frontend_dist/
  echo "Synchronization complete. Keeping container alive..."
  tail -f /dev/null
'
