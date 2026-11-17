# Supabase API and Local Admin

The public read API and the contact form run as a Supabase Edge Function over the
Supabase Postgres database. The Django admin runs on your own machine against the
same database. This replaces the VPS for public traffic; DRF stays in the repo as
the reference implementation of the API contract.

## Request Path

```mermaid
flowchart LR
    Browser["Browser"] --> Worker["Cloudflare Worker<br/>(portfolio-fe)"]
    Worker -->|"x-origin-secret,<br/>X-Visitor-IP"| Fn["Supabase Edge Function<br/>supabase/functions/api"]
    Fn -->|"role portfolio_api<br/>(read-only)"| DB[("Supabase Postgres")]
    Fn -->|"302 presigned URL"| R2[("Cloudflare R2")]
    Fn -->|"contact mail"| Resend["Resend API"]
    Admin["Django admin<br/>(localhost:8000)"] -->|"role portfolio"| DB
    Admin --> R2
```

- The FE Worker calls the function with `SSR_API_URL` (the function URL) and adds
  `x-origin-secret` from the `API_ORIGIN_SECRET` Worker secret. The browser never
  calls the function directly.
- Media links in API responses point at `https://$SITE_DOMAIN/image-files/...`;
  the FE rewrites them to `/app/image-files/...`, the Worker proxies them and the
  function answers 302 with a short-lived presigned R2 URL.

## Edge Function (`supabase/functions/api`)

- 1:1 port of the DRF read endpoints: same paths, query params, status codes and
  JSON. `contract/compare.ts` deep-compares every endpoint against a running DRF
  (`deno task contract`, with `BASELINE_URL`, `FUNCTION_URL`, `API_ORIGIN_SECRET`).
- Hidden API: `router.ts` first requires `API_ORIGIN_SECRET` to be set (else a bare
  503), then `x-origin-secret` to match (else 403), before any routing or DB work.
- Media signing uses `MEDIA_SIGNING_KEY` (HMAC over `slug:expiry`), separate from
  Django's `SECRET_KEY`. Like Django on R2, the serve endpoint does not check that
  the file exists; a missing file ends in R2's own XML error.
- DB: postgres.js, one connection per isolate, prepared statements. Deployed it
  uses the direct connection (`db.<ref>.supabase.co:5432`); local runs use the
  session pooler (port 5432). Never the transaction pooler (6543): it breaks
  prepared statements.
- Local checks, in `supabase/functions/api`: `deno task test`, `deno task check`,
  `deno task lint`, `deno task fmt:check`; `deno task serve` runs it on :8001.

### Contact form (`POST /v1/contact/`)

Mirrors the Django view: kill switch (`contact_form_enabled`), throttle before
validation (per IP 5/h, per email 3/h, IP+email 2/h), payload limit, DRF
validation messages, 5-minute duplicate check, then two mails.

- `portfolio_api` has no rights on `inbox_contactmessage`. It may only execute
  `api_private.contact_throttle` and `api_private.contact_submit` (SECURITY
  DEFINER, owned by `portfolio`), so the API can add a message but never read
  stored ones. Both are called in `begin read write` transactions because the
  role defaults to read-only.
- Mail goes through the Resend HTTP API (`mail.ts`); Supabase blocks outbound SMTP
  ports 25 and 587. Sender `kontakt@$SITE_DOMAIN`; the owner notification replies
  to the visitor, the confirmation replies to `CONTACT_EMAIL`. Templates in
  `contact_emails.ts` are ports of the Django templates in `backend/inbox/`.
  Mail failures are logged and never change the 201.
- The Supabase gateway overwrites `X-Real-IP` and `X-Forwarded-For` with the
  caller's IP (the Worker). The Worker therefore sends the visitor IP in
  `X-Visitor-IP`, which the function trusts only after the origin secret check.

### Gateway behaviour to remember

- `text/html` responses are rewritten to `text/plain` (no custom domain), so HTML
  error pages show as source text when opened directly.
- Malformed `%`-encoding is answered with 400 by the gateway before the function.

## Database Roles and Migrations (`supabase/migrations`)

- Django migrations own every table. Supabase migrations hold only roles, grants
  and the contact functions.
- `portfolio`: the Django role (admin, migrations). `portfolio_api`: read-only,
  explicit table allow-list, column grants where a table holds source-file paths
  (`astrophotography_astroimage`, background and shop tables).
- Order on a fresh project: the first two Supabase migrations, then Django
  `migrate`, then the remaining Supabase migrations (they grant on Django tables).
  A Django migration that recreates a table drops its grants: re-apply them.
- When the API needs a new table or column, grant it in a new migration.

## Deploy

```bash
doppler run --project portfolio --config prd -- supabase/deploy-api.sh
```

The script sets the function secrets from Doppler (DB, `MEDIA_SIGNING_KEY`,
`API_ORIGIN_SECRET`, R2, `RESEND_API_KEY`, `CONTACT_EMAIL`, `PROJECT_OWNER`,
`SITE_DOMAIN`) and deploys with the Supabase CLI (`npx supabase@2.121.0`).

## Local Production Admin

```bash
infra/scripts/run_admin.sh            # newest release tag
infra/scripts/run_admin.sh v2.21.0    # a specific release
```

Pulls the released `production-be` image from GHCR, runs `migrate` and
`createcachetable`, then serves the admin at http://localhost:8000/admin/
(`docker-compose.supabase.yml`, all config from Doppler). Background work
(image variants, translations) runs in-process: stop with Ctrl+C only after it
has finished. Nothing here touches the VPS.
