# Landing Page Total Time Spent System

## Purpose

This document describes how the landing page "total time spent" statistic works
today.

It is meant for:
- engineers changing the statistic
- future LLM/code sessions that need stable implementation context


## Current Truth / Scope

This document describes the current implemented behavior.

If code and this document disagree:
- code is the current truth
- this document should then be updated


## System Summary

The landing page total-time-spent stat is derived from astrophotography image
metadata.

Current model:
- each `AstroImage` stores its own internal `calculated_exposure_hours`
- the public landing-page total is computed from the sum of those per-image
  values
- the API adds a small presentation safety buffer before rounding for display

This is intentionally a derived statistic, not a manually maintained global
counter.


## Data Model

### `AstroImage.calculated_exposure_hours`

Location:
- `backend/astrophotography/models.py`

Purpose:
- stores the parsed exposure duration for one image
- value is internal/derived
- value is stored in hours as a float

Important behavior:
- this field is the source of truth for the total-time calculation
- updates to this field should invalidate landing-page/settings cache

### Landing page API value

Location:
- `backend/core/serializers.py`

Purpose:
- sums `AstroImage.calculated_exposure_hours`
- adds the presentation safety buffer
- rounds to the integer shown in the frontend

Important distinction:
- stored per-image values remain raw derived floats
- frontend receives a rounded presentation statistic


## Calculation Flow

### Per-image calculation

Main task:
- `core.calculate_astroimage_exposure_hours`

Flow:
1. Read one image's `exposure_details`
2. Normalize HTML-rich text into plain text
3. Send the normalized text to the LLM
4. Parse the returned float hour value
5. Save it into `AstroImage.calculated_exposure_hours`
6. Recompute the landing-page total

### Global total recomputation

Main task:
- `core.recalculate_landing_page_total_time_spent`

Flow:
1. Aggregate `Sum("calculated_exposure_hours")`
2. Treat that sum as the raw portfolio total
3. Invalidate landing-page/settings cache
4. Invalidate frontend SSR `settings` cache tag


## Rebuild Command

Management command:
- `recalculate_landing_page_total_time_spent`

Modes:
- default: calculate only images where `calculated_exposure_hours == 0`
- `--recalculate`: rebuild all image values from scratch

Operational use:
- use `--recalculate` after prompt changes
- use the default mode for backfilling newly added images


## Save/Signal Behavior

Relevant signals live in:
- `backend/astrophotography/signals.py`

Current behavior:
- changing default-language `exposure_details` queues per-image recalculation
- deleting an `AstroImage` queues total recomputation
- changing `calculated_exposure_hours` invalidates landing-page/settings cache
  and frontend SSR `settings`

Important rule:
- bulk `QuerySet.update(...)` does not call `save()` and does not trigger model
  signals
- if signal-driven cache invalidation is required, use per-object `save(...)` or
  explicitly invalidate cache afterward


## LLM Boundary

The LLM is used only for interpreting one image's exposure text into decimal
hours.

Current implementation:
- one image per LLM request
- file-backed system prompt
- prompt contains strict arithmetic rules and worked examples
- response must be a single non-negative number

Important limitation:
- this remains LLM-based arithmetic over semi-structured text
- prompt improvements reduce mistakes but do not provide deterministic
  correctness

If higher confidence is required:
- prefer deterministic parsing for known exposure patterns
- reserve the LLM for ambiguous free-form cases only


## Cache Invalidation

This feature touches both backend and frontend cache behavior.

Current invalidation points:
- total recomputation invalidates landing-page backend cache
- total recomputation invalidates frontend SSR `settings`
- `AstroImage.calculated_exposure_hours` changes invalidate the same settings
  cache path

Why this matters:
- the total is exposed via `/v1/settings/`
- clearing only astrophotography cache is not enough for this statistic


## Frontend Rendering

Relevant files:
- `frontend/src/components/About.tsx`
- `frontend/src/types/index.ts`

Current behavior:
- frontend reads `settings.total_time_spent`
- value is shown in the About stat section as `xh +`
- stat includes a reusable tooltip explaining the metric


## Testing Expectations

When changing this feature, cover both backend behavior and frontend rendering.

Minimum backend coverage:
- service parsing and prompt loading
- per-image task behavior
- total recomputation behavior
- signal behavior for `exposure_details`
- signal behavior for `calculated_exposure_hours`
- command behavior
- settings serializer output

Minimum frontend coverage:
- About stat rendering when value exists
- About stat hiding when value is missing
- tooltip rendering behavior


## Current State Summary

The system currently works in this form:

- per-image derived hours stored on `AstroImage`
- total derived from the sum of image values
- integer public display value produced in the settings serializer
- cache invalidation wired to settings-dependent paths
- rebuild command for backfill and full recalculation
- prompt-driven LLM extraction with worked arithmetic examples
