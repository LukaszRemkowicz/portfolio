# Deploy (Build → Release → Switch)

This project uses a simple, repeatable deployment flow based on Docker images
tagged with the current git commit (`TAG`). The goal is predictable deployments
and easy rollbacks.

---

## Files

- `scripts/deploy/build.sh`
  Builds production images only (no migrations, no container restarts).

- `scripts/deploy/deploy.sh`
  Runs backend release tasks and switches running containers to the new images.

- `docker-compose.yml`
  Base (local / dev) configuration.

- `docker-compose.prod.yml`
  Production overrides and the `release` service definition.

---

## Core idea

### Image vs container

- **Image** – a built, versioned artifact (e.g. `portfolio-backend:1a2b3c4`).
- **Container** – a running instance of an image.

“Switching” means Docker Compose recreates containers so they run the image
tag specified in `docker-compose.prod.yml` (`image: ...:${TAG}`).

---

## Why the `release` step exists (backend only)

The backend performs stateful operations that must run once per deploy:

- Django database migrations (`migrate`)
- Translation compilation (`compilemessages`)
- Static files collection (`collectstatic`)

These tasks are executed via a one-off `release` service defined in
`docker-compose.prod.yml`.

Frontend does not require a release step — its production artifact (`dist`)
is already baked into the image during build.

---

## Environment variables (Doppler)

### Why Doppler is needed for both build and deploy

Your `docker-compose.prod.yml` contains many `${VAR}` entries under `environment:`
(without defaults). Docker Compose interpolates these variables when it loads
the compose file — even for `docker compose build`.

That means **any compose command** (`build`, `run`, `up`) must be executed with
those variables present in the shell environment. If your secrets live in
Doppler, you wrap the scripts with `doppler run`.

### Recommended usage (scripts)

Build images:

```bash
doppler run -- ./scripts/deploy/build.sh
```

Release + switch containers:

```bash
doppler run -- TAG=$(git rev-parse --short HEAD) ./scripts/deploy/deploy.sh
```

> If your `build.sh` already exports `TAG`, you can also run:
> `doppler run -- ./scripts/deploy/deploy.sh`
> as long as `TAG` is set consistently.

### Manual usage (no scripts)

```bash
doppler run -- bash -lc '
  TAG=$(git rev-parse --short HEAD)
  docker compose -f docker-compose.yml -f docker-compose.prod.yml build
  docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm release
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
'
```

### When you *don’t* need Doppler

If required variables are already present in the environment (CI, systemd unit,
exported in shell, etc.), you can run the scripts without `doppler run`.

---

## Standard production flow

From the repository root:

1) Build images:

```bash
doppler run -- ./scripts/deploy/build.sh
```

2) Release + switch:

```bash
doppler run -- TAG=$(git rev-parse --short HEAD) ./scripts/deploy/deploy.sh
```

---

## Rollback

Rollback is switching `TAG` to an older commit tag and recreating containers:

```bash
doppler run -- bash -lc '
  export TAG=<older_commit>
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
'
```

Old images are intentionally not removed to keep rollback simple.

---

## Notes

- Do not run migrations in the backend container `CMD`. Keep them in the
  one-off `release` step.
- Static and media files are shared via volumes so Nginx can serve `/static/`
  and `/media/` consistently.
- Keep deploy boring. Add “options” to `build.sh`, not `deploy.sh`.
