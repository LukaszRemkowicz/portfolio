# React SSR Migration Plan

## Goal

Move the current frontend from a client-rendered Vite SPA to a server-rendered React application in controlled phases, while keeping the frontend runnable after each phase.

This plan assumes:

- Django remains the backend API source of truth
- Traefik and Nginx stay in front of the frontend
- the frontend should migrate incrementally, not through a framework rewrite
- each phase must preserve a working frontend, even if SSR is only partially enabled

## Current Architecture

The current frontend is a Vite SPA:

- [frontend/src/index.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/index.tsx) mounts the app with `createRoot`
- [frontend/src/App.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/App.tsx) uses `BrowserRouter`
- page data is fetched on the client via React Query hooks
- [docker/frontend/Dockerfile](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/Dockerfile) builds static assets
- [docker/frontend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/entrypoint.sh) copies them into a shared volume for Nginx

This means the current production frontend is not a running application server. It is a static bundle distributed by Nginx.

## Recommended Target Architecture

Use Vite-based SSR first, not a Next.js rewrite.

Target shape:

- React app rendered on a Node SSR runtime
- Vite client build for browser assets
- Vite server build for HTML rendering
- Nginx serves static assets and proxies HTML requests to the frontend SSR server
- Django continues to expose API endpoints
- React Query is hydrated from server-fetched data on critical pages
- browser-only behavior stays in explicit client-only boundaries

Why this approach:

- lowest migration risk from the current codebase
- preserves most of the current React component tree
- avoids mixing framework migration with rendering migration
- supports phased adoption route by route

## Target Infrastructure Topology

After SSR, the frontend should no longer be a static artifact sync container.

Target request flow:

```text
Client
  -> Traefik
  -> Nginx
     -> Node SSR frontend for HTML/document requests
     -> Django API for /api and admin/API-related upstreams
     -> static assets directly from Nginx or frontend public build output
```

Target runtime responsibilities:

- Traefik:
  - TLS
  - host routing
  - staging IP restriction
  - edge security headers that belong at proxy level
- Nginx:
  - path routing
  - static asset serving
  - media/X-Accel-Redirect handling
  - request buffering/timeouts/rate limits
- Frontend Node SSR service:
  - server-rendered HTML
  - React hydration payload generation
  - route-level data prefetching
- Django backend:
  - API and admin
  - media authorization logic
  - content source of truth

## Infrastructure Impact Summary

SSR requires changes in four places:

### 1. Frontend Container

The current frontend image builds files and copies them into a shared volume. SSR requires:

- a Node runtime image
- a server entrypoint
- a long-running process
- health checks
- logs to stdout/stderr

### 2. Compose Topology

Compose must stop treating `fe` as a one-shot asset synchronization container and instead treat it as an application service with:

- exposed internal port
- healthcheck
- restart policy
- environment for SSR runtime

### 3. Nginx Routing

Nginx must distinguish between:

- HTML/document requests that go to the SSR frontend
- static asset requests that can be served directly
- backend API/admin/media paths that continue to go to Django or internal locations

### 4. Deployment Scripts

Build and release scripts must:

- build client and server frontend artifacts
- package the Node SSR runtime image
- deploy the SSR service as a long-running process
- verify SSR health, not only asset availability

## Architecture Principles

1. Keep the app runnable after every phase.
2. Do not rewrite routing, rendering, and deployment in one step.
3. Move critical public routes to SSR first.
4. Keep browser-only logic out of shared render paths.
5. Treat SSR as a runtime and deployment change, not only a React refactor.

## Main SSR Gaps In The Current Frontend

### Rendering Model

- [frontend/src/index.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/index.tsx) is client-only
- [frontend/src/App.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/App.tsx) assumes `BrowserRouter`

### Data Fetching

