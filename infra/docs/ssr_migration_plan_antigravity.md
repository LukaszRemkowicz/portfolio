# SSR Migration Plan — Portfolio Frontend

> **Prepared:** 2026-03-19
> **Author:** Antigravity (AI Architect Review)
> **References:** `infra/docs/react_ssr_migration_plan.md` (original), full codebase audit

---

## Audit Summary

### Agreement With The Original Plan

The original plan at `infra/docs/react_ssr_migration_plan.md` is architecturally sound:

- Correct to **stay with Vite-based SSR** rather than rewriting to Next.js
- Correct phasing: Prepare → Dual Entrypoints → Runtime → Data → SEO/i18n → Polish
- Correct infrastructure model: Node SSR process replacing static volume sync
- Correct route-first migration order

### Deviations And Additions

| Area | Original Plan | This Plan |
|------|--------------|-----------|
| Router on server | `StaticRouter` from react-router-dom v6 | **React Router v7** native SSR (`createStaticHandler`) |
| SEO | `react-helmet-async` continue | **Phase 4**: replace with server `<head>` injection via `renderToString` context |
| SSR server runtime | Not specified | **Hono** (lightweight, fast, works great with Vite SSR) |
| i18n blocker severity | Phase 4 | Flagged as **phase 0 blocker** |
| TanStack Query dehydration | Mentioned lightly | **Explicit API** in Phase 3 |
| Streaming | Phase 6 | Merged into Phase 5 as a natural extension |
| Operational Hardening | Phase 7 | Merged into Phase 5 |
| Phase count | 8 phases | **6 phases** (more practical) |

---

## Current Architecture — Audit Findings

### SSR Blockers (Critical)

| File | Issue | Severity |
|------|-------|----------|
| `src/index.tsx` | `document.getElementById`, `window.addEventListener` for Sentry | 🔴 Critical |
| `src/App.tsx` | `BrowserRouter`, `document.addEventListener` in `useEffect` | 🔴 Critical |
| `src/i18n.ts` | `i18next-browser-languagedetector` — `localStorage`/`navigator` detection | 🔴 Critical |
| `src/api/constants.ts` | `getEnv('API_URL')` uses `import.meta.env` (Vite client build) | 🔴 Critical |
| `src/serviceWorkerRegistration.ts` | browser-only API | 🟠 High |
| `vite.config.ts` | PWA plugin (`vite-plugin-pwa`) is client-only build artifact | 🟠 High |
| `src/hooks/useGoogleAnalytics.ts` | browser-only analytics | 🟡 Medium |
| `src/utils/analytics.ts` | likely `localStorage` usage | 🟡 Medium |

### Browser-Only Components (Must Be Isolated)

- `StarBackground.tsx`, `ShootingStars.tsx` — canvas/animation, DOM-dependent
- `CookieConsent` — `localStorage`, browser events
- `ScrollToHash` — `window.location`, `document`
- `AnalyticsTracker` — `window.gtag`
- Service worker registration in `index.tsx`

### Data Fetching — All Client-Side Today

All data for critical routes is fetched client-side via TanStack Query:

- `useProfile` → `GET /v1/profile/`
- `useBackground` → `GET /v1/background/`
- `useTravelHighlights` → `GET /v1/travel-highlights/`
- `useAstroImages` → `GET /v1/astroimages/`

These hooks are the primary targets for server prefetch + dehydration in Phase 3.

### Infrastructure Today

```text
Build-time:
  Vite build → static dist/
  Dockerfile: node:20 (build) → nginx:alpine (prod)
  entrypoint.sh: copies dist/ into /frontend_dist/ shared volume

Runtime:
  Nginx serves all HTML + assets from shared volume
  No running Node process
  Django API on /api/* and /admin/*
```

---

## Target Architecture

```text
Build-time:
  Vite client build → dist/client/
  Vite server build → dist/server/
  Dockerfile: node:20 (build) → node:20-alpine (runtime)

Runtime:
  Hono SSR server (port 3000) — renders HTML, dehydrates React Query state
  Nginx proxies / and /* to Hono SSR server
  Nginx serves /assets/* directly
  Django API on /api/* and /admin/*
  Traefik: TLS, host routing (unchanged)
```

---

## Technology Decisions

### SSR Server: **Hono**

- Tiny, zero-dependency runtime (12kb)
- First-class Vite SSR integration
- Works well with Node, Bun, Cloudflare Workers (future flexibility)
- No Express boilerplate overhead

