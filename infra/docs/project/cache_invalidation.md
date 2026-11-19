# Cache Invalidation

How the Django backend caches API responses and invalidates them when content
changes.

The frontend (`portfolio-fe`) runs on Cloudflare Workers.

## Cache backend

By default, the API cache uses Django's `DatabaseCache`:

- caches: `default` (table `django_cache`) and Select2 (table `django_select2_cache`)
- tables are created by `python manage.py createcachetable`, which runs after
  `migrate` (dev `be` command and the production `release` job)
- API responses are stored under keys such as `api_cache:/v1/astroimages`

The local production admin opts into `LocMemCache` through `CACHE_BACKEND` in
`docker-compose.supabase.yml`, avoiding database cache writes. This cache is
process-local; the default remains `DatabaseCache`.

## Invalidation flow

1. Django signals (`post_save`, `post_delete`, `m2m_changed`) fire on content
   models. See `backend/core/signals.py`, `backend/astrophotography/signals.py`,
   `backend/users/signals.py`, `backend/shop/signals.py`.
2. The handler calls a `CacheService.invalidate_*` method
   (`backend/core/cache_service.py`).
3. Each call clears the whole cache
   (`cache.clear()`). The prefix argument only documents what changed.
4. The next API request repopulates the cache from the database.

Example:

```python
@receiver([post_save, post_delete], sender=AstroImage)
def invalidate_astroimage_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()
```

## LandingPageSettings edge case

`LandingPageSettings` controls `latest_filters` and image-format toggles, so
saving it also invalidates the astrophotography cache. Changes show up on the
homepage gallery on the next API request.

## Manual clear

```bash
doppler --config dev run -- docker compose exec -T be python manage.py clear_cache
```
