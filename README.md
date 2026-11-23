# 🌌 Portfolio Landing Page

Backend and infrastructure for a personal portfolio (astrophotography, travel stories, programming work). This repository holds the Django 6 backend (admin only; Python 3.14, `uv`), the Supabase Edge Function that serves the public API (`supabase/`), Docker/compose files and the operational scripts. The frontend lives in [`LukaszRemkowicz/portfolio-fe`](https://github.com/LukaszRemkowicz/portfolio-fe) (React Router 7 on Cloudflare Workers).

## 🌍 Live

- Site: [lukaszremkowicz.com](https://lukaszremkowicz.com)

## 📸 Screenshots

<details>
<summary><b>Click to expand screenshots</b></summary>

### Home Page
![Home Page](screenshots/homepage.jpg)

### Astrophotography Gallery
![Gallery](screenshots/gallery.jpg)

### Contact Form
![Contact](screenshots/contact.jpg)

</details>

## 🏗️ Architecture

Production request path: the browser talks to the Cloudflare Worker `portfolio-fe` (separate repo; SSR plus a BFF under `/app/*`), which calls the Supabase Edge Function in this repo (`supabase/functions/api`, Deno, `/v1/*`, requires the `x-origin-secret` header). The function reads Supabase Postgres 17 through the read-only role `portfolio_api` (explicit grants), answers 302 with presigned R2 URLs for originals, sends contact mail through Resend and serves the sitemap data. Public image variants come straight from the R2 bucket `portfolio-media` at `media.lukaszremkowicz.com`; the private bucket `portfolio-originals` holds sources and database backups.

![Production architecture](screenshots/architecture.svg)

- Django 6 is the admin only and is never public. It runs locally: the dev stack (`docker compose`, Django + PostgreSQL) or the released `production-be` image against Supabase through `infra/scripts/run_admin.sh`.
- The DRF/Django public API was removed (v2.25.0). Django no longer caches or invalidates API responses.
- Secrets come from Doppler.
- The former DigitalOcean VPS was retired on 2026-11-23.

More: [Supabase API and local admin](infra/docs/project/supabase_api.md).

## 🗂️ Repository Layout

- `backend/` - Django application: admin, translations, media logic, background tasks (`common/background.py`)
- `supabase/` - the Edge Function API (`functions/api`), SQL migrations for roles and grants (`migrations`) and `deploy-api.sh`
- `docker/` - Dockerfiles and entrypoint for the backend (`docker/backend/`)
- `infra/scripts/` - `run_admin.sh`, `run_local_api.sh`, DB backup scripts (`db_backup/`, local dev DB), shared helpers
- `infra/docs/` - agent docs (`agent/`) and project docs (`project/`)
- `docker-compose.yml` - dev stack (Django + PostgreSQL); `docker-compose.supabase.yml` - local production admin
- `.github/` - CI/CD workflows, secrets doc, PR templates
- `screenshots/` - README screenshots

Component docs:

- Backend: [backend/README.md](backend/README.md)
- Infra scripts: [infra/scripts/README.md](infra/scripts/README.md)

## 📖 Glossary

- `SITE_DOMAIN`: public website host, for example `lukaszremkowicz.com`.
- `ADMIN_DOMAIN`: Django admin host, `localhost` locally (the admin is not public).
- `X-Request-ID`: request correlation header. The backend reuses or creates it, echoes it in responses and logs it.

## 🖼️ Media

`MEDIA_STORAGE` selects the storage backend: `r2` (default) or `local`. Dev compose and tests use `local` (files on disk, served by Django).

In `r2` mode (code: [backend/common/storage.py](backend/common/storage.py)):

- public bucket `portfolio-media`, served at `media.lukaszremkowicz.com`: generated thumbnail and detail variants
- private bucket `portfolio-originals`: source uploads and high-resolution variants, served through short-lived presigned URLs
- secrets `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` come from Doppler (startup fails without them)

More detail: [cropper and media doc](infra/docs/project/django_admin_image_cropper_mechanism.md).

## ⚙️ Background Tasks & Caching

- Background work (translations, image processing) runs through `submit()` in [backend/common/background.py](backend/common/background.py): an in-process thread pool started after the transaction commits, with timer-based retries. There is no broker, so tasks are lost if the process stops. `BACKGROUND_TASK_WORKERS` sets the pool size (default 1). Tests run tasks inline (`BACKGROUND_TASKS_SYNC`).
- Django `DatabaseCache` (`django_cache`, `django_select2_cache`) exists for the admin only (parler, Select2). `createcachetable` runs after `migrate` (dev `be` command and `run_admin.sh`). There is no API response cache. See [cache_invalidation.md](infra/docs/project/cache_invalidation.md).

## ⚡ Quick Start

Local development is Docker Compose only; `python manage.py runserver` on the host is not a supported workflow.

Prerequisites: Docker with the Compose plugin, Doppler CLI with access to the project secrets, `/etc/hosts` access.

```bash
git clone https://github.com/LukaszRemkowicz/portfolio.git
cd portfolio
doppler login
doppler setup
```

Create the external Docker resources the local stack expects:

```bash
docker volume create portfolio_dev_db_data || true
docker volume create portfolio_dev_static_data || true
```

Start the stack (the `be` service runs migrations, `createcachetable`, message compilation and `collectstatic` on start):

```bash
doppler --config dev run -- docker compose up --build
```

Admin: `http://localhost:8000/admin/` (`/` redirects there).

Media defaults to `MEDIA_STORAGE=local` in dev compose, so no R2 credentials are needed.

```bash
curl -I http://localhost:8000/admin/login/
```

Common compose commands:

```bash
doppler --config dev run -- docker compose down
doppler --config dev run -- docker compose restart be
doppler --config dev run -- docker compose logs -f be
```

## 🧰 Useful Commands

Run from the repository root.

General pattern for Django management commands:

```bash
doppler --config dev run -- docker compose exec -T be python manage.py <command> [args]
```

Backfill responsive image variants:

```bash
# generate missing variants
doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants

# preview only
doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants --dry-run

# regenerate all variants from originals
doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants --force

# convert one object
doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants --object-id <uuid>

# convert multiple objects
doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants --object-ids <uuid1> <uuid2>
```

### Custom management commands

- `clear_cache`
  - clears the Django cache (database cache)
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py clear_cache
    ```
- `backfill_image_variants`
  - generates missing responsive `ImageVariant` rows from original images
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py backfill_image_variants
    ```
- `seed_settings`
  - creates or repairs singleton landing page settings and meteors config
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py seed_settings
    ```
- `seed_regions`
  - seeds region and sub-place data used by travel highlights
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py seed_regions
    doppler --config dev run -- docker compose exec -T be python manage.py seed_regions --dry-run
    doppler --config dev run -- docker compose exec -T be python manage.py seed_regions --retranslate
    ```
- `recalculate_landing_page_total_time_spent`
  - rebuilds per-image exposure hours (see [total time doc](infra/docs/project/landing_page_total_time_spent_system.md))
- `fix_parler_language_codes`
  - rewrites legacy `en-us` Parler translations to `en`
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py fix_parler_language_codes
    ```

### Common built-in Django commands

```bash
doppler --config dev run -- docker compose exec -T be python manage.py migrate
doppler --config dev run -- docker compose exec -T be python manage.py makemigrations
doppler --config dev run -- docker compose exec -T be python manage.py createsuperuser
doppler --config dev run -- docker compose exec -T be python manage.py shell
doppler --config dev run -- docker compose exec -T be python manage.py collectstatic --noinput
doppler --config dev run -- docker compose exec -T be python manage.py compilemessages
```

## 🧪 Testing And Checks

Canonical test run (pytest in the Docker `test` service):

```bash
cd backend && uv run test
```

Other checks:

```bash
# type checking
doppler --config dev run -- docker compose exec -T be uv run mypy .

# lint, format and tests via pre-commit
cd backend && uv run pre-commit run --all-files
```

Pre-commit runs lint, mypy and tests (see [.pre-commit-config.yaml](.pre-commit-config.yaml)). Python tool configuration lives in [backend/pyproject.toml](backend/pyproject.toml).

## 🚀 Release & Deployment

The version lives only in `backend/pyproject.toml`.

1. Merge feature PRs into `dev`.
2. Bump the version once per release (version-only commit with `[skip ci]`).
3. Open a PR `dev` -> `main` titled `Release vX.Y.Z 🚀`.
4. On merge, `.github/workflows/release.yml` creates tag `vX.Y.Z` and publishes the images to GHCR.
5. Then manually, in this order, when the release needs it:
   1. `infra/scripts/run_admin.sh [tag]` - Django migrations on Supabase (see below).
   2. Apply new `supabase/migrations/*.sql` grants (after `migrate`).
   3. Deploy the Edge Function (secrets from Doppler):

```bash
doppler run --project portfolio --config prd -- supabase/deploy-api.sh
```

The frontend deploys from its own repo CI. There is no staging environment.

### Production admin and local API

Run the production Django admin on your machine against Supabase: it pulls the newest released `production-be` image from GHCR (Doppler `prd`, Supabase DB and R2), runs migrations on start and serves http://localhost:8000/admin/ (pass a tag such as `v2.21.0` to pin a release). Stop it with Ctrl+C after background work (image variants, translations) has finished.

```bash
infra/scripts/run_admin.sh
```

Run the public API function locally against the dev compose Postgres (serves http://localhost:8001, media from `localhost:8000/media`; header `x-origin-secret: local-dev-secret`):

```bash
infra/scripts/run_local_api.sh
```

More: [supabase_api.md](infra/docs/project/supabase_api.md), [.github/SECRETS.md](.github/SECRETS.md).

## 💾 Database Backup & Maintenance

Production (Supabase) backups: `.github/workflows/supabase-maintenance.yml` pings the database every 6 hours to keep the project awake and takes a monthly encrypted `pg_dump` to `portfolio-originals/backups/supabase/` (62-day retention). Restore steps: [Keep-alive and Backups](infra/docs/project/supabase_api.md#keep-alive-and-backups). Its repo secrets are listed in [.github/SECRETS.md](.github/SECRETS.md).

The scripts in `infra/scripts/db_backup/` are for the local Docker database only:

```bash
./infra/scripts/db_backup/backup_db.sh      # compressed SQL dump
./infra/scripts/db_backup/test_restore.sh   # verify a dump in a temporary container
```

See [Backup Maintenance Guide](infra/scripts/db_backup/MAINTENANCE.md) for more details.

## 🔭 Observability

The admin (Django) logs JSON to Docker stdout locally; see [logging_structure_overview.md](infra/docs/project/logging_structure_overview.md). The Edge Function logs live in the Supabase function logs. `X-Request-ID` is echoed and logged by the Django middleware.

Log and sitemap monitoring lived in the separate `agent-monitoring` project; it is not part of this stack, so do not assume it still runs.

## 📚 Docs Index

- [backend/README.md](backend/README.md) - backend overview, security, development
- [infra/scripts/README.md](infra/scripts/README.md) - local tooling and DB backup scripts
- [infra/scripts/db_backup/MAINTENANCE.md](infra/scripts/db_backup/MAINTENANCE.md) - local database backup and restore
- [.github/SECRETS.md](.github/SECRETS.md) - GitHub secrets, variables and CI/CD
- [infra/docs/project/](infra/docs/project/) - system docs: [cache invalidation](infra/docs/project/cache_invalidation.md), [release and deploy](infra/docs/project/release_deploy_architecture.md), [logging](infra/docs/project/logging_structure_overview.md), [feature flags](infra/docs/project/feature_flag_mechanism.md), [latest image tags](infra/docs/project/latest_images_tags.md), [total time spent](infra/docs/project/landing_page_total_time_spent_system.md), [admin image cropper](infra/docs/project/django_admin_image_cropper_mechanism.md), [translations](infra/docs/project/translation_system_overview.md), [Supabase API and local admin](infra/docs/project/supabase_api.md)
- [infra/docs/agent/](infra/docs/agent/) - agent routing and engineering conventions ([AGENTS.md](AGENTS.md))
