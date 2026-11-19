# Release And Deploy Architecture

## Purpose

Describes the current release flow (Supabase + Cloudflare) and, in a separate
part, the VPS release/deploy model that is stopped and kept only as a rollback
path. Production only; staging was removed.

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
   (`production-be`, plus `production-nginx` for the VPS rollback path).
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

## VPS Rollback (stopped since 2026-11-17)

The DigitalOcean VPS stack (Traefik, nginx, cloudflared tunnel, gunicorn,
`docker-compose.prod.yml`) has been stopped since 2026-11-17 and is kept only as a
rollback path until the droplet is retired. Everything below describes that
stack; do not use it for a normal release.

### Core Model

The application uses a tag-based release model. The source of truth for a
release is the Git tag `vX.Y.Z`.

- release and deploy logic are tag-based
- mutable tags such as `latest` are not part of the deployment contract

### Release Identity

The version lives only in `backend/pyproject.toml` `[project].version` (there is
no `VERSION` file).

`.github/workflows/release.yml`:

- runs on push to `main`
- calls the shared `pyproject-release-tag` workflow, which reads the version and
  creates tag `vX.Y.Z` if it is new
- when a new tag is created, builds and pushes the production images to GHCR

### Artifact Sources

Production artifacts are published to GHCR as:

```text
<registry>/<namespace>/production-be:vX.Y.Z
<registry>/<namespace>/production-nginx:vX.Y.Z
```

On the VPS, `infra/scripts/release/prepare_images.sh`:

- resolves `TAG` from git if omitted and validates it as SemVer-like
- logs in to GHCR and pulls the production images
- tags them locally as `production-be:${TAG}` and `production-nginx:${TAG}`
- removes the GHCR tag locally so the VPS keeps only the runtime-local names
- records pulled image digests under the production state directory

GHCR is the artifact source, not the runtime image naming contract.

Fallback: `infra/scripts/release/build.sh` builds the same two images locally
from an exact git tag (`production-be:${TAG}`, `production-nginx:${TAG}`). Use it
only when the GHCR flow is unavailable.

### Runtime Image Naming

Compose and runtime scripts use environment-prefixed local names:

```text
production-be:${TAG}
production-nginx:${TAG}
```

There is no frontend image: the frontend is deployed from `portfolio-fe` to
Cloudflare Workers.

### Service-To-Image Mapping

`be` and `release` both use `${ENVIRONMENT}-be:${TAG}`. They are separate
containers with separate commands that share one backend image. `nginx` uses
`${ENVIRONMENT}-nginx:${TAG}`.

The `release` job runs: `migrate`, `createcachetable`, `scripts/release_entrypoint.py`,
`collectstatic` (see `docker-compose.prod.yml`).

### Compose Behavior

Compose stays runtime-focused. It references local image names, never GHCR URLs;
artifact preparation stays outside compose.

The `cloudflared` service (profile `tunnel`) is not part of the deploy; it is
started separately (see [infra/scripts/README.md](../../scripts/README.md)).

### Script Responsibilities

#### `infra/scripts/release/prepare_images.sh`

Production-only artifact preparation from GHCR (see above). It does not run
migrations or switch services.

#### `infra/scripts/release/build.sh`

Manual fallback: builds the local images. It does not run migrations, deploy
containers, or update rollback state.

#### `infra/scripts/release/release.sh`

One-shot release tasks. It:

- enforces a release lock
- resolves the release image from compose
- ensures dependencies such as db are healthy
- refreshes the nginx bot blocklist
- creates a pre-release database backup
- runs the `release` job and captures its logs

It does not build images, pull from GHCR, or switch long-running containers.

#### `infra/scripts/release/deploy.sh`

Switches running services to a specified tag. It:

- verifies the requested images already exist locally
- switches `be` and `nginx` (the only deploy-managed services)
- runs post-switch health checks (container health plus an HTTPS check of
  `SITE_DOMAIN` through the local edge proxy on `127.0.0.1:443`)
- updates rollback state

It accepts only `ENVIRONMENT=production`. It does not build images, pull from
GHCR, or run release tasks.

#### `infra/scripts/release/deploy_production.sh`

Guided wrapper. Requires `TAG`, asks for approval between phases and runs
`prepare_images.sh` -> `release.sh` -> `deploy.sh`.

### Production Flow

1. feature PR into `dev`
2. bump `backend/pyproject.toml` version once per release (version-only commit
   with `[skip ci]`)
3. PR `dev` -> `main` titled `Release vX.Y.Z`
4. on merge, `release.yml` creates tag `vX.Y.Z` and pushes the images to GHCR
5. on the VPS, in `~/portfolio`:

```bash
git pull
TAG=vX.Y.Z doppler run --project portfolio --config prd -- ./infra/scripts/release/deploy_production.sh
```

Production deploy is explicit and operator-driven. There is no listener or
auto-deploy agent on the VPS.

### Rollback Model

Rollback is tag-based. State files live under the environment state directory,
typically:

```text
/var/lib/portfolio/<environment>/
```

Important state: `current_tag` and `prev_tag`. `deploy.sh` updates them after a
successful deployment. Rollback re-deploys a previous version tag (never a
mutable tag):

```bash
TAG=v1.1.0 ENVIRONMENT=production doppler run --project portfolio --config prd -- ./infra/scripts/release/deploy.sh
```

#### Celery and Redis removal (history)

Historical note for the VPS stack. `deploy.sh` did not pass `--remove-orphans`, so the old `redis`, `celery-worker`
and `celery-beat` containers kept running after the first deploy without them.
They were removed with:

```bash
docker rm -f portfolio-prod-redis-1 portfolio-prod-celery-worker-1 portfolio-prod-celery-beat-1
```

Do not remove the orphan `fe` container (no longer defined in this repo's
compose): nginx still has an `fe:8080` upstream in `infra/nginx/static_server.conf`
and needs it to resolve. Remove it only after that upstream is removed.

Rolling back to a release from before the removal needs Redis again (its
settings use `RedisCache` and Celery): start it from that release's checkout with
`docker compose -f docker-compose.common.yml -f docker-compose.prod.yml up -d redis celery-worker`.
After the removal, the `portfolio_prod_celerybeat_data` volume and the
`REDIS_PASSWORD` secret in Doppler are unused.

### Registry And Local Retention

- GHCR: long-term artifact store; keep production release tags conservatively
- VPS local Docker images: short-term runtime cache; a small recent set is kept
  (`prepare_images.sh` and `build.sh` prune older images, protecting the current
  and previous tags)

### Security Model

- publishing uses the built-in `GITHUB_TOKEN`; package visibility should stay private
- `prepare_images.sh` on the VPS requires `GHCR_USERNAME`, `GHCR_TOKEN`,
  `GHCR_NAMESPACE` (`GHCR_REGISTRY` defaults to `ghcr.io`); use a dedicated
  read-only package credential stored in Doppler, not in the repository

### Invariants To Preserve

- `release.sh` and `deploy.sh` consume local image names and explicit tags
- production gets those local images from `prepare_images.sh` (or `build.sh` as fallback)
- compose remains runtime-focused
- rollback remains explicit and tag-based