### Router: **React Router v7**

The project is on `react-router-dom` v6. React Router v7 is the direct upgrade with:
- Native `createStaticHandler` for SSR route matching
- Native data loading on server
- Drop-in upgrade from v6 (same API, new capability)

Upgrade path: `npm install react-router-dom@7`

### TanStack Query Hydration

Use the built-in `dehydrate` / `HydrationBoundary` API:

```ts
// Server
const queryClient = new QueryClient()
await queryClient.prefetchQuery(...)
const dehydratedState = dehydrate(queryClient)

// Client (entry-client.tsx)
<HydrationBoundary state={dehydratedState}>
  <App />
</HydrationBoundary>
```

### SEO: Server-Rendered `<head>` Injection

Replace `react-helmet-async` with direct `<head>` injection at the SSR layer. Each route exports a `meta()` function (similar to React Router v7 convention):

```ts
export function meta({ data }: { data: ProfileData }) {
  return {
    title: `${data.first_name} ${data.last_name} — Portfolio`,
    description: data.short_description,
  }
}
```

The Hono SSR handler injects these into the HTML template string directly.

### i18n: Server-Safe Per-Request Init

Replace the singleton browser detector with a factory:

```ts
// i18n.server.ts — creates fresh i18n instance per request
export async function createI18n(acceptLanguage: string) {
  const i18n = i18next.createInstance()
  await i18n.use(initReactI18next).init({
    lng: detectLanguage(acceptLanguage),
    resources: { en, pl },
    fallbackLng: 'en',
  })
  return i18n
}
```

The browser `i18n.ts` remains but uses the singleton pattern only on the client.

---

## Migration Phases

### Phase 0 — SSR Readiness Audit And Isolation

**Goal:** Prepare the codebase for SSR rendering without changing any runtime behavior.

**The app must remain fully functional at the end of this phase.**

#### 0.1 Browser Global Audit

- [ ] Search for all `window`, `document`, `localStorage`, `navigator` usages
- [ ] Flag each: can it run on the server? Does it need a guard?
- [ ] Update `StarBackground`, `ShootingStars`, `ScrollToHash` to be `useEffect`-only (no SSR execution)
- [ ] Move Sentry bootstrap from `index.tsx` top level into a `initClientSideServices()` function

#### 0.2 Service Worker Isolation

- [ ] Move `serviceWorkerRegistration.unregister()` call from `index.tsx` into a `useEffect` or dedicated bootstrap file
- [ ] Ensure `service-worker.ts` and `serviceWorkerRegistration.ts` are never imported in any shared/server path

#### 0.3 i18n Isolation

- [ ] Create `src/i18n.client.ts` (current i18n.ts, renamed) — keeps `LanguageDetector`, `localStorage` cache
- [ ] Create `src/i18n.server.ts` — per-request `createInstance()`, no detector plugin, no localStorage
- [ ] `src/i18n.ts` becomes a re-export barrel: client path uses `i18n.client.ts`, server path uses `i18n.server.ts`

#### 0.4 Environment Variable Strategy

- [ ] Create `src/utils/env.shared.ts` — resolves env vars from both `import.meta.env` (Vite client) and `process.env` (Node server)
- [ ] Update `src/api/constants.ts` to import from `env.shared.ts` so the API base URL resolves correctly in both environments

#### 0.5 Route Metadata Inventory

Define a route manifest structure (used later in Phase 4 for SSR meta injection):

```ts
// src/app/routes.ts
export const ROUTES = [
  { path: '/',            component: 'HomePage',            prefetch: ['profile', 'background'] },
  { path: '/astrophotography', component: 'AstroGallery',  prefetch: ['astroImages'] },
  { path: '/travel/:countrySlug/:placeSlug/:dateSlug', component: 'TravelHighlightsPage', prefetch: ['travelDetail'] },
  { path: '/programming', component: 'Programming',          prefetch: [] },
  { path: '/privacy',     component: 'PrivacyPolicy',        prefetch: [] },
]
```

#### Acceptance Criteria — Phase 0

- [ ] SPA runs unchanged in browser (no regressions)
- [ ] No shared render file imports `window`, `document`, or browser-only modules at module level
- [ ] `npm run build` still succeeds
- [ ] `npm run test` passes (existing Jest suite)

---

