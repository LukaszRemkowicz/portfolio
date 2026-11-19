# 🐍 Portfolio Backend

Django backend for portfolio content, admin, secure media, and translations. The public API lives in the Supabase Edge Function (`supabase/functions/api`).


## 🚀 Features

### Core Functionality
- **Portfolio Content Models** - User profile, homepage settings, astrophotography content, and travel highlights.
- **Image Management** - `BaseImage` abstract model with automatic thumbnail generation and consistent scaling.
- **Contact System** - Contact messages stored and managed in the admin (the public form is handled by the Supabase function).
- **Translations** - Multi-language content support for public portfolio data.

### Travel destinations

In Places, choose **Country**, **Place**, or **Region**. A country destination is
stored as a non-region Place with a country code and an empty source-language name.
Use the **+** beside a travel highlight's Destination selector to add one (for
example Spain). The admin prevents duplicate country destinations in this workflow.

Regions retain an editable, optional country: Bieszczady can have Poland and
sub-places such as Lutowiska and Wetlina. A region spanning several countries can
leave its own country blank. Sub-places may be specific places, countries, or
nested regions. Country nodes include every image location in that country;
named places include their own images. A region includes its own images and its
children, or falls back to its country when no children are configured. A region
without a country or children includes only images directly assigned to it.

The admin and travel detail page share geographic filtering. The admin offers
all matching dates and retains previously selected images/backgrounds. The detail
page automatically includes matching images within the trip's stored date range
(respecting its exclusive upper bound), plus explicitly selected images regardless
of date or destination. If only certain stops should be included, use a region
with those sub-places rather than a country destination.

Saving a Place also refreshes linked travel slugs in the source language. Previous
country/place slug pairs are stored as aliases, so existing links continue to work.
Canonical matches take precedence; an ambiguous alias returns 404. Date changes
are not versioned by these aliases. (Historical: migration `0022_mainpagelocation_legacy_slugs`
had to run before code using these aliases was deployed; it is long applied.)

(Historical) The known record, Place 53, was repaired to Poland by an earlier release;
releases no longer run this step. For a manual repair, preview the exact change first (run inside the backend
environment, e.g. the local production admin container):

```bash
python manage.py repair_travel_place --place-id 53 --country PL
python manage.py repair_travel_place --place-id 53 --country PL --apply
```

The first command writes nothing; `--apply` repairs that Place, refreshes its
linked highlights, and retains previous URL aliases. Verify the place ID before
applying. The command does not infer countries for other regions or change translated text.

Travel highlight text uses the requested language, then English, and never an
arbitrary third language. An empty English Highlight Title stays empty in the API,
allowing the frontend's localized default subtitle. Other models retain their
existing translation fallback policy. A previously lost English title must be
restored from its source; clearing caches does not reconstruct it.

## 🛡️ Security Architecture

We use a defense-in-depth model across the backend, API, and admin surfaces.