- most data is fetched after hydration through hooks like:
  - [frontend/src/hooks/useProfile.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useProfile.ts)
  - [frontend/src/hooks/useBackground.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useBackground.ts)
  - [frontend/src/hooks/useTravelHighlights.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useTravelHighlights.ts)
  - [frontend/src/hooks/useAstroImages.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useAstroImages.ts)

### Browser-Only Behavior

- service worker handling is client-only
- analytics bootstrapping is client-only
- DOM listeners in [frontend/src/App.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/App.tsx) must not run during server rendering
- language detection in [frontend/src/i18n.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/i18n.ts) is browser-first

### SEO

- [frontend/src/components/common/SEO.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/components/common/SEO.tsx) currently depends on client-side rendering through `react-helmet-async`
- metadata is not guaranteed to exist in the initial HTML response

### Deployment

- the frontend container is currently a build artifact sync job, not a request-serving runtime
- SSR requires a real Node process in production

## Migration Phases

## Phase 0: SSR Readiness Audit And Isolation

### Objective

Prepare the codebase so it can render safely in a non-browser environment without changing runtime behavior yet.

### Scope

- audit all browser-only APIs
- isolate bootstrap logic from render logic
- define route ownership and route data requirements
- identify components that must remain client-only

### Changes

- split app bootstrap from app tree
- move browser-only startup work out of shared render path
- audit:
  - `window`
  - `document`
  - `localStorage`
  - `navigator`
  - service worker registration
  - analytics init
  - Sentry lazy loading
- define route metadata requirements
- define route data requirements

### Key Files

- [frontend/src/index.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/index.tsx)
- [frontend/src/App.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/App.tsx)
- [frontend/src/i18n.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/i18n.ts)

### Deliverables

- SSR blocker inventory
- client-only boundary inventory
- proposed app entrypoint split
- infrastructure delta inventory

### Infrastructure Work In This Phase

- document the current frontend deploy flow from:
  - [docker/frontend/Dockerfile](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/Dockerfile)
  - [docker/frontend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/entrypoint.sh)
  - [docker-compose.prod.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.prod.yml)
  - [docker-compose.stage.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.stage.yml)
- identify all Nginx locations that currently assume static SPA delivery
- define the future SSR upstream contract:
  - frontend container name
  - internal port
  - health endpoint
  - startup command

### Acceptance Criteria

- current SPA still works unchanged
- no shared render code hard-crashes when imported in Node
- the app tree can be imported without immediately touching browser globals

## Phase 1: Dual Entrypoints And Shared App Shell

### Objective

Introduce the minimal SSR-capable structure while keeping the application client-rendered by default.

### Scope

- create separate client and server entrypoints
- create a shared app shell
- replace direct router assumptions with runtime-aware routing wrappers

### Changes

- add `entry-client.tsx`
- add `entry-server.tsx`
- extract shared providers into reusable composition
- use:
  - `BrowserRouter` on client
  - `StaticRouter` on server
- keep current pages and hooks unchanged for now

### Suggested Structure

```text
frontend/src/
  app/
    AppShell.tsx
    providers.tsx
    routes.tsx
  entry-client.tsx
  entry-server.tsx
```

### Deliverables

- server render function returns HTML for the shell
- client hydrates the same tree

### Infrastructure Work In This Phase

- no production topology change yet
- add local-only SSR dev start command alongside current Vite dev mode
- decide whether development will use:
  - Vite middleware mode, or
  - separate client/server dev commands

### Docker Output Of This Phase

No mandatory production Docker change yet. The output should still be deployable as the existing SPA.

### Acceptance Criteria

- the current frontend still works in browser mode
- a basic SSR render can execute in Node without route crashes
- hydration completes without structural mismatches on the shell

## Phase 2: SSR Runtime And Container Architecture

### Objective

Replace the static frontend deployment model with a real SSR frontend runtime.

### Scope

- create Node runtime for frontend SSR
- adjust Nginx to proxy HTML requests to the frontend
- keep asset serving efficient

### Changes

