# Production & Staging Scripts: Build, Release, Deploy

This repository uses shell scripts to manage deployments for both **Staging** and **Production** environments on a single VPS.

- `build.sh` → **builds Docker images** with environment prefixes and service suffixes (e.g. `production-be:v1.0.0`).
- `release.sh` → runs **one-shot release tasks** (migrations, collectstatic, etc.) targeting the correct environment services.
- `deploy.sh` → performs the **deployment switch** and updates environment-specific rollback state.
- `utils.sh` → shared utility functions used by the scripts above (e.g., directory resolution, state management).

---

## Environment Variables

These scripts **require** several variables to be set (typically via Doppler).

### Mandatory
1. **`ENVIRONMENT`**: Determines tags and isolated state (e.g., `production`, `stg`).
2. **`TAG`**: The git tag or version (e.g., `v1.2.3`).
3. **`PROJECT_OWNER`**: Injected into frontend metadata.
4. **`SITE_DOMAIN`** & **`API_DOMAIN`**: Used for Nginx templates and frontend builds.
5. **`ALLOWED_HOSTS`**: Django security setting.

### Optional
- `FRONTEND_PORT`: Defaults to `8080`.
- `DEBUG`: Set to `true` for staging logs.

---

## 1. Staging Workflow

Used for testing on the staging stack (`docker-compose.stg.yml`).

```bash
# 1. Build staging images
# Tags as stg-be:v1.0.0-test, stg-fe:v1.0.0-test, etc.
TAG=v1.0.0-test ENVIRONMENT=stg doppler run -- ./scripts/release/build.sh

# 2. Run release tasks (migrations/static)
# Targets db, redis, release inside the stg project
TAG=v1.0.0-test ENVIRONMENT=stg COMPOSE_FILE=docker-compose.stg.yml DEBUG=true doppler run -- ./scripts/release/release.sh

# 3. Deploy (switches containers, runs health checks)
TAG=v1.0.0-test ENVIRONMENT=stg COMPOSE_FILE=docker-compose.stg.yml DEBUG=true doppler run -- ./scripts/release/deploy.sh
```

---

## 2. Production Workflow

Used for the live stack (`docker-compose.prod.yml`).

```bash
# 1. Build production images
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./scripts/release/build.sh

# 2. Run release tasks
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./scripts/release/release.sh

# 3. Deploy
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./scripts/release/deploy.sh
```

---

## Shared Conventions

### Tag Discipline
- Deploy **only** versioned releases (e.g., `v1.2.3` or `1.2.3`).
- The scripts enforce that image exists locally before proceeding.

### Image Naming
Images are tagged as follows:
- Backend: `${ENVIRONMENT}-be:${TAG}`
- Frontend: `${ENVIRONMENT}-fe:${TAG}`
- Worker: `${ENVIRONMENT}-worker:${TAG}`

---

## Infrastructure

- **PostgreSQL**: Version **18** is used across all environments.
- **Redis**: Version **alpine** (7.x) is used across all environments.

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
