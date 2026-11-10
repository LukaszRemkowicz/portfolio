# Tags in Latest Images

This document explains how the "Tags" (filters) in the "Latest Images" section of
the homepage are configured and cached in the Django backend. Rendering happens
in the separate `portfolio-fe` repository.

## 1. Controlling the Tags (Django Admin)
The tags shown above the "Latest Images" gallery are not generated from the most
recent uploads. They are curated in the Django Admin.

- **Model:** `LandingPageSettings`
- **Field:** `latest_filters` (Many-to-Many relationship to `astrophotography.Tag`)

The selected tags are returned by the latest-images API (`/v1/astroimages/latest/`)
and rendered by the frontend as clickable category filters.

## 2. Caching
The latest-images payload (including the configured tags) is cached in the Django
`DatabaseCache` like other API responses.

## 3. Cache Invalidation Flow
Because the available tags are tied to `LandingPageSettings`, changing them must
flush the cached astrophotography responses.

When you modify the tags on `LandingPageSettings` in the Django admin,
`CacheService.invalidate_astrophotography_cache()` is called from the signal
handler. It clears the database cache, including the tags and the latest images
payload. The next request returns the updated tags and images.

See `infra/docs/project/cache_invalidation.md` for the general mechanism.
