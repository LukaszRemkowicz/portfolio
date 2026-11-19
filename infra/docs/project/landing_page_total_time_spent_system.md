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

### Landing page API value

Location:
- `supabase/functions/api/core.ts` (settings payload)

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
- `astrophotography.calculate_astroimage_exposure_hours`

Flow:
1. `AstroImage.save()` queues the task when the default-language
   `exposure_details` changed and is non-empty
2. Read one image's `exposure_details`
3. Normalize HTML-rich text into plain text
4. Send the normalized text to the LLM
5. Parse the returned float hour value
6. Save it into `AstroImage.calculated_exposure_hours`
7. Nothing is cached: the Edge Function sums the stored values on each request

Clearing the saved default-language exposure details resets the stored hours to
zero without scheduling a calculation.
A completed calculation updates the hours only if the saved default-language
exposure text still matches its input; otherwise the stale result is discarded.

### Global total rendering

The portfolio total is not persisted or asynchronously recomputed anymore.

Flow:
1. `AstroImage.calculated_exposure_hours` is kept current per image
2. The settings endpoint aggregates the sum of `calculated_exposure_hours` on demand
3. The endpoint adds the presentation safety buffer
4. The API returns the rounded value to the frontend


## Rebuild Command

Management command:
- `recalculate_landing_page_total_time_spent`

Implementation location:
- `backend/astrophotography/management/commands/recalculate_landing_page_total_time_spent.py`

Modes:
- default: calculate only images where `calculated_exposure_hours == 0`
- `--recalculate`: rebuild all image values from scratch

Operational use:
- use `--recalculate` after prompt changes
- use the default mode for backfilling newly added images
- the command recalculates each image directly in a loop; it does not dispatch background tasks
- failures preserve the prior value, do not stop other images, and are reported by ID


## Save Behavior

Current behavior:
- `AstroImage.save()` queues per-image recalculation when the default-language
  `exposure_details` changed and is non-empty
- clearing the default-language `exposure_details` resets the hours to 0 without a task

Important rule:
- bulk `QuerySet.update(...)` does not call `save()` and does not queue recalculation


## LLM Boundary

The LLM is used only for interpreting one image's exposure text into decimal
hours.

Current implementation:
- one image per LLM request
- `backend/astrophotography/agent/agent.py` owns the prompt/provider call boundary
- `backend/astrophotography/services.py` owns the LLM-backed extraction
  service and exposure-hours validation
- a future orchestrator can choose between the LLM agent service and
  non-agent fallback parsers without changing the domain service
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


## Caching

There is no API cache. The total is exposed via `/v1/settings/` and is read from
the stored per-image values by the Supabase Edge Function on each request, so a
recalculation shows up immediately without clearing anything.

## Frontend Rendering

The frontend (`portfolio-fe`) reads `settings.total_time_spent` from `/v1/settings/`
and shows it in the About stat section.


## Testing Expectations

When changing this feature, cover backend behavior (frontend rendering is tested in `portfolio-fe`).

Minimum backend coverage:
- service parsing and prompt loading
- per-image task behavior
- save behavior for `exposure_details`
- command behavior


## Current State Summary

The system currently works in this form:

- per-image derived hours stored on `AstroImage`
- `AstroImage.save()` is the trigger point for per-image recalculation
- total derived on the fly from the sum of image values
- integer public display value produced by the settings endpoint (Supabase function)
- rebuild command for backfill and full recalculation without task fan-out
- prompt-driven LLM extraction with worked arithmetic examples
