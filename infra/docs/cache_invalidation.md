# Frontend and Backend Cache Invalidation

This document explains how cache invalidation works between the Django backend and the Node.js frontend (SSR server).

## Overview
The architecture relies on two layers of caching to ensure high performance and low latency:
1. **Backend API Cache (Django/Redis)**: Caches the JSON responses for API endpoints.
2. **Frontend SSR Shell Cache (Node.js)**: Caches the shared HTML shell parts (e.g. Navigation, Footer, Background, Latest Images) injected during Server-Side Rendering (SSR).

When content changes in the Django admin, the backend must clear both its own API cache and proactively notify the frontend to flush its SSR cache.

## Django Signals
We use Django signals (`post_save`, `post_delete`, `m2m_changed`) to detect when models are modified.
For example, in `backend/core/signals.py` and `backend/astrophotography/signals.py`:

```python
@receiver([post_save, post_delete], sender=AstroImage)
def invalidate_astroimage_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["latest-astro-images", "travel-highlights"])
```

### 1. Backend API Cache Invalidation
The `CacheService` handles removing the cached JSON payloads from Redis using prefix matching (e.g. `api_cache:/v1/astroimages`).
This ensures that the next API call (either from a browser fetch or from the SSR Node server) returns fresh data.

### 2. Frontend SSR Cache Invalidation Hook
For the SSR shell, we rely on Celery tasks triggered `on_commit` to send an HTTP POST webhook to the frontend Node server.
The webhook URL is configured via the `SSR_CACHE_INVALIDATION_URL` environment variable. The backend uses the shared task `invalidate_frontend_ssr_cache_task`, which sends a payload containing the cache tags to invalidate.

Example payload sent to Node:
```json
{
  "tags": ["latest-astro-images", "settings"]
}
```

## Frontend SSR Server
The frontend runs a Node.js server (`server/index.mjs`) which exposes an internal endpoint: `/internal/cache/invalidate`.
This endpoint expects a POST request with the `tags` array and a matching Authorization Bearer token (`SSR_CACHE_INVALIDATION_TOKEN`).

When the backend hits this endpoint, the Node server executes `invalidateCacheTags(tags)` in `server/ssrCache.js`.

### What gets cleared?
The Node server groups its SSR cache by "tags" defined in `SHELL_RESOURCES` (e.g., `background`, `latestAstroImages`, `profile`, `settings`, `travelHighlights`).
When a tag like `"latest-astro-images"` is invalidated, the Node SSR server dumps its in-memory cache for that specific resource. The very next time a user visits a page, the SSR process will execute a fresh fetch against the clear Backend API. Since the backend just flushed its redis cache too, the Node server retrieves the latest database data, caches it again, and serves the updated HTML.

## LandingPageSettings Edge Case
Because `LandingPageSettings` dictates which images are tagged as the "latest_filters" and whether "serve_webp_images" is toggled, saving `LandingPageSettings` also invalidates the astrophotography backend cache and the `"latest-astro-images"` frontend SSR cache. This ensures that changes to the settings immediately bubble up to the homepage gallery.
