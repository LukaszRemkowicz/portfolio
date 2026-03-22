# SSR Client-Only Boundary Inventory

> Phase 0 classification of components and modules that must **never** be imported
> in the SSR render path (`entry-server.tsx` and any module it imports).

---

## Language Contract For SSR

Language resolution follows this priority order on the server:

1. `Accept-Language` request header (parsed in `createServerI18n()` in `i18n.server.ts`)
2. Falls back to `'en'` if header is absent or contains no supported language

**Supported languages:** `en`, `pl`

This is the contract used in Phase 3+ when `entry-server.tsx` calls
`createServerI18n(req.headers['accept-language'])`.

---

## Client-Only Modules (Must Never Be Imported On Server)

| File                               | Reason                                                |
| ---------------------------------- | ----------------------------------------------------- |
| `src/i18n.client.ts`               | `LanguageDetector` reads `localStorage` + `navigator` |
| `src/utils/initClientServices.ts`  | Sentry `window` listeners + SW unregister             |
| `src/serviceWorkerRegistration.ts` | `navigator.serviceWorker`                             |
| `src/utils/analytics.ts`           | `window.gtag`, `document.head`, `localStorage`        |
| `src/hooks/useGoogleAnalytics.ts`  | calls `loadGoogleAnalytics`                           |

---

## Client-Only Components (Must Be Wrapped In `<ClientOnly>` In Phase 5)

| Component                         | Reason                                            |
| --------------------------------- | ------------------------------------------------- |
| `StarBackground.tsx`              | canvas / `requestAnimationFrame`                  |
| `ShootingStars.tsx`               | canvas animation                                  |
| `CookieConsent.tsx`               | `localStorage`, `setTimeout`                      |
| `ScrollToHash.tsx`                | `window.location.hash`, `document.getElementById` |
| `AnalyticsTracker` (in `App.tsx`) | `window.gtag`                                     |

---

## SSR-Safe Shared Modules (Confirmed Phase 0)

| File                      | Status                                                                |
| ------------------------- | --------------------------------------------------------------------- |
| `src/utils/env.shared.ts` | ✅ Safe — no browser globals                                          |
| `src/api/api.ts`          | ✅ Safe — `setLanguageGetter` pattern, no i18n import                 |
| `src/api/constants.ts`    | ✅ Safe — uses `getSharedEnv` + `getEnv`                              |
| `src/api/services.ts`     | ✅ Safe — no browser globals (uses `api.ts`)                          |
| `src/api/routes.ts`       | ✅ Safe — constants only                                              |
| `src/i18n.server.ts`      | ✅ Safe — Node-only factory                                           |
| `src/i18n.ts`             | ✅ Safe as barrel — re-exports `i18n.client` (client build uses this) |

---

## What Stays For Phase 1

The components marked "client-only" above remain in their current locations.
The `<ClientOnly>` wrapper component is introduced in **Phase 5**.
For now, the constraint is: **do not import them from `entry-server.tsx`**.
