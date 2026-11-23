# Release And Deploy Architecture

## Purpose

Describes the release flow (Supabase + Cloudflare). Production only; staging was
removed.

Related docs:

- [supabase_api.md](supabase_api.md) - Edge Function, grants, release order, backups
- [infra/scripts/README.md](../../scripts/README.md)

## Current Release Flow

Production runs on Cloudflare (Worker `portfolio-fe`) and Supabase (Edge Function
`supabase/functions/api` over Postgres 17). Django is the admin only and runs
locally. The source of truth for a release is the Git tag `vX.Y.Z`.

The version lives only in `backend/pyproject.toml` `[project].version` (no `VERSION`
file), bumped once per release.

1. Merge feature PRs into `dev`.
2. Bump the version once per release (version-only commit with `[skip ci]`).
3. Open a PR `dev` -> `main` titled `Release vX.Y.Z 🚀`.
4. On merge, `.github/workflows/release.yml` (shared `pyproject-release-tag`
   workflow) creates tag `vX.Y.Z` if it is new and publishes the images to GHCR
   (`production-be`).
5. Then manually, in this order, when the release needs it:
   1. `infra/scripts/run_admin.sh [tag]`: pulls the released `production-be` image
      and runs Django migrations on Supabase (migrate runs on start).
   2. Apply new `supabase/migrations/*.sql` grants (after Django `migrate`).
   3. `doppler run --project portfolio --config prd -- supabase/deploy-api.sh`:
      deploys the Edge Function.
6. The frontend deploys from the `portfolio-fe` repo CI.

Deploys are explicit and operator-driven; there is no listener or auto-deploy.
Database keep-alive and monthly backups are the `supabase-maintenance` workflow
(see [supabase_api.md](supabase_api.md)).
