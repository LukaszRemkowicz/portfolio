# Engineering Conventions

## Purpose

This document contains repo implementation conventions that are useful during coding, but too detailed for `AGENTS.md`.

Use this file for style and implementation guidance. Use `AGENTS.md` for routing and hard repo rules.


## General

- Read relevant docs or code before editing.
- Make minimal, targeted changes.
- Prefer small, clear functions over clever abstractions.
- Avoid heavy new dependencies unless there is a clear payoff.
- Use `docker compose`, not `docker-compose`.
- After a feature or fix, run the relevant tests for the touched area.
- Do not commit or push automatically without explicit user permission.


## Python

- Follow PEP 8 unless the existing local pattern in a file clearly differs.
- Follow normal Python naming: `snake_case` for variables/functions, `PascalCase` for classes.
- Prefer descriptive variable names over cryptic single-letter names.
- In loops and dictionary iteration, use meaningful names when practical, for example `image`, `user`, `field_name`, `field_value`.
- Keep code compatible with the project's typing and `mypy` expectations in touched areas.
- Add type hints where they improve clarity.
- Add docstrings for non-trivial public modules, classes, and functions.


## Design Principles

- Prefer clear, readable code over clever or overly compact code.
- Apply DRY in moderation: remove real duplication, but do not create premature abstractions.
- Prefer SOLID-style boundaries when they improve maintainability, especially around services, adapters, and domain logic.
- Keep responsibilities narrow: views/routes handle transport, services handle orchestration, models/types hold domain structure.
- Refactor toward simpler structure when touching confusing code, but avoid unnecessary rewrites.


## React / Frontend

- Keep browser-only logic isolated from shared SSR code.
- Prefer functional components and custom hooks for reusable behavior.
- Do not introduce client-only assumptions into SSR paths without guarding them.
- Keep FE-owned transport endpoints under `/app/*` separate from public page routes.
- Reuse existing React Query, routing, and SEO patterns unless there is a strong reason to change them.
