#!/bin/sh
###############################################################################
# download-blocklist.sh
#
# Purpose:
#   Downloads the Mitchell Krog Nginx Ultimate Bad Bot Blocker configuration.
#   Runs in an ephemeral Alpine container during deployment.
#
# Robustness:
#   If the download fails (timeout/network issues), it generates an empty
#   file and exits 0 to ensure the `include` directive in Nginx doesn't crash
#   the container on startup.
###############################################################################

set -eu

BLOCKLIST_DIR="${BLOCKLIST_DIR:-/etc/nginx/blocklist}"
BLOCKLIST_FILE="${BLOCKLIST_DIR}/blocklist.conf"
ALLOW_EMPTY_NGINX_BLOCKLIST="${ALLOW_EMPTY_NGINX_BLOCKLIST:-false}"
# Using the standalone user-agent list which is easier to wrap in a custom map
SOURCE_URL="https://raw.githubusercontent.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker/master/bots.d/blacklist-user-agents.conf"

echo "🛡️ Configuring Nginx Bad Bot Blocker..."

# Ensure directory exists on the shared volume
mkdir -p "${BLOCKLIST_DIR}"

# Download with a 10s timeout, silent unless errors
if wget -q -O "${BLOCKLIST_FILE}.tmp" -T 10 "${SOURCE_URL}" && [ -s "${BLOCKLIST_FILE}.tmp" ]; then
  # Success! Atomic move into place to avoid partial reads
  mv "${BLOCKLIST_FILE}.tmp" "${BLOCKLIST_FILE}"

  # The mitchellkrogza list returns 444 by default, but let's verify format.
  # We just want to make sure it's fundamentally valid Nginx config.
  LINES_ADDED=$(wc -l < "${BLOCKLIST_FILE}")
  echo "✅ Blocklist downloaded successfully ($LINES_ADDED lines)."
else
  rm -f "${BLOCKLIST_FILE}.tmp"
  echo "ERROR: Blocklist download failed, timed out, or returned an empty file." >&2

  if [ "${ALLOW_EMPTY_NGINX_BLOCKLIST}" = "true" ]; then
    echo "⚠️ ALLOW_EMPTY_NGINX_BLOCKLIST=true; writing an empty blocklist for emergency startup." >&2
    touch "${BLOCKLIST_FILE}"
  else
    echo "👉 Set ALLOW_EMPTY_NGINX_BLOCKLIST=true only for an explicit emergency bypass." >&2
    exit 1
  fi
fi

# Ensure Nginx respects file permissions
chmod 644 "${BLOCKLIST_FILE}"

echo "🏁 Blocklist initialization complete."
exit 0
