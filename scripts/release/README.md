# Production Scripts: Build, Release, Deploy

This repository uses three small shell scripts to manage production changes on a single VPS:

- `build.sh` → **builds Docker images** for a tagged release (no deploy)
- `release.sh` → runs the **one-shot release job** (migrations/static/messages/seeds)
- `deploy.sh` → performs the **deployment switch** to the new tag and updates rollback state

These scripts are designed for a “boring”, rollback-aware workflow:
**tag == release**, deployment is manual, and images are built on the server.

---

## Quick start (the happy path)

From the repo root on the server:

```bash
# Build images for the currently checked-out tag on HEAD
doppler run -- ./build.sh

# Run release tasks (DB migrate, collectstatic, etc.)
TAG=vX.Y.Z doppler run -- ./release.sh

# Deploy (runs release.sh, switches services, runs health checks, writes state)
TAG=vX.Y.Z doppler run -- ./deploy.sh
```

If you’re already on an exactly-tagged commit, you can omit `TAG=...` for scripts that auto-detect it (depending on your current implementation).

---

## Shared conventions

### Tag discipline (important)
These scripts assume:

- You deploy **only** tagged releases (example: `v1.2.3`)
- The tag points to the exact commit you intend to run in production

If HEAD is not exactly tagged, the scripts should fail rather than deploy ambiguous code.

### Environment injection
Production configuration is expected to be injected at runtime, typically via Doppler:

```bash
doppler run -- ./build.sh
TAG=v1.2.3 doppler run -- ./release.sh
TAG=v1.2.3 doppler run -- ./deploy.sh
```

### Compose file
Production stack is defined in:

- `docker-compose.prod.yml` (default)

You can override the path for `release.sh` / `deploy.sh` via `COMPOSE_PROD=/path/to/file.yml` if your scripts support it.

### State files (rollback metadata)
The deployment flow maintains:

- `/var/lib/portfolio/current_tag`
- `/var/lib/portfolio/prev_tag`

`deploy.sh` should update these **only after** a successful deploy + health check.

---

## `build.sh`

### What it does
- Validates it’s running inside the git repo
- Ensures the working tree is clean (no uncommitted changes)
- Ensures a valid release tag is selected (SemVer-like)
- Builds images:
  - `portfolio-backend:<TAG>`
  - `portfolio-frontend:<TAG>`
- Cleans up old images while keeping:
  - the tag just built
  - `current_tag`
  - `prev_tag`

### What it does NOT do
- Does not run DB migrations
- Does not start containers
- Does not change `current_tag/prev_tag`

### Typical usage
```bash
doppler run -- ./build.sh
# or explicitly:
TAG=v1.2.3 doppler run -- ./build.sh
```

### Required environment (typical)
Exact requirements depend on your script, but commonly include:

- `API_DOMAIN` (domain only, e.g. `api.example.com`)
- `SITE_DOMAIN` (domain only, e.g. `example.com`)
- Any FE build-time variables needed to bake config into the static build

If your FE expects `API_URL`, your build script may derive it from `API_DOMAIN` and pass:
`API_URL=https://$API_DOMAIN` as a Docker build-arg.

---

## `release.sh`

### What it does
- Prevents concurrent releases (lock file)
- Ensures dependencies are up (`db`, `redis`)
- Waits for DB health (via Docker healthcheck)
- Ensures the backend image for the tag exists locally (release never builds)
- Runs the compose `release` service once:

Typical `release` command includes:
- `python manage.py migrate --noinput`
- `python manage.py seed_settings`
- `python manage.py compilemessages`
- `python manage.py collectstatic --noinput`

### What it does NOT do
- Does not deploy/switch long-running services
- Does not update `current_tag/prev_tag`

### Usage
```bash
TAG=v1.2.3 doppler run -- ./release.sh
```

### Dry run (if supported)
```bash
TAG=v1.2.3 doppler run -- ./release.sh --dry-run
```

---

## `deploy.sh`

### What it does
A proper deploy script should:
1. Prevent concurrent deploys (lock file)
2. Resolve a tag (SemVer-like, tag == release)
3. Confirm required images exist locally (never builds)
4. Run `release.sh` for that tag
5. Switch services to the new tag:
   - `docker compose up -d --remove-orphans`
6. Run a post-deploy health check (frontend + backend)
7. Update state files:
   - `prev_tag` ← old `current_tag`
   - `current_tag` ← new `TAG`

### Usage
```bash
TAG=v1.2.3 doppler run -- ./deploy.sh
```

### Dry run (if supported)
```bash
TAG=v1.2.3 doppler run -- ./deploy.sh --dry-run
```

### Health check endpoints
Your deploy health check should use endpoints that **actually exist** in production, e.g.:

- Frontend: `https://$SITE_DOMAIN/`
- Backend: a stable endpoint such as:
  - `https://$API_DOMAIN/healthz` (recommended if you have it)
  - or another always-on endpoint you control (avoid expensive calls)

If the endpoint doesn’t exist, deploy will report failure even if the system is fine.

---

## Rollback

This setup is intended to make rollback simple:

1. Read rollback target:
   ```bash
   cat /var/lib/portfolio/prev_tag
   ```
2. Deploy the previous tag:
   ```bash
   TAG="$(cat /var/lib/portfolio/prev_tag)" doppler run -- ./deploy.sh
   ```

**Note:** Whether rollback is safe depends on your migrations strategy.
If you ship irreversible migrations, rollback may require manual DB intervention.

---

## Troubleshooting

### “Missing image …”
Run `build.sh` first for the same tag:
```bash
TAG=v1.2.3 doppler run -- ./build.sh
```

### “db did not become healthy”
Check DB container logs and status:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs db
```

### “release already running” / “deploy already running”
A previous run may have stalled.
Check what’s running:
```bash
ps aux | grep -E 'release.sh|deploy.sh'
```

Lock files:
- `/var/lock/portfolio-release.lock`
- `/var/lock/portfolio-deploy.lock`

---

## Operator checklist (before/after)

Before:
- Confirm you are on the correct tag: `git describe --tags --exact-match`
- Confirm Doppler environment is correct for production

After:
- Confirm FE is reachable and serving the new build
- Confirm BE endpoints behave as expected
- Confirm `current_tag` updated:
  ```bash
  cat /var/lib/portfolio/current_tag
  ```
