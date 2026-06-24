# AGENTS.md

Repo-level first-stop guide for Codex and future engineering sessions.

## Hard Rules

- Always read this file before doing any work in this repository.
- Before changing behavior, check whether the behavior is already documented.
- Never delete, relocate, or empty files in `infra/docs/project/analysis/` unless the user explicitly names the exact file and asks for that deletion in the current turn.
- Do not commit or push without explicit user permission.
- For commit messages and pull request messages, use the repo-local matching task-specific guidance. Do not route these tasks through external custom skills.

## Agent Docs

- `infra/docs/agent/repository_routing.md`
  Use for project README routing, project-doc map, feature/runbook routing, and doc update expectations.
- `infra/docs/agent/engineering_conventions.md`
  Use for coding conventions, Python/React guidance, clean-code expectations, context hygiene, and testing defaults.
- `infra/docs/agent/implementation_process.md`
  Use for larger changes, phased delivery, and implementation documentation.

## Fast Routing

- Cache, SSR/BFF, deployment/release, monitoring, admin media/image behavior, translations, feature flags, latest images, or total-time stats -> read the matching document listed in `infra/docs/agent/repository_routing.md` before inferring from code.
- Backend validation -> run backend `uv` commands from `backend/`; canonical validation is `cd backend && uv run test`.
- Frontend validation -> use the frontend Docker container rather than assuming the host runtime.

Keep this file tiny. Put stable details in `infra/docs/agent/` and link them here.
