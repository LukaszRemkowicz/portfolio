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
- `backend/monitoring/monitoring_agent_runner.py`
- `backend/monitoring/prompt_assets.py`
- `backend/monitoring/agent_assets/`


## Monitoring Celery Beat Tasks

The app currently has three monitoring-related Celery beat tasks.

Queue routing detail:
- monitoring tasks are routed to the `monitoring` Celery queue
- the worker must listen to both `celery` and `monitoring`
- otherwise scheduled or manually queued monitoring jobs will be created but
  never consumed

### 1. `daily_log_analysis_task`

Location:
- `backend/monitoring/tasks.py`

Schedule:
- configured in `backend/settings/base.py`
- only scheduled when `RUN_LEGACY_DAILY_TASK=True`

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

Legacy status:
- guarded by `RUN_LEGACY_DAILY_TASK`
- disabled by default
- kept only as a rollback fallback

### 2. `daily_monitoring_agent_log_task`

Location:
- `backend/monitoring/tasks.py`

Schedule:
- configured in `backend/settings/base.py`
- runs daily at `02:00` UTC by default

Responsibility:
- run the current log-monitoring path through the bounded monitoring agent
- store the final `LogAnalysis` result
- send the existing log-monitoring email

### 3. `daily_sitemap_analysis_task`

Location:
- `backend/monitoring/tasks.py`

Schedule:
- configured in `backend/settings/base.py`
- runs at `03:00` UTC
- every `5` days

Responsibility:
- run deterministic sitemap auditing against `SITE_DOMAIN`
- summarize findings with the LLM only when the sitemap audit finds issues
- store `SitemapAnalysis`
- send a separate sitemap email
- support an admin-triggered on-demand run from the sitemap changelist

### 4. `cleanup_old_logs_task`

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
2. `daily_monitoring_agent_log_task` starts the orchestration.
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


## Sitemap Monitoring Flow

The sitemap flow follows the same principle, but with a stricter split
between deterministic checks and LLM explanation.

Live schedule:
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

Operational hardening detail:
- when the deterministic sitemap audit finds no issues, the system skips the
  sitemap LLM call and sends a deterministic all-clear summary instead
- this keeps healthy runs cheaper and quieter while still storing the audit
  result

Admin operations detail:
- the sitemap admin changelist includes a manual "Run Sitemap Analysis Now"
  button
- it queues the existing sitemap Celery task instead of running the analysis
  inline in the HTTP request
- the standard add action is hidden so operators use the queued monitoring flow
  instead of creating raw rows by hand
- after queueing, the admin page polls a DRF status endpoint every `0.5`
  seconds and updates a status bar directly under the button
- polling stops immediately when the task reaches `success` or `failed`


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


## Current And Emerging Architecture

At this point the monitoring system has two layers:

### 1. Current live production layer

This is the part already used by the running daily log-monitoring job.

It includes:
- deterministic log collection handoff from the host scheduler
- `daily_monitoring_agent_log_task`
- `MonitoringAgentLogOrchestrator`
- `MonitoringToolLoopRunner`
- database persistence in `LogAnalysis`
- the current log monitoring email

The legacy compatibility boundary remains available only behind
`RUN_LEGACY_DAILY_TASK`.

### 2. Emerging bounded-agent layer

This is the newer architecture being prepared for later integration into
scheduled monitoring jobs.

It includes:
- file-backed prompt and skill assets
- typed job and tool contracts
- deterministic monitoring tools
- a bounded LLM tool loop
- on-demand skill retrieval instead of sending all skill text every time

Important constraint:
- this bounded-agent layer exists now as infrastructure
- it is not yet the live execution path for the current daily log task
- wiring it into scheduled monitoring logic is a later integration step


## Bounded Tool-Loop Architecture

The monitoring system is moving toward a small constrained AI-agent model.

The core idea is:
- code still decides the scheduled job and its scope
- the LLM operates only within that explicit job
- the LLM may request one or more app-level tools
- tools return deterministic data or a specific skill fragment
- the LLM returns a final report when it has enough context

