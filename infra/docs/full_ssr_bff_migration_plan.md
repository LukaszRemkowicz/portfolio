# Full SSR / BFF Migration Plan

## Goal

Move from the current hybrid SSR setup to a BFF-style architecture:

- browser talks only to the frontend server
- frontend server talks to backend internally
- public backend API exposure is removed or heavily reduced
- admin remains separately reachable

This is a follow-up architecture plan, not part of the already completed SSR migration phases.

## Target Architecture

## Non-Negotiable Routing Rule

Public website URLs must remain unchanged.

This includes routes such as:

- `/`
- `/astrophotography`
- `/astrophotography/:slug`
- `/travel/:country/:place/:date`
- `/programming`
- `/privacy`

Only FE <-> BE communication paths are allowed to change.

That means:

- public page routes remain stable for users, SEO, canonical tags, and Django sitemap generation
- frontend-owned BFF routes are transport endpoints only
- backend API routes can move behind the frontend server or become internal
- sitemap generation can remain in Django without changing its public URL output

### Public entrypoints

- `SITE_DOMAIN` -> frontend SSR / BFF server
- `ADMIN_DOMAIN` -> Django admin

### Internal only

- backend API service
- secure image/signing helpers
- any SSR-only data endpoints

### Desired browser behavior

The browser should no longer call backend endpoints such as:

- `/v1/profile/`
- `/v1/background/`
- `/v1/settings/`
- `/v1/travel-highlights/`
- `/v1/travel/...`
- `/v1/categories/`
- `/v1/tags/`
- `/v1/astroimages/...`
- `/v1/contact/`

Instead, it should use:

- document requests to the frontend server
- frontend-owned BFF routes where client interactivity still needs JSON

### Public route ownership source of truth

Public FE-owned routes should continue to be inferred from the public site routing and Django sitemap output, not from temporary transport endpoints.

Current sitemap-backed public FE pages include:

- `/`
- `/privacy`
- `/astrophotography`
- `/programming`
- `/travel`
- `/astrophotography/:slug`
- `/travel/:country/:place/:date`

This means:

- these routes must stay public and stable on the frontend hostname
- transport endpoints such as `/app/...` are not public website routes
- `/app/...` routes must never appear in sitemap, canonical URLs, or public navigation

## Current State Summary

The current implementation is hybrid SSR:

- first page load is server-rendered
- initial data fetches are done server-side for key routes
- client components still reuse backend API hooks after hydration and on client navigation
- the backend API is still publicly reachable and still part of the browser-facing architecture

That means SSR is implemented, but the backend API is not hidden.

## Work Phases

## Phase 0: Endpoint Inventory

Create a concrete matrix of every frontend data dependency.

For each endpoint, record:

- backend route
- current caller
- route(s) that use it
- SSR-prefetched or not
- browser-called after hydration or not
- can be internal-only immediately or not

Suggested output columns:

| Backend endpoint | Current caller | Used on routes | Browser calls today | Target owner |
| --- | --- | --- | --- | --- |

Target owner values:

- SSR only
- frontend BFF endpoint
- remains public temporarily

### Phase 0 inventory

Current frontend/backend contract derived from:

- [frontend/src/api/services.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/services.ts)
- [frontend/src/api/imageUrlService.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/imageUrlService.ts)
- [frontend/src/entry-server.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/entry-server.tsx)
- frontend hooks and component call sites under [frontend/src/hooks](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks) and [frontend/src/components](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/components)

