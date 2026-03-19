#!/bin/sh
set -e

HTPASSWD_FILE="/tmp/dashboard.htpasswd"
TRAEFIK_TEMPLATE="/etc/traefik/traefik.yml.template"
TRAEFIK_RENDERED="/tmp/traefik.yml"
TRAEFIK_DYNAMIC_TEMPLATE="/etc/traefik/dynamic_conf.yml.template"
TRAEFIK_DYNAMIC_RENDERED="/tmp/dynamic_conf.yml"
ACME_DIR="/letsencrypt"
ACME_FILE="$ACME_DIR/acme.json"

# Always generate a users file so the dashboard auth middleware stays valid.
if [ -n "$TRAEFIK_USER" ] && [ -n "$TRAEFIK_PASSWORD" ]; then
    echo "Generating Traefik dashboard auth file for user: $TRAEFIK_USER"
    htpasswd -nbB "$TRAEFIK_USER" "$TRAEFIK_PASSWORD" > "$HTPASSWD_FILE"
else
    PLACEHOLDER_PASSWORD="$(dd if=/dev/urandom bs=18 count=1 2>/dev/null | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
    echo "TRAEFIK_USER or TRAEFIK_PASSWORD not set. Generating placeholder credentials to keep the dashboard locked."
    htpasswd -nbB "disabled" "$PLACEHOLDER_PASSWORD" > "$HTPASSWD_FILE"
fi

chmod 600 "$HTPASSWD_FILE"

mkdir -p "$ACME_DIR"
touch "$ACME_FILE"
chmod 600 "$ACME_FILE"

if [ ! -f "$TRAEFIK_TEMPLATE" ]; then
    echo "Traefik config template not found: $TRAEFIK_TEMPLATE" >&2
    exit 1
fi

if [ ! -f "$TRAEFIK_DYNAMIC_TEMPLATE" ]; then
    echo "Traefik dynamic config template not found: $TRAEFIK_DYNAMIC_TEMPLATE" >&2
    exit 1
fi

envsubst '${CONTACT_EMAIL}' < "$TRAEFIK_TEMPLATE" > "$TRAEFIK_RENDERED"
envsubst '${SITE_DOMAIN}' < "$TRAEFIK_DYNAMIC_TEMPLATE" > "$TRAEFIK_DYNAMIC_RENDERED"

if [ "${1:-}" = "traefik" ]; then
    shift
fi

exec traefik --configFile="$TRAEFIK_RENDERED" "$@"
