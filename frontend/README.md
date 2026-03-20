# 🎨 Portfolio Frontend

React + TypeScript frontend rendered by a Node SSR server. The frontend owns:

- SSR page rendering
- BFF transport for the remaining browser-side JSON flows
- public env injection for the HTML shell
- frontend-side SSR shell caching

## ✨ Features

- server-side rendered public website
- astrophotography gallery with filtering and image detail flows
- travel highlights and travel story pages
- dynamic profile, background, and homepage shell content
- contact form submitted through FE-owned transport endpoints
- SEO metadata and sitemap-compatible public routing
- structured request logging and request correlation

## 🧱 Technology Stack

- React 19
- TypeScript
- Vite
- Node.js SSR server
- TanStack Query v5
- React Router
- React Helmet Async
- Axios
- CSS Modules
- i18next
- Sentry
- Vite PWA plugin

## 🔐 Environment Variables

The frontend uses both public browser env values and server-side SSR env values.

Important frontend-related variables in the current setup:

- `SITE_DOMAIN` - public website host used by SSR, media normalization, and public env injection
- `API_URL` - public backend API base URL used as a fallback/public reference
- `SSR_API_URL` - internal backend URL used by the SSR server for direct backend requests
- `PROJECT_OWNER` - public site metadata
- `GA_TRACKING_ID` - Google Analytics tracking ID
- `ENABLE_GA` - analytics toggle
- `SENTRY_DSN_FE` - frontend Sentry DSN
- `ENVIRONMENT` - current deployment environment
- `SSR_CACHE_INVALIDATION_TOKEN` - token used by backend invalidation webhooks to clear FE SSR cache

Browser build aliases still use `VITE_`-prefixed values where needed:

- `VITE_API_URL`
- `VITE_GA_TRACKING_ID`
- `VITE_ENABLE_GA`
- `VITE_SENTRY_DSN_FE`
- `VITE_ENVIRONMENT`

In Docker Compose, these values are wired through the frontend container configuration.

## ⚡ Performance Features

- TanStack Query for frontend data fetching, caching, and hydration
- SSR shell prefetch with dehydrated React Query state
- frontend-side `24h` SSR cache for shared shell data
- backend-triggered cache invalidation webhook for fresh shared content
- route-level code splitting through Vite
- lazy loading for non-critical images
- skeleton loading states for interactive content
- nginx delivery for public static media on `SITE_DOMAIN`

## 📱 PWA Support

The frontend includes Progressive Web App support through the Vite PWA plugin.

Current PWA-related pieces:

- generated web app manifest
- service worker registration in the frontend app
- cacheable static assets for repeat visits
- installable app metadata for supported browsers

PWA support is a frontend concern and does not change the SSR/BFF request flow.

## 🧭 Frontend Role In The Current Architecture

The frontend server is the main public application entrypoint on `SITE_DOMAIN`.

Request flow:

1. browser requests a page on `SITE_DOMAIN`
2. frontend SSR renders HTML
3. frontend server fetches backend data internally
4. dehydrated React Query state is embedded into the HTML
5. browser hydrates
6. if client-side JSON is still needed, browser talks to FE-owned endpoints, not directly to backend

## 📖 Glossary

- `SSR`: Server-Side Rendering
- `BFF`: Backend For Frontend. FE-owned server routes that proxy/shape backend data for the browser.
- `SITE_DOMAIN`: public website hostname
- `ADMIN_DOMAIN`: Django admin hostname
- `views`: FE server-side modules that own request/data contracts, similar in spirit to Django views

## 🏗️ Frontend Architecture

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

## 🗂️ Current FE Structure

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

## 🔌 Endpoint Configuration

Backend API route definitions are centralized in:

- [frontend/src/api/routes.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/routes.ts)
- [frontend/src/api/constants.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/src/api/constants.ts)

These files define:

- backend `/v1/*` routes used by SSR and internal FE services
- browser-facing FE transport endpoints under `/app/*`
- public route constants used by the frontend application

