# Monitoring LLM and Sitemap Audit Implementation Plan

## Status
Proposed

## Purpose

Define a phased implementation plan for evolving the current monitoring system from a
single-purpose daily log analysis pipeline into scheduled monitoring jobs with LLM
analysis that can:

- execute only the scheduled monitoring job scope determined by code
- execute deterministic monitoring tools for logs and sitemap checks
- summarize findings with the LLM
- store structured execution metadata for observability and future iteration

This document is the implementation source of truth for the work. Each phase is
designed to be independently reviewable, testable, and approval-gated.

## Current System Summary

The current backend already has a strong base for this work:

- Celery task scheduling in `backend/settings/base.py`
- daily log-analysis orchestration in `backend/monitoring/tasks.py`
- service-layer orchestration in `backend/monitoring/services.py`
- a dedicated LLM log-analysis implementation in `backend/monitoring/agent/agent.py`
- prompt-building logic in `backend/monitoring/agent/skills.py`
- existing tests across tasks, services, and LLM behavior in `backend/monitoring/tests`

The plan below extends this system instead of replacing it.

## Goals

- Keep deterministic monitoring logic outside the LLM.
- Let the LLM act as an analyzer and summarizer, not a scheduler.
- Add a sitemap audit pipeline that produces structured findings first.
- Move long prompts and LLM instructions out of Python constants into versioned files.
- Use structured data for job contracts, tool outputs, LLM responses, and execution metadata.
- Preserve rollback safety by keeping the existing log pipeline and current log email rendering behavior working while the new system is introduced.

## Non-Goals

- No free-form autonomous monitoring agent with unconstrained tool access.
- No replacement of Celery scheduling with LLM reasoning.
- No broad site crawler in the first sitemap implementation.
- No immediate prompt-engineering rewrite across unrelated apps such as translation.

## Architecture Decisions

### ADR-001: Deterministic scheduled jobs, LLM analysis within job scope

#### Context

The original direction was to make the monitoring system feel like "one real agent"
choosing tools. After design review, that approach adds complexity without giving real
autonomy, because schedule, scope, and safety still need to be enforced in code.

#### Options Considered

| Option | Pros | Cons | Complexity | When Valid |
|--------|------|------|------------|-----------|
| LLM decides both schedule and tools | Most agent-like on paper | Brittle, hard to test, easy to drift from policy | Medium | Rarely valid |
| Deterministic scheduled jobs plus in-job LLM analysis | Reliable, simple, honest architecture | Less "agent-like" in marketing terms | Low | Best fit here |

#### Decision

Use deterministic scheduled jobs as the primary orchestration model.

- the log-monitoring job runs on its fixed schedule
- the sitemap-monitoring job runs on its fixed schedule
- each job gathers deterministic data first
- when the deterministic findings meet the job requirements, the system performs a dedicated LLM call for analysis and summarization

The LLM is not responsible for deciding schedule, eligibility, or job selection.

#### Rationale

- Scheduling is business logic and should be testable without model calls.
- The current problem does not require true multi-tool agent planning.
- Separate scheduled jobs are easier to implement, test, observe, and maintain.
- This avoids pretending there is an autonomous agent where there is really a scheduled pipeline with LLM assistance.

#### Trade-offs

- The system is better described as scheduled monitoring with LLM analysis, not as a general agent.
- If true multi-tool orchestration is needed later, the architecture can be extended.
- Some earlier "agent" naming may remain for implementation convenience, but behavior should follow the deterministic scheduled-job model.

### ADR-002: Deterministic report generation first, LLM summary second

#### Context

Both logs and sitemap checks produce factual telemetry. The LLM is strongest at
compression, explanation, prioritization, and operator-friendly summaries.

#### Decision

Each monitoring tool must first produce a structured deterministic result payload. The
LLM only summarizes or prioritizes those results.

#### Rationale

- Lower hallucination risk
- Better alerting and diffing
- Easier testing
- Lower cost because healthy runs can bypass deep summarization

### ADR-003: Prompt assets live in files, schemas live in structured files

#### Decision

- Use `.md` files for prompt instructions and context fragments.
- Use `.json` files for schemas, job contracts, and example payloads.
- Keep Python code responsible for loading and composing these assets.

#### Rationale

- Easier prompt iteration and review
- Better versioning
- Cleaner code
- More transparent for future LLM-assisted work

### ADR-004: Store LLM execution metadata, not private reasoning traces