The loop is bounded and safe:
- no shell access
- no arbitrary filesystem access
- no arbitrary network access beyond what the app-level tools allow
- no open-ended autonomy

Current loop rules:
- each LLM step may call one or more tools
- if no tool is needed, the LLM must return the final report immediately
- repeated identical tool calls are blocked
- the loop stops on final report
- the loop also stops if `max_iterations` is reached
- current planned default: `10` iterations

This makes the monitoring agent practical, narrow, and testable instead of
pretending to be a general autonomous agent.


## What `agent_assets` Is

`backend/monitoring/agent_assets/` is the file-backed source of truth for
monitoring prompts, skill fragments, tool documentation, response schemas,
and example payloads.

Its purpose is to move monitoring prompt logic out of Python string constants
and into reviewable versioned files.

This has several benefits:
- easier prompt iteration
- easier review in pull requests
- cleaner Python modules
- better reuse across current and future monitoring flows
- easier future LLM calls, because the project guidance is already structured


## `agent_assets` Folder Structure

### `agent_assets/prompts/`

Purpose:
- system and user instructions for monitoring LLM calls
- summary instructions for specific job types
- explicit response-format instructions

Examples:
- `monitoring_job_system.md`
- `monitoring_job_rules.md`
- `monitoring_log_summary.md`
- `monitoring_sitemap_summary.md`
- `monitoring_tool_loop_system.md`
- `monitoring_tool_loop_user.md`
- `monitoring_log_response_format.md`

How to think about this folder:
- prompts define how the LLM should behave in a given monitoring context
- they are the orchestration text, not the factual monitoring data

### `agent_assets/skills/`

Purpose:
- reusable domain guidance fragments that can be attached to analysis when needed
- project-specific expertise for the monitoring LLM

Examples:
- `project_context.md`
- `normal_patterns.md`
- `application_monitoring.md`
- `bot_detection.md`
- `owasp_security.md`
- `severity_guide.md`
- `recommendations_guide.md`
- `historical_context.md`

How to think about this folder:
- skills are not executable tools
- they are analysis playbooks
- they teach the LLM how to interpret findings in this project

Examples of use:
- `owasp_security.md` when logs suggest suspicious security behavior
- `bot_detection.md` when logs show scanning or probing patterns
- `historical_context.md` when temporal comparison is needed

### `agent_assets/tools/`

Purpose:
- tool documentation shown to the LLM in the bounded tool loop
- defines what each app-level tool is for and when it should be used

Examples:
- `prepare_log_report.md`
- `get_skill_owasp.md`
- `get_skill_response_format.md`
- `get_skill_bot_detection.md`

How to think about this folder:
- these files do not execute anything themselves
- they document the app-level tools exposed to the LLM
- they help the LLM choose the correct tool with less prompt ambiguity

Each tool doc should explain:
- purpose
- when to use
- when not to use
- output shape

### `agent_assets/schemas/`

Purpose:
- JSON schemas for expected structured outputs
- contracts for summaries, loop decisions, and report payloads

Examples:
- `log_report.schema.json`
- `sitemap_report.schema.json`
- `monitoring_job_response.schema.json`
- `monitoring_tool_loop_response.schema.json`
- `final_summary.schema.json`

How to think about this folder:
- schemas define the shape of machine-readable data
- they reduce ambiguity for both engineers and LLM prompts

### `agent_assets/examples/`

Purpose:
- concrete examples of valid payloads and responses
- reference material for tests, prompt tuning, and future LLM context

Examples:
- `monitoring_job_response.example.json`
- `monitoring_tool_loop_response.example.json`
- `sitemap_report.example.json`

How to think about this folder:
- examples are not validation rules
- they are practical illustrations of what “good output” looks like


## How The New Bounded Agent Pieces Fit Together

The key modules are:
- `backend/monitoring/prompt_assets.py`
  - loads prompt, tool, schema, skill, and example files from `agent_assets`