## 🌐 Current Public Contract

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

Backend API routes currently used by the frontend include:

- `/v1/profile/`
- `/v1/background/`
- `/v1/settings/`
- `/v1/astroimages/`
- `/v1/astroimages/latest/`
- `/v1/astroimages/:slug/`
- `/v1/travel-highlights/`
- `/v1/travel/:country/:place/:date/`
- `/v1/tags/`
- `/v1/categories/`
- `/v1/images/`
- `/v1/images/:slug/`
- `/v1/images/:slug/serve/`
- `/v1/contact/`

## 🧠 Frontend SSR Cache

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

## 📈 Observability

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

## 🛠️ Development

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

## 🔄 Hot Reload

The frontend container runs `npm run dev:ssr` in local development.

That command uses Node watch mode and rebuilds/restarts the SSR server when files change in:

- `src/`
- `server/`
- `public/`
- `index.html`

So the supported local workflow still has live reload, but it is provided through the Compose-managed frontend container rather than a standalone host `npm run dev` process.

## 🧪 Testing

Frontend tests and checks run inside the Compose-managed frontend container.

Common commands:

```bash
# run frontend unit/integration tests
doppler --config dev run -- docker compose exec -T fe npm test -- --watchAll=false

# run frontend lint
doppler --config dev run -- docker compose exec -T fe npm run lint

# run frontend type-check
doppler --config dev run -- docker compose exec -T fe npm run type-check
```

The project also defines a dedicated Compose test service:

```bash
doppler --config dev run -- docker compose run --rm fe-test
```

## E2E Tests

The frontend also includes browser-level end-to-end coverage with Playwright.

Relevant files:

- [frontend/playwright.config.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/playwright.config.ts)
- [frontend/e2e/cookie-consent.spec.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/e2e/cookie-consent.spec.ts)
- [frontend/e2e/stability.spec.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/e2e/stability.spec.ts)

Available commands inside the frontend container:

```bash
# run Playwright end-to-end tests
doppler --config dev run -- docker compose exec -T fe npm run test:e2e

# open Playwright UI mode
doppler --config dev run -- docker compose exec -T fe npm run test:e2e:ui
```

There is also a lightweight SSR smoke test:

- [frontend/scripts/ssr-smoke-test.ts](/Users/lukaszremkowicz/Projects/landingpage/frontend/scripts/ssr-smoke-test.ts)

Run it with:

```bash
doppler --config dev run -- docker compose exec -T fe npm run smoke:ssr
```

## Notes

- The browser uses `SITE_DOMAIN` as its public application host.
- Public-safe media is served by nginx on `SITE_DOMAIN`, not by FE.
- FE server-side `views` are now the preferred place for request/data ownership cleanup going forward.

## 🎨 Styling Architecture

### Design System

- **CSS Variables**: Consistent colors, spacing, typography, and other design tokens
- **Utility Classes**: Reusable mixins for common patterns (flexbox, spacing, etc.)
- **Responsive Design**: Mobile-first approach with consistent breakpoints
- **Skeleton Screens**: Shimmer animations for smooth loading transitions

### Component Styles

All component styles are organized in `styles/components/` directory:

- **Modular Structure**: Each component has its dedicated CSS file
- **Consistent Naming**: All files follow `ComponentName.module.css` convention
- **Easy Maintenance**: Clear separation makes styles easy to find and modify

## 📱 Pages & Components

### HomePage (`/`)

- Hero section with dynamic background
- User profile display
- Quick gallery preview
- About section with bio

### Astrophotography (`/astrophotography`)

- Full-screen image gallery
- Filter by celestial object type
- Modal lightbox for image details
- Equipment and processing info

### Programming (`/programming`)

- Currently shows "under construction"
- Planned: Project showcase with screenshots
- Technology stacks and links

### Contact (`/contact`)

- Full implementation with validation and spam protection
- Integrated with backend API