#### Decision

Persist structured execution metadata such as:

- `session_id`
- `reasoning_effort`
- `job_name`
- `job_scope`
- `findings_summary`
- `prompt_version`
- `tokens_used`
- `cost_usd`
- `execution_time_seconds`
- `status`

Do not persist chain-of-thought or hidden private reasoning.

#### Rationale

- Useful observability without over-collecting sensitive or low-signal text
- Safer long-term storage model
- Easier analytics on run quality, cost, and tool usage

### ADR-005: Existing log monitoring flow is a compatibility boundary

#### Context

The current daily log-monitoring flow already works in production and already has
integration-level coverage. That makes it the source of truth for existing behavior.

Current compatibility anchors include:

- task integration coverage in `backend/monitoring/tests/test_tasks.py`
- email integration coverage in `backend/monitoring/tests/test_email.py`
- the current log email template in `backend/monitoring/templates/monitoring/email/log_analysis.html`

#### Decision

Treat the current log-monitoring task and current log email template as compatibility
boundaries.

- do not rewrite the current log pipeline unless a change is strictly required
- before changing existing log behavior, strengthen integration coverage if gaps are found
- do not modify the current log email template for sitemap work
- create a separate sitemap email template by copying the current style where useful

#### Rationale

- Protects working behavior
- Reduces risk of breaking the existing monitoring feature
- Makes new sitemap work additive rather than invasive

#### Trade-offs

- Some duplication between log and sitemap email templates is acceptable
- The plan favors stability over aggressive deduplication

## Proposed System Design

### Core Runtime Components

1. Celery schedule plus per-job guard helpers
- Celery beat remains the primary scheduling mechanism
- small helper functions may validate job-specific runtime conditions
- avoid a dedicated policy abstraction unless rules become materially more complex

2. Per-job monitoring services
- each scheduled job owns its deterministic collection and validation flow
- initial jobs:
  - log-report preparation
  - sitemap-report preparation

3. LLM summary services
- build the LLM context for a single scheduled job
- receive the explicit job contract and deterministic findings
- perform the LLM analysis call within that job scope
- return the parsed summary payload

4. `PromptAssetLoader`
- loads prompt markdown and JSON schema assets from disk
- versions prompt bundles cleanly

5. `Structured Payload Models`
- typed models for tool definitions, inputs, outputs, decisions, and run metadata

6. `Persistence Layer`
- keeps existing `LogAnalysis`
- adds separate storage for sitemap runs and LLM-backed monitoring runs

### Initial Tool Set

#### Tool: `prepare_log_report`

Responsibility:
- reuse current log collection and analysis flow
- return structured findings payload
- remain backward-compatible with current reporting

Primary output shape:
- timestamp range
- severity
- key findings
- recommendations
- trend summary
- usage/cost metrics

#### Tool: `prepare_sitemap_report`

Responsibility:
- fetch sitemap XML or sitemap index
- expand all child sitemaps
- normalize and deduplicate URLs
- request URLs with rate limiting and timeouts
- classify findings deterministically

Initial checks:
- `200` expected for canonical sitemap URLs
- redirects in sitemap
- `4xx`
- `5xx`
- final URL mismatch
- duplicate URLs
- non-production domains

Phase-two checks:
- canonical mismatch
- `noindex`
- robots mismatch if needed

### Scheduled Execution Model

Scheduled flow:

1. Celery triggers the daily log-monitoring path at 02:00.
2. Celery triggers the sitemap-monitoring path at 03:00 every 5 days.
3. deterministic code gathers and validates the job inputs, with small per-job guards where needed.
4. the job-specific LLM summary service sends the LLM:
   - `session_id`
   - the explicit scheduled job contract for this invocation
   - job-specific execution rules
   - deterministic findings payload
   - the structured response schema
5. The LLM analyzes and summarizes the job findings.
6. The system parses, validates, and stores the result.
7. The system stores metadata and sends a separate email for that job.

## Scheduling Proposal

### Logs

- due daily at 02:00
- remains part of the current operational monitoring baseline
- email behavior should remain as close as possible to the current system

### Sitemap

- due every 5 days
- runs separately at 03:00
- checks production sitemap only

The cadence should be implemented in deterministic code, not prompt text alone.

## Structured Data Plan

Use typed data models for the following contracts:

- `MonitoringJobDefinition`
- `MonitoringJobExecutionContext`
- `LogReportResult`
- `SitemapIssue`
- `SitemapReportResult`
- `LLMSummaryResult`
- `LLMRunRecord`

