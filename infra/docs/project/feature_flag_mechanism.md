# Feature Flag Mechanism

This document describes the backend half of the feature flags. The frontend
half lives in the separate [`portfolio-fe`](https://github.com/LukaszRemkowicz/portfolio-fe)
repository (React Router 7 on Cloudflare Workers); see that repo for how
routes and navigation consume the flags.

Use this document when:
- adding a new `LandingPageSettings` boolean that gates a public module
- debugging why the settings API still returns an old flag value
- checking cache implications for feature-driven changes


## Overview

`LandingPageSettings` is the source of truth for public feature availability.

Today, the main public feature flags are:
- `programming_enabled`
- `shop_enabled`

The flow is:
1. Django stores the booleans on `LandingPageSettings`
2. the settings API exposes them as normalized feature flags
3. the frontend reads them and decides whether a module is visible


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

That normalization keeps the frontend independent of Django field names like
`programming_enabled`.

Current flags:

- `shop`: `LandingPageSettings.shop_enabled`
- `programming`: `LandingPageSettings.programming_enabled`


## What To Change For A New Feature

Backend steps for a new public module such as `events` or `courses`:

1. Add a new boolean to `LandingPageSettings` (with a migration)
2. Expose it in the settings serializer as a frontend-friendly flag
3. Make sure saving `LandingPageSettings` invalidates the cache entries the
   feature depends on
4. Add serializer/view tests

Then consume the flag in `portfolio-fe`.


## Cache Implications

The settings endpoint is served from the Django `DatabaseCache`. Saving
`LandingPageSettings` clears the API cache through `CacheService` (see
`infra/docs/project/cache_invalidation.md`), so a flag change is visible on the
next API request.

Example: disabling `shop` should invalidate both settings and shop-related
cached data, otherwise stale content can still be served.


## Sitemap Note

Feature flags can also affect SEO output.

If a sitemap includes feature-gated routes such as `/shop` or `/programming`,
the sitemap strategy must match the desired freshness:
- either keep sitemap generation live
- or cache it and explicitly invalidate that cache when relevant flags change

Do not assume sitemap correctness if the route logic is dynamic but the sitemap
response is cached separately.


## Testing Guidance

Backend tests should cover:
- settings serializer/view behavior
- sitemap behavior if the flag affects public URLs
- cache invalidation if the flag affects cached endpoints

Run them with `cd backend && uv run test`. Frontend behavior (navbar, route
gating) is tested in `portfolio-fe`.
