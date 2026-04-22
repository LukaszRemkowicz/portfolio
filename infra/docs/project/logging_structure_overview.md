# Logging Structure Overview

## Purpose

This document describes the current logging structure across the portfolio stack and clarifies which components already emit JSON logs versus plain-text logs.

It is intended as:

- a current-state reference for future logging work,
- an operational guide for reading logs across backend, frontend, nginx, and Traefik,
- a baseline for future log normalization and ingestion work.

Current state verified on 2026-04-17.

## Short Answer

Current JSON logging status:

- Backend Django app: yes, JSON to Docker stdout
- Frontend SSR request logs: yes, JSON to Docker stdout
- Nginx access logs: yes, JSON to file and Docker stdout
- Traefik access logs: yes, JSON to file
- Traefik runtime logs: yes, JSON
- Frontend SSR startup/error logs: yes, JSON

Current plain-text / non-JSON areas:

- Backend startup / any non-logging `print` usage: possible plain text
- Nginx error logs: plain text
- Shell entrypoint scripts: plain text

So the stack is partially normalized, but not fully JSON everywhere yet.

## Component Status

## 1. Backend Django

### Current format

Backend application logs now use JSON through Django logging configuration in:

- [backend/settings/base.py](/Users/lukaszremkowicz/Projects/landingpage/backend/settings/base.py:421)
- [backend/common/utils/logging.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/utils/logging.py:1)

The backend writes logs to standard output through the console handler, which means Docker captures them directly.

### Current structured fields

The backend JSON formatter currently emits fields such as:

- `timestamp`
- `level`
- `logger`
- `module`
- `function`
- `line`
- `process`
- `thread`
- `message`
- `environment`

When the log happens during an HTTP request, it also includes:

- `request_id`
- `request_method`
- `request_path`
- `request_host`

Some log lines also include extra fields such as:

- `status_code`
- `duration_ms`
- `exception`

### Backend app / logger namespaces

The current Django logging config explicitly configures these backend app namespaces:

- `common`
- `core`
- `users`
- `shop`
- `monitoring`
- `translation`
- `astrophotography`
- `programming`
- `django`
- `django.request`
- `django.server`
- `django.db.backends`
- `celery`

Each of the app namespaces above currently uses the same JSON formatter and the same stdout handler.

That means the log structure is consistent across those apps:

- `timestamp`
- `level`
- `logger`
- `module`
- `function`
- `line`
- `process`
- `thread`
- `message`
- `environment`

### How logs are structured for specific backend apps

#### `common`

Typical purpose:

- shared services
- email task dispatch
- SSR cache invalidation
- shared image-processing workflow

Common log shape:

- base JSON fields
- optional request context when called in-request
- optional task/service extras such as:
  - `status_code`
  - `duration_ms`
  - custom `extra={...}` values

Examples live in:

- [backend/common/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/tasks.py:1)
- [backend/common/ssr_cache.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/ssr_cache.py:1)
- [backend/common/image_processing.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/image_processing.py:1)

#### `core`

Typical purpose:

- shared domain infrastructure
- `BaseImage` lifecycle
- cache services

#### `scripts`

Typical purpose:

- release-time backend orchestration
- rollout-only startup hooks

These modules emit structured logs through the normal app-level namespace configuration, for example:

- [backend/common/image_processing.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/image_processing.py:1)
- [backend/core/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/models.py:1)
- [backend/core/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/tasks.py:1)
- [backend/core/management/commands/backfill_baseimage_fields.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/management/commands/backfill_baseimage_fields.py:1)
- shared image task compatibility wrapper

Common log shape:

- base JSON fields
- optional request context
- model/task specific extras when provided

Examples live in:

- [backend/core/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/models.py:1)
- [backend/core/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/tasks.py:1)
- [backend/core/cache_service.py](/Users/lukaszremkowicz/Projects/landingpage/backend/core/cache_service.py:1)

#### `users`

Typical purpose:

- profile/user image lifecycle
- user/profile admin or API logic

Common log shape:

- base JSON fields
- request context when logs happen during HTTP request flow
- cache invalidation or image-processing related extras when provided

Examples live in:

