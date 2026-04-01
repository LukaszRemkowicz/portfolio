#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FILTER_DIR_SRC="${SCRIPT_DIR}/fail2ban/filter.d"
JAIL_SRC="${SCRIPT_DIR}/fail2ban/jail.d/portfolio-probe-blocker.local"

FILTER_DIR_DEST="/etc/fail2ban/filter.d"
JAIL_DIR_DEST="/etc/fail2ban/jail.d"
JAIL_DEST="${JAIL_DIR_DEST}/portfolio-probe-blocker.local"
TRAEFIK_LOG_DIR="/var/log/portfolio/traefik"
TRAEFIK_LOG_FILE="${TRAEFIK_LOG_DIR}/access.log"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root or with sudo."
  exit 1
fi

NGINX_LOG_FILE=""
for candidate in \
  /var/log/portfolio/nginx/prod/access.log \
  /etc/nginx/logs/access.log
do
  if [ -f "${candidate}" ]; then
    NGINX_LOG_FILE="${candidate}"
    break
  fi
done

if [ -z "${NGINX_LOG_FILE}" ]; then
  NGINX_LOG_FILE="/var/log/portfolio/nginx/prod/access.log"
  mkdir -p "$(dirname "${NGINX_LOG_FILE}")"
  touch "${NGINX_LOG_FILE}"
fi

mkdir -p "${TRAEFIK_LOG_DIR}"
touch "${TRAEFIK_LOG_FILE}"

mkdir -p "${FILTER_DIR_DEST}" "${JAIL_DIR_DEST}"
cp "${FILTER_DIR_SRC}/"*.conf "${FILTER_DIR_DEST}/"
sed "s#__NGINX_ACCESS_LOG__#${NGINX_LOG_FILE}#g" "${JAIL_SRC}" > "${JAIL_DEST}"

if command -v fail2ban-client >/dev/null 2>&1; then
  fail2ban-client reload || systemctl restart fail2ban
else
  systemctl restart fail2ban
fi

echo "Installed fail2ban probe blocker configuration."
echo "Using nginx log path: ${NGINX_LOG_FILE}"
echo "Using traefik log path: ${TRAEFIK_LOG_FILE}"
echo "Verify with: fail2ban-client status portfolio-nginx-probes"
echo "Verify with: fail2ban-client status portfolio-traefik-probes"