- `backend/monitoring/agent/context.py`
  - exposes file-backed monitoring context sections to the current log prompt builder
- `backend/monitoring/agent/skills.py`
  - composes the file-backed monitoring skill fragments into current monitoring prompts
- `backend/monitoring/monitoring_agent_runner.py`
  - defines the bounded LLM tool-loop runtime

Inside `monitoring_agent_runner.py`:

### `MonitoringToolRegistry`

Purpose:
- declare which app-level tools exist
- attach human-readable description and usage rules to each tool

Why it matters:
- it is the tool policy boundary for the monitoring agent
- the LLM only sees tools declared here
- adding a tool is an explicit architecture and safety decision

What it contains:
- tool name
- short description
- documentation asset path
- `when_to_use`
- `when_not_to_use`

### `MonitoringToolExecutor`

Purpose:
- run a tool selected by the LLM
- return deterministic tool output

Current responsibilities:
- return the prepared log report
- return specific skill fragments on demand

Important boundary:
- this class is the execution layer, not the policy layer
- it does not let the LLM run arbitrary code
- it maps a small fixed tool set to narrow Python implementations

Why it matters:
- it keeps tool execution deterministic
- it keeps the monitoring agent safe and debuggable
- it is the place where future app-level monitoring tools will be added

### `MonitoringToolLoopRunner`

Purpose:
- run the bounded LLM loop
- send tool definitions and current context to the LLM
- parse the LLM decision
- execute tool calls
- stop on final report or loop limit

Core runtime flow:
1. receive the already-approved monitoring job scope from application code
2. build the system prompt and current user message
3. send the current context plus available tools to the LLM
4. parse whether the LLM wants:
   - one or more tool calls
   - or the final report
5. execute requested tools through `MonitoringToolExecutor`
6. append tool results to the next iteration context
7. stop when:
   - the LLM returns the final report
   - the LLM returns an empty response
   - only duplicate tool calls remain
   - max iterations is reached

Why it matters:
- this is the main runtime for the bounded monitoring agent
- it is the most important new control-flow module in the emerging architecture
- later scheduled monitoring jobs will use this runner as the bridge between
  deterministic monitoring data and LLM-guided tool usage

What it does not do:
- decide whether a scheduled job should run
- decide global tool availability outside the approved registry
- access shell or filesystem directly on behalf of the LLM
- replace deterministic monitoring services

Standalone trace mode:
- the runner supports a verbose trace mode for local standalone runs
- this prints a simplified live agent trace to stdout
- it is intended for debugging and development, not for exposing hidden
  model chain-of-thought

The trace is designed to show:
- job start
- current iteration
- when the runtime is asking the LLM for the next action
- which decision was returned
- which tools were requested
- when each tool starts and finishes
- why the loop stopped

Typical trace output looks like:
- `[monitoring-agent] starting job=log_report`
- `[monitoring-agent] iteration=1 asking_llm..`
- `[monitoring-agent] iteration=1 decision=call_tools tools=[prepare_log_report,get_skill_owasp]`
- `[monitoring-agent] iteration=1 tool=prepare_log_report start..`
- `[monitoring-agent] iteration=1 tool=prepare_log_report done`
- `[monitoring-agent] stop_reason=final_report`

This trace is an execution trace, not private chain-of-thought. The goal is
to make the runtime observable and debuggable without depending on raw hidden
reasoning text from the LLM.


## Current vs Future Usage Of The New Architecture

Current state:
- the existing daily log task still uses the older direct `LogAnalysisAgent` path
- `agent_assets` already backs the prompt content used by that path
- the bounded tool loop exists and is tested
- the bounded tool loop is not yet wired into the live Celery monitoring flow

Future state:
- scheduled monitoring jobs will prepare deterministic job context
- the bounded tool loop will run inside that job scope
- the LLM will request the minimum tools needed
- the final report will be generated from deterministic evidence plus optional
  on-demand project skills

This is the intended long-term architecture.


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