| Backend endpoint | Current caller | Used on routes | SSR-prefetched | Browser calls today | Target owner |
| --- | --- | --- | --- | --- | --- |
| `/v1/settings/` | `fetchSettings` via `useSettings` | `/`, `/astrophotography`, navbar, contact, shooting stars, travel highlights | Yes | Yes | frontend BFF endpoint |
| `/v1/profile/` | `fetchProfile` via `useProfile` | `/`, footer | Yes | Yes | frontend BFF endpoint |
| `/v1/background/` | `fetchBackground` via `useBackground` | `/`, `/astrophotography`, `/travel/:country/:place/:date` | Yes | Yes | frontend BFF endpoint |
| `/v1/travel-highlights/` | `fetchTravelHighlights` via `useTravelHighlights` | `/`, travel highlights section | Yes | Yes | frontend BFF endpoint |
| `/v1/astroimages/latest/` | `fetchLatestAstroImages` via `useLatestAstroImages` | `/`, gallery section | Yes | Yes | frontend BFF endpoint |
| `/v1/travel/:country/:place/:date/` | `fetchTravelHighlightDetail` via `useTravelHighlightDetail` | travel detail page | Yes | Yes | frontend BFF endpoint |
| `/v1/categories/` | `fetchCategories` via `useCategories` | `/astrophotography` | Yes | Yes | frontend BFF endpoint |
| `/v1/tags/` | `fetchTags` via `useTags` | `/astrophotography` | Yes | Yes | frontend BFF endpoint |
| `/v1/astroimages/` | `fetchAstroImages` via `useAstroImages` | `/astrophotography` | Yes | Yes | frontend BFF endpoint |
| `/v1/astroimages/:slug/` | `fetchAstroImageDetail` via `useAstroImageDetail` and modal prefetch | gallery modal, travel image modal, hover prefetch | No | Yes | frontend BFF endpoint |
| `/v1/images/` | `fetchImageUrls` via `useImageUrls` | gallery modal, travel detail images | No | Yes | frontend BFF endpoint |
| `/v1/images/:slug/` | `fetchSingleImageUrl` | image helper flow | No | Yes | frontend BFF endpoint |
| `/v1/contact/` | `fetchContact` | contact form | No | Yes | frontend BFF endpoint |
| `/v1/projects/` | `fetchProjects` | programming section | No | No, frontend currently returns `[]` | keep disabled / decide later |

### Immediate interpretation

There are currently no important backend endpoints that are already SSR-only in the browser-facing architecture.

The first request for several routes is server-side today, but the same data sources are still wired into browser hooks after hydration or on client navigation. That means the backend API is still a browser dependency even for routes with SSR prefetch.

### Best first candidates for hiding

These are the lowest-risk groups to move behind the frontend BFF first:

1. Page shell read endpoints
   - `/v1/settings/`
   - `/v1/profile/`
   - `/v1/background/`

2. Homepage read endpoints
   - `/v1/travel-highlights/`
   - `/v1/astroimages/latest/`

3. Travel detail read endpoint
   - `/v1/travel/:country/:place/:date/`

These are good first candidates because they are already SSR-prefetched and mostly shape page content rather than highly interactive ad hoc operations.

Important note:

- these are good migration candidates because they are easy to move away from the public backend API
- they are not necessarily good long-term public BFF endpoints
- the final target for this group is likely SSR-internal fetch only, with no public `/app/...` transport route

### Higher-risk endpoint groups

These should be migrated later in the BFF rollout:

- `/v1/astroimages/`
- `/v1/categories/`
- `/v1/tags/`
- `/v1/astroimages/:slug/`
- `/v1/images/`
- `/v1/images/:slug/`

Reason:

- they support gallery interaction, filtering, modal flows, and image URL/signing behavior
- they will require more careful client-navigation and media strategy work

### Write endpoint inventory

Current browser write path:

- `/v1/contact/`

This is a good early BFF write candidate because it is isolated and has no dependency on gallery/media behavior.

## Phase 1: Define Frontend BFF Surface

Add frontend-owned endpoints to the SSR server for all user-facing data flows that still need JSON.

Suggested route examples:

- `/app/settings`
- `/app/profile`
- `/app/background`
- `/app/travel-highlights`
- `/app/travel/:country/:place/:date`
- `/app/gallery`
- `/app/categories`
- `/app/tags`
- `/app/image/:slug`
- `/app/contact`

Rules:

- browser talks only to frontend hostname
- frontend server forwards internally to backend
- frontend routes normalize response shape and errors

### Phase 1 progress

The first frontend-owned read endpoints now exist on the SSR server:

- `/app/settings`
- `/app/profile`
- `/app/background`
- `/app/travel-highlights`
- `/app/latest-astro-images`
- `/app/travel/:country/:place/:date`

These endpoints currently proxy to backend JSON routes through the frontend server. They establish the public frontend-owned API surface required for the next migration step, but browser hooks have not been switched over yet.

Important note:

- this Phase 1 surface is transitional
- for page-shell data such as settings/profile/background/homepage shell content, the preferred end state is SSR-internal fetches, not permanent public `/app/...` endpoints

## Phase 2: Migrate Read-Only Data First

Move read-only frontend behavior from direct backend API usage to frontend-owned data endpoints.

Priority order:

1. homepage shell data
2. travel highlights and travel detail
3. astro gallery list/filtering
4. categories/tags
5. image detail data

Implementation tasks:

- refactor hooks to call frontend BFF endpoints
- keep SSR prefetch using the same internal server-side fetch layer
- remove direct browser dependency on `API_URL`

Success criteria:

- browser DevTools shows no `api.` requests for homepage and travel pages
- SSR and client navigation both still work
- public page URLs and sitemap entries remain unchanged

### Phase 2 progress

The first low-risk browser reads have been switched to frontend-owned `/app/...` routes:

- settings
- profile
- background
- travel highlights
- latest astro images
- travel detail

Implementation note:

- browser calls now use frontend BFF endpoints for this group
- SSR prefetch still talks directly to the backend via the internal server client to avoid frontend-to-frontend loopback during render

This means the browser-side contract for these routes has started moving away from the public backend API, while the SSR server keeps the more direct internal fetch path.

## Phase 2b: Remove Transitional Page-Shell BFF Endpoints

After the browser is no longer dependent on direct JSON fetches for page-shell content, remove transitional public `/app/...` routes for data that should be SSR-internal only.

Primary cleanup targets:

- `/app/settings`
- `/app/profile`
- `/app/background`
- `/app/travel-highlights`
- `/app/latest-astro-images`

Rules:

- keep public page URLs unchanged
- keep sitemap output unchanged
- keep SSR prefetch internal from FE to BE
- only retain frontend-owned public JSON endpoints for genuinely interactive client-side flows

Allowed Phase 2b cleanup scope:

- remove transitional `/app/...` endpoints only for page-shell data that belongs to sitemap-backed public FE pages
- do not change or rename any public FE route currently represented in sitemap
- do not move sitemap generation away from Django
- do not remove BFF routes still required by interactive client-side flows

Phase 2b checklist:

1. Confirm the data belongs to a sitemap-backed public FE page.
2. Confirm the data is already prefetched during SSR for that page.
3. Confirm browser interactivity does not require standalone JSON fetches for that data after hydration.
4. Convert the data source to SSR-internal only.
5. Remove the now-unused transitional `/app/...` route.

Success criteria:

- page-shell data is fetched only during SSR / document render
- browser does not call either `api.*` or transitional `/app/...` endpoints for homepage shell content
- remaining `/app/...` routes are limited to interactive flows that truly need client-side JSON

### Phase 2b progress

The transitional page-shell BFF routes have been removed for:

- settings
- profile
- background
- travel highlights
- latest astro images

Implementation note:

- these queries are now carried by SSR document prefetch on all public page routes
- the client cache keeps them indefinitely for the lifetime of the SPA session
- the remaining frontend-owned `/app/...` read surface is now limited to travel detail, which is still interactive-route-specific and not yet part of the page-shell cleanup

## Phase 3: Migrate Writes

Move browser writes behind the frontend server.

Initial write flow:

- contact form

Implementation tasks:

- browser posts to frontend BFF route
- frontend server validates and forwards internally
- preserve current error mapping and user-facing behavior

Success criteria:

- contact form no longer calls backend directly from browser

### Phase 3 progress

The isolated contact write flow now goes through the frontend server:

- browser submit -> `/app/contact`
- frontend server -> backend `/v1/contact/`

Implementation note:

- backend validation and error status semantics are preserved
- the Contact UI contract stays the same
- public page URLs remain unchanged

## Phase 4: Media and Image Strategy

This is the most sensitive part because this is a photography portfolio.

Split image delivery into two categories:

### Public-safe derived media

Can stay publicly served by nginx:

- thumbnails
- public-safe background derivatives
- other intentionally public media

### Protected or signed image flows

Should move behind frontend mediation if backend API is hidden:

- signed image metadata endpoints
- secure image helper routes

Implementation options:

1. keep public nginx media for safe assets only
2. proxy secure image URL generation through frontend BFF
3. keep backend signing internal and let frontend server forward only the final browser-safe response

Success criteria:

- browser does not depend on public backend helper endpoints for image metadata/signing

### Phase 4 progress

Phase 4 is complete under the chosen media boundary:

- browser image URL helper calls now use frontend-owned `/app/images/` routes
- frontend server proxies those requests internally to backend `/v1/images/` routes
- frontend-server SSR and BFF requests forward the current site host to Django, so backend-generated absolute URLs resolve on `SITE_DOMAIN` instead of the public API hostname
- public-safe image delivery remains on nginx for performance
- secure image serving remains on the existing backend/nginx signed-media path, but uses the site hostname in browser-visible URLs

