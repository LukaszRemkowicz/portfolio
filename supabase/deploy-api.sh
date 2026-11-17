#!/usr/bin/env bash
# Deploys the `api` Edge Function and its secrets; every value comes from Doppler.
#
#   doppler run --project portfolio --config prd -- supabase/deploy-api.sh
#
# One-time: `npx -y supabase@2.121.0 login`.
set -euo pipefail
cd "$(dirname "$0")/.."
SUPABASE="npx -y supabase@2.121.0"

# The deployed function talks to Postgres directly (~40% faster than the pooler, measured
# 2026-11-11); local runs keep the IPv4 pooler values from Doppler (SUPABASE_API_DB_*).
# Links point at the site (like DRF behind the Worker's X-Forwarded-Host), so the browser
# opens them through the Worker; the function itself answers only the Worker (API_ORIGIN_SECRET).
# Owner-only temp file, removed on exit (npx does not pass /dev/fd through).
umask 077
ENV_FILE=$(mktemp)
trap 'rm -f "$ENV_FILE"' EXIT
# Single-quoted dotenv values are taken literally ($, #, spaces); a quote or newline is refused.
put() {
  case $2 in *"'"* | *$'\n'*) echo "deploy-api: $1 contains a quote or newline" >&2; exit 1 ;; esac
  printf "%s='%s'\n" "$1" "$2" >>"$ENV_FILE"
}
put API_DB_HOST "db.$SUPABASE_PROJECT_REF.supabase.co"
put API_DB_PORT 5432
put API_DB_NAME "$SUPABASE_DB_NAME"
put API_DB_USER "${SUPABASE_API_DB_USER%%.*}"
put API_DB_PASSWORD "$SUPABASE_API_DB_PASSWORD"
put MEDIA_SIGNING_KEY "$MEDIA_SIGNING_KEY"
put API_PUBLIC_BASE_URL "https://$SITE_DOMAIN"
put API_ORIGIN_SECRET "$API_ORIGIN_SECRET"
put R2_ACCESS_KEY_ID "$R2_ACCESS_KEY_ID"
put R2_SECRET_ACCESS_KEY "$R2_SECRET_ACCESS_KEY"
put RESEND_API_KEY "$RESEND_API_KEY"
put CONTACT_EMAIL "$CONTACT_EMAIL"
put CONTACT_FROM_EMAIL "kontakt@$SITE_DOMAIN"
put PROJECT_OWNER "$PROJECT_OWNER"
put SITE_DOMAIN "$SITE_DOMAIN"
$SUPABASE secrets set --project-ref "$SUPABASE_PROJECT_REF" --env-file "$ENV_FILE"

$SUPABASE functions deploy api --project-ref "$SUPABASE_PROJECT_REF" --use-api