- [backend/users/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/users/models.py:1)
- [backend/users/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/users/tasks.py:1)

#### `shop`

Typical purpose:

- shop settings image lifecycle
- product/shop API and admin logic

Common log shape:

- base JSON fields
- request context when logs happen during HTTP request flow
- image-processing extras when provided

Examples live in:

- [backend/shop/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/shop/models.py:1)
- [backend/shop/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/shop/tasks.py:1)

#### `monitoring`

Typical purpose:

- log analysis
- sitemap analysis
- monitoring agent/tool-loop execution

Common log shape:

- base JSON fields
- usually no request context, because many logs are task/background-job based
- monitoring-specific free-form messages and any explicit extra fields

Examples live in:

- [backend/monitoring/tasks.py](/Users/lukaszremkowicz/Projects/landingpage/backend/monitoring/tasks.py:1)
- [backend/monitoring/services.py](/Users/lukaszremkowicz/Projects/landingpage/backend/monitoring/services.py:1)
- [backend/monitoring/monitoring_agent_runner.py](/Users/lukaszremkowicz/Projects/landingpage/backend/monitoring/monitoring_agent_runner.py:1)

#### `translation`

Typical purpose:

- translation lifecycle orchestration
- background translation processing

Current structure:

- same base backend JSON structure
- request context only when logs happen inside request flow

#### `astrophotography`

Typical purpose:

- gallery/admin flows
- image/domain operations
- background-image related flows

Current structure:

- same base backend JSON structure
- request context when emitted during HTTP requests

Examples live in:

- [backend/astrophotography/models.py](/Users/lukaszremkowicz/Projects/landingpage/backend/astrophotography/models.py:1)
- [backend/astrophotography/admin.py](/Users/lukaszremkowicz/Projects/landingpage/backend/astrophotography/admin.py:1)

#### `programming`

Typical purpose:

- programming portfolio domain/admin flows

Current structure:

- same base backend JSON structure
- request context when emitted during HTTP requests

Examples live in:

- [backend/programming/admin.py](/Users/lukaszremkowicz/Projects/landingpage/backend/programming/admin.py:1)

#### `django.request`

This logger is especially important because it now carries request completion/failure events from the request correlation middleware.

Current structured request-event fields:

- base JSON fields
- `request_id`
- `request_method`
- `request_path`
- `request_host`
- `status_code`
- `duration_ms`
- `exception` for failure events

Current event messages:

- `request_completed`
- `request_failed`

### Backend structure summary

For backend app namespaces, the structure is unified.

The main differences between apps are not formatter differences but:

- logger name
- whether request context is present
- which custom `extra={...}` fields the code adds

### Request correlation

Request correlation comes from:

- [backend/common/middleware.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/middleware.py:20)

The middleware:

- reuses incoming `X-Request-ID` or creates one,
- stores request metadata in contextvars,
- emits structured `request_completed` and `request_failed` logs.

### Conclusion

Backend runtime logging is already JSON and suitable for Docker log parsing.

## 2. Frontend SSR Server

### Current format

Frontend SSR logging is now structured for request, startup, warning, and error paths used by the SSR runtime.

Relevant files:

- [frontend/server/logging.js](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/logging.js:1)
- [frontend/server/index.mjs](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/index.mjs:1)

The SSR server uses:

- `logRequest(...)` to emit JSON request logs
- `logEvent(...)` for structured runtime/startup logs
- `logWarning(...)` for structured warning logs
- `logError(...)` for structured error logs

### Current structured fields

Frontend SSR logs currently include:

- `timestamp`
- `service`
- `level`
- `request_id`
- request-specific payload fields such as:
  - `event`
  - `kind`
  - `method`
  - `path`
  - `status`
  - `duration_ms`
  - optional `error`
  - optional `error_name`
  - optional `error_message`
  - optional `error_stack`

### Conclusion

Frontend SSR server/runtime logging is now JSON in the main request/startup/error paths. Browser-side client `console.*` calls still exist in frontend code, but they are not the same as server runtime logs.

## 3. Nginx

### Current format

Nginx access logging is JSON.

Relevant config:

- [infra/nginx/static_server.conf](/Users/lukaszremkowicz/Projects/landingpage/infra/nginx/static_server.conf:43)

