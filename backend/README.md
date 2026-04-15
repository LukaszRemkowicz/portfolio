# 🐍 Portfolio Backend

Django + DRF backend for portfolio content, admin, secure media, translations, and monitoring.


## 🚀 Features

### Core Functionality
- **Portfolio Content Models** - User profile, homepage settings, astrophotography content, and travel highlights.
- **Image Management** - `BaseImage` abstract model with automatic thumbnail generation and consistent scaling.
- **Contact System** - Contact form processing with anti-spam protection and email notifications.
- **Translations** - Multi-language content support for public portfolio data.

## 🛡️ Security Architecture

We use a defense-in-depth model across the backend, API, and admin surfaces.

### 1. Brute Force Protection (**Django Axes**)
We use [Django Axes](https://github.com/jazzband/django-axes) to protect the admin portal and API from brute-force attacks.
- Locked-out users are tracked by IP and username.
- Configurable cool-off periods and failure limits.

### 2. API Abuse Prevention (**DRF Throttling**)
Granular rate limiting is enforced across all endpoints:
- **Anonymous Throttling**: Limits unauthenticated users.
- **Contact Form Throttling**: Specialized 5-per-hour limit to prevent spam.
- **Method Restriction**: Critical ViewSets (like Contact/Users) explicitly restrict HTTP verbs to the bare minimum (e.g., POST-only or GET-only).

### 3. Dependency Scanning (**Safety**)
We use [Safety](https://github.com/pyupio/safety) to scan our dependencies for known vulnerabilities.
- Integrated into the CI/CD pipeline and available via `uv run security`.

### 4. Infrastructure Security
- **Non-Root Execution**: Docker containers run under a restricted `appuser`.
- **Environment Isolation**: Secure configuration via `django-environ`.
- **Docker-Locked Environment**: Verified multi-stage builds and restricted `.dockerignore`.

### Technical Features
- **Modern Stack** - Python 3.13, Django 6.0, and `uv` for dependency management.
- **Caching** - Redis-backed caching for Django Select2 and internal performance.
- **Error Tracking** - Sentry integration for production monitoring and telemetry.
- **Internationalization (i18n)** - Multi-language support (EN/PL) with automatic message compilation.
- **Docker Integration** - Multi-stage builds with automated static collection.

### Prerequisites
- **Docker & Docker Compose**
- **Python 3.13** *(optional, only if you want to run `uv`/manual host commands)*
- **uv** *(optional, only if you want to run `uv`/manual host commands)*


## 🧭 Backend Role In The Current Architecture

Today it mainly serves as:

- content owner for portfolio data
- admin application on `ADMIN_DOMAIN`
- internal API consumed by the frontend server
- secure media signer / backend partner for nginx protected media
- source of truth for sitemap and SEO-backed dynamic URLs

Normal public website traffic reaches the frontend server first. Django is the content/admin/internal API layer.

## 📖 Glossary

- `SITE_DOMAIN`: public website host.
- `ADMIN_DOMAIN`: public Django admin host.
- `X-Request-ID`: request correlation header used for tracing requests across services.

## 🧱 Backend Responsibilities

- portfolio content models:
  - astrophotography
  - travel highlights
  - background images
  - user profile
- translation workflows
- secure media signing and `X-Accel-Redirect` cooperation with nginx
- contact form processing
- monitoring and daily log analysis
- cache invalidation signals for frontend cache

## 🔌 Service Integration

Key points:

- backend serves content and API responses over internal service networking
- backend emits cache invalidation webhooks after relevant content changes
- backend cooperates with nginx for protected media delivery
- backend provides sitemap and dynamic content data consumed by the frontend server

Invalidation is triggered from model save/delete signals after transaction commit.

## 🛡️ Security / Delivery Model

Public media delivery and protected media delivery are split between Django and nginx.

Protected media flow:

- Django signs or authorizes access
- nginx serves bytes through `X-Accel-Redirect`

So:

- Django owns access control and URL decisions
- nginx owns efficient file delivery

## 📈 Observability

What exists:

- FE generates or forwards `X-Request-ID`
- backend middleware reuses or creates request IDs
- backend responses echo `X-Request-ID`
- backend logs include:
  - request ID
  - method
  - path
  - status
  - duration
  - host

Middleware path:

- [backend/common/middleware.py](common/middleware.py)

## 🤖 Monitoring

Monitoring includes frontend, backend, nginx, and traefik logs.

Daily monitoring pipeline:

1. host cron collects Docker logs
2. backend monitoring app reads pre-collected log files
3. LLM summarizes findings
4. analysis is stored in Django admin and emailed

Collected log groups:

- `backend.log`
- `frontend.log`
- `nginx_access.log`
- `nginx_runtime.log`
- `traefik_access.log`
- `traefik_runtime.log`

## 🛠️ Development

Local backend development is handled through Docker Compose, not a standalone `python manage.py runserver` workflow.

Start or rebuild the stack from the repository root:

```bash
doppler --config dev run -- docker compose up --build
```

Useful backend commands:

```bash
# backend logs
doppler --config dev run -- docker compose logs -f be

# restart only the backend container
doppler --config dev run -- docker compose restart be

# backend management commands
doppler --config dev run -- docker compose exec -T be python manage.py migrate
doppler --config dev run -- docker compose exec -T be python manage.py compilemessages

# backend checks
doppler --config dev run -- docker compose exec -T be uv run pytest
doppler --config dev run -- docker compose exec -T be uv run mypy .
doppler --config dev run -- docker compose exec -T be uv run pre-commit run --all-files
```

### 🧰 Manual Commands

If you need more control or want to run tools individually on your host, these are optional host-side commands and require local `uv`/Python setup:

```bash
# run pytest with custom arguments on the host
uv run pytest -v

# run linters and formatters on the host
uv run pre-commit run --all-files
```

## 🐳 Docker Integration (Recommended)

### 🚀 Deployment

```bash
# run from the project root with centralized secrets.
# choose the proper Doppler config for the target environment,
# for example: --config dev, --config stg, or --config prod
doppler --config dev run -- docker compose up --build
```

## 🗂️ Important Backend Areas

- settings and singleton config:
  - [backend/core/models.py](core/models.py)
- astrophotography domain:
  - [backend/astrophotography/models.py](astrophotography/models.py)
- user/profile domain:
  - [backend/users/models.py](users/models.py)
- monitoring:
  - [backend/monitoring/services.py](monitoring/services.py)

## 📝 Notes

- Django still owns sitemap generation and should remain the source of truth for dynamic public URLs.
- The backend public API host should be treated as internal/administrative architecture, not the main browser contract.



## 🗄️ Database Maintenance

We provide specialized "God-Tier" scripts for automated database backups and restore verification.

- **Atomic Backups**: `infra/scripts/db_backup/backup_db.sh` creates validated, timestamped dumps with overlap protection.
- **Restore Verification**: `infra/scripts/db_backup/test_restore.sh` automatically verifies that backups are healthy by performing a full restore in a temporary container.

> [!TIP]
> For detailed instructions on configuration (Doppler/Env), retention policies, and restore procedures, see the [Database Maintenance Guide](../infra/scripts/db_backup/MAINTENANCE.md).

##  TODO - Backend Improvements

### 📸 Features & Processing
- [ ] Prettify email messages (add HTML template)

### 🚀 API & Reliability
- [ ] **Structured Logging** - Implement JSON structured logs for production