### Phase 1 — Dual Entrypoints And Shared App Shell

**Goal:** Introduce the minimal SSR-capable structure while keeping the app client-rendered in production.

**The app must remain fully functional at the end of this phase.**

#### 1.1 App Shell Extraction

```
frontend/src/
  app/
    AppShell.tsx      ← extracted from App.tsx, SSR-compatible
    ClientProviders.tsx  ← browser-only providers (CookieConsent, Analytics)
    routes.tsx        ← route definitions, no router wrapper
  entry-client.tsx    ← new (replaces index.tsx bootstrap)
  entry-server.tsx    ← new SSR render function
  index.tsx           ← calls entry-client.tsx (thin entry)
```

**`AppShell.tsx`** — SSR-safe:
```tsx
// No BrowserRouter here — router is provided by entry-client or entry-server
export function AppShell() {
  return (
    <HelmetProvider>
      <Suspense fallback={<LoadingScreen />}>
        <ErrorBoundary>
          <Routes>{/* routes from routes.tsx */}</Routes>
        </ErrorBoundary>
      </Suspense>
    </HelmetProvider>
  )
}
```

**`entry-client.tsx`** — browser only:
```tsx
import { hydrateRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// ... browser bootstrap (Sentry, SW, analytics)
hydrateRoot(document.getElementById('root')!, <BrowserRouter><AppShell /></BrowserRouter>)
```

**`entry-server.tsx`** — Node only:
```tsx
import { renderToString } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server'
export function render(url: string) {
  return renderToString(<StaticRouter location={url}><AppShell /></StaticRouter>)
}
```

#### 1.2 Vite Config Update

Add server entry to `vite.config.ts`:
```ts
build: {
  rollupOptions: {
    input: {
      client: './index.html',
    }
  }
}
// SSR build is separate: vite build --ssr entry-server.tsx
```

Add `npm run build:client` and `npm run build:server` scripts in `package.json`.

#### 1.3 Local SSR Dev Command

Add to `package.json`:
```json
"dev:ssr": "node server/dev-server.js"
```

A minimal `server/dev-server.js` that runs Vite in middleware mode so dev works without changing prod flow.

#### Acceptance Criteria — Phase 1

- [ ] `npm run dev` still works as before (CSR mode unchanged)
- [ ] `npm run dev:ssr` starts a local SSR dev server
- [ ] A `curl localhost:3000/` returns HTML with `<div id="root">` populated (not empty)
- [ ] Client hydration completes without structural mismatch warnings in browser console
- [ ] `npm run build` still works (CSR production build unchanged)

---

### Phase 2 — SSR Runtime And Container Architecture

**Goal:** Replace the static frontend deployment model with a real SSR Node runtime.

**The app must serve SSR HTML in production after this phase.**

#### 2.1 Hono SSR Server

Create `server/index.ts`:

```ts
import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { serveStatic } from '@hono/node-server/serve-static'

const app = new Hono()

// Static assets
app.use('/assets/*', serveStatic({ root: './dist/client' }))

// SSR catch-all
app.get('*', async (c) => {
  const { render } = await import('./dist/server/entry-server.js')
  const html = await render(c.req.url)
  // Inject into HTML template
  return c.html(template.replace('<!--ssr-outlet-->', html))
})

serve({ fetch: app.fetch, port: 3000 })
```

#### 2.2 Dockerfile — Replace Static Model

```dockerfile
# --- base ---
FROM node:20-alpine AS base
WORKDIR /app
RUN npm install -g npm@latest

# --- build ---
FROM base AS build
ARG SITE_DOMAIN
ARG API_URL
ARG ENVIRONMENT=production
ARG PROJECT_OWNER

ENV VITE_API_URL=$API_URL
ENV VITE_ENVIRONMENT=$ENVIRONMENT
ENV PROJECT_OWNER=$PROJECT_OWNER

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build:client   # → dist/client/
RUN npm run build:server   # → dist/server/

# --- runtime (Node SSR) ---
FROM node:20-alpine AS runtime
WORKDIR /app

# Copy only production files
COPY --from=build /app/dist ./dist
COPY --from=build /app/server ./server
COPY --from=build /app/package.json ./

RUN npm ci --omit=dev

RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "server/index.js"]
```

#### 2.3 Docker Compose Changes

Update `fe` service in all compose files (`docker-compose.yml`, `docker-compose.stage.yml`, `docker-compose.prod.yml`):

