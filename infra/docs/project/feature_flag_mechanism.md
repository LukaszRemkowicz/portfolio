# Feature Flag Mechanism

This document describes the backend half of the feature flags. The frontend
half lives in the separate [`portfolio-fe`](https://github.com/LukaszRemkowicz/portfolio-fe)
repository (React Router 7 on Cloudflare Workers); see that repo for how
routes and navigation consume the flags.

Use this document when:
- adding a new `LandingPageSettings` boolean that gates a public module
- debugging why the settings API still returns an old flag value


## Overview

`LandingPageSettings` is the source of truth for public feature availability.

Today, the main public feature flags are:
- `programming_enabled`
- `shop_enabled`

The flow is:
1. Django stores the booleans on `LandingPageSettings`
2. the settings API (Supabase function, `supabase/functions/api`) exposes them as normalized feature flags
3. the frontend reads them and decides whether a module is visible


## Backend Source Of Truth

Backend source of truth lives in:
- `backend/core/models.py`
- `supabase/functions/api/core.ts` (settings payload)

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
2. Expose it in the settings payload of the Supabase function as a frontend-friendly flag
3. Add function tests

Then consume the flag in `portfolio-fe`.


## Testing Guidance

Settings payload and sitemap behavior are covered by the function tests
(`cd supabase/functions/api && deno task test`). Frontend behavior (navbar, route
gating) is tested in `portfolio-fe`.
