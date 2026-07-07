# 🧰 Infrastructure Scripts Runbook

This repository uses shell scripts to manage deployments, backups, and related operational tasks.

## 🗂️ Script Groups

Primary script groups:

- `release/` -> image build, release jobs, deployment switch, rollback flow
- `db_backup/` -> backup, restore, restore validation
- `utils.sh` -> shared utility functions used across infra scripts

---

## 🚀 Release Scripts

Release scripts manage **Staging** and **Production** deployments on a single VPS.

- `release/build.sh` -> **builds Docker images** with environment prefixes and service suffixes (e.g. `production-be:v1.0.0`)
- `release/prepare_images.sh` -> pulls production images from GHCR, retags them to the local runtime names, and removes the GHCR tag from the VPS
- `release/prepare_staging_images.sh` -> pulls staging images from GHCR, retags them to the local runtime names, and removes the GHCR tag from the VPS
- `release/release.sh` -> runs **one-shot release tasks** (migrations, collectstatic, etc.) targeting the correct environment services
- `release/deploy.sh` -> performs the **deployment switch only** and updates environment-specific rollback state
- `release/deploy_staging.sh` -> guided staging workflow with approval prompts between staging image preparation, release, and deploy
- `release/manual_deploy_staging.sh` -> legacy guided staging workflow with approval prompts between VPS-local build, release, and deploy
- `release/deploy_production.sh` -> guided production workflow with approval prompts between image preparation, release, and deploy

## 🔐 Environment Variables

These scripts **require** several variables to be set, typically via Doppler.

### ✅ Mandatory
1. `ENVIRONMENT`: Determines tags and isolated state (e.g. `production`, `stage`)
2. `TAG`: The git tag or version (e.g. `v1.2.3`)
3. `PROJECT_OWNER`: Injected into frontend metadata
4. `SITE_DOMAIN` and `API_DOMAIN`: Used for Nginx templates and frontend builds
5. `ALLOWED_HOSTS`: Django security setting

### 🏭 GHCR image preparation
- `GHCR_USERNAME`: registry username used by `prepare_images.sh` and `prepare_staging_images.sh`
- `GHCR_TOKEN`: registry token with package read access
- `GHCR_REGISTRY`: registry host used by image preparation scripts (defaults to `ghcr.io`)
- `GHCR_NAMESPACE`: full image namespace used by image preparation scripts

### 🔐 Manual GHCR login and pull example

```bash
doppler -c dev run -- sh -c 'printenv GHCR_TOKEN | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin && docker pull <registry image url>'
```

### ➕ Optional
- `FRONTEND_PORT`: Defaults to `8080`

### 🚨 Emergency bypass
If you must build from an uncommitted state, pass `--emergency` or set `EMERGENCY=1`:

```bash
doppler run -- ./infra/scripts/release/build.sh --emergency
EMERGENCY=1 doppler run -- ./infra/scripts/release/build.sh
```

> [!WARNING]
> The working tree is still printed in the output so you know exactly what was uncommitted. Use only in genuine emergencies and follow up with a proper commit and tagged build.

---

## 🧪 Staging Workflow

Staging currently has two artifact paths:

- **Legacy VPS-local path**: build the images on the VPS, then release and
  deploy them locally.
- **Registry publish path**: build the staging images in GitHub Actions and
  push them to GHCR. This avoids stressing the VPS during image builds.

### Registry-backed staging deploy

Guided flow:

```bash
doppler run -- ./infra/scripts/release/deploy_staging.sh
```

Staging deploy does not start `celery-worker`. To run the staging worker on
demand after images are prepared:

```bash
TAG=v0.0.0-STG ENVIRONMENT=stage doppler run -- docker compose -f docker-compose.common.yml -f docker-compose.stage.yml --profile manual-worker up -d celery-worker
```

Image preparation only, for debugging the registry pull step without running
release/deploy:

```bash
doppler run -- ./infra/scripts/release/prepare_staging_images.sh
```

### Registry publish path

To publish staging images without building them on the VPS:

1. Open the pull request for the branch you want to publish.
2. Add the PR label:

```text
publish-staging
```

The `Publish Staging Images` workflow builds the PR head SHA and pushes these
constant staging tags to GHCR:

```text
stage-be:v0.0.0-STG
stage-fe:v0.0.0-STG
stage-nginx:v0.0.0-STG
```

`prepare_staging_images.sh` creates the local `stage-worker:v0.0.0-STG` tag
from `stage-be:v0.0.0-STG`, matching production: worker and backend use the
same backend artifact.

If the PR branch is updated while the `publish-staging` label is still present,
the workflow publishes the new PR head commit again. Remove the label to stop
publishing future branch updates.

