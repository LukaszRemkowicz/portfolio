# Portfolio Frontend

React + TypeScript frontend rendered by a Node SSR server. The frontend owns:

- SSR page rendering
- BFF transport for the remaining browser-side JSON flows
- public env injection for the HTML shell
- frontend-side SSR shell caching

## Frontend Role In The Current Architecture

The frontend server is the main public application entrypoint on `SITE_DOMAIN`.

Request flow:

1. browser requests a page on `SITE_DOMAIN`
2. frontend SSR renders HTML
3. frontend server fetches backend data internally
4. dehydrated React Query state is embedded into the HTML
5. browser hydrates
6. if client-side JSON is still needed, browser talks to FE-owned endpoints, not directly to backend

## Glossary

- `SSR`: Server-Side Rendering
- `BFF`: Backend For Frontend. FE-owned server routes that proxy/shape backend data for the browser.
- `SITE_DOMAIN`: public website hostname
- `ADMIN_DOMAIN`: Django admin hostname
- `views`: FE server-side modules that own request/data contracts, similar in spirit to Django views

## Frontend Architecture

### Page rendering

- SSR renders the initial HTML document
- FE prefetches page-shell data from BE during render
- React Query state is dehydrated into the HTML
- the browser hydrates from server-provided state

### Browser transport

- browser-facing app traffic uses `SITE_DOMAIN`
- interactive browser JSON flows go through FE-owned transport endpoints
- FE proxies those requests to BE when needed
- public media stays on nginx and `SITE_DOMAIN`

### Observability

- structured FE logs include `request_id`
- FE propagates `X-Request-ID` to backend
- FE responses expose `X-Request-ID` for request tracing

### Caching

- FE has a `24h` in-memory SSR cache for shared shell data
- BE invalidates FE cache through an internal webhook
- cache keys use resource + language + site host

## Current FE Structure

### Browser-side low-level transport

- [frontend/src/api/api.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/api.ts)
- [frontend/src/api/bff.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/bff.ts)
- [frontend/src/api/services.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/services.ts)
- [frontend/src/api/media.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/media.ts)

### Server-side views

- [frontend/server/views/shell.js](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/views/shell.js)
- [frontend/server/views/bff.js](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/views/bff.js)

These `views` are the beginning of the FE-side source of truth for server-owned data contracts.

### Server runtime

- [frontend/server/index.mjs](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/index.mjs)

Responsibilities:

- request routing
- SSR document rendering
- BFF endpoint handling
- internal cache invalidation endpoint
- structured request logging

### SSR entrypoint

- [frontend/src/entry-server.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/entry-server.tsx)

Responsibilities:

- per-request QueryClient creation
- route-aware SSR prefetch
- dehydrated state generation

## Current Public Contract

Public page URLs:

- `/`
- `/privacy`
- `/astrophotography`
- `/astrophotography/:slug`
- `/programming`
- `/travel/:country/:place/:date`

These are FE-owned public routes used by sitemap and SEO.

Current FE-owned transport endpoints still exposed for browser interactivity:

- `/app/contact`
- `/app/images/`
- `/app/images/:slug/`
- `/app/travel/:country/:place/:date`

These are transport endpoints, not website routes. They must not appear in sitemap or canonical URLs.

## Frontend SSR Cache

Cache targets:

- `settings`
- `profile`
- `background`
- `travel-highlights`
- `latest-astro-images`

Properties:

- in-memory FE cache
- keyed by resource + language + site host
- `24h` TTL
- invalidated by backend through:
  - `POST /internal/cache/invalidate`

Internal cache files:

- [frontend/server/ssrCache.js](/Users/lukaszremkowicz/Projects/landingpage/frontend/server/ssrCache.js)

## Observability

Frontend structured logs now include:

- `kind`
- `request_id`
- path
- status
- duration
- upstream path/base URL for SSR/BFF backend calls

Main log groups:

- `document`
- `static`
- `bff`
- `ssr-backend`
- `cache-invalidate`
- `health`

## Development

Local frontend development is handled through Docker Compose, not a standalone `npm run dev` workflow.

Start or rebuild the stack from the repository root:

```bash
doppler --config dev run -- docker compose up --build
```

Useful frontend commands:

```bash
# frontend logs
doppler --config dev run -- docker compose logs -f fe

# restart only the frontend container
doppler --config dev run -- docker compose restart fe

# frontend checks
doppler --config dev run -- docker compose exec -T fe npm run type-check
doppler --config dev run -- docker compose exec -T fe npm run lint
doppler --config dev run -- docker compose exec -T fe npm test -- --watchAll=false
```

## Notes

- The browser uses `SITE_DOMAIN` as its public application host.
- Public-safe media is served by nginx on `SITE_DOMAIN`, not by FE.
- FE server-side `views` are now the preferred place for request/data ownership cleanup going forward.