```yaml
fe:
  build:
    context: .
    dockerfile: docker/frontend/Dockerfile
    target: runtime
  restart: unless-stopped
  expose:
    - "3000"
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
    interval: 30s
    timeout: 5s
    retries: 3
  environment:
    - NODE_ENV=production
    - SITE_URL=${SITE_DOMAIN}
    - API_URL=${API_URL}
  # Remove: volumes, the old frontend_dist volume
```

Remove the `frontend_dist` shared volume declaration and all references.

#### 2.4 Nginx Routing Changes

Update Nginx site config:

```nginx
upstream ssr_frontend {
  server fe:3000;
  keepalive 32;
}

# Static built assets (served directly from SSR container via pass-through or CDN)
location /assets/ {
  proxy_pass http://ssr_frontend;
  expires 1y;
  add_header Cache-Control "public, immutable";
}

# API — unchanged
location /api/ { proxy_pass http://be:8000; }
location /admin/ { proxy_pass http://be:8000; }
location /media/ { ... existing rules ... }

# All other paths → SSR frontend
location / {
  proxy_pass http://ssr_frontend;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header Host $host;
  proxy_http_version 1.1;
  proxy_set_header Connection "";
}
```

#### 2.5 Health Endpoint

Add to `server/index.ts`:
```ts
app.get('/health', (c) => c.json({ status: 'ok', uptime: process.uptime() }))
```

#### 2.6 Release Script Updates

Update `infra/scripts/release/` to:
- Build both client and server bundles
- Push the Node runtime image tag
- Health-check `GET /health` after deploy (not just asset file existence)
- Include rollback: `docker service update --rollback fe`

#### Acceptance Criteria — Phase 2

- [ ] `fe` container runs as a long-lived process (not a one-shot)
- [ ] `GET /` returns SSR-rendered HTML (visible content, not empty `<div id="root">`)
- [ ] `GET /health` returns `200`
- [ ] Static assets load correctly (JS/CSS/images)
- [ ] Existing Django API routes still work via Nginx
- [ ] Deploy + rollback procedure documented and tested

---

### Phase 3 — SSR Data Prefetching For Critical Routes

**Goal:** Move high-value public routes to true SSR with server data fetching and TanStack Query hydration.

**The app must remain usable after this phase, with SSR data on key routes and CSR fallback on others.**

#### 3.1 Server-Side QueryClient

Extend `entry-server.tsx` to accept a queryClient and prefetch data:

```ts
// entry-server.tsx
import { dehydrate, QueryClient } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'

export async function render(url: string, apiBaseUrl: string) {
  const queryClient = new QueryClient()

  // Route-specific prefetching
  if (url === '/' || url.startsWith('/?')) {
    await Promise.all([
      queryClient.prefetchQuery({ queryKey: ['profile'], queryFn: () => fetchProfile(apiBaseUrl) }),
      queryClient.prefetchQuery({ queryKey: ['background'], queryFn: () => fetchBackground(apiBaseUrl) }),
    ])
  }

  if (url.startsWith('/travel/')) {
    const [, , countrySlug, placeSlug, dateSlug] = url.split('/')
    await queryClient.prefetchQuery({
      queryKey: ['travelDetail', countrySlug, placeSlug, dateSlug],
      queryFn: () => fetchTravelDetail(apiBaseUrl, countrySlug, placeSlug, dateSlug),
    })
  }

  const dehydratedState = dehydrate(queryClient)
  const html = renderToString(
    <HydrationBoundary state={dehydratedState}>
      <StaticRouter location={url}><AppShell /></StaticRouter>
    </HydrationBoundary>
  )

  return { html, dehydratedState }
}
```

#### 3.2 Server-Side Service Functions

Create `src/api/services.server.ts`:
- Same fetch logic as `services.ts` but uses Node `fetch` or `axios` with absolute `apiBaseUrl`
- No `import.meta.env` — uses `process.env.API_URL`

#### 3.3 Client Hydration

Update `entry-client.tsx`:
```ts
const dehydratedState = window.__REACT_QUERY_STATE__

hydrateRoot(
  document.getElementById('root')!,
  <QueryClientProvider client={queryClient}>
    <HydrationBoundary state={dehydratedState}>
      <BrowserRouter><AppShell /></BrowserRouter>
    </HydrationBoundary>
  </QueryClientProvider>
)
```

