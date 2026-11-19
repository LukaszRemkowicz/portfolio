#!/usr/bin/env bash
# Public API Edge Function on this machine, against the docker-compose dev Postgres
# (127.0.0.1:5436, db portfolio_dev) with media served by the dev Django (:8000/media).
# Needs `docker compose up -d db` and Doppler (config dev) for DB_USER/DB_PASSWORD.
# Serves http://localhost:8001; the origin secret is the fixed local value below.
#
#   infra/scripts/run_local_api.sh
set -euo pipefail
cd "$(dirname "$0")/../../supabase/functions/api"

DB_USER=$(doppler secrets get DB_USER --plain --config dev)
DB_PASSWORD=$(doppler secrets get DB_PASSWORD --plain --config dev)

export API_DB_HOST=127.0.0.1 API_DB_PORT=5436 API_DB_NAME=portfolio_dev
export API_DB_USER="$DB_USER" API_DB_PASSWORD="$DB_PASSWORD"
export API_DB_SSL=disable
export API_MEDIA_BASE_URL=http://localhost:8000/media
export API_PUBLIC_BASE_URL=http://localhost:8001 PORT=8001
export API_ORIGIN_SECRET=local-dev-secret
# Required by the function but unused for public variant URLs.
export MEDIA_SIGNING_KEY=${MEDIA_SIGNING_KEY:-local-placeholder}
export R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID:-local-placeholder}
export R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY:-local-placeholder}

exec deno run --allow-net --allow-env index.ts