- change [docker/frontend/Dockerfile](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/Dockerfile) from static-copy model to:
  - client asset build
  - server bundle build
  - runtime container with Node entrypoint
- remove or replace [docker/frontend/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/frontend/entrypoint.sh)
- update compose files to run frontend as a long-lived server
- update Nginx upstream rules:
  - HTML to SSR app
  - built assets directly from Nginx or SSR public path

### Required Docker Changes

- replace the current `prod` frontend image stage based on `nginx:alpine`
- use a Node runtime base image for SSR
- create a startup command such as:
  - `node dist/server/entry-server.js`
  - or framework-equivalent SSR bootstrap
- ensure runtime image contains:
  - built client assets
  - built server bundle
  - only runtime dependencies

### Required Compose Changes

Update:

- [docker-compose.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.yml)
- [docker-compose.stage.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.stage.yml)
- [docker-compose.prod.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.prod.yml)

Expected changes:

- `fe` becomes a real application container
- remove shared `frontend_dist` sync semantics as the primary frontend delivery path
- add internal service port for SSR, for example `3000`
- add healthcheck such as `GET /health` or `GET /ready`
- add restart policy suitable for a long-running app server
- add environment variables needed at runtime, not only at build time

### Required Nginx Changes

Update the Nginx site config so that:

- `/assets/*` or equivalent static build output is served directly
- document requests like `/`, `/astrophotography`, `/travel-highlights/...` proxy to the frontend SSR upstream
- API/admin/media/protected media rules remain separated from the frontend SSR upstream

### Required Script Changes

Update release tooling under [infra/scripts/release](/Users/lukaszremkowicz/Projects/landingpage/infra/scripts/release) so that:

- frontend build step produces SSR-compatible image output
- deploy waits for frontend SSR health
- rollback logic understands a stateful SSR process, not just asset replacement

### Deliverables

- frontend container serves SSR HTML
- static assets still resolve correctly
- existing routes still function

### Acceptance Criteria

- frontend container is healthy and long-running
- homepage returns rendered HTML from the SSR server
- the app remains usable even if page data is still fetched client-side after hydration

## Phase 3: SSR For Critical Public Routes

### Objective

Move high-value public routes to true SSR with server data fetching and hydration.

### Priority Routes

1. `/`
2. `/travel-highlights/:countrySlug/:placeSlug/:dateSlug`
3. `/astrophotography`

### Scope

- fetch critical page data on the server
- dehydrate query state into the HTML
- hydrate on the client without duplicate waterfalls

### Changes

- create server-side route loaders
- prefetch React Query data on the server
- dehydrate query cache into the response
- rehydrate query cache on the client

### Primary Data Domains

- profile
- homepage background
- travel highlights
- route-specific travel detail data

### Key Files

- [frontend/src/HomePage.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/HomePage.tsx)
- [frontend/src/api/services.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/services.ts)
- [frontend/src/hooks/useProfile.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useProfile.ts)
- [frontend/src/hooks/useBackground.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useBackground.ts)
- [frontend/src/hooks/useTravelHighlights.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/hooks/useTravelHighlights.ts)

### Acceptance Criteria

- homepage source HTML contains meaningful content before hydration
- critical routes do not rely on client-side fetch to paint above-the-fold content
- no duplicate first-load request waterfall for prefetched data

### Infrastructure Work In This Phase

- confirm Nginx forwards only document requests to SSR
- verify cache headers separately for:
  - HTML
  - JS/CSS assets
  - images
- confirm Traefik staging restriction still applies before Nginx/SSR

## Phase 4: Request-Aware SEO And i18n

### Objective

Make metadata and localization fully SSR-aware.

### Scope

- render SEO tags on the server
- make language resolution request-scoped
- remove browser-only assumptions from server path

### Changes

- replace singleton browser-first i18n init with server-aware per-request initialization
- determine locale from request context
- render title, description, OG tags, canonical URLs on the server
- preserve client hydration without metadata flicker