This means:

- browser-facing image helper metadata/signing no longer depends on public backend JSON endpoints
- nginx still serves public/static media directly
- the backend secure-image serving implementation remains unchanged internally, but the browser no longer needs a separate `api.` hostname for those generated URLs

## Phase 5: Frontend Data Layer Refactor

Separate concerns in the frontend:

- server/BFF fetch layer
- UI hooks
- SSR prefetch adapters

Rules:

- client code must not import backend host assumptions
- client code should only know frontend-owned endpoints
- browser must not depend on `api.` domain env

Success criteria:

- `API_URL` is no longer required for browser behavior
- public frontend config remains minimal and frontend-only

## Phase 6: Infra Lockdown

Once browser no longer depends on public backend routes:

- remove public Traefik exposure for backend API
- keep backend reachable only on internal Docker/network
- keep admin exposed if needed
- tighten nginx route ownership so site routes go only to frontend server

Optional production model:

- public:
  - main site
  - admin
- internal only:
  - backend API

Recommended safety:

- keep backend API directly reachable in local and possibly staging until rollout is complete
- hide it in production only after verification

## Phase 7: Observability

Once the frontend server becomes the only public entrypoint, logging has to be stronger.

Add:

- request IDs propagated from frontend server to backend
- structured frontend BFF logs:
  - browser route
  - internal backend target
  - status
  - duration
- dashboard/alerts for:
  - frontend upstream failures
  - SSR render failures
  - backend dependency failures

Success criteria:

- an operator can trace a single user request from frontend entrypoint to backend dependency

## Phase 8: SSR Cache and Response Optimization

Add caching only after the transport and ownership model is stable.

Primary targets:

- shared SSR shell data:
  - settings
  - profile
  - background
  - travel highlights
  - latest astro images
- frontend BFF responses that remain public after cleanup
- optionally full document responses for stable public pages

Recommended order:

1. confirm final route/data ownership after Phases 1-7
2. add short-TTL frontend-server cache for shared shell SSR data
3. review backend cache coverage for the same queries
4. evaluate reverse-proxy or CDN caching for full document responses
5. add invalidation only where actually necessary

Rules:

- do not mix cache work into transport refactors
- keep cache TTLs short at first
- prefer correctness and debuggability over aggressive cache hit rate
- keep public page URLs and sitemap output unchanged

Success criteria:

- shared shell data is not re-fetched from backend on every SSR request
- backend load for stable page-shell queries is reduced
- browser-visible behavior does not change
- cache behavior is visible in logs and can be disabled during debugging

## Phase 9: Rollout

Recommended rollout order:

1. build frontend BFF endpoints
2. move read-only routes first
3. move write routes
4. move secure image helpers
5. verify no browser traffic hits `api.` for key pages
6. remove public backend API exposure
7. verify production routing and monitoring

Rollout safety checks:

- browser DevTools on homepage
- browser DevTools on travel detail
- browser DevTools on astrophotography filters
- contact form submission
- image modal/detail flow
- admin still reachable

## Risks

### Operational

- frontend SSR/BFF server becomes a more critical dependency
- poor logging will make debugging harder than today

### Application

- image delivery/signing flow is the highest-risk change
- gallery interactions may still need lightweight JSON endpoints
- caching behavior may shift from backend-facing to frontend-facing

### Rollout

- misrouting can become more subtle if frontend and backend contracts are not clearly separated

## Definition of Done

This migration is complete when all of the following are true:

- browser no longer calls `api.lukaszremkowicz.com` for normal site usage
- browser no longer calls the public API domain for normal site usage
- frontend hostname is the only public site entrypoint
- backend API is internal-only in production
- admin remains reachable and functional
- SSR, client navigation, gallery interactions, travel pages, and contact form still work
- logs clearly show frontend -> backend internal calls for debugging

## Recommendation

This direction is reasonable for this project because it is:

- mostly read-heavy
- SEO-sensitive
- portfolio-oriented rather than SPA-product-oriented
- low on complex authenticated browser workflows

The best next step is not immediate implementation. It is a Phase 0 endpoint inventory document that marks which current endpoints:

- are already effectively SSR-owned
- still leak to the browser
- can be moved first with low risk