The dehydrated state is embedded in the HTML template:
```html
<script>window.__REACT_QUERY_STATE__ = <!--dehydrated-state-->;</script>
```

#### 3.4 Priority Route Order

1. `/` — profile + background (highest SEO value)
2. `/travel/:countrySlug/:placeSlug/:dateSlug` — shareable travel pages
3. `/astrophotography` — gallery (optional, heavier)

#### Acceptance Criteria — Phase 3

- [ ] `curl https://yourdomain.com/` returns HTML with `<h1>`, profile name, and above-the-fold content before JavaScript loads
- [ ] Browser DevTools Network tab shows **no duplicate API calls** for prefetched data on initial load
- [ ] TanStack Query `dehydratedState` is visible in the `<script>` tag of HTML source
- [ ] App remains functional with JS disabled (content visible, interactions degrade gracefully)

---

### Phase 4 — Server-Side SEO And Request-Aware i18n

**Goal:** Make metadata and localization fully SSR-aware.

**The app must have correct `<title>`, OG tags, and localized content in the initial HTML response.**

#### 4.1 Route Meta Functions

Each route page exports a `meta()` function:

```ts
// HomePage.tsx
export function meta(data?: ProfileData) {
  return {
    title: data ? `${data.first_name} ${data.last_name} — Portfolio` : 'Portfolio',
    description: data?.short_description || '',
    og: { type: 'website', image: data?.avatar || '' },
  }
}
```

Server injects into the HTML template before sending:

```ts
// server/index.ts
const meta = getRouteMeta(url, dehydratedState)
const headHtml = `
  <title>${meta.title}</title>
  <meta name="description" content="${meta.description}" />
  <meta property="og:title" content="${meta.title}" />
  <meta property="og:image" content="${meta.og.image}" />
  <link rel="canonical" href="${siteUrl}${url}" />
`
const finalHtml = template.replace('<!--head-outlet-->', headHtml)
```

**Later:** evaluate dropping `react-helmet-async` entirely once server-rendered `<head>` is stable.

#### 4.2 Server-Safe i18n Per Request

```ts
// i18n.server.ts (from Phase 0)
const i18n = await createI18n(c.req.header('accept-language') ?? 'en')
// Pass i18nInstance into render()
```

Client continues using the existing `i18n.ts` (singleton) — it reads `localStorage` and `navigator.language`.

#### 4.3 Canonical URL And Forwarded Headers

Ensure Nginx passes these headers to Hono:
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host  $host;
```

Hono reads them to construct canonical URLs.

#### Acceptance Criteria — Phase 4

- [ ] `curl https://yourdomain.com/ | grep '<title>'` shows portfolio owner name
- [ ] `curl https://yourdomain.com/ | grep 'og:image'` shows a real image URL
- [ ] `curl -H "Accept-Language: pl" https://yourdomain.com/` returns Polish content in HTML
- [ ] No React hydration warnings about `<head>` mismatch

---

### Phase 5 — Streaming, Suspense, Client Islands, And Operational Hardening

**Goal:** Complete the SSR implementation with streaming, explicit client boundaries, observability, and production-ready ops.

**This is the final polish phase. The app must be production-stable.**

#### 5.1 Streaming SSR

Replace `renderToString` with `renderToPipeableStream` or `renderToReadableStream`:

```ts
import { renderToReadableStream } from 'react-dom/server'

export async function render(url: string, ...) {
  const stream = await renderToReadableStream(
    <StaticRouter location={url}><AppShell /></StaticRouter>,
    {
      bootstrapScripts: ['/assets/entry-client.js'],
      onError(err) { console.error('[SSR]', err) },
    }
  )
  await stream.allReady // wait in dev; stream in prod
  return stream
}
```

Hono supports Response streaming natively.

#### 5.2 Suspense Boundaries For Heavy Sections

```tsx
// HomePage.tsx
<Suspense fallback={<GallerySkeleton />}>
  <Gallery />    {/* deferred — not blocking initial paint */}
</Suspense>
<Suspense fallback={<TravelSkeleton />}>
  <TravelHighlights />
</Suspense>
```

Above-the-fold content (`<Home />`, `<Navbar />`) renders immediately; heavy sections stream in.

#### 5.3 Client-Only Islands

Wrap browser-only components with a `ClientOnly` boundary:

```tsx
// components/common/ClientOnly.tsx
import { useEffect, useState } from 'react'
export function ClientOnly({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  if (!mounted) return null
  return <>{children}</>
}
```

