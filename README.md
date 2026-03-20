# Portfolio Landing Page

Personal portfolio web app for astrophotography, travel stories, and programming work. The stack is:

- frontend SSR server: React + TypeScript
- backend: Django + DRF
- edge/static layer: nginx
- local/server routing: Traefik
- secrets: Doppler

## Live

- Site: [lukaszremkowicz.com](https://lukaszremkowicz.com)

## Current Architecture

Current request flow:

1. browser requests `SITE_DOMAIN`
2. frontend SSR server renders the page
3. frontend server fetches backend data internally
4. nginx serves public static/media files directly
5. browser hydrates with server-provided React Query state

Application structure:

- public page URLs are the normal website addresses used by users, search engines, and the sitemap
- the browser uses `SITE_DOMAIN` as its public application host
- Django remains the content owner and still handles sitemap generation

## Glossary

- `SSR`: Server-Side Rendering. The frontend server renders HTML before it reaches the browser.
- `BFF`: Backend For Frontend. A frontend-owned server layer that the browser talks to instead of calling backend APIs directly.
- `SITE_DOMAIN`: Public website host, for example `portfolio.local`.
- `ADMIN_DOMAIN`: Public Django admin host, for example `admin.portfolio.local`.
- `API`: Internal backend API contract used by the frontend server and Django admin integrations.

## Architecture Overview

### Public entrypoints

- `SITE_DOMAIN`
  - public website
  - SSR HTML
  - FE-owned transport endpoints for the remaining interactive browser flows
  - public media served by nginx
- `ADMIN_DOMAIN`
  - Django admin

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

## Quick Start

Local development is Docker Compose only. This project is not maintained as a standalone `manage.py runserver` / `npm start` workflow.

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

### 3. Start local stack

```bash
doppler --config dev run -- docker compose up --build
```

Local hosts:

- Site: `https://portfolio.local/`
- Admin: `https://admin.portfolio.local/`

Recommended `/etc/hosts` entries:

```text
127.0.0.1 portfolio.local
127.0.0.1 admin.portfolio.local
```

### 4. Verify local services

```bash
curl -k https://portfolio.local/
curl -k https://admin.portfolio.local/
```

## Local Development

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

Standalone local development commands such as `python manage.py runserver` or `npm run dev` are not the supported workflow described by this repository.

## Deployment

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

## Operations

### Monitoring

Monitoring analyses:

- backend logs
- frontend SSR/BFF logs
- nginx logs
- traefik logs collected on host

Collector docs:

- [infra/scripts/monitoring/README.md](/Users/lukaszremkowicz/Projects/landingpage/infra/scripts/monitoring/README.md)

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

## Component Docs

- Frontend: [frontend/README.md](/Users/lukaszremkowicz/Projects/landingpage/frontend/README.md)
- Backend: [backend/README.md](/Users/lukaszremkowicz/Projects/landingpage/backend/README.md)
