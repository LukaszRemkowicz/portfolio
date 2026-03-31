#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FILTER_DIR_SRC="${SCRIPT_DIR}/fail2ban/filter.d"
JAIL_SRC="${SCRIPT_DIR}/fail2ban/jail.d/portfolio-probe-blocker.local"

FILTER_DIR_DEST="/etc/fail2ban/filter.d"
JAIL_DIR_DEST="/etc/fail2ban/jail.d"
JAIL_DEST="${JAIL_DIR_DEST}/portfolio-probe-blocker.local"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root or with sudo."
  exit 1
fi

mkdir -p "${FILTER_DIR_DEST}" "${JAIL_DIR_DEST}"
cp "${FILTER_DIR_SRC}/"*.conf "${FILTER_DIR_DEST}/"
cp "${JAIL_SRC}" "${JAIL_DEST}"

if command -v fail2ban-client >/dev/null 2>&1; then
  fail2ban-client reload || systemctl restart fail2ban
else
  systemctl restart fail2ban
fi

echo "Installed fail2ban probe blocker configuration."
echo "Verify with: fail2ban-client status portfolio-nginx-sensitive-probes"
echo "Verify with: fail2ban-client status portfolio-traefik-sensitive-probes"
