# Monitoring System Overview

## Purpose

This document describes the monitoring system as it exists today.

It is meant for:
- engineers working on the codebase
- future LLM calls that need stable project documentation

Core rule:
- deterministic code gathers facts
- the LLM turns those facts into readable analysis


## Current Truth / Scope

This document is the high-level source of truth for the current monitoring
architecture.

It describes:
- live production behavior
- active monitoring entry points
- current LLM boundaries

If code and this document ever disagree:
- production code wins
- this document should then be updated

This document describes the current implemented system, not speculative future
architecture unless that is stated explicitly.


## Hard Rules / Invariants

These rules should be treated as hard constraints.

- deterministic code owns facts
- the LLM only summarizes and interprets findings
- `daily_monitoring_agent_log_task` is manual-only
- `daily_log_analysis_task` is disabled unless `RUN_LEGACY_DAILY_TASK=True`
- sitemap monitoring is deterministic-first and manual-only
- admin actions queue real Celery tasks and do not create monitoring rows directly
- no scheduled monitoring jobs are defined in Celery Beat
- no monitoring tasks are routed to a dedicated monitoring queue


## Live Monitoring Jobs

The application currently has four monitoring-related Celery tasks in
`backend/monitoring/tasks.py`.

### 1. `daily_monitoring_agent_log_task`

Status: manual-only

- no production environment config is provided for old snapshot inputs
- stores results in `LogAnalysis`
- sends the standard log-monitoring email

### 2. `daily_log_analysis_task`

Status: disabled by default

- runs only when `RUN_LEGACY_DAILY_TASK=True`
- disabled by default

### 3. `daily_sitemap_analysis_task`

Status: manual-only sitemap job

- stores results in `SitemapAnalysis`
- sends a separate sitemap email

### 4. `cleanup_old_logs_task`

Status: manual-only

- not scheduled from Celery Beat
- kept until the monitoring app is removed


## Queue Routing

No monitoring tasks are routed to the `monitoring` Celery queue.

Manually queued monitoring tasks use default Celery routing.


## Manual Log Monitoring Flow

The Django admin log flow is manual:

1. An admin queues `daily_monitoring_agent_log_task` from Django admin.
2. `DockerLogCollector` expects snapshot files from a configured log directory.
3. `HistoricalContextBuilder` loads recent monitoring history.
4. `LogReportPreparationService` builds the typed report that is stored and emailed.
5. `LogStorageService` stores the final `LogAnalysis`.
6. `LogAnalysisEmailService` sends the email.

Current implementation detail:
- the bounded monitoring-agent loop remains in the codebase as an experimental
  path, but the live daily log flow currently uses the single analyzed report
  from `LogReportPreparationService` as the final source of truth

Important operational detail:
- Celery does not collect Docker logs directly
- the backend environment does not have Docker daemon access
- no production `DOCKER_LOGS_DIR` setting or compose mount is configured
- no scheduled log-monitoring Celery Beat entry exists


## Sitemap Monitoring Flow

High-level flow:

1. `daily_sitemap_analysis_task` starts orchestration.
2. `SitemapHTTPClient` fetches the root sitemap from `SITE_DOMAIN`.
3. `SitemapAuditService` performs deterministic checks.
4. If issues exist, the LLM summarizes them into operator-readable text.
5. If no issues exist, the system skips the LLM call and stores a
   deterministic all-clear result.
6. `SitemapAnalysisStorageService` stores the final `SitemapAnalysis`.
7. `SitemapAnalysisEmailService` sends the sitemap email.

Deterministic sitemap checks include:
- sitemap fetch and XML expansion
- nested sitemap traversal
- duplicate URL detection
- non-production domain detection
- broken URL detection
- redirect detection
- final URL mismatch detection
- canonical mismatch detection
- `noindex` detection

Development environment detail:
- TLS verification is enabled by default
- in local debug mode, sitemap fetching may use the internal Docker URL path
  so local self-signed/public-host routing does not break the worker


## Manual Admin Runs

Both monitoring reports can be triggered manually from Django admin:

- `admin/monitoring/loganalysis/`
- `admin/monitoring/sitemapanalysis/`

Those admin pages provide:
- a manual “run now” button
- a progress/status bar
- polling of the shared task-status API endpoint

Important behavior:
- admin does not create raw monitoring rows directly
- it queues the real Celery task
- the standard “add” action is hidden for these changelists


## LLM Entry Points And Main Modules

Where the LLM enters:
- logs: `LogAnalyzer` in `backend/monitoring/services.py`
- sitemap: only after deterministic audit, and only when issues exist

Important rule:
- code owns scheduling, data collection, and deterministic checks
- the LLM only summarizes and interprets findings

Main files:
- `backend/monitoring/tasks.py`
  - Celery entry points
- `backend/monitoring/services.py`
  - orchestration, storage, email flow
- `backend/monitoring/sitemap_services.py`
  - deterministic sitemap audit
- `backend/monitoring/monitoring_agent_runner.py`
  - bounded tool loop kept for future monitoring-agent work
- `backend/monitoring/prompt_assets.py`
  - loader for file-backed prompt assets
- `backend/monitoring/agent_assets/`
  - prompt bundle used by the monitoring LLM flows
  - `prompts/`, `skills/`, `tools/`, `schemas/`, `examples/`


## Current State Summary

The system currently works in this form:

- no scheduled log-analysis Celery beat entry
- no scheduled sitemap-analysis Celery beat entry
- manual log analysis currently stores the first analyzed report directly
- disabled log-analysis task runs only when `RUN_LEGACY_DAILY_TASK=True`
- sitemap monitoring can still be triggered manually
- separate log and sitemap emails
- manual admin runs for both report types
- shared admin task-status polling endpoint
- file-backed monitoring prompt assets