### Key Files

- [frontend/src/components/common/SEO.tsx](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/components/common/SEO.tsx)
- [frontend/src/i18n.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/i18n.ts)

### Acceptance Criteria

- initial HTML includes correct metadata
- localized content is rendered from the server response
- hydration does not replace page title and meta tags unexpectedly

### Infrastructure Work In This Phase

- propagate request host/proto/forwarded headers correctly from Traefik to Nginx to SSR runtime
- ensure canonical URL generation uses real forwarded host and scheme
- confirm staging and prod domains generate different canonical bases when required

## Phase 5: Client-Only Islands And Boundary Cleanup

### Objective

Reduce hydration risk and make client-only behavior explicit.

### Scope

- identify components and features that should never drive SSR
- move them into explicit client-only islands

### Likely Client-Only Areas

- cookie consent
- analytics bootstrapping
- browser event listeners
- modal/lightbox behavior
- image interaction protections
- service worker registration

### Changes

- define SSR-safe shell components
- isolate client-only widgets behind lazy client boundaries
- keep route content server-first

### Acceptance Criteria

- server render path contains no accidental browser-only side effects
- hydration scope is smaller and more predictable
- interactive features still work after hydration

### Infrastructure Work In This Phase

- ensure analytics and consent logic remain browser-only and do not affect SSR response time
- keep frontend logs clean by separating:
  - server render failures
  - client/browser telemetry

## Phase 6: Streaming, Suspense, And Performance Tuning

### Objective

Use SSR to improve real performance instead of only changing delivery mode.

### Scope

- stream route content
- parallelize server fetches
- trim hydration payload
- reduce bundle cost of non-critical features

### Changes

- introduce streaming SSR where appropriate
- place Suspense boundaries around slow route sections
- start independent fetches in parallel
- defer non-critical analytics and heavy widgets

### Guidance

Apply the most useful patterns from the local best-practice material:

- parallel data fetching
- smaller client bundles
- targeted hydration
- server-side deduplication

### Acceptance Criteria

- homepage and travel routes improve initial render quality
- no SSR waterfall between independent data sources
- hydration payload is measurably smaller than naive full-page hydration

### Infrastructure Work In This Phase

- confirm Nginx proxy settings support streamed responses
- review timeout and buffering settings for SSR responses
- validate that Traefik/Nginx do not accidentally buffer away streaming benefits

## Phase 7: Operational Hardening

### Objective

Make the SSR frontend production-ready from an operations standpoint.

### Scope

- add health checks
- add SSR server logs
- add frontend server observability
- define caching strategy
- define failure handling

### Changes

- add SSR health endpoint
- add structured request logs from frontend runtime
- add server-side Sentry support if desired
- set process and memory limits
- document cache rules for:
  - HTML
  - static assets
  - API calls

### Acceptance Criteria

- frontend SSR server can be monitored independently
- failures are observable through logs and health state
- deploy, rollback, and restart procedures are documented and repeatable

### Required Infrastructure Deliverables

- frontend SSR health endpoint contract
- container resource limits in compose
- production and staging deploy procedure updates
- log collection updates so frontend server logs are collected from stdout/stderr
- rollback procedure for bad SSR releases

## Concrete Docker And Infra Refactor Plan

## Step A: Replace The Current Frontend Runtime Model

Current model:

- build static frontend
- copy files to shared volume
- Nginx serves all frontend HTML/assets

Target model:

- build client assets
- build server bundle
- run Node SSR process in `fe`
- Nginx proxies HTML to `fe`
- Nginx serves static assets directly if practical

## Step B: Update Frontend Dockerfile

The frontend Dockerfile should evolve into three concerns:

1. dependency install
2. client and server build
3. runtime image

Recommended outcome:

```text
docker/frontend/Dockerfile
  base deps
  build-client
  build-server
  runtime-node
```

