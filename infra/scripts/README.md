# 🧰 Infrastructure Scripts Runbook

This repository uses shell scripts to manage deployments, backups, and related operational tasks.

## 🗂️ Script Groups

Primary script groups:

- `release/` -> image build, release jobs, deployment switch, rollback flow
- `db_backup/` -> backup, restore, restore validation
- `utils.sh` -> shared utility functions used across infra scripts

---

## 🚀 Release Scripts

Release scripts manage **Production** deployments on a single VPS. Staging no longer exists.

- `release/build.sh` -> manual fallback: **builds Docker images locally** with environment prefixes and service suffixes (`production-be:v1.0.0`, `production-nginx:v1.0.0`)
- `release/prepare_images.sh` -> pulls production images from GHCR, retags them to the local runtime names, and removes the GHCR tag from the VPS
- `release/release.sh` -> runs **one-shot release tasks** (migrations, `createcachetable`, collectstatic, etc.)
- `release/deploy.sh` -> performs the **deployment switch only** (`be` and `nginx`, `ENVIRONMENT=production` only) and updates rollback state
- `release/deploy_production.sh` -> guided production workflow with approval prompts between image preparation, release, and deploy

## 🔐 Environment Variables

These scripts **require** several variables to be set, typically via Doppler.

### ✅ Mandatory
1. `ENVIRONMENT`: Determines tags and isolated state (`production`)
2. `TAG`: The git tag or version (e.g. `v1.2.3`)
3. `PROJECT_OWNER`: Backend runtime setting
4. `SITE_DOMAIN` and `API_DOMAIN`: Used for Nginx templates and Django configuration
5. `ALLOWED_HOSTS`: Django security setting

### 🏭 GHCR image preparation
- `GHCR_USERNAME`: registry username used by `prepare_images.sh`
- `GHCR_TOKEN`: registry token with package read access
- `GHCR_REGISTRY`: registry host used by image preparation scripts (defaults to `ghcr.io`)
- `GHCR_NAMESPACE`: full image namespace used by image preparation scripts

### 🔐 Manual GHCR login and pull example

```bash
doppler -c dev run -- sh -c 'printenv GHCR_TOKEN | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin && docker pull <registry image url>'
```

### ➕ Optional

### 🚨 Emergency bypass
If you must build from an uncommitted state, pass `--emergency` or set `EMERGENCY=1`:

```bash
doppler run -- ./infra/scripts/release/build.sh --emergency
EMERGENCY=1 doppler run -- ./infra/scripts/release/build.sh
```

> [!WARNING]
> The working tree is still printed in the output so you know exactly what was uncommitted. Use only in genuine emergencies and follow up with a proper commit and tagged build.

---

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

## 🔌 Cloudflare Tunnel (frontend on Workers)

The Workers frontend (`portfolio-fe`) reaches the backend through the
`cloudflared` service (profile `tunnel`), which forwards the tunnel hostname to
`http://be:8000` inside the compose network. It opens no ports, and `deploy.sh` does not touch it (pinned public image, not
`${TAG}`).

One-time setup:

1. Cloudflare Zero Trust -> Networks -> Tunnels: create a tunnel and put its
   token in Doppler as `CLOUDFLARE_TUNNEL_TOKEN`.
2. Add a public hostname (e.g. `internal-api.<domain>`) -> service
   `http://be:8000`. Do NOT set "HTTP Host Header": cloudflared then
   overwrites `X-Forwarded-Host` with the tunnel hostname, and Django
   (`USE_X_FORWARDED_HOST`) rejects it with 400 DisallowedHost. Without it,
   Django sees the site domain the Worker sends in `X-Forwarded-Host`.
3. Zero Trust -> Access: application for that hostname with a Service Auth
   policy and a service token. The token goes to the Worker secrets
   `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET`.
4. Start the connector (once; it restarts by itself afterwards):

```bash
doppler run -- docker compose -f docker-compose.prod.yml up -d cloudflared
```

Stop with `docker compose -f docker-compose.prod.yml stop cloudflared`.

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
- Production uses `prepare_images.sh` to pull GHCR images (published by `.github/workflows/release.yml`), retag them locally, and remove the GHCR tag so only the local runtime names remain
- `build.sh` is a manual fallback that builds the same images on the VPS

### 🧾 Compose File Overrides
- `build.sh`, `release.sh` and `deploy.sh` resolve `docker-compose.<env>.yml` from `ENVIRONMENT` (`production` -> `docker-compose.prod.yml`) unless `COMPOSE_FILE` is set
- `release.sh` and `deploy.sh` both load `docker-compose.common.yml` in addition to the target environment compose file
- `deploy_production.sh` pauses for operator approval before each phase unless `--yes` is passed

### 🔒 Locking
- These scripts use `flock` to prevent concurrent deployments
- If `flock` is missing, they warn and continue without a lock

### 🧪 Dry runs

- `release.sh --dry-run` validates inputs and dependency state without executing the release job
- `deploy.sh --dry-run` shows the deployment flow without switching running containers
- `deploy_production.sh --dry-run` passes dry-run through to release/deploy steps

---

## 🩺 Troubleshooting

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

If you are intentionally building on the VPS instead, run `build.sh` first.

### 💾 Backup scripts

Validate a dump in a temporary Postgres container:

```bash
./infra/scripts/db_backup/test_restore.sh /path/to/backup.dump
```

Restore a dump into the current local Docker DB:

```bash
./infra/scripts/db_backup/restore_db.sh /path/to/backup.dump
```
