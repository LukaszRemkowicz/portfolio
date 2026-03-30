# Release And Deploy Architecture

## Purpose

This document describes the current release and deployment model of the application.

It is intended as compact context for future engineering or LLM-assisted work.

For operator-facing commands and day-to-day usage, see:

- [infra/scripts/README.md](../../scripts/README.md)
- [infra/scripts/release/README.md](../../scripts/release/README.md)

It focuses on:

- release identity
- artifact sources
- staging vs production behavior
- script responsibilities
- runtime image naming
- operational flow and rollback

## Core Model

The application uses a tag-based release model.

Source of truth for a release:

```text
vX.Y.Z
```

Key rule:

- release and deploy logic are tag-based
- mutable tags such as `latest` are not part of the deployment contract

## Environments

There are two distinct artifact flows:

### Staging

- built locally on the VPS
- uses `infra/scripts/release/build.sh`
- usually built from the branch currently being tested
- does not depend on GHCR publication

### Production

- images are built in GitHub Actions
- images are published to GitHub Container Registry
- VPS pulls the published production images with `infra/scripts/release/prepare_images.sh`
- `release.sh` and `deploy.sh` then use the locally tagged images

## Release Identity

Release identity is derived from `VERSION` and Git tags.

### GitHub release tag flow

`.github/workflows/release.yml`:

- runs on push to `main`
- reads `VERSION`
- compares it to the latest `v*` tag
- creates a new annotated tag `vX.Y.Z` if needed
- publishes production images to GHCR when a new release tag is created

## Artifact Sources

### Staging artifact source

Staging artifacts are created locally by:

```text
infra/scripts/release/build.sh
```

This script:

- resolves `TAG` from git if omitted
- requires `ENVIRONMENT`
- builds:
  - `${ENVIRONMENT}-be:${TAG}`
  - `${ENVIRONMENT}-worker:${TAG}`
  - `${ENVIRONMENT}-fe:${TAG}`
  - `${ENVIRONMENT}-nginx:${TAG}`
- prunes older local images while protecting:
  - current tag
  - previous tag
  - newly built tag

### Production artifact source

Production artifacts are published to GHCR as:

```text
<registry>/<namespace>/production-be:vX.Y.Z
<registry>/<namespace>/production-fe:vX.Y.Z
<registry>/<namespace>/production-nginx:vX.Y.Z
```

On the production VPS, `infra/scripts/release/prepare_images.sh`:

- resolves `TAG` from git if omitted
- assumes production
- logs in to GHCR
- pulls production images from GHCR
- tags them locally as:
  - `production-be:${TAG}`
  - `production-fe:${TAG}`
  - `production-nginx:${TAG}`
- records pulled image digests under the production state directory

So production runtime still uses local Docker image names.
GHCR is the artifact source, not the runtime image naming contract.

## Runtime Image Naming

The naming contract used by compose and runtime scripts is environment-prefixed:

```text
production-be:${TAG}
production-fe:${TAG}
production-nginx:${TAG}
stage-be:${TAG}
stage-fe:${TAG}
stage-nginx:${TAG}
```

This naming is preserved intentionally because it matches current VPS operations and existing scripts.

## Service-To-Image Mapping

The important runtime simplification is:

- `be`
- `celery-worker`
- `celery-beat`
- `release`

all use the same backend artifact:

```text
${ENVIRONMENT}-be:${TAG}
```

This does not mean they are the same container.

It means:

- separate containers
- separate processes
- separate commands
- shared backend image artifact

Frontend and nginx remain separate artifacts:

- `${ENVIRONMENT}-fe:${TAG}`
- `${ENVIRONMENT}-nginx:${TAG}`

## Compose Behavior

Compose remains runtime-focused.

It still references local image names rather than GHCR URLs.

This is intentional because:

- it keeps compose concerned with runtime topology
- it avoids mixing artifact-source logic into compose
- artifact preparation stays outside compose

Production compose change already made:

- `celery-worker` now uses `${ENVIRONMENT}-be:${TAG}`

`celery-beat`, `be`, and `release` were already using `${ENVIRONMENT}-be:${TAG}`.

## Script Responsibilities

### `infra/scripts/release/build.sh`

Primary role:

- build local environment-prefixed images

Current intended usage:

- standard path for staging
- fallback path for production if GHCR flow is unavailable

Runbook:

- [infra/scripts/README.md](../../scripts/README.md)
- [infra/scripts/release/README.md](../../scripts/release/README.md)

It does not:

- run migrations
- deploy containers
- update rollback state

### `infra/scripts/release/prepare_images.sh`

Primary role:

- production-only artifact preparation from GHCR

It does:

- pull production images from GHCR
- tag them locally to the names already expected by compose
- record digests for verification/audit

It does not:

- run migrations
- switch running services

Runbook:

- [infra/scripts/README.md](../../scripts/README.md)

### `infra/scripts/release/release.sh`

Primary role:

- execute one-shot release tasks

It does:

- enforce release lock
- resolve the release image from compose
- ensure dependencies such as db and redis are healthy
- run the release container/job
- capture release logs
- create pre-release backup in production

It expects:

- the correct local image for `TAG` already exists

It does not:

- build images
- pull from GHCR
- switch long-running containers

Runbook:

- [infra/scripts/README.md](../../scripts/README.md)
- [infra/scripts/release/README.md](../../scripts/release/README.md)

### `infra/scripts/release/deploy.sh`

Primary role:

- switch running services to a specified tag

It does:

- enforce deploy lock
- verify required local images exist
- run `release.sh`
- run `docker compose up -d`
- reload nginx
- run frontend and backend health checks
- update rollback state files

It expects:

- the correct local images for `TAG` already exist

It does not:

- build images
- pull from GHCR

Runbook:

- [infra/scripts/README.md](../../scripts/README.md)
- [infra/scripts/release/README.md](../../scripts/release/README.md)

### Shared Design Principle

`release.sh` and `deploy.sh` remain shared between staging and production.

Artifact-source logic stays outside them.

That is why production uses:

```text
prepare_images.sh -> release.sh -> deploy.sh
```

while staging uses:

```text
build.sh -> release.sh -> deploy.sh
```

## Production Flow

High-level production flow:

1. update `VERSION`
2. merge to `main`
3. `release.yml` creates tag `vX.Y.Z`
4. `release.yml` builds and pushes production images to GHCR
5. on VPS, run `prepare_images.sh`
6. run `release.sh`
7. run `deploy.sh`

This means production deploy is still explicit and operator-driven.

There is no listener service or auto-deploy agent on the VPS.

## Staging Flow

High-level staging flow:

1. choose branch/tag/build target
2. run `build.sh` for staging
3. run `release.sh`
4. run `deploy.sh`

Staging remains intentionally separate from the production registry flow.

## Rollback Model

Rollback is tag-based.

State files are stored under the environment state directory, typically:

```text
/var/lib/portfolio/<environment>/
```

Important state:

- `current_tag`
- `prev_tag`

`deploy.sh` updates these after successful deployment.

Rollback uses a previous version tag, not a mutable tag.

## Registry And Local Retention

Recommended retention split:

### GHCR

- long-term artifact store
- keep production release tags conservatively

### VPS local Docker images

- short-term runtime cache
- keep a small recent set locally
- rely on GHCR as the durable artifact source

This keeps migration/recovery possible even if the VPS is replaced.

## Security Model

### GitHub side

- publishing uses built-in `GITHUB_TOKEN`
- package visibility should remain private

### Production VPS side

`prepare_images.sh` requires:

- `GHCR_USERNAME`
- `GHCR_TOKEN`
- `GHCR_NAMESPACE`

`GHCR_REGISTRY` defaults to `ghcr.io`

Best practice:

- use a dedicated read-only package credential
- store it in Doppler, not in the repository

## Current Status

Implemented:

- production image publish workflow
- production image preparation script
- shared backend artifact usage in production compose
- digest capture for prepared production images
- production/staging documentation updates

Not built into the scripts:

- automatic invocation of `prepare_images.sh` from `release.sh` or `deploy.sh`

This is intentional because staging and production use different artifact sources.

## Practical Summary

If future work touches release/deploy behavior, the main invariant to preserve is:

- `release.sh` and `deploy.sh` consume local image names and explicit tags
- staging gets those local images from `build.sh`
- production gets those local images from `prepare_images.sh`
- compose remains runtime-focused
- rollback remains explicit and tag-based
