# Implementation Process

## Purpose

This document contains process conventions for larger changes, especially phased work.

Use it when a task is big enough to benefit from implementation planning, staged delivery, or evolving technical documentation.


## Large Changes

- For a large feature or architectural change, prefer a short implementation doc placed directly in `infra/docs/project/NEW/` before coding.
- Break large changes into phases when that reduces risk.
- When work is split into phases, start or update the matching documentation at the beginning of the phased work, not only at the end.
- Each phase should extend the documentation with current scope, decisions, and status.
- Each phase should have matching verification, and new behavior should come with tests.


## Documentation Placement

- Place implementation docs directly in `infra/docs/project/NEW`.
- Do not create a separate `infra/docs/NEW/` area.
- Name new docs clearly so they are easy to discover and route to later.


## Practical Expectation

- Use process guidance when it helps reduce risk, improve clarity, or coordinate a large change.
- Do not force full phased ceremony for small fixes that do not need it.
