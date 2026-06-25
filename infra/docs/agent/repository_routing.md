# Repository Routing

## Purpose

This document contains the detailed repo routing that used to live in
`AGENTS.md`. Read it when the tiny root router points here or when task context
is missing.

## Project Context

For general project context, architecture, and repository structure, read:

- `README.md`
- `frontend/README.md`
- `backend/README.md`
- `infra/scripts/README.md`

Use `infra/docs/project/` for system behavior, architecture, runbooks, and
feature-specific technical context.

Use Codex skills on demand through the current session's available skill list.
Prefer built-in/session Codex skills first. Custom personal skills may also live
in `../skills`; consult that library only when no available Codex skill clearly
covers the task, and read only the relevant skill entry point.

## Context Hygiene

Do not open large analysis records by default. Files under
`infra/docs/project/analysis/` are for explicit planning, audit, and phase/TODO
work. Read them only when the user asks for analysis/TODO/phase context or when
smaller routed docs and targeted code inspection are insufficient.

When the user gives a precise file, function, method, or expected behavior, start
there. Expand only to direct callers, tests, and documented contracts before
running broad searches.

## Preferred Context Order

When context is missing:

1. Read `AGENTS.md`.
2. Use available Codex skills only when the task clearly matches them; use a
   matching custom skill from `../skills` only as a fallback.
3. Read the relevant file in `infra/docs/project/` or `infra/docs/agent/`.
4. Read the matching README if needed.
5. Only then inspect implementation code.

If docs and code disagree, code is the current truth; update docs after
confirming behavior.

## Project Document Map

- `infra/docs/project/cache_invalidation.md`
  Use for stale homepage/shared content, Django signals, Redis invalidation, or
  frontend SSR cache invalidation. Describes the two-layer cache model and
  backend-to-frontend invalidation flow.
- `infra/docs/project/django_admin_image_cropper_mechanism.md`
  Use for Django admin image cropper changes, preview/media bugs, or extending
  cropper behavior. Describes the cropper contract, browser flow, media serving
  rules, and derived image pipeline.
- `infra/docs/project/latest_images_tags.md`
  Use for homepage latest-image filters and `LandingPageSettings.latest_filters`.
  Describes how tags are curated, rendered, cached, and invalidated.
- `infra/docs/project/feature_flag_mechanism.md`
  Use for `LandingPageSettings`-driven feature visibility, frontend route/navbar
  gating, and adding public feature flags. Describes the backend-to-frontend
  feature-flag flow and expected consumption pattern.
- `infra/docs/project/landing_page_total_time_spent_system.md`
  Use for landing-page total-time calculation,
  `AstroImage.calculated_exposure_hours`, rebuild flow, serializer rounding, and
  cache invalidation. Describes the derived-stat architecture and operational
  caveats.
- `infra/docs/project/logging_structure_overview.md`
  Use for backend/frontend/nginx logging formats, JSON-vs-plain-text status, and
  application log emission structure.
- `infra/docs/project/translation_system_overview.md`
  Use for translation lifecycle, `TranslationTask` debugging, translation admin
  behavior, serializer fallback behavior, and adding translation support to new
  models. Describes the async translation architecture and operational
  boundaries.
- `infra/docs/project/release_deploy_architecture.md`
  Use for release scripts, deploy logic, image naming, artifact flow, and
  rollback behavior. Describes the tag-based release/deploy model and script
  responsibilities.
- `infra/docs/project/SSR Migration/STAGE-1_ssr_migration.md`
  Use for SSR architecture decisions and initial migration direction. Describes
  the preferred incremental SSR strategy and early-phase non-goals.
- `infra/docs/project/SSR Migration/STAGE-2_full_ssr_bff_migration_plan.md`
  Use for BFF route ownership and FE-to-BE transport migration. Describes the
  target BFF architecture, endpoint inventory, and transitional `/app/*` rules.
- `infra/docs/project/architecture.png`
  Use for quick visual orientation. Describes the platform architecture at a high
  level.
- `infra/docs/agent/image_variant_quickstart.md`
  Use as the cheap entry point for image variant specs, generated image files,
  variant sync, and compatibility methods before opening larger analysis docs.

## Short Routing Guide

- Cache bug or stale homepage content -> `infra/docs/project/cache_invalidation.md`
- Homepage latest-image filters/tags -> `infra/docs/project/latest_images_tags.md`
- Feature-gated frontend modules or `LandingPageSettings` booleans -> `infra/docs/project/feature_flag_mechanism.md`
- Landing page total-time stat or exposure-hours rebuilds -> `infra/docs/project/landing_page_total_time_spent_system.md`
- Django admin image cropping or preview/media bug -> `infra/docs/project/django_admin_image_cropper_mechanism.md`
- Backend/frontend/nginx logging structure -> `infra/docs/project/logging_structure_overview.md`
- Translation queue/status/admin translation issues -> `infra/docs/project/translation_system_overview.md`
- Release/deploy script logic or image naming -> `infra/docs/project/release_deploy_architecture.md`
- Production release procedure -> `infra/scripts/README.md`
- SSR architecture direction -> `infra/docs/project/SSR Migration/STAGE-1_ssr_migration.md`
- BFF route ownership or `/app/...` migration -> `infra/docs/project/SSR Migration/STAGE-2_full_ssr_bff_migration_plan.md`
- Image variant generation, `ImageVariantSpec`, `ViewportWidths`, or
  `ImageVariantModelMixin` -> `infra/docs/agent/image_variant_quickstart.md`
- Explicit phase/TODO/analysis work -> the named file under
  `infra/docs/project/analysis/`

## Documentation Maintenance

When adding a new important runbook or stable architecture doc under
`infra/docs/project/` or `infra/docs/agent/`, add a short entry here with path,
when to use it, and what it describes.