### Legacy VPS-local build and deploy

Use this only when the staging registry path is unavailable or you explicitly
want to build on the VPS:

```bash
doppler run -- ./infra/scripts/release/manual_deploy_staging.sh
```

Manual legacy flow:

```bash
TAG=v1.0.0-test ENVIRONMENT=stage doppler run -- ./infra/scripts/release/build.sh
TAG=v1.0.0-test ENVIRONMENT=stage COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/release.sh
TAG=v1.0.0-test ENVIRONMENT=stage COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/deploy.sh
```

## 🏭 Production Workflow

Before the first production release, ensure the backup directories exist and are writable by the deploy user:

```bash
sudo mkdir -p /var/backups/portfolio/pre_release/prod
sudo chown -R <user>:<user> /var/backups/portfolio
sudo chmod -R u+rwX /var/backups/portfolio
```

Guided flow:

```bash
TAG=v1.2.0 doppler run -- ./infra/scripts/release/deploy_production.sh
```

Manual flow:

```bash
TAG=v1.2.0 doppler run -- ./infra/scripts/release/prepare_images.sh
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/release.sh
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

Production release refreshes the Nginx bot blocklist before migrations. If the
download fails, release stops instead of silently deploying with an empty
blocklist. Use `ALLOW_EMPTY_NGINX_BLOCKLIST=true` only as an explicit emergency
bypass.

For test-only GHCR tags that are not SemVer-like:

```bash
TEST=true TAG=test-feat-add-image-registry-2f0b23d doppler -c dev run -- ./infra/scripts/release/prepare_images.sh
```

## ↩️ Rollback

1. Check current and previous tags in `/var/lib/portfolio/<environment>/` or your fallback state directory.
2. Re-deploy the previous tag:

```bash
TAG=v1.1.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

---

## 📏 Shared Conventions

### 🏷️ Tag Discipline
- Deploy only versioned releases such as `v1.2.3`
- The scripts enforce that required images exist locally before proceeding

### 📦 Image Naming
- Images follow `${ENVIRONMENT}-<service>:${TAG}`

### 📥 Artifact Source
- Staging normally uses CI-published GHCR images from the `publish-staging` PR label workflow and `prepare_staging_images.sh`; the legacy local-build path remains available through `manual_deploy_staging.sh`
- Production uses `prepare_images.sh` to pull GHCR images, retag them locally, and remove the GHCR tag so only the local runtime names remain

### 🧾 Compose File Overrides
- `build.sh` auto-detects the environment compose file
- `release.sh` and `deploy.sh` default to production unless `COMPOSE_FILE` is overridden
- `release.sh` and `deploy.sh` both load `docker-compose.common.yml` in addition to the target environment compose file
- `deploy_staging.sh` and `deploy_production.sh` pause for operator approval before each phase unless `--yes` is passed

### 🔒 Locking
- These scripts use `flock` to prevent concurrent deployments
- If `flock` is missing, they warn and continue without a lock

### 🧪 Dry runs

- `release.sh --dry-run` validates inputs and dependency state without executing the release job
- `deploy.sh --dry-run` shows the deployment flow without switching running containers
- `deploy_staging.sh --dry-run` and `deploy_production.sh --dry-run` pass dry-run through to release/deploy steps

---

## 🩺 Troubleshooting

### “FATAL: database portfolio_stage does not exist”
If you changed project names or moved volumes, the staging database may need a fresh initialization:

```bash
docker compose -f docker-compose.stage.yml down -v
```

Then rerun `release.sh`.

### “Port is already allocated”
Ensure you are not running two stacks that collide on the same ports. Use:

```bash
docker compose ls
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

### “Pre-release database backup failed” or “Permission denied” under `/var/backups/portfolio`
Ensure the backup directories exist and are writable by the deploy user:

```bash
sudo mkdir -p /var/backups/portfolio/pre_release/prod
sudo chown -R <user>:<user> /var/backups/portfolio
sudo chmod -R u+rwX /var/backups/portfolio
```

### “Missing image production-be:<tag>” or similar
For production, run:

```bash
TAG=v1.2.0 doppler run -- ./infra/scripts/release/prepare_images.sh
```

For staging, run `deploy_staging.sh`. The registry-backed staging scripts own the fixed `v0.0.0-STG` image tag. If you are intentionally using the legacy VPS-local path, run `build.sh` first instead.

### 💾 Backup scripts

Validate a dump in a temporary Postgres container:

```bash
./infra/scripts/db_backup/test_restore.sh /path/to/backup.dump
```

Restore a dump into the current local Docker DB:

```bash
./infra/scripts/db_backup/restore_db.sh /path/to/backup.dump
```
