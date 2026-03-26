# 🌌 Portfolio Landing Page

Personal portfolio web app for astrophotography, travel stories, and programming work. The stack is:

- frontend SSR server: React + TypeScript
- backend: Django + DRF
- edge/static layer: nginx
- local/server routing: Traefik
- secrets: Doppler

## 🌍 Live

- Site: [lukaszremkowicz.com](https://lukaszremkowicz.com)

## 🗂️ Repository Layout

- `frontend/` - React + TypeScript app, SSR runtime, browser app, tests, and public assets
- `backend/` - Django + DRF application, admin, Celery jobs, monitoring, and media logic
- `docker/` - Dockerfiles and entrypoints for frontend, backend, redis, nginx, and traefik
- `infra/` - nginx templates, traefik config, release scripts, monitoring scripts, and ops docs
- `screenshots/` - README screenshots

Component docs:

- Frontend: [frontend/README.md](frontend/README.md)
- Backend: [backend/README.md](backend/README.md)
- Infra scripts: [infra/scripts/README.md](infra/scripts/README.md)

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

The project follows a modern, highly decoupled architecture for performance and security. It supports **Environment Isolation** (Production & Staging) on the server, with an identical stack for **Development** (Local):

![Architecture Illustration](infra/docs/architecture.png)

### Key Components:
- **Traefik (Edge Proxy)**: The central entry point for all subdomains. Handles SSL, HSTS, and routing.
- **Environment Isolation**: Parallel stacks (`PROD` and `STAGE`) ensure zero-collision deployments.
- **Development Stack**: Local development uses the same core `Nginx + Frontend SSR + Django + PostgreSQL` architecture via `portfolio-dev`. Traefik is also available locally through an optional Compose profile when you want to mirror the full edge setup.
- **Doppler**: Centralized, secure secret management across **all** environments (Local & Server).


Current request flow:

1. browser requests `SITE_DOMAIN`
2. nginx receives the public request
3. nginx either serves public static/media directly or proxies the request to the frontend SSR server
4. frontend SSR renders the page and fetches backend data internally when needed
5. browser hydrates with server-provided React Query state

Application structure:

- public page URLs are the normal website addresses used by users, search engines, and the sitemap
- the browser uses `SITE_DOMAIN` as its public application host
- Django remains the content owner and still handles sitemap generation

## 📖 Glossary

- `SSR`: Server-Side Rendering. The frontend server renders HTML before it reaches the browser.
- `BFF`: Backend For Frontend. A frontend-owned server layer that the browser talks to instead of calling backend APIs directly.
- `SITE_DOMAIN`: Public website host, for example `portfolio.local`.
- `ADMIN_DOMAIN`: Public Django admin host, for example `admin.portfolio.local`.
- `API`: Internal backend API contract used by the frontend server and Django admin integrations.

## 🧭 Architecture Overview

### Public entrypoints

- `SITE_DOMAIN`
  - public website
  - SSR HTML
  - FE-owned transport endpoints for the remaining interactive browser flows
  - public media served by nginx
- `ADMIN_DOMAIN`
  - Django admin

### Traefik Role

- In staging and production, Traefik is the external edge proxy in front of nginx.
- It handles host-based routing, TLS termination, and security middleware at the edge.
- In local development, Traefik is available through an optional Compose profile when you want to mirror the full edge setup.
- The default local stack can also run directly through nginx without Traefik.

### Frontend server responsibilities

- SSR page rendering
- request/data composition for page-shell content
- BFF transport for the remaining browser JSON flows
- public environment injection into HTML
- structured logging and request correlation
- in-memory SSR shell cache

### Backend responsibilities

- content ownership and business logic
- admin application
- internal API used by FE
- sitemap generation
- secure media authorization/signing
- monitoring and analysis
- cache invalidation webhooks to FE

### Media Delivery

Public-safe media is served directly by nginx on `SITE_DOMAIN`.

Protected media uses a split flow:

- Django signs or authorizes access
- nginx serves file bytes through `X-Accel-Redirect`

### Caching

The frontend SSR server keeps a `24h` in-memory cache for shared shell data:

- `settings`
- `profile`
- `background`
- `travel-highlights`
- `latest-astro-images`

The backend invalidates those FE cache tags through an internal webhook after content changes.

### Observability

The stack uses request correlation across FE and BE:

- FE generates or forwards `X-Request-ID`
- FE logs include `request_id`
- FE forwards `X-Request-ID` to BE
- BE echoes and logs the same request ID

## ⚡ Quick Start

Local development is Docker Compose only. This project is not maintained as a standalone `manage.py runserver` / `npm start` workflow.

### ✅ Prerequisites

- Docker with the Compose plugin
- Doppler CLI with access to the project secrets
- `openssl` for generating local self-signed certificates
- `/etc/hosts` access for local domain mapping

### 1. Clone

```bash
git clone <your-repo-url>
cd landingpage
```

### 2. Configure secrets with Doppler

```bash
doppler login
doppler setup
```

### 3. Bootstrap local Docker resources

The local Compose stack expects these external Docker resources to already exist:

```bash
docker network create traefik_proxy || true
docker volume create portfolio_dev_db_data || true
docker volume create portfolio_dev_fe_node_modules || true
docker volume create portfolio_dev_static_data || true
```

Generate local TLS certificates used by nginx:

```bash
./infra/scripts/nginx/generate-cert.sh
```

### 4. Configure local hosts

Add these entries to `/etc/hosts`:

```text
127.0.0.1 portfolio.local
127.0.0.1 admin.portfolio.local
127.0.0.1 api.portfolio.local
```

### 5. Start local stack

```bash
doppler --config dev run -- docker compose up --build
```

Local hosts:

- Site: `https://portfolio.local/`
- Admin: `https://admin.portfolio.local/`
- API: `https://api.portfolio.local/` (still available as a backend host, but no longer the normal browser-facing application entrypoint)
- Django health endpoint: `http://127.0.0.1:8000/health`
- Flower: `http://127.0.0.1:5555/`

### 6. Verify local services

```bash
curl -k https://portfolio.local/
curl -k https://admin.portfolio.local/
curl -fsS http://127.0.0.1:8000/health
```

## 🛠️ Local Development

Use Docker Compose for all normal local work:

```bash
doppler --config dev run -- docker compose up --build
```

Common commands:

```bash
# stop the stack
doppler --config dev run -- docker compose down

# restart one service
doppler --config dev run -- docker compose restart fe

# show logs
doppler --config dev run -- docker compose logs -f fe be nginx

# run backend management commands
doppler --config dev run -- docker compose exec -T be python manage.py migrate

# run frontend checks
doppler --config dev run -- docker compose exec -T fe npm run type-check
```

## 🧰 Useful Commands

Run everything from the repository root unless noted otherwise.

### Frontend

Clear the FE SSR cache without restarting the service:

```bash
doppler --config dev run -- docker compose exec -T fe sh -lc 'cd /app && npm run cache:clear:ssr'
```

Clear only selected SSR cache tags:

```bash
doppler --config dev run -- docker compose exec -T fe sh -lc 'cd /app && npm run cache:clear:ssr -- profile travel-highlights'
```

Clear all known SSR cache tags:

```bash
doppler --config dev run -- docker compose exec -T fe sh -lc 'cd /app && npm run cache:clear:ssr -- --all-tags'
```

### Backend

General pattern for Django management commands:

```bash
doppler --config dev run -- docker compose exec -T be python manage.py <command> [args]
```

Clear the full Django cache:

```bash
doppler --config dev run -- docker compose exec -T be python manage.py clear_cache
```

Convert stored images to WebP:

```bash
# convert everything
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp

# preview only
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp --dry-run

# reconvert already-converted images from originals
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp --force

# convert one object
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp --object-id <uuid>

# convert multiple objects
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp --object-ids <uuid1> <uuid2>

# override output size for a run
doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp --dimension-percentage 50
```

Regenerate thumbnails:

```bash
doppler --config dev run -- docker compose exec -T be python manage.py regenerate_thumbnails
doppler --config dev run -- docker compose exec -T be python manage.py regenerate_thumbnails --force
```

### Custom management commands in this repository

- `clear_cache`
  - clears the active Django cache backend
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py clear_cache
    ```
- `convert_images_to_webp`
  - batch-converts stored images to WebP and preserves rollback originals
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py convert_images_to_webp
    ```
- `regenerate_thumbnails`
  - rebuilds thumbnails using current thumbnail settings
  - run:
    ```bash
    doppler --config dev run -- docker compose exec -T be python manage.py regenerate_thumbnails
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

Optional local profile:

- `docker compose --profile traefik up --build` starts `nginx-traefik` so local routing can run through Traefik instead of binding nginx directly to ports `80/443`.

Standalone local development commands such as `python manage.py runserver` or `npm run dev` are not the supported workflow described by this repository.

## 🧪 Testing And Checks

Typical project checks:

```bash
# frontend type checks and linting
doppler --config dev run -- docker compose exec -T fe npm run type-check
doppler --config dev run -- docker compose exec -T fe npm run lint

# frontend unit tests
doppler --config dev run -- docker compose exec -T fe npm test -- --runInBand

# frontend e2e tests
doppler --config dev run -- docker compose exec -T fe npm run test:e2e

# backend test suite
doppler --config dev run -- docker compose exec -T be poetry run pytest

# backend static analysis
doppler --config dev run -- docker compose exec -T be poetry run mypy .
```

Compose also exposes dedicated test services:

```bash
doppler --config dev run -- docker compose --profile test run --rm fe-test
doppler --config dev run -- docker compose --profile test run --rm test
```

## 🚀 Deployment

Typical release flow:

```bash
# Build images
doppler run -p portfolio -c portfolio-prod -- ./infra/scripts/release/build.sh

# Deploy on server
doppler run -p portfolio -c portfolio-prod -- ./infra/scripts/release/deploy.sh
```

Production/stage deploys rebuild:

- `fe` when SSR/public env changes
- `nginx` when routing or public media rules change
- `be` when invalidation, serializers, or backend routes change

## 🔧 Operations

### 📈 Monitoring

Monitoring analyses:

- backend logs
- frontend SSR/BFF logs
- nginx logs
- traefik logs collected on host and analyzed with the daily report

Collector docs:

- [infra/scripts/monitoring/README.md](infra/scripts/monitoring/README.md)

## 📝 Notes

- Active Node scripts live in [frontend/package.json](frontend/package.json).
- Python dependency and tool configuration live in [backend/pyproject.toml](backend/pyproject.toml).
- Local startup runs Django migrations, `seed_settings`, message compilation, and `collectstatic` automatically as part of the `be` service command.

### Cache Invalidation

Frontend SSR cache covers shared shell data:

- `settings`
- `profile`
- `background`
- `travel-highlights`
- `latest-astro-images`

Backend invalidates this cache through an internal FE webhook after content changes.

### Frontend Views

The frontend server mirrors Django's `views` concept in its server-side ownership model:

- server-side FE request/data ownership lives in `frontend/server/views/*`
- SSR and BFF routes should reuse those views instead of duplicating transport logic
- low-level HTTP clients stay separate from request/data contract ownership


## 💾 Database Backup & Maintenance

Database maintenance scripts are located in `infra/scripts/db_backup/`.

### 1. Manual Backup
Create a compressed SQL dump of the production database:
```bash
./infra/scripts/db_backup/backup_db.sh
```
The backup should be stored outside the repository, for example in `/var/backups/portfolio/`.

### 2. Testing Restores
Always verify your backups by running a test restore:
```bash
./infra/scripts/db_backup/test_restore.sh
```
This script creates a temporary container and verifies that the SQL dump is valid and can be fully imported.

See [Backup Maintenance Guide](infra/scripts/db_backup/MAINTENANCE.md) for more details.

## Testing

### Backend (Dedicated Service)
The backend tests now run in a dedicated, isolated environment using Docker Compose Profiles. This inherits your development configuration but remains isolated.

```bash
doppler --config dev run -- docker compose run --rm test
```

### Frontend
```bash
doppler --config dev run -- docker compose exec -T fe npm test -- --watchAll=false
doppler --config dev run -- docker compose run --rm fe-test
```

## 🔄 Release Lifecycle

To ensure version traceability and zero-downtime, follow this mandatory flow for all new features and fixes:

### 1. Development to Dev
- **Merge Request**: Create an MR from your feature branch to `dev`.
- **Squash & Delete**: Perform a **Squash and Merge** and delete the feature branch to keep history clean.

### 2. Versioning (Tags)
- **Tag the Commit**: Once code is on `dev`, tag it with a version (e.g., `v1.2.0`).
- **Push Tag**: `git push origin v1.2.0`
- **Automatic Detection**: The `build.sh` and `deploy.sh` scripts automatically detect this tag and use it as the Docker image reference.

### 3. Promotion to Main
- **Merge Request**: Merge `dev` into `main`.
- **Production Anchor**: This ensures `main` always stable and aligned with a specific Git tag.

### 4. Direct Deployment
On your production server, simply run:
```bash
# TAG is auto-detected from the Git tag on main
./infra/scripts/release/deploy.sh
```

> [!IMPORTANT]
> **Production Requirement**: Deployments **must** use a Git tag as the reference. This allows for instant rollbacks by just changing the `TAG` variable.

---


## Component Docs

- Frontend: [frontend/README.md](frontend/README.md)
- Backend: [backend/README.md](backend/README.md)


### TODO:
- add script for checking sitemap
- Admin improve
- add ci registry
- Add email template
- Fix issues with "go back" on the website (Fe)
- fix small visual issues in django admin
- Agent check structured data + move prompts to yaml or md add skills. Add function, which llm could use to get proper prompt? Make agent more agent, not like a function. Rebuild response with userID, ID session, speed reasoning.
