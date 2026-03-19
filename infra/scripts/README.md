# Infrastructure Scripts Runbook

This repository uses shell scripts to manage deployments, backups, monitoring, and related operational tasks.

Primary script groups:

- `release/` -> image build, release jobs, deployment switch, rollback flow
- `db_backup/` -> backup, restore, restore validation
- `monitoring/` -> host-side Docker log collection and monitoring helpers
- `utils.sh` -> shared utility functions used across infra scripts

---

## Release Scripts

Release scripts manage **Staging** and **Production** deployments on a single VPS.

- `release/build.sh` -> **builds Docker images** with environment prefixes and service suffixes (e.g. `production-be:v1.0.0`)
- `release/release.sh` -> runs **one-shot release tasks** (migrations, collectstatic, etc.) targeting the correct environment services
- `release/deploy.sh` -> performs the **deployment switch** and updates environment-specific rollback state

## Environment Variables

These scripts **require** several variables to be set, typically via Doppler.

### Mandatory
1. `ENVIRONMENT`: Determines tags and isolated state (e.g. `production`, `staging`)
2. `TAG`: The git tag or version (e.g. `v1.2.3`)
3. `PROJECT_OWNER`: Injected into frontend metadata
4. `SITE_DOMAIN` and `API_DOMAIN`: Used for Nginx templates and frontend builds
5. `ALLOWED_HOSTS`: Django security setting

### Optional
- `FRONTEND_PORT`: Defaults to `8080`

### Emergency bypass
If you must build from an uncommitted state, pass `--emergency` or set `EMERGENCY=1`:

```bash
doppler run -- ./infra/scripts/release/build.sh --emergency
EMERGENCY=1 doppler run -- ./infra/scripts/release/build.sh
```

> [!WARNING]
> The working tree is still printed in the output so you know exactly what was uncommitted. Use only in genuine emergencies and follow up with a proper commit and tagged build.

---

## Staging Workflow

```bash
TAG=v1.0.0-test ENVIRONMENT=staging doppler run -- ./infra/scripts/release/build.sh
TAG=v1.0.0-test ENVIRONMENT=staging COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/release.sh
TAG=v1.0.0-test ENVIRONMENT=staging COMPOSE_FILE=docker-compose.stage.yml doppler run -- ./infra/scripts/release/deploy.sh
```

## Production Workflow

Before the first production release, ensure the backup directories exist and are writable by the deploy user:

```bash
sudo mkdir -p /var/backups/portfolio/pre_release/prod
sudo chown -R <user>:<user> /var/backups/portfolio
sudo chmod -R u+rwX /var/backups/portfolio
```

```bash
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/build.sh
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/release.sh
TAG=v1.2.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

## Rollback

1. Check current and previous tags in `/var/lib/portfolio/<environment>/` or your fallback state directory.
2. Re-deploy the previous tag:

```bash
TAG=v1.1.0 ENVIRONMENT=production doppler run -- ./infra/scripts/release/deploy.sh
```

---

## Shared Conventions

### Tag Discipline
- Deploy only versioned releases such as `v1.2.3`
- The scripts enforce that required images exist locally before proceeding

### Image Naming
- Images follow `${ENVIRONMENT}-<service>:${TAG}`

### Compose File Overrides
- `build.sh` auto-detects the environment compose file
- `release.sh` and `deploy.sh` default to production unless `COMPOSE_FILE` is overridden

### Locking
- These scripts use `flock` to prevent concurrent deployments
- If `flock` is missing, they warn and continue without a lock

---

## Troubleshooting

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
Release expects images to be built before migrations or deploy. Run `build.sh` first for the same `ENVIRONMENT` and `TAG`, then rerun `release.sh`.

### Backup scripts

Validate a dump in a temporary Postgres container:

```bash
./infra/scripts/db_backup/test_restore.sh /path/to/backup.dump
```

Restore a dump into the current local Docker DB:

```bash
./infra/scripts/db_backup/restore_db.sh /path/to/backup.dump
```