Apply to: `<StarBackground />`, `<ShootingStars />`, `<CookieConsent />`, `<AnalyticsTracker />`, `<ScrollToHash />`

#### 5.4 Server-Side Sentry (Optional)

```ts
// server/index.ts
import * as Sentry from '@sentry/node'
Sentry.init({ dsn: process.env.SENTRY_DSN_BE, environment: process.env.NODE_ENV })
```

Server-side Sentry captures SSR render failures separately from browser Sentry.

#### 5.5 Structured SSR Logs

Use `pino` for structured JSON logs from the Hono server:

```ts
import pino from 'pino'
const logger = pino()
app.use('*', async (c, next) => {
  const start = Date.now()
  await next()
  logger.info({ url: c.req.url, status: c.res.status, ms: Date.now() - start })
})
```

Log collection (existing `collect-logs.sh`) picks up stdout/stderr from the `fe` container automatically.

#### 5.6 Resource Limits

Add to compose files:
```yaml
fe:
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 256M
```

#### 5.7 Nginx — Confirm Streaming Support

```nginx
# Remove proxy_buffering for SSR routes to support streaming
location / {
  proxy_pass http://ssr_frontend;
  proxy_buffering off;
  proxy_cache off;
}
```

#### Acceptance Criteria — Phase 5

- [ ] `<head>` renders before body completes (streaming verified with `curl --no-buffer`)
- [ ] `StarBackground`, `ShootingStars`, `CookieConsent`, Analytics do not execute during SSR
- [ ] No `window is not defined` or `localStorage is not defined` errors in server logs
- [ ] Server logs in JSON format appear in `docker logs fe`
- [ ] `GET /health` still responds during streaming render
- [ ] Memory usage of `fe` container stays under 256MB under normal load
- [ ] Sentry captures SSR exceptions (if enabled)

---

## Proposed Execution Order

```
Phase 0  → Phase 1 (local dev SSR prototype)
          → Phase 2 (production deployment model changed)
               → Phase 3 (SSR data, biggest SEO win)
                    → Phase 4 (SEO meta + i18n)
                         → Phase 5 (streaming + hardening)
```

Each phase ends with a deployable, working application.

---

## Library Upgrades Required

| Package | Current | Target | Reason |
|---------|---------|--------|--------|
| `react-router-dom` | v6.22.3 | **v7.x** | Native SSR `createStaticHandler` |
| `react` + `react-dom` | ^18.0.0 | **18.3.x** | `renderToReadableStream` API stable |
| `hono` | not installed | **^4.x** | New SSR server runtime |
| `@hono/node-server` | not installed | **^1.x** | Node adapter for Hono |
| `pino` | not installed | **^9.x** | Structured SSR logs |
| `@sentry/node` | not installed | **^8.x** | Optional: server-side Sentry |
| `vite-plugin-pwa` | ^0.21.2 | keep | Only applies to client build |

---

## Risks And Mitigations

| Risk | Mitigation |
|------|-----------|
| Hydration mismatch from i18n | Per-request i18n from Phase 0, server and client use same detected locale |
| Double fetch waterfall | TanStack Query dehydration (Phase 3) prevents re-fetch of prefetched data |
| Memory leak in SSR server | `QueryClient` created per-request and discarded; resource limits in compose |
| PWA breaks after SSR | `vite-plugin-pwa` generates SW for client build only; SSR server serves SW endpoint via static pass-through |
| Streaming breaks Nginx buffering | Phase 5 sets `proxy_buffering off` for SSR upstream |
| i18n singleton on server | Phase 0 splits `i18n.client.ts` from `i18n.server.ts` before any SSR code runs |

---

## Definition Of Done For First SSR Milestone (Post Phase 2–3)

- [ ] Homepage HTML rendered by Node SSR server
- [ ] Profile name and above-the-fold content visible in `curl` output
- [ ] SEO metadata (title, description) present in initial HTML
- [ ] TanStack Query dehydrated state embedded in HTML
- [ ] Client hydration completes without warnings
- [ ] Nginx and Traefik still route traffic correctly
- [ ] `GET /health` responds `200`
- [ ] App usable on all existing routes (CSR fallback for non-SSR routes)

---

*This document supersedes `infra/docs/react_ssr_migration_plan.md` for implementation purposes.
The original document remains as architectural context.*
