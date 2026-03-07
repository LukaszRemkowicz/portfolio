# Production & Staging Scripts: Build, Release, Deploy

This repository uses shell scripts to manage deployments for both **Staging** and **Production** environments on a single VPS.

- `build.sh` → **builds Docker images** with environment prefixes (e.g. `stage-v1.0.0`).
- `release.sh` → runs **one-shot release tasks** (migrations, collectstatic, etc.) targeting the correct environment services.
- `deploy.sh` → performs the **deployment switch** and updates environment-specific rollback state.
- `utils.sh` → shared utility functions used by the scripts above (e.g., directory resolution, state management).

---

## Environment Variable: `ENVIRONMENT`

These scripts **require** the `ENVIRONMENT` variable to be set (typically via Doppler). This determines:
1. **Image Tags**: Images are tagged as `${ENVIRONMENT}-${TAG}` (e.g. `stage-v1.2.3` or `production-v1.2.3`).
2. **Service Mapping**: Scripts automatically target `stage-db`/`stage-redis` for staging, and `db`/`redis` for production.
3. **Rollback State**: State is tracked separately for each environment.

---

## 1. Staging Workflow

Used for testing on the staging stack (`docker-compose.stage.yml`).

```bash
# 1. Build staging images
# Tags as portfolio-backend:stage-v1.0.0-test, Tag is necessary to not overwrite production images. Also Staging wont be a strict connected to git tags.
TAG=v1.0.0-test doppler run --config stg -- ./scripts/release/build.sh

# 2. Run release tasks (migrations/static)
# Targets stage-db, stage-redis, stage-release
TAG=v1.0.0-test COMPOSE_FILE=docker-compose.stage.yml DEBUG=true doppler run --config stg -- ./scripts/release/release.sh

# 3. Deploy (switches containers, runs health checks)
TAG=v1.0.0-test COMPOSE_FILE=docker-compose.stage.yml DEBUG=true doppler run --config stg -- ./scripts/release/deploy.sh
```

---

## 2. Production Workflow

Used for the live stack (`docker-compose.prod.yml`).

```bash
# 1. Build production images
# Tags as portfolio-backend:production-v1.2.0. Tag is optional.
TAG=v1.2.0 doppler run --config prd -- ./scripts/release/build.sh

# 2. Run release tasks
# Targets db, redis, release
TAG=v1.2.0 doppler run --config prd -- ./scripts/release/release.sh

# 3. Deploy
TAG=v1.2.0 doppler run --config prd -- ./scripts/release/deploy.sh
```

---

## Shared Conventions

### Tag Discipline
- Deploy **only** tagged releases (example: `v1.2.3`).
- The scripts enforce that the exact `${ENVIRONMENT}-${TAG}` image exists locally before proceeding.

### Compose File Overrides
- `build.sh`: Automatically detects the environment.
- `release.sh` / `deploy.sh`: Defaults to `docker-compose.prod.yml`. Always override for staging:
  `COMPOSE_FILE=docker-compose.stage.yml`

### Project Name
The scripts default to `COMPOSE_PROJECT_NAME=landingpage` (matching the local repository folder).

### Locking
- These scripts use `flock` to prevent concurrent deployments.
- **macOS Compatibility**: If `flock` is missing (common on macOS), the scripts will print a warning and proceed without a lock. This is intended for local testing only.

---

## Rollback (Staging or Production)

1. Check current/previous tags in `/var/lib/portfolio/<environment>/` or your local state dir.
2. Re-deploy the previous tag:
   ```bash
   TAG="v1.1.0" ENVIRONMENT="production" doppler run -- ./scripts/release/deploy.sh
   ```

---

## Infrastructure

- **PostgreSQL**: Version **17** (LTS) is used across all environments.
- **Redis**: Version **7-alpine** is used across all environments.

---

## Troubleshooting

### “FATAL: database portfolio-stage does not exist”
If you changed project names or moved volumes, the staging database might need a fresh initialization:
```bash
docker compose -f docker-compose.stage.yml down -v
# Then re-run release.sh
```

### “Port is already allocated”
Ensure you are not running two stacks (e.g. `portfolio` and `landingpage`) that collide on the same ports. Use `docker compose ls` to see active projects.
