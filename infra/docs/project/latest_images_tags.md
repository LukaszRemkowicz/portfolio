# Tags in Latest Images

This document explains how the "Tags" (filters) work within the "Latest Images" section on the homepage, and how they are configured and cached between the Django Backend and Node.js Frontend.

## 1. Controlling the Tags (Django Admin)
The specific tags that appear above the "Latest Images" gallery are not automatically generated from the most recent uploads. Instead, they are explicitly curated via the Django Admin to allow complete control over the visitor experience.

- **Model:** `LandingPageSettings`
- **Field:** `latest_filters` (Many-to-Many relationship to `astrophotography.Tag`)

When an admin selects tags in the `latest_filters` field on the `LandingPageSettings`, those exact tags are passed to the frontend to be rendered as clickable category filters above the latest images section.

## 2. Frontend Rendering & SSR Caching
The Node.js Server-Side Rendering (SSR) process fetches the latest images payload (which includes the configured tags) from the backend API: `/v1/astroimages/latest/`.

To ensure the homepage loads quickly for all visitors, the Node.js frontend caches this specific section under a dedicated SSR cache key:
- **SSR Cache Tag:** `"latest-astro-images"`

Similarly, the React client expects the tags to be provided in the initial HTML payload (dehydrated state) to prevent content flashes when the user loads the page.

## 3. Cache Invalidation Flow
Because the available Tags are tied to `LandingPageSettings`, updating these tags requires flushing both the backend and frontend caches to prevent visitors from seeing stale filters.

When you modify the tags on the `LandingPageSettings` model in the Django admin:
1. **Backend Cache Flush:** `CacheService.invalidate_astrophotography_cache()` is called. This clears the Redis cache for all astrophotography responses, including the tags and the latest images payload.
2. **Frontend SSR Flush:** An asynchronous Celery task (`invalidate_frontend_ssr_cache_task`) sends a webhook to the Node.js SSR server containing the `["latest-astro-images"]` key. This forces the Node server to drop its cached HTML shell piece for the latest images gallery.

On the very next page visit, the frontend fetches the freshly updated tags and images direct from the backend, caches them, and correctly renders the new filters.
