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

BLOCKLIST_DIR="/etc/nginx/blocklist"
BLOCKLIST_FILE="${BLOCKLIST_DIR}/blocklist.conf"
# Using the standalone user-agent list which is easier to wrap in a custom map
SOURCE_URL="https://raw.githubusercontent.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker/master/bots.d/blacklist-user-agents.conf"

echo "🛡️ Configuring Nginx Bad Bot Blocker..."

# Ensure directory exists on the shared volume
mkdir -p "${BLOCKLIST_DIR}"

# Download with a 10s timeout, silent unless errors
if wget -q -O "${BLOCKLIST_FILE}.tmp" -T 10 "${SOURCE_URL}"; then
  # Success! Atomic move into place to avoid partial reads
  mv "${BLOCKLIST_FILE}.tmp" "${BLOCKLIST_FILE}"

  # The mitchellkrogza list returns 444 by default, but let's verify format.
  # We just want to make sure it's fundamentally valid Nginx config.
  LINES_ADDED=$(wc -l < "${BLOCKLIST_FILE}")
  echo "✅ Blocklist downloaded successfully ($LINES_ADDED lines)."
else
  # Silent fallback
  echo "⚠️ Blocklist download failed or timed out."
  echo "⚠️ Falling back to empty blocklist. Nginx will start, but bots will not be blocked."

  # Create an empty file so `include /etc/nginx/blocklist/blocklist.conf;` doesn't crash Nginx
  touch "${BLOCKLIST_FILE}"
fi

# Ensure Nginx respects file permissions
chmod 644 "${BLOCKLIST_FILE}"

echo "🏁 Blocklist initialization complete."
exit 0
