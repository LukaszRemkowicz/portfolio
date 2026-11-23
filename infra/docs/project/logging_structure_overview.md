# Logging Structure Overview

## Purpose

This document describes the current logging structure inside the landingpage application stack and clarifies which components already emit JSON logs versus plain-text logs.

It is intended as:

- a current-state reference for future logging work,
- an operational guide for reading logs across the backend,
- a baseline for future log normalization and ingestion work.

Current state verified on 2026-04-17; updated for the Supabase architecture on 2026-11.

The public API logs are not in this stack: they live in the Supabase Edge Function logs (Supabase dashboard). Django is the admin only and runs locally, so its JSON logs go to local Docker stdout.

## Short Answer

Current JSON logging status:

- Backend Django app: yes, JSON to Docker stdout

Current plain-text / non-JSON areas:

- Backend startup / any non-logging `print` usage: possible plain text
- Shell entrypoint scripts: plain text

So the stack is partially normalized, but not fully JSON everywhere yet.

## Component Status

## 1. Backend Django

### Current format

Backend application logs now use JSON through Django logging configuration in:

- [backend/settings/base.py](../../../backend/settings/base.py)
- [backend/common/utils/logging.py](../../../backend/common/utils/logging.py)

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
- `translation`
- `astrophotography`
- `programming`
- `django`
- `django.request`
- `django.server`
- `django.db.backends`

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
- shared image-processing workflow

Common log shape:

- base JSON fields
- optional request context when called in-request
- optional task/service extras such as:
  - `status_code`
  - `duration_ms`
  - custom `extra={...}` values

Examples live in:

- [backend/common/utils/image.py](../../../backend/common/utils/image.py)

#### `core`

Typical purpose:

- shared domain infrastructure
- `BaseImage` lifecycle

#### `scripts`

Typical purpose:

- release-time backend orchestration
- rollout-only startup hooks

These modules emit structured logs through the normal app-level namespace configuration, for example:

- [backend/common/utils/image.py](../../../backend/common/utils/image.py)
- [backend/core/models.py](../../../backend/core/models.py)
- [backend/core/tasks.py](../../../backend/core/tasks.py)
- [backend/core/management/commands/backfill_image_variants.py](../../../backend/core/management/commands/backfill_image_variants.py)
- shared image task compatibility wrapper

Common log shape:

- base JSON fields
- optional request context
- model/task specific extras when provided

Examples live in:

- [backend/core/models.py](../../../backend/core/models.py)
- [backend/core/tasks.py](../../../backend/core/tasks.py)

#### `users`

Typical purpose:

- profile/user image lifecycle
- user/profile admin logic

Common log shape:

- base JSON fields
- request context when logs happen during HTTP request flow
- image-processing related extras when provided

Examples live in:

- [backend/users/models.py](../../../backend/users/models.py)

#### `shop`

Typical purpose:

- shop settings image lifecycle
- product/shop admin logic

Common log shape:

- base JSON fields
- request context when logs happen during HTTP request flow
- image-processing extras when provided

Examples live in:

- [backend/shop/models.py](../../../backend/shop/models.py)

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

- [backend/astrophotography/models.py](../../../backend/astrophotography/models.py)
- [backend/astrophotography/admin.py](../../../backend/astrophotography/admin.py)

#### `programming`

Typical purpose:

- programming portfolio domain/admin flows

Current structure:

- same base backend JSON structure
- request context when emitted during HTTP requests

Examples live in:

- [backend/programming/admin.py](../../../backend/programming/admin.py)

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

- [backend/common/middleware.py](../../../backend/common/middleware.py)

The middleware:

- reuses incoming `X-Request-ID` or creates one,
- stores request metadata in contextvars,
- emits structured `request_completed` and `request_failed` logs.

### Conclusion

Backend runtime logging is already JSON and suitable for Docker log parsing.

## 2. Shell Entrypoints / Startup Scripts

Current startup scripts still emit plain text via shell `echo`.

Examples:

- [docker/backend/entrypoint.sh](../../../docker/backend/entrypoint.sh)

These are operational bootstrap logs, not application logs, and they are currently plain text.

## Current Stack Summary

### Fully or mostly JSON today

- Backend Django runtime logs

### Still plain text today

- shell entrypoint logs

## Practical Reading Guide

If you are looking at live Docker logs:

- backend logs are JSON
- entrypoint lines are plain text

Landingpage owns application log emission only.

## Verified Sources

- [backend/settings/base.py](../../../backend/settings/base.py)
- [backend/common/utils/logging.py](../../../backend/common/utils/logging.py)
- [backend/common/middleware.py](../../../backend/common/middleware.py)
- [docker/backend/entrypoint.sh](../../../docker/backend/entrypoint.sh)
