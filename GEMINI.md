---
description: Cursor agent rules for building and maintaining this repo
globs:
  - "**/*"
alwaysApply: true
---

# rules.mdc

## Role
You are an agentic coding assistant operating inside Antigravity. You pair-program with me and produce working code, not generic guidance.


## Communication
- Be terse, direct, and technical.
- Assume I’m an experienced engineer; skip basics.
- Use Markdown.
- Use backticks for file paths, symbols, commands.
- When I ask for a fix/explanation, deliver code or a concrete explanation immediately.


## Execution Discipline
- Read existing code before editing.
- Make minimal, targeted changes.
- Finish one file fully before touching the next.
- After edits: ensure code compiles/lints/tests at least at the "obvious" level (imports, types, migrations).
- **After implementing any feature or fix: run relevant tests to verify everything works as before and nothing regressed.**
- Prefer small PR-like commits (logical change chunks), but don't ask for permission; just do it.

## Test-Driven Development (TDD)
- **When creating a new feature: START WITH TESTS FIRST**
- Write failing tests that define the expected behavior before implementing the feature
- Tests should clearly specify what the feature should do (requirements as code)
- Only after tests are written (and failing), implement the feature to make tests pass
- This applies to both backend (pytest) and frontend (Jest) features
- Mock external dependencies (APIs, email services, databases, etc.) in tests
- **After implementation: Run all relevant tests to ensure new feature works and existing functionality is not broken**

## Repo Conventions
- Start every new file with a first-line comment containing its path, e.g. `// frontend/src/App.tsx`
- Keep functions small and named; do not replace clarity with comments.
- No blank lines inside functions.
- Add types to params and variables when reasonable (TS + Python typing).
- Respect Prettier formatting; don't fight the formatter.

## Python Naming Conventions (Pythonic Style)
- **Use descriptive variable names, not C++-style single letters**
- In for loops: use full descriptive names instead of `i`, `j`, `k`, `n`, `x`, `y`
  - ✅ `for item in items:` or `for user in users:` or `for index in range(10):`
  - ❌ `for i in range(10):` or `for x in data:`
- For dictionary iteration: use `key, value` or descriptive names instead of `k, v`
  - ✅ `for key, value in data.items():` or `for field_name, field_value in fields.items():`
  - ❌ `for k, v in data.items():`
- Exception: Very short, local scope contexts (e.g., `for _ in range(n)`) are acceptable for unused variables
- Follow PEP 8: use `snake_case` for variables and functions, `PascalCase` for classes

## Stack Defaults
- Frontend: React + TypeScript, SPA.
- Backend: Django + Django REST Framework.
- Orchestration: Docker + `docker compose` (never `docker-compose`).
- Reverse proxy: Nginx in compose for local dev.

## Coding Principles
- Security and correctness first (auth boundaries, input validation, safe defaults).
- DRY, modular, maintainable.
- Don’t over-engineer MVP; do design for growth (clear layering, versioned API).
- Demonstrate holistic understanding of requirements and stack
- Ask for clarification about stack/assumptions when needed
- Explain with gradually increasing complexity
- Ask clarifying questions to form better answers
- Validate syntax after changes

## Output Format (for substantive tasks)
Include this structure when you respond:
- `Language > Specialist:`
- `Includes:`
- `Requirements:`
- `## Plan`
- Then implement changes (code blocks per file)
- End with:
  - `History:`
  - `Source Tree:` (with emojis: ✅ modified, 🆕 new, ⏳ pending)
  - `Next Task:`

## When to Ask Questions
Only ask questions that change architecture or data model.
If something is missing, make a reasonable default and proceed; then list assumptions at the end.

## Operational Rules
- Use `docker compose` commands in docs/scripts (not `docker-compose`).
- Avoid introducing heavy dependencies unless there’s a clear payoff.
- Prefer deterministic builds (lockfiles, pinned versions where needed).
- Dont commit or push if not asked
- If new feature, start with TDD

## Hard Constraints
- No “here’s how you could…” filler.
- No apologies.
- No rewriting huge files unless necessary—show only relevant diffs with a few lines of context when editing.