Current access log definition:

- `log_format json_analytics escape=json ...`
- `access_log /var/log/nginx/access.log json_analytics;`
- `access_log /dev/stdout json_analytics;`

### Current structured fields

The JSON access log contains:

- `time_local`
- `remote_addr`
- `host`
- `upstream_addr`
- `request`
- `status`
- `body_bytes_sent`
- `request_time`
- `upstream_response_time`
- `upstream_status`
- `http_referrer`
- `http_user_agent`

### What is not JSON yet

Nginx error logs are still plain text:

- `error_log /var/log/nginx/error.log warn;`
- `error_log /dev/stderr warn;`

### Conclusion

Nginx access logs are already JSON and visible through Docker stdout. Nginx error logs are still plain text.

## 4. Traefik

### Current format

Traefik access logging is JSON.

Relevant config:

- [infra/traefik/traefik.yml](/Users/lukaszremkowicz/Projects/landingpage/infra/traefik/traefik.yml:38)

Current access log definition:

- `accessLog.format: json`
- file output:
  - `/var/log/traefik/access.log`

### Current structured fields

Traefik access logs keep default fields and explicitly keep:

- `RequestHost`
- `RouterName`
- `ServiceName`
- `ServiceURL`

### Runtime logs

Traefik runtime logs are now configured for JSON through:

- `log.level: INFO`
- `log.format: json`

### Conclusion

Traefik access logs are JSON and Traefik runtime logs are now configured as JSON too.

## 5. Shell Entrypoints / Startup Scripts

Current startup scripts still emit plain text via shell `echo`.

Examples:

- [docker/backend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/backend/entrypoint.sh:1)
- [docker/frontend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/entrypoint.sh:1)
- [docker/traefik/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/traefik/entrypoint.sh:1)

These are operational bootstrap logs, not application logs, and they are currently plain text.

## Current Stack Summary

### Fully or mostly JSON today

- Backend Django runtime logs
- Frontend SSR request logs
- Nginx access logs
- Traefik access logs

### Still plain text today

- Nginx error logs
- shell entrypoint logs

## Recommended Cross-Stack Field Direction

The stack does not yet use one single field schema everywhere.

Current examples:

- Backend:
  - `timestamp`
  - `level`
  - `logger`
  - `request_id`
- Frontend:
  - `timestamp`
  - `service`
  - `level`
  - `request_id`
- Nginx:
  - `time_local`
  - `request`
  - `status`
- Traefik:
  - Traefik-native JSON field names

For future normalization, a better common field direction would be:

- `timestamp`
- `service`
- `component`
- `level`
- `message`
- `request_id`
- `method`
- `path`
- `host`
- `status_code`
- `duration_ms`
- `client_ip`
- `upstream`
- `environment`

This does not need to happen immediately, but it is the clean target if the project later adds centralized parsing or dashboards.

## Practical Reading Guide

If you are looking at live Docker logs:

- backend logs are JSON
- nginx access logs are JSON
- frontend SSR runtime logs are JSON
- Traefik runtime/access logs are JSON
- nginx error lines remain plain text

If you are collecting logs for monitoring/fail2ban:

- Traefik access log file is JSON
- Nginx access log file is JSON
- Nginx error log remains plain text

## Verified Sources

- [backend/settings/base.py](/Users/lukaszremkowicz/Projects/landingpage/backend/settings/base.py:421)
- [backend/common/utils/logging.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/utils/logging.py:1)
- [backend/common/middleware.py](/Users/lukaszremkowicz/Projects/landingpage/backend/common/middleware.py:20)
- [frontend/server/logging.js](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/logging.js:1)
- [frontend/server/index.mjs](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/index.mjs:1)
- [infra/nginx/static_server.conf](/Users/lukaszremkowicz/Projects/landingpage/infra/nginx/static_server.conf:43)
- [infra/traefik/traefik.yml](/Users/lukaszremkowicz/Projects/landingpage/infra/traefik/traefik.yml:38)
- [docker/backend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/backend/entrypoint.sh:1)
- [docker/frontend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/entrypoint.sh:1)
- [docker/traefik/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/traefik/entrypoint.sh:1)