Implementation note:

- prefer standard-library `dataclass` or Django-friendly typed dicts if staying light
- introduce Pydantic only if the team wants stronger validation and accepts the dependency

Decision for this repository:

- use standard-library `dataclasses` and `Enum` types where useful
- add explicit lightweight validation helpers where needed
- do not introduce Pydantic at this stage
- reassess only if report payload complexity grows materially later

## Prompt Asset Plan

Recommended prompt asset structure:

```text
backend/monitoring/agent_assets/
  prompts/
    monitoring_job_system.md
    monitoring_job_rules.md
    monitoring_log_summary.md
    monitoring_sitemap_summary.md
  schemas/
    monitoring_job_response.schema.json
    log_report.schema.json
    sitemap_report.schema.json
    final_summary.schema.json
  examples/
    monitoring_job_response.example.json
    sitemap_report.example.json
```

Notes:

- existing prompt constants from `backend/monitoring/agent/context.py` can be migrated incrementally
- do not rewrite every prompt in one phase

## Phase Plan

Every phase must end with all three of the following:

1. targeted tests added or updated
2. `pre-commit run --all-files`
3. explicit human approval before starting the next phase

No phase is considered complete until those three conditions are met.

### Phase 0: Baseline and Guardrails

#### Scope

- add a repository-level `.pre-commit-config.yaml` if missing
- validate the current log-monitoring integration coverage before changing production behavior
- add missing integration assertions first if current coverage is insufficient
- define the implementation directory layout for LLM prompt assets and new monitoring modules
- add typed structured-data models for scheduled job and LLM contracts
- add a prompt asset loader without changing current runtime behavior
- document file/version naming rules for prompts and schemas

#### Deliverables

- pre-commit configuration committed
- confirmed or strengthened integration protection for the existing log pipeline
- initial prompt asset loader
- initial structured contract models
- tests for loader behavior and basic schema validation

#### Tests

- existing log-monitoring integration tests reviewed and kept green
- existing log email integration tests reviewed and kept green
- new integration assertions added first if gaps are found
- unit tests for prompt file loading
- unit tests for missing-file behavior
- unit tests for structured payload validation

#### Exit Verification

- `poetry run pytest monitoring/tests common/tests`
- `pre-commit run --all-files`
- wait for approval

### Phase 1: Refactor Log Analysis into a Tool Contract

#### Scope

- wrap the existing log-analysis flow in a deterministic tool interface
- preserve current task behavior and current `LogAnalysis` persistence
- preserve the current log email template output as a compatibility requirement
- normalize the tool result into a structured payload
- keep current email behavior unchanged

#### Deliverables

- `prepare_log_report` tool service
- backward-compatible orchestration
- regression-safe structured log-report payload

#### Tests

- existing task/service tests updated to pass through the new tool abstraction
- new tests asserting payload structure and backward compatibility
- integration coverage must still prove current log email rendering is unchanged

#### Exit Verification

- targeted `monitoring` pytest run
- `pre-commit run --all-files`
- wait for approval

### Phase 2: Implement Deterministic Sitemap Audit Tool

#### Scope

- build sitemap XML reader for sitemap index and child sitemap support
- build URL checker with timeout, retry, redirect capture, and rate limiting
- classify deterministic issues without LLM involvement

#### Deliverables

- sitemap fetch/parser service
- URL audit service
- structured sitemap report payload

#### Tests

- parser tests for sitemap index and nested sitemap fixtures
- HTTP client tests with mocked responses
- severity/classification tests

#### Exit Verification

- targeted sitemap and monitoring pytest run
- `pre-commit run --all-files`
- wait for approval

### Phase 3: Add Sitemap Quality Signals

#### Scope

- extend sitemap report with page-level SEO signals
- inspect selected HTML responses when content type allows it

#### Deliverables

- canonical mismatch detection
- `noindex` detection
- optional robots conflict detection if relevant to production behavior

#### Tests

- HTML parsing tests
- canonical/noindex fixture tests
- regression tests for non-HTML responses

#### Exit Verification

- targeted pytest run
- `pre-commit run --all-files`
- wait for approval

### Phase 4: Introduce Scheduled LLM-Backed Monitoring Jobs

#### Scope

- add scheduled job entry points
- add per-job deterministic services and LLM summary services
- add prompt assets for job execution and summarization
- allow the LLM to operate only within the explicit scheduled job scope

