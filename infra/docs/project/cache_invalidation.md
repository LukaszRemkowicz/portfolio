# Cache Invalidation

How the Django backend caches API responses and invalidates them when content
changes.

> The frontend (`portfolio-fe`) runs on Cloudflare Workers. The old Node SSR
> cache webhook (`backend/common/ssr_cache.py`, `SSR_CACHE_INVALIDATION_URL`) is
> a disabled leftover: the URL defaults to an empty string, and the task returns
> early without sending anything. Signals still `submit()` it, which is a no-op.

## Cache backend

The API cache is Django's `DatabaseCache`:

- caches: `default` (table `django_cache`) and Select2 (table `django_select2_cache`)
- tables are created by `python manage.py createcachetable`, which runs after
  `migrate` (dev `be` command and the production `release` job)
- API responses are stored under keys such as `api_cache:/v1/astroimages`

## Invalidation flow

1. Django signals (`post_save`, `post_delete`, `m2m_changed`) fire on content
   models. See `backend/core/signals.py`, `backend/astrophotography/signals.py`,
   `backend/users/signals.py`, `backend/shop/signals.py`.
2. The handler calls a `CacheService.invalidate_*` method
   (`backend/core/cache_service.py`).
3. `DatabaseCache` cannot delete by prefix, so each call clears the whole cache
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
