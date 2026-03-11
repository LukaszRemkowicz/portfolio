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
### Emergency bypass (dirty working tree)
If you **must** build from an uncommitted state (e.g., hotfix not yet committed), pass the `--emergency` flag or set `EMERGENCY=1`:

```bash
# via flag
doppler run -- ./scripts/release/build.sh --emergency

# via env var
EMERGENCY=1 doppler run -- ./scripts/release/build.sh
```

> [!WARNING]
> The working tree is still printed in the output so you know exactly what was uncommitted. Use only in genuine emergencies — always follow up with a proper commit + tagged build as soon as possible.

---

## 1. Staging Workflow

Used for testing on the staging stack (`docker-compose.stage.yml`).

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

## 3. Rollback (Staging or Production)

1. Check current/previous tags in `/var/lib/portfolio/<environment>/` or your local state dir.
2. Re-deploy the previous tag:
   ```bash
   TAG="v1.1.0" ENVIRONMENT="production" doppler run -- ./scripts/release/deploy.sh
   ```

---

## Shared Conventions

### Tag Discipline
- Deploy **only** versioned releases (e.g., `v1.2.3` or `1.2.3`).
- The scripts enforce that image exists locally before proceeding.

### Image Naming
- Worker: `${ENVIRONMENT}-worker:${TAG}`

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

## Troubleshooting

### “FATAL: database portfolio-stage does not exist”
If you changed project names or moved volumes, the staging database might need a fresh initialization:
```bash
docker compose -f docker-compose.stage.yml down -v
# Then re-run release.sh
```

### “Port is already allocated”
Ensure you are not running two stacks (e.g. `portfolio` and `landingpage`) that collide on the same ports. Use `docker compose ls` to see active projects.
