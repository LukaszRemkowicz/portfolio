# Monitoring System Overview

## Purpose

This document explains how the monitoring system works in this application
today and how the planned sitemap-monitoring flow fits into it.

It is written for both:
- engineers working on the codebase
- future LLM calls that may need stable project documentation before
  analyzing monitoring or sitemap-reporting behavior

The main rule is simple:
- deterministic code gathers facts
- the LLM turns those facts into readable analysis


## Current Monitoring Scope

The current production monitoring flow is focused on daily Docker log
analysis. It already works in production and should be treated as the
compatibility boundary for further work.

Relevant code:
- `backend/settings/base.py`
- `backend/monitoring/tasks.py`
- `backend/monitoring/services.py`
- `backend/monitoring/agent/agent.py`
- `backend/monitoring/agent/skills.py`


## Two Celery Beat Tasks

The app currently has two monitoring-related Celery beat tasks.

### 1. `daily_log_analysis_task`

Location:
- `backend/monitoring/tasks.py`

Schedule:
- configured in `backend/settings/base.py`
- runs daily at `02:00` UTC

Responsibility:
- orchestrate the daily log-analysis workflow
- store the analysis result in the database
- send the monitoring email
- mark the email as sent

Return shape:
- status
- log analysis id
- severity
- analysis date

### 2. `cleanup_old_logs_task`

Location:
- `backend/monitoring/tasks.py`

Schedule:
- configured in `backend/settings/base.py`
- runs weekly on Sunday at `08:00` UTC

Responsibility:
- delete old `LogAnalysis` rows
- keep the monitoring table small and maintainable
- enforce the retention window, currently `30` days

Return shape:
- status
- deleted record count
- retained days


## How Daily Log Monitoring Works

The daily log-monitoring path is deterministic until the LLM analysis step.

High-level flow:
1. A host cron job collects container logs into the mounted directory used by
   the backend.
2. `daily_log_analysis_task` starts the orchestration.
3. `DockerLogCollector` reads the prepared log files from
   `settings.DOCKER_LOGS_DIR`.
4. `HistoricalContextBuilder` loads recent monitoring history from the
   database.
5. `LogAnalysisAgent` sends the selected log content plus history to the LLM.
6. The parsed result is normalized into a typed `LogReportResult`.
7. `LogStorageService` stores the result in `LogAnalysis`.
8. `LogAnalysisEmailService` renders and sends the monitoring email.

Important design detail:
- log collection itself is not done by Celery
- Celery analyzes already-collected logs
- the reason is operational, not stylistic: the backend task environment does
  not have direct access to the Docker CLI
- log collection is therefore handled by a host-level Ubuntu scheduled task
  that runs `infra/scripts/monitoring/collect-logs.sh`
- the backend then reads the collected log files from the mounted directory
  and performs analysis and reporting only


## Why The Current Log System Uses an LLM

Logs are noisy, long, repetitive, and often contain many low-signal lines.
The LLM is useful here because it can convert a raw log tail into a compact,
human-readable incident summary.

The LLM is not used because deterministic code cannot parse logs at all.
It is used because the desired output is not only:
- match error patterns
- count lines
- detect status codes

The desired output is also:
- explain what is likely happening
- group related failures
- describe severity in human terms
- produce recommendations
- compare today against recent history

This is why the current log-monitoring email is readable by a human operator
instead of being only a raw machine report.


## Planned Sitemap Monitoring Flow

The planned sitemap flow follows the same principle, but with a stricter split
between deterministic checks and LLM explanation.

Planned schedule:
- sitemap reporting task at `03:00` UTC
- every `5` days
- production sitemap only
- separate email from the log-monitoring email

Planned deterministic sitemap checks:
- fetch root sitemap XML
- expand sitemap indexes and child sitemaps
- collect URLs
- detect duplicate URLs
- detect non-production domains
- detect redirects in sitemap
- detect broken URLs
- detect final URL mismatches
- detect canonical mismatches
- detect `noindex` pages

Important environment rule:
- TLS verification stays enabled by default
- local development may disable verification explicitly when `settings.DEBUG`
  is `True`, because local hosts may use self-signed certificates


## Why Use an LLM For Sitemap Monitoring

The sitemap checker itself should not depend on the LLM for the facts.
Those facts must come from deterministic code.

Examples of deterministic sitemap facts:
- `30` URLs were found
- `2` URLs returned `404`
- `1` URL redirects
- `3` pages are marked `noindex`
- `1` page has a canonical mismatch

The LLM is added after that step for two reasons.

### 1. Human-readable summary

The LLM can turn a flat findings list into a short operational summary such as:
- what matters most
- which findings are likely real SEO issues
- what should be fixed first
- whether this looks like a regression or low-priority noise

This is useful for email or inbox-style reporting.

### 2. Analyzer text

The LLM can provide analyst-style interpretation instead of only raw counts.

For example, instead of:
- `redirect_in_sitemap: 4`
- `canonical_mismatch: 2`

it can say:
- several sitemap entries are not final canonical URLs, which weakens sitemap
  quality and suggests stale route generation
- two indexed pages declare a different canonical target, which may split
  indexing signals and should be reviewed in the routing or metadata layer

That kind of explanation is valuable for operators and future debugging, but
it should be built on top of deterministic evidence, not instead of it.


## Why We Do Not Want A Fake Agent

For this system, orchestration should remain explicit.

The LLM should not decide:
- calendar eligibility
- whether a scheduled job runs
- which environment is valid
- whether production safety checks are enabled

Code should decide those things.

The LLM should do the part it is actually good at:
- summarizing findings
- prioritizing issues
- producing readable analysis text

This keeps the system honest, testable, and easier to maintain.


## Planned Tool Loop For LLM Calls

The next step in the monitoring architecture is a small bounded tool loop.

The intent is not to give the in-app LLM shell access or filesystem access.
It will only receive explicit app-level tools.

Planned loop rules:
- each LLM step may call one or more tools
- tools return deterministic data or a specific project skill fragment
- skill text should be fetched on demand, not preloaded in full on every run
- the loop ends when the LLM returns the final report
- if the LLM decides no tool is needed, it must return the final report in that step
- max iterations should stay bounded, currently planned as `10`

Examples of planned tools:
- `prepare_log_report`
- `get_skill_owasp`
- `get_skill_response_format`
- later: sitemap and other domain-specific tools

This gives the monitoring system a small practical AI-agent shape while keeping
all execution safe and explicit.


## Current Truth Sources

When changing monitoring behavior, these are the main truth sources:
- the working daily log-monitoring implementation
- integration and service tests under `backend/monitoring/tests`
- the current log email template, which should not be modified for sitemap work

The sitemap work should be additive:
- add new services
- add new tests
- add a separate sitemap email template
- avoid invasive changes to the current log pipeline unless clearly necessary