Runtime image requirements:

- no dev dependencies
- startup command for SSR server
- non-root execution
- healthcheck compatibility
- stdout/stderr logging

## Step C: Update Compose Service Contract

The `fe` service should become similar in operational behavior to `be`:

- stable internal port
- long-running process
- healthcheck
- restart policy
- observability

Recommended new contract:

- `fe` serves HTML on internal port such as `3000`
- health endpoint like `/health`
- environment variables for:
  - public site URL
  - API base URL
  - environment
  - optional SSR cache settings

## Step D: Update Nginx Ownership Boundaries

Nginx should continue to own:

- static asset delivery
- media and protected media rules
- rate limits
- upstream proxy behavior

Nginx should stop owning:

- generation of application HTML for frontend routes

Recommended path split:

- `/api/*` -> backend
- `/admin/*` -> backend
- `/media/*` -> existing controlled media rules
- `/assets/*` -> static frontend assets
- all public frontend document routes -> SSR frontend upstream

## Step E: Update Release And Deploy Tooling

Release/deploy scripts must be changed to verify a running SSR server, not only built assets.

Expected changes:

- frontend image build produces SSR runtime image
- deploy starts/replaces long-running `fe`
- health verification checks frontend SSR endpoint
- smoke tests validate rendered HTML, not only file existence

## Step F: Update Monitoring

After SSR, frontend logs become useful again.

Monitoring should then collect:

- frontend SSR runtime logs from container stdout/stderr
- Nginx access/error logs
- backend logs

This is different from the current static frontend model, where frontend logs have little value.

## Route Migration Strategy

Do not migrate every route at once.

Recommended order:

1. `/`
2. `/travel-highlights/:countrySlug/:placeSlug/:dateSlug`
3. `/astrophotography`
4. `/programming`
5. policy and lower-priority routes

Why:

- the homepage gives the highest SEO and first-paint return
- travel detail pages benefit strongly from server metadata and sharable HTML
- astrophotography likely has more complex interactive behavior and should follow after the SSR pipeline is proven

## Proposed Execution Order

1. Phase 0
2. Phase 1
3. Phase 2
4. SSR homepage only
5. SSR travel detail route
6. SSR metadata and request-aware i18n
7. client-only island cleanup
8. performance tuning
9. operational hardening

## Risks

### 1. Browser-Only Side Effects During SSR

The current app contains browser assumptions in bootstrap and render-adjacent code. These must be isolated first.

### 2. Hydration Mismatch

Client-only language detection, metadata differences, or inconsistent initial data can cause hydration warnings and broken interaction.

### 3. Deployment Complexity

The frontend currently ships as static assets. SSR introduces:

- a long-running Node process
- runtime memory concerns
- new health and logging requirements

### 4. Double Fetching

If route data is fetched on the server and then fetched again immediately on the client, SSR benefits will be diluted.

### 5. Framework Rewrite Temptation

Trying to adopt Next.js or another full framework during this migration will increase risk and slow delivery.

## Out Of Scope For The First SSR Milestone

- full framework rewrite
- replacing Django API with frontend-owned backend-for-frontend logic
- full edge rendering
- advanced personalization at render time
- complete route migration in one release

## Definition Of Done For The First Real SSR Milestone

The first meaningful SSR milestone should satisfy all of the following:

- homepage HTML is rendered by the frontend server
- homepage SEO metadata is present in the initial response
- React Query data used above the fold is prefetched and hydrated
- client hydration completes without warnings
- Nginx and Traefik still route traffic correctly
- the app remains usable if only the homepage is SSR and other routes stay CSR

## Recommendation

Start with Phase 0 and Phase 1 only. Do not change deployment topology until the shared app tree is proven SSR-safe.

The best low-risk milestone is:

- dual entrypoints
- SSR-capable app shell
- homepage-only SSR

That gives useful business value without forcing a full application rewrite.
