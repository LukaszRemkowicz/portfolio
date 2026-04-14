# Feature Flag Mechanism

This document describes how feature flags work across the Django backend and
the frontend application.

Use this document when:
- adding a new feature-gated frontend module
- debugging why a route or navbar entry still appears after disabling it
- deciding where a new `LandingPageSettings` boolean should be consumed
- checking cache implications for feature-driven UI changes


## Overview

The portfolio uses `LandingPageSettings` as the source of truth for public
feature availability.

Today, the main public feature flags are:
- `programming_enabled`
- `shop_enabled`

The flow is:
1. Django stores the booleans on `LandingPageSettings`
2. the settings API exposes them to the frontend as normalized feature flags
3. the frontend reads them through one shared settings entry point
4. routes and shared UI elements decide whether a module is visible


## Backend Source Of Truth

Backend source of truth lives in:
- `backend/core/models.py`
- `backend/core/serializers.py`
- `backend/core/views.py`

`LandingPageSettings` holds the canonical booleans.

The settings API returns a frontend-oriented payload, for example:

```json
{
  "programming": true,
  "shop": false
}
```

That normalization allows the frontend to avoid coupling itself to Django
field names like `programming_enabled`.


## Frontend Entry Point

Frontend feature flags should always start from:
- `frontend/src/hooks/useSettings.ts`

That hook is the single data-entry point for settings fetched from the backend.

Feature-specific logic should then build on top of:
- `frontend/src/hooks/useFeatureFlag.ts`

This gives two levels of access:
- `useSettings()` for the raw shared settings payload
- `useFeatureFlags()` / `useFeatureFlag()` for reusable boolean checks

When adding a new feature flag, prefer updating this shared hook layer instead
of teaching each module to fetch or interpret settings on its own.


## Expected Frontend Consumption Pattern

For a new module, there are usually three places that should rely on the same
shared feature flag source:

1. Settings layer
- add the flag to the backend serializer and frontend types
- expose it through `useSettings()` / `useFeatureFlag()`

2. Module route
- gate the public route in a dedicated route component
- for example: `ShopRoute`, `ProgrammingRoute`

3. Shared navigation or global UI
- navbar links should only render when the feature is enabled

This keeps the system predictable:
- one backend source of truth
- one frontend settings source of truth
- one shared flag-checking pattern


## Current Pattern

Current routed feature modules follow this shape:

- `shop`
  - backend flag: `LandingPageSettings.shop_enabled`
  - frontend flag: `settings.shop`
  - route gate: `ShopRoute`
  - shared UI gate: `Navbar`

- `programming`
  - backend flag: `LandingPageSettings.programming_enabled`
  - frontend flag: `settings.programming`
  - route gate: `ProgrammingRoute`
  - shared UI gate: `Navbar`


## What To Change For A New Feature

When introducing a new public module such as `events`, `prints`, or `courses`,
the expected steps are:

1. Add a new boolean to `LandingPageSettings`
2. Expose it in the settings serializer as a frontend-friendly flag
3. Add it to `frontend/src/types/index.ts`
4. Extend `FeatureFlagName` in `frontend/src/hooks/useFeatureFlag.ts`
5. Gate the route through a dedicated route component
6. Gate any shared navigation entry through the same shared hook
7. Add focused tests for navbar, route behavior, and SSR behavior if needed


## SSR And Client Behavior

Feature flags affect more than client-side navigation.

They can also affect:
- SSR route prefetch decisions
- whether a route should render or redirect
- whether shared shell content such as the navbar exposes the feature

If a public route is feature-gated, SSR should respect the same flag and avoid
prefetching or rendering the module as if it were always enabled.


## Cache Implications

Feature flags interact with two cache layers:
- backend API cache
- frontend SSR cache

Changing `LandingPageSettings` must invalidate:
- backend settings cache
- any backend API cache tied to the feature
- frontend SSR cache tags that depend on settings

Example:
- disabling `shop` should invalidate both settings and shop-related cached data
- otherwise the frontend can continue to render stale UI or stale content

For broader cache details, see:
- `infra/docs/project/cache_invalidation.md`


## Sitemap Note

Feature flags can also affect SEO output.

If a sitemap includes feature-gated routes such as `/shop` or `/programming`,
the sitemap strategy must match the desired freshness:
- either keep sitemap generation live
- or cache it and explicitly invalidate that cache when relevant flags change

Do not assume sitemap correctness if the route logic is dynamic but the sitemap
response is cached separately.


## Testing Guidance

When changing feature flags, validate at the level where the behavior lives:

- backend
  - settings serializer/view behavior
  - sitemap behavior if the flag affects public URLs
  - cache invalidation if the flag affects cached endpoints

- frontend
  - navbar visibility
  - route gating
  - SSR prefetch behavior when relevant

For frontend tests, use the frontend container rather than assuming the host is
the right runtime.


## Anti-Patterns

Avoid:
- fetching settings separately inside each module
- hardcoding feature decisions in components without using the shared hook
- gating the route but forgetting the navbar, or vice versa
- relying on stale cached settings after admin changes
- introducing different frontend names for the same flag in multiple places


## Summary

The intended pattern is:
- Django `LandingPageSettings` is the source of truth
- the settings API normalizes backend booleans for the frontend
- `useSettings()` is the frontend entry point
- `useFeatureFlag()` is the shared feature-checking layer
- each module consumes the shared flag in its route and shared UI surfaces

That keeps future feature additions local, readable, and testable.
