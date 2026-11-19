# Cache

Django no longer serves or caches API responses: the public API runs in the
Supabase Edge Function (see `supabase_api.md`), and the DRF API, `CacheService`
and the cache-invalidation signals were removed.

The frontend (`portfolio-fe`) runs on Cloudflare Workers.

## What is still cached

Django's `CACHES` (`backend/settings/base.py`) are still configured:

- `default` (table `django_cache`) is used by parler and other Django internals
- `select2` (table `django_select2_cache`) is used by Django Select2 in the admin
- tables are created by `python manage.py createcachetable`, which runs after
  `migrate`

The local production admin opts into `LocMemCache` through `CACHE_BACKEND` in
`docker-compose.supabase.yml`, avoiding database cache writes. This cache is
process-local; the default remains `DatabaseCache`.

## Manual clear

```bash
doppler --config dev run -- docker compose exec -T be python manage.py clear_cache
```
