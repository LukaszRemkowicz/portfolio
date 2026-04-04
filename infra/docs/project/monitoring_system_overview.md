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
- `daily_monitoring_agent_log_task` is the live daily log path
- `daily_log_analysis_task` is legacy rollback only
- sitemap monitoring is deterministic-first and does not use the bounded tool loop
- admin actions queue real Celery tasks and do not create monitoring rows directly
- log collection is handled outside the backend/Celery monitoring flow
- monitoring jobs are consumed from the `monitoring` queue


## Live Monitoring Jobs

The application currently has four monitoring-related Celery tasks in
`backend/monitoring/tasks.py`.

### 1. `daily_monitoring_agent_log_task`

Status: live, primary

- scheduled from `backend/settings/base.py`
- runs daily at `02:00` UTC
- default scheduled log path
- stores results in `LogAnalysis`
- sends the standard log-monitoring email

### 2. `daily_log_analysis_task`

Status: legacy, rollback only

- scheduled only when `RUN_LEGACY_DAILY_TASK=True`
- disabled by default
- kept as an emergency fallback

### 3. `daily_sitemap_analysis_task`

Status: live, primary sitemap job

- scheduled from `backend/settings/base.py`
- runs at `03:00` UTC
- runs every 5 days
- stores results in `SitemapAnalysis`
- sends a separate sitemap email

### 4. `cleanup_old_logs_task`

Status: support task

- runs weekly
- deletes old `LogAnalysis` rows


## Queue Routing

Monitoring jobs are routed to the `monitoring` Celery queue.

Operational requirement:
- the worker must listen to both `celery` and `monitoring`

If it does not, monitoring jobs may be created but never consumed.


## Log Monitoring Flow

The daily log flow is:

1. A trusted log collector runtime gathers runtime logs and access/error log files.
2. The collector writes snapshot files into `DOCKER_LOGS_DIR`.
3. `daily_monitoring_agent_log_task` starts orchestration.
4. `DockerLogCollector` reads the collected files.
5. `HistoricalContextBuilder` loads recent monitoring history.
6. `LogReportPreparationService` builds a typed deterministic report.
7. `MonitoringToolLoopRunner` runs the bounded LLM analysis loop.
8. `LogStorageService` stores the final `LogAnalysis`.
9. `LogAnalysisEmailService` sends the email.

Important operational detail:
- Celery does not collect Docker logs directly
- the backend environment does not have Docker daemon access
- log collection is handled by a separate collector path
- the collector may need both Docker daemon access and direct access to
  host-mounted log files, depending on the configured source type


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
- logs: `MonitoringToolLoopRunner` in
  `backend/monitoring/monitoring_agent_runner.py`
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
  - bounded tool loop for log monitoring
- `backend/monitoring/prompt_assets.py`
  - loader for file-backed prompt assets
- `backend/monitoring/agent_assets/`
  - prompt bundle used by the monitoring LLM flows
  - `prompts/`, `skills/`, `tools/`, `schemas/`, `examples/`


## Current State Summary

The system currently works in this form:

- daily monitoring-agent log analysis at `02:00` UTC
- legacy log task kept only as rollback
- sitemap monitoring at `03:00` UTC every 5 days
- separate log and sitemap emails
- manual admin runs for both report types
- shared admin task-status polling endpoint
- file-backed monitoring prompt assets
