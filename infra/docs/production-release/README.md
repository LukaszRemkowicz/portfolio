# Production Release Runbook

## Purpose

This runbook describes the current production release flow after the GHCR publish work.

It covers:

- what must be configured in GitHub
- what must be configured in Doppler on the production VPS
- what remains local-only for staging
- how to publish and deploy a production release

## Current Model

The current release model is:

- staging is still built locally with `infra/scripts/release/build.sh`
- production images are published to GHCR from GitHub Actions
- production VPS pulls those production images with `infra/scripts/release/prepare_images.sh`
- `release.sh` and `deploy.sh` keep their existing tag-based behavior

Production artifact names in GHCR:

```text
<registry>/<namespace>/production-be:vX.Y.Z
<registry>/<namespace>/production-fe:vX.Y.Z
<registry>/<namespace>/production-nginx:vX.Y.Z
```

Local image names expected on the production VPS:

```text
production-be:vX.Y.Z
production-fe:vX.Y.Z
production-nginx:vX.Y.Z
```

## GitHub Setup

## Repository Variables

Add these in:

`GitHub -> Repository -> Settings -> Secrets and variables -> Actions -> Variables`

Required for production image publish:

- `SITE_DOMAIN`
- `API_DOMAIN`
- `GA_TRACKING_ID`
- `ALLOWED_HOSTS`
- `PROJECT_OWNER`

These are used by `.github/workflows/ci-cd.yml` during the production frontend build.

## Repository Secrets

Add these in:

`GitHub -> Repository -> Settings -> Secrets and variables -> Actions -> Secrets`

Required for production image publish:

- `SENTRY_DSN_FE`

Built-in token used automatically by GitHub Actions:

- `GITHUB_TOKEN`

You do not add `GITHUB_TOKEN` manually.

## GitHub Workflows Involved

- `.github/workflows/release.yml`
  Creates `vX.Y.Z` tag from `VERSION` when `main` changes.

- `.github/workflows/ci-cd.yml`
  Runs validation jobs first and then publishes production images to GHCR as the final job for release tags or manual publish runs.

## Package Visibility

Keep GHCR packages private.

After the first successful publish, verify package visibility in GitHub Packages and keep it private.

## Production VPS Doppler Setup

## New Variables Needed For GHCR Pull

Add these to the production Doppler config used on the VPS:

- `GHCR_USERNAME`
- `GHCR_TOKEN`
- `GHCR_NAMESPACE`

Recommended values:

- `GHCR_REGISTRY=ghcr.io`
- `GHCR_NAMESPACE=ghcr.io/lukaszremkowicz/portfolio`

Requirements:

- `GHCR_TOKEN` should be read-only for packages
- use a dedicated machine token or narrowly scoped fine-grained token
- do not store this token in the repository
- keep the actual registry namespace in Doppler rather than hardcoding it in scripts
- `GHCR_REGISTRY` may be omitted from Doppler because the script defaults it to `ghcr.io`

## Existing Production Variables Still Required

The production release/deploy flow still relies on your existing production Doppler config.

At minimum, the current production compose and release scripts use variables such as:

- `ENVIRONMENT=production`
- `TAG`
- `SECRET_KEY`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `ADMIN_DOMAIN`
- `API_DOMAIN`
- `SITE_DOMAIN`
- `CSRF_COOKIE_DOMAIN`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `CONTACT_EMAIL`
- `SESSION_COOKIE_DOMAIN`
- `SENTRY_DSN`
- `SENTRY_DSN_FE`
- `PROJECT_OWNER`
- `REDIS_PASSWORD`
- `OPENAI_API_KEY`
- `SSR_CACHE_INVALIDATION_TOKEN`
- `SSR_CACHE_INVALIDATION_URL`
- `NGINX_LOG_DIR`
- `DB_BACKUP_DIR`

This runbook does not replace your existing production Doppler config. It adds the GHCR pull credentials on top of it.

## Production VPS Prerequisites

Before the first production release with GHCR:

1. Docker and Docker Compose must already work on the VPS.
2. Doppler production config must be available on the VPS.
3. Backup directories must exist and be writable:

```bash
sudo mkdir -p /var/backups/portfolio/pre_release/prod
sudo chown -R <user>:<user> /var/backups/portfolio
sudo chmod -R u+rwX /var/backups/portfolio
```

4. The production server must be able to log in to GHCR.

