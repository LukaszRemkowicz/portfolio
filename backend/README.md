# Portfolio Backend

Django + DRF backend for portfolio content, admin, secure media, translations, and monitoring.

## Backend Role In The Current Architecture

Today it mainly serves as:

- content owner for portfolio data
- admin application on `ADMIN_DOMAIN`
- internal API consumed by the frontend server
- secure media signer / backend partner for nginx protected media
- source of truth for sitemap and SEO-backed dynamic URLs

Normal public website traffic reaches the frontend server first. Django is the content/admin/internal API layer.

## Glossary

- `SITE_DOMAIN`: public website host.
- `ADMIN_DOMAIN`: public Django admin host.
- `X-Request-ID`: request correlation header used for tracing requests across services.

## Backend Responsibilities

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

## Service Integration

Key points:

- backend serves content and API responses over internal service networking
- backend-generated media URLs are normalized onto `SITE_DOMAIN` at the frontend layer
- backend emits cache invalidation webhooks after relevant content changes

Invalidation is triggered from model save/delete signals after transaction commit.

## Security / Delivery Model

Public media delivery and protected media delivery are split between Django and nginx.

Protected media flow:

- Django signs or authorizes access
- nginx serves bytes through `X-Accel-Redirect`

So:

- Django owns access control and URL decisions
- nginx owns efficient file delivery

## Observability

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

- [backend/common/middleware.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/middleware.py)

## Monitoring

Monitoring includes frontend, backend, and nginx logs.

Daily monitoring pipeline:

1. host cron collects Docker logs
2. backend monitoring app reads pre-collected log files
3. LLM summarizes findings
4. analysis is stored in Django admin and emailed

Collected log groups:

- `backend.log`
- `frontend.log`
- `nginx.log`
- `traefik.log`

## Development

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
doppler --config dev run -- docker compose exec -T be poetry run pytest
doppler --config dev run -- docker compose exec -T be poetry run mypy .
doppler --config dev run -- docker compose exec -T be pre-commit run --all-files
```

## Important Backend Areas

- settings and singleton config:
  - [backend/core/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/models.py)
- astrophotography domain:
  - [backend/astrophotography/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/astrophotography/models.py)
- user/profile domain:
  - [backend/users/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/users/models.py)
- monitoring:
  - [backend/monitoring/services.py](/Users/lukaszremkowicz/Projects/landingpage/backend/monitoring/services.py)

## Notes

- Django still owns sitemap generation and should remain the source of truth for dynamic public URLs.
- The backend public API host should be treated as internal/administrative architecture, not the main browser contract.