### 1. Brute Force Protection (**Django Axes**)
We use [Django Axes](https://github.com/jazzband/django-axes) to protect the Django admin login from brute-force attacks. The public API is not served by Django.
- Locked-out users are tracked by IP and username.
- Configurable cool-off periods and failure limits.

### 2. Dependency Scanning (**Safety**)
We use [Safety](https://github.com/pyupio/safety) to scan our dependencies for known vulnerabilities.
- Integrated into the CI/CD pipeline and available via `uv run security`.

### 3. Infrastructure Security
- **Non-Root Execution**: Docker containers run under a restricted `appuser`.
- **Environment Isolation**: Secure configuration via `django-environ`.
- **Docker-Locked Environment**: Verified multi-stage builds and restricted `.dockerignore`.

### Technical Features
- **Modern Stack** - Python 3.14, Django 6.0, and `uv` for dependency management.
- **Caching** - Database-backed caching (Django `DatabaseCache`, tables created by `manage.py createcachetable`) for Django Select2. Background work (emails, translations, image processing) runs in an in-process thread pool (`common/background.py`).
- **Error Tracking** - Sentry integration for production monitoring and telemetry.
- **Internationalization (i18n)** - Multi-language support (EN/PL) with automatic message compilation.
- **Docker Integration** - Multi-stage builds with automated static collection.

### Prerequisites
- **Docker & Docker Compose**
- **Python 3.14** *(optional, only if you want to run `uv`/manual host commands)*
- **uv** *(optional, only if you want to run `uv`/manual host commands)*


## 🧭 Backend Role In The Current Architecture

Today it mainly serves as:

- content owner for portfolio data
- admin application, run locally (dev stack at http://localhost:8000/admin/, or the released image against Supabase via `infra/scripts/run_admin.sh`); it is never public
- secure media signer for admin previews

Public website traffic goes browser -> Cloudflare Worker (`portfolio-fe`) -> Supabase Edge Function; Django is not in that path. Django is the content/admin layer.

## 📖 Glossary

- `SITE_DOMAIN`: public website host.
- `ADMIN_DOMAIN`: Django admin host (`localhost` locally; the admin is not public).
- `X-Request-ID`: request correlation header used for tracing requests across services.

## 🧱 Backend Responsibilities

- portfolio content models:
  - astrophotography
  - travel highlights
  - background images
  - user profile
- translation workflows
- secure media signing for admin previews
- contact message storage and admin

## 🔌 Service Integration

Key points:

- public API and sitemap are served by the Supabase Edge Function (`supabase/functions/api`, see [supabase_api.md](../infra/docs/project/supabase_api.md))


## 🛡️ Security / Delivery Model

Protected (admin) media flow:

- Django checks staff status and the signed URL
- on R2 (production) it redirects to a short-lived presigned URL
- on local storage (dev, tests) it streams the file itself

## 📈 Observability

What exists:

- backend middleware reuses or creates request IDs (admin requests only; there is no FE -> Django request path)
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

Backend log and sitemap report inspection now belongs to the standalone
`agent-monitoring` project. This backend emits application logs; the sitemap is
served by the Supabase function. It no longer contains the legacy Django monitoring app,
report models, admin report actions, or monitoring migrations.

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

Production runs the released `production-be` image through `infra/scripts/run_admin.sh [tag]` (Doppler `prd`, Supabase DB and R2; migrations run on start). The release order (migrations, Supabase grants, Edge Function deploy) is in [supabase_api.md](../infra/docs/project/supabase_api.md) and the root [README](../README.md). Local development:

```bash
# run from the project root with centralized secrets (Doppler config: dev)
doppler --config dev run -- docker compose up --build
```

## 🗂️ Important Backend Areas

- settings and singleton config:
  - [backend/core/models.py](core/models.py)
- astrophotography domain:
  - [backend/astrophotography/models.py](astrophotography/models.py)
- user/profile domain:
  - [backend/users/models.py](users/models.py)

## 📝 Notes

- Django serves no public traffic; the browser contract is the Cloudflare Worker plus the Supabase Edge Function.



## 🗄️ Database Maintenance

Production (Supabase) backups are the monthly encrypted dump of the `supabase-maintenance` workflow (see "Keep-alive and Backups" in [supabase_api.md](../infra/docs/project/supabase_api.md)). The scripts below are for the local Docker database and the stopped VPS Postgres.

- **Atomic Backups**: `infra/scripts/db_backup/backup_db.sh` creates validated, timestamped dumps with overlap protection.
- **Restore Verification**: `infra/scripts/db_backup/test_restore.sh` automatically verifies that backups are healthy by performing a full restore in a temporary container.

> [!TIP]
> For detailed instructions on configuration (Doppler/Env), retention policies, and restore procedures, see the [Database Maintenance Guide](../infra/scripts/db_backup/MAINTENANCE.md).

##  TODO - Backend Improvements

### 📸 Features & Processing
- [ ] Prettify email messages (add HTML template)

### 🚀 API & Reliability
- [ ] **Structured Logging** - Implement JSON structured logs for production