#### Deliverables

- scheduled task flow for logs and sitemap
- per-job guard helpers where needed
- job-execution contract
- out-of-scope guard and response validation

#### Tests

- schedule and guard-helper tests where applicable
- LLM response parsing tests
- job-scope enforcement tests
- end-to-end mocked run tests

#### Exit Verification

- targeted pytest run for tasks/services
- `pre-commit run --all-files`
- wait for approval

### Phase 5: Add LLM Run Persistence and Metadata

#### Scope

- add a dedicated model for LLM-backed monitoring execution records
- store session and execution metadata
- link LLM runs to produced reports where useful

#### Deliverables

- `LLMRun` or equivalent execution model
- admin visibility
- metadata capture in task flow

#### Tests

- model tests
- persistence tests
- admin tests where relevant

#### Exit Verification

- targeted pytest run
- `pre-commit run --all-files`
- wait for approval

### Phase 6: Final Summary and Notification Behavior

#### Scope

- add one summary stage per scheduled job
- avoid unnecessary LLM calls on healthy unchanged runs
- keep deterministic summaries for low-signal runs
- keep the existing log notification template untouched
- introduce a separate sitemap notification template

#### Deliverables

- final summary policy
- separate notification structure for logs and sitemap
- fallback deterministic summary path
- dedicated sitemap email template modeled after the current log email where useful

#### Tests

- tests for summary policy branching
- tests for no-issue deterministic output
- email rendering tests for separate log and sitemap reports
- regression tests proving the existing log template behavior remains unchanged

#### Exit Verification

- targeted pytest run
- `pre-commit run --all-files`
- wait for approval

### Phase 7: Cutover and Cleanup

#### Scope

- switch Celery beat to the scheduled LLM-backed monitoring jobs
- preserve rollback path temporarily
- retire obsolete prompt constants and dead code once parity is verified

#### Deliverables

- beat schedule update
- cleanup of superseded code paths
- rollout notes and rollback steps

#### Tests

- regression suite for old and new entry points where still present
- configuration tests for Celery scheduling and task routing

#### Exit Verification

- full relevant pytest run
- `pre-commit run --all-files`
- wait for approval

## Better Solution Notes

The original idea was "second report, second LLM call." The refined design is:

- separate scheduled runs
- deterministic job execution
- one summary stage per scheduled job

This preserves the existing 02:00 log-monitoring behavior, cleanly adds a 03:00 sitemap
run every 5 days, and keeps the architecture honest: deterministic scheduled jobs with
LLM analysis, rather than a fake general-purpose agent.

## Risks and Mitigations

### Risk: LLM monitoring complexity grows too fast

Mitigation:
- keep tools deterministic
- phase the rollout
- keep current log task working until cutover is complete

### Risk: Sitemap checks become noisy

Mitigation:
- rate-limit requests
- classify issues by severity
- diff against previous runs
- suppress transient failures behind retry rules

### Risk: Prompt migration causes regression

Mitigation:
- move prompts incrementally
- add prompt asset loader tests
- keep old prompt assembly in place until parity is verified

### Risk: Over-collecting LLM execution metadata

Mitigation:
- store compact execution metadata only
- do not store hidden reasoning traces

## Confirmed Decisions

The following decisions are now fixed unless explicitly changed later:

1. Sitemap cadence:
- every 5 days

2. Notification model:
- separate emails
- log monitoring remains at 02:00
- sitemap monitoring runs at 03:00

3. Target environment for sitemap checks:
- production domain only

4. Metadata identity:
- use generated `session_id`
- do not add `user_id` for now

## Recommended Default Answers

Current approved defaults are:

- sitemap cadence: every 5 days
- notifications: separate emails, logs at 02:00 and sitemap at 03:00
- target domain: production only for sitemap checks
- actor identity: generated `session_id` only

## Suggested Initial File Targets

Likely implementation targets:

- `backend/monitoring/tasks.py`
- `backend/monitoring/services.py`
- `backend/monitoring/models.py`
- `backend/monitoring/agent/agent.py`
- new `backend/monitoring/agent_assets/`
- new sitemap-audit service modules under `backend/monitoring/`

## Approval Policy

The implementation should proceed one phase at a time.

For each phase:

1. implement the scoped changes
2. add or update tests
3. run the agreed pytest scope
4. run `pre-commit run --all-files`
5. stop and wait for approval
