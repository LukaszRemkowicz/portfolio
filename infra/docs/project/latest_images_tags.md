# Tags in Latest Images

This document explains how the "Tags" (filters) in the "Latest Images" section of
the homepage are configured in the Django backend. Rendering happens
in the separate `portfolio-fe` repository.

## 1. Controlling the Tags (Django Admin)
The tags shown above the "Latest Images" gallery are not generated from the most
recent uploads. They are curated in the Django Admin.

- **Model:** `LandingPageSettings`
- **Field:** `latest_filters` (Many-to-Many relationship to `astrophotography.Tag`)

The selected tags are returned by the latest-images API (`/v1/astroimages/latest/`, served by the Supabase function)
and rendered by the frontend as clickable category filters.
