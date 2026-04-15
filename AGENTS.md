# AGENTS.md

## Purpose

This file is the repo-level working guide for Codex and future engineering sessions.

Use it as the first-stop routing file before implementation. This file is mainly a router to documentation and hard repo rules, not the full source of truth for project behavior.


## Project Context

For general project context, architecture, and repository structure, read:

- `README.md`
- `frontend/README.md`
- `backend/README.md`
- `collector/README.md`
- `infra/scripts/README.md`

Use this file mainly as a routing guide for task-specific documentation in `infra/docs/project/` and `infra/docs/agent/`.

Check `.agent/skills/` first for task-specific execution guidance when relevant.


## Project Docs

Use `infra/docs/project/` for system behavior, architecture, runbooks, and feature-specific technical context.


## Agent/Process Docs

Use `infra/docs/agent/engineering_conventions.md` for repo coding conventions, Python/React guidance, and clean-code expectations.
Use `infra/docs/agent/implementation_process.md` for larger changes, phased delivery, and implementation-documentation expectations.
Use `.agent/skills/` for task-specific authoring guidance, especially for commit messages and pull request messages.


## Working Rule

Before making changes, check whether the behavior is already documented.

Preferred order when context is missing:

1. Read this file
2. Check `.agent/skills/` for relevant task-specific guidance
3. Read the relevant file in `infra/docs/project/` or `infra/docs/agent/`
4. Read the matching README if needed
5. Only then dive into implementation code

If a task touches deployment, release flow, SSR/BFF architecture, monitoring, cache invalidation, or admin media/image behavior, consult docs first instead of inferring behavior from scattered files.


## Document Map

Use these documents as fast context before implementation.

- `infra/docs/project/cache_invalidation.md`
  Use for stale homepage/shared content, Django signals, Redis invalidation, or FE SSR cache invalidation. Describes the two-layer cache model and backend-to-frontend invalidation flow.
- `infra/docs/project/django_admin_image_cropper_mechanism.md`
  Use for Django admin image cropper changes, preview/media bugs, or extending cropper behavior. Describes the cropper contract, browser flow, media serving rules, and derived image pipeline.
- `infra/docs/project/latest_images_tags.md`
  Use for homepage latest-image filters and `LandingPageSettings.latest_filters`. Describes how tags are curated, rendered, cached, and invalidated.
- `infra/docs/project/feature_flag_mechanism.md`
  Use for `LandingPageSettings`-driven feature visibility, frontend route/navbar gating, and adding new public feature flags. Describes the backend-to-frontend feature-flag flow and expected consumption pattern.
- `infra/docs/project/landing_page_total_time_spent_system.md`
  Use for landing-page total-time calculation, `AstroImage.calculated_exposure_hours`, rebuild flow, serializer rounding, and cache invalidation. Describes the current derived-stat architecture and operational caveats.
- `infra/docs/project/monitoring_system_overview.md`
  Use for monitoring jobs, scheduling, queue routing, log analysis, sitemap analysis, and LLM boundaries. Describes the live monitoring architecture and hard invariants.
- `collector/README.md`
  Use for the dedicated Python log collector, Docker collector image, manifest-driven source resolution, runtime contract, manual runs, cron installation, and rollout checks. Describes the standalone collector app and its operational boundary.
- `infra/docs/project/translation_system_overview.md`
  Use for translation lifecycle, `TranslationTask` debugging, translation admin behavior, serializer fallback behavior, and adding translation support to new models. Describes the async translation architecture and its operational boundaries.
- `infra/docs/project/release_deploy_architecture.md`
  Use for release scripts, deploy logic, image naming, artifact flow, and rollback behavior. Describes the tag-based release/deploy model and script responsibilities.
- `infra/docs/prod/fail2ban_probe_blocker_playbook.md`
  Use for production probe blocking, repeated `.env` scans, and host-level IP banning. Describes the `fail2ban` setup for nginx and Traefik logs.
- `infra/docs/project/SSR Migration/STAGE-1_ssr_migration.md`
  Use for SSR architecture decisions and initial migration direction. Describes the preferred incremental SSR strategy and early-phase non-goals.
- `infra/docs/project/SSR Migration/STAGE-2_full_ssr_bff_migration_plan.md`
  Use for BFF route ownership and FE-to-BE transport migration. Describes the target BFF architecture, endpoint inventory, and transitional `/app/*` rules.
- `infra/docs/project/architecture.png`
  Use for quick visual orientation. Describes the platform architecture at a high level.
- `infra/docs/agent/engineering_conventions.md`
  Use for repo coding conventions, Python/React guidance, and clean-code expectations. Describes implementation style rules that do not belong in this router file.
- `infra/docs/agent/implementation_process.md`
  Use for phased work, implementation-plan docs, and documentation/process expectations for larger changes.


## Short Routing Guide

Use this quick mapping when a task arrives:

- Cache bug or stale homepage content -> `infra/docs/project/cache_invalidation.md`
- Homepage latest-image filters/tags -> `infra/docs/project/latest_images_tags.md`
- Feature-gated frontend modules or `LandingPageSettings` booleans -> `infra/docs/project/feature_flag_mechanism.md`
- Landing page total-time stat or exposure-hours rebuilds -> `infra/docs/project/landing_page_total_time_spent_system.md`
- Django admin image cropping or preview/media bug -> `infra/docs/project/django_admin_image_cropper_mechanism.md`
- Monitoring, Celery monitoring jobs, sitemap checks -> `infra/docs/project/monitoring_system_overview.md`
- Collector app architecture, manifest contract, rebuild/run path, or cron rollout work -> `collector/README.md`
- Translation queue/status/admin translation issues -> `infra/docs/project/translation_system_overview.md`
- Release/deploy script logic or image naming -> `infra/docs/project/release_deploy_architecture.md`
- Production release procedure -> `infra/scripts/README.md`
- SSR architecture direction -> `infra/docs/project/SSR Migration/STAGE-1_ssr_migration.md`
- BFF route ownership or `/app/...` migration -> `infra/docs/project/SSR Migration/STAGE-2_full_ssr_bff_migration_plan.md`


## Implementation Guidance

- Prefer documented behavior over assumptions.
- If docs and code disagree, code is the current truth; update docs after confirming behavior.
- If a proposed implementation seems risky, inconsistent, or likely incorrect, say so clearly and discuss it. Push back when needed; collaboration and correction are expected.
- Avoid broad infra changes without checking the relevant runbook first.
- For commit messages and pull request messages, check `.agent/skills/` first and follow the matching message-writing guidance.
- For deploy/release work, be explicit about environment: `dev`, `stage`, or `production`.
- For monitoring work, remember the hard boundary: deterministic code gathers facts; the LLM summarizes and interprets.
- For cache-related work, think about both backend Redis invalidation and frontend SSR cache invalidation.


## Testing

Use these defaults when validating changes:

- Backend: use the backend project test entrypoint, `uv run test`
  Treat this as the canonical backend validation command for the repo, not as a shorthand for "run pytest directly". This wrapper may use the expected backend runtime and scripts under `backend/`.
- Frontend: use the frontend Docker container for test commands rather than assuming the host machine is the correct runtime


## Keep This File Updated

When adding a new important runbook or stable architecture doc under `infra/docs/project/` or `infra/docs/agent/`, add a short entry here with path, when to use it, and what it describes.

Keep this file short, practical, and optimized for routing, not for full project documentation.