Optional smoke check:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
```

## Production Release Flow

## 1. Prepare The Release In Git

1. Update `VERSION` in the branch that will land on `main`.
2. Merge to `main`.
3. GitHub Actions runs `.github/workflows/release.yml`.
4. That workflow creates and pushes tag `vX.Y.Z`.
5. GitHub Actions runs the publish job inside `.github/workflows/ci-cd.yml`.
6. Production images are pushed to GHCR.

## 2. On The Production VPS, Pull Prepared Images

Run:

```bash
TAG=vX.Y.Z doppler run -- ./infra/scripts/release/prepare_images.sh
```

What this does:

- logs in to GHCR
- pulls:
  - `production-be:${TAG}`
  - `production-fe:${TAG}`
  - `production-nginx:${TAG}`
- tags them locally as:
  - `production-be:${TAG}`
  - `production-fe:${TAG}`
  - `production-nginx:${TAG}`
- records digests in the production state directory

## 3. Run Release Tasks

Run:

```bash
TAG=vX.Y.Z ENVIRONMENT=production doppler run -- ./infra/scripts/release/release.sh
```

This executes:

- migrations
- seed settings
- collectstatic
- pre-release backup flow already built into `release.sh`

## 4. Deploy The Running Services

Run:

```bash
TAG=vX.Y.Z ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

This:

- uses the locally prepared production images
- starts/updates the running services
- performs health checks
- updates rollback state files

## 5. Rollback

Rollback remains tag-based.

Example:

```bash
TAG=v1.2.2 ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

## What Changed In Production Compose

`docker-compose.prod.yml` still uses local image names, not GHCR URLs.

That means compose remains runtime-focused.

The main image change is:

- `celery-worker` now uses `${ENVIRONMENT}-be:${TAG}`

These services now share the same backend artifact:

- `be`
- `celery-worker`
- `celery-beat`
- `release`

They are still separate containers and separate processes.

## Staging Is Different

Staging does not use GHCR in this flow.

Staging remains:

```bash
TAG=v1.0.0-test ENVIRONMENT=staging doppler run -- ./infra/scripts/release/build.sh
TAG=v1.0.0-test ENVIRONMENT=staging COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/release.sh
TAG=v1.0.0-test ENVIRONMENT=staging COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/deploy.sh
```

This is intentional, because staging is used for branch-based testing and should not depend on production release publication.

## Verification Checklist

Before calling the production flow complete, verify:

1. The `Publish Production Images` job in `ci-cd.yml` succeeded for the target tag.
2. GHCR package visibility is private.
3. `prepare_images.sh` works on the production VPS.
4. `release.sh` succeeds using the prepared images.
5. `deploy.sh` succeeds using the prepared images.
6. Frontend and backend health checks pass.
7. Rollback to the previous tag still works.
8. Digest file exists after preparation.

## Artifact Verification

### What CI already generates

The production publish workflow generates:

- version-tagged production images in GHCR
- SBOM metadata via `docker/build-push-action`
- provenance metadata via `docker/build-push-action`

### What is recorded on the VPS

When production images are prepared with:

```bash
TAG=vX.Y.Z doppler run -- ./infra/scripts/release/prepare_images.sh
```

the script records pulled digests in:

```text
/var/lib/portfolio/production/prepared_image_digests.env
```

If `/var/lib/portfolio` is not writable, the state directory falls back to:

```text
$HOME/.portfolio-state/production/prepared_image_digests.env
```

### Artifact verification checklist

1. Confirm the requested tag matches the intended production release.
2. Confirm the publish workflow succeeded for the same `vX.Y.Z` tag.
3. Run `prepare_images.sh` for production.
4. Inspect the recorded digest file.
5. Confirm local image tags exist for:
   - `production-be:${TAG}`
   - `production-fe:${TAG}`
   - `production-nginx:${TAG}`
6. Run `release.sh`.
7. Run `deploy.sh`.
8. Confirm health checks pass.
9. Keep the digest file with deploy notes for rollback/audit reference.

## Useful Commands

Check local production images:

```bash
docker image ls | egrep 'production-(be|fe|nginx)'
```

Show recorded digests:

```bash
cat /var/lib/portfolio/production/prepared_image_digests.env
```

If `/var/lib/portfolio` is not writable, check:

```bash
cat "$HOME/.portfolio-state/production/prepared_image_digests.env"
```

Inspect a local image:

```bash
docker image inspect production-be:vX.Y.Z
```

Show the pulled remote digest carried by the local image:

```bash
docker image inspect --format '{{join .RepoDigests "\n"}}' production-be:vX.Y.Z
```

## Related Files

- `.github/workflows/release.yml`
- `.github/workflows/ci-cd.yml`
- `infra/scripts/release/prepare_images.sh`
- `infra/scripts/release/release.sh`
- `infra/scripts/release/deploy.sh`
- `infra/scripts/README.md`
- `infra/docs/github_registry_rollout_plan.md`
