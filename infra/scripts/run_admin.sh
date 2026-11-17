#!/usr/bin/env bash
# Production Django admin on this machine, against the Supabase database.
# Pulls the newest released backend image from GHCR, runs migrations, then serves
# the admin at http://localhost:8000/admin/ (Ctrl+C to stop, after background work
# such as variants and translations has finished). Nothing here touches the VPS.
#
#   infra/scripts/run_admin.sh            # newest vX.Y.Z tag on GitHub
#   infra/scripts/run_admin.sh v2.21.0    # a specific release
set -euo pipefail
cd "$(dirname "$0")/../.."

TAG=${1:-$(git ls-remote --tags --refs origin 'v*' | sed 's#.*/##' | sort -V | tail -1)}
[[ $TAG =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "run_admin: bad tag '$TAG'" >&2; exit 1; }
echo "run_admin: backend image $TAG"

TAG=$TAG exec doppler run --project portfolio --config prd -- sh -c '
  printf "%s" "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin >/dev/null
  exec docker compose -f docker-compose.supabase.yml up
'
