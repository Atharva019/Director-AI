# Deploy runbook — Phase 1

Target: **$0/mo**. Neon (Postgres) + any S3-compatible object store (images) +
Render free (API) + Vercel (frontend). No Redis, no billing, no job queue.

> **Credentials check.** The local secret files (`backend/.env`,
> `backend/firebase-service-account.json`, etc.) were verified as **never
> committed** and are covered by `.gitignore` — no history surgery needed. See
> `docs/security.md`. Rotating the AI provider keys before launch is still
> sensible if they've ever left your machine.

---

## 1. Database — Neon

1. Create a project at [neon.tech](https://neon.tech) (free tier, no card).
2. Copy the **pooled** connection string.
3. Use it verbatim as `DATABASE_URL` in step 3. **No editing required.**

The app normalises the connection string itself:

- **Driver** — `postgresql://` and the legacy `postgres://` are both rewritten
  to `postgresql+asyncpg://` for the app engine, and to `postgresql://`
  (psycopg2) for Alembic. Getting this wrong by hand produced
  `The asyncio extension requires an async driver to be used`, which names
  neither the variable nor the fix.
- **Query parameters** — `?sslmode=require&channel_binding=require` are kept
  for psycopg2 (which needs them) and translated for asyncpg (which rejects
  them outright).

Paste what the provider gives you. The same applies to Supabase, Heroku, or any
other managed Postgres.

Schema is created by `alembic upgrade head`, which the container runs at boot —
no manual migration step.

## 2. Image storage — any S3-compatible provider

The backend talks plain S3, so the provider is a configuration choice, not a code
change. Pick one and fill in the same six variables.

> **If Cloudflare R2 rejects your card:** R2 requires a payment method even on
> the free tier, and Indian debit cards frequently decline the international
> authorization hold (international transactions are off by default on most
> cards, and RBI e-mandate rules block many card-on-file authorizations).
> Enabling international transactions in your bank app often fixes it; a credit
> card is more reliable than debit. If neither works, use Supabase or Backblaze
> below — nothing in the code cares.

### Variables (identical for every provider)

| Variable | Meaning |
|---|---|
| `S3_ENDPOINT_URL` | provider API endpoint (see table below) |
| `S3_ACCESS_KEY_ID` | from the provider's API credentials |
| `S3_SECRET_ACCESS_KEY` | from the provider's API credentials — usually shown once |
| `S3_BUCKET` | bucket name |
| `S3_PUBLIC_BASE_URL` | public read base, no trailing slash |
| `S3_REGION` | `auto` for R2, a real region elsewhere |

### Per-provider values

| Provider | `S3_ENDPOINT_URL` | `S3_REGION` | Card required? |
|---|---|---|---|
| Cloudflare R2 | `https://<account_id>.r2.cloudflarestorage.com` | `auto` | **yes** |
| Supabase Storage | `https://<project>.supabase.co/storage/v1/s3` | project region | no |
| Backblaze B2 | `https://s3.<region>.backblazeb2.com` | e.g. `us-west-004` | verify |

Card requirements and free-tier limits change — confirm on the provider's
current pricing page rather than trusting this table.

### Setup, whichever you pick

1. Create a bucket (e.g. `director-ai-images`).
2. Make it **public-read** — the app links directly to objects; it does not proxy
   them.
3. Create API credentials scoped to **read + write on that bucket only**.
4. Copy the public base URL and set the six variables above.

Object keys are `analyses/<uuid4-hex><ext>` — unguessable, which matters because
a public bucket means the key is the only access control.

> The API refuses to start in production unless `S3_ENDPOINT_URL`,
> `S3_ACCESS_KEY_ID`, `S3_BUCKET` and `S3_PUBLIC_BASE_URL` are all set. That is
> deliberate: with them missing, uploads would be written to the database as
> unusable relative paths, and an empty endpoint would send them to real AWS S3.

## 3. Backend — Render

1. Render → **New → Blueprint**, point it at this repo. It picks up
   `backend/render.yaml` (Docker runtime, free plan, health check on `/health`).
2. Fill in **every** `sync: false` variable in the dashboard before the first
   deploy — the API refuses to boot in production if any of these is missing:
   - `DATABASE_URL` — from step 1
   - `NVIDIA_NIM_API_KEY` (and `GEMINI_API_KEY` if using the fallback)
   - `FIREBASE_SERVICE_ACCOUNT_JSON` — the entire service-account JSON, one line
   - the six `S3_*` values from step 2
   - `CORS_ORIGINS` — **must be non-empty now, not later.** You pick your Vercel
     project name, so the domain is predictable: set
     `https://<your-vercel-project>.vercel.app`. Correct it in step 5 if the
     real domain differs.
3. Deploy. Confirm `https://<service>.onrender.com/health` returns
   `{"status":"healthy",...}`.

`APP_ENV=production` turns on fail-fast startup checks: incomplete object
storage, empty/wildcard `CORS_ORIGINS`, and a broken Firebase credential each
abort the boot rather than serving a subtly broken API. That is deliberate, but
it means **a missing variable looks like a failed deploy**. The log line names
the exact variable — see Troubleshooting below.

> Free-tier Render spins down after ~15 min idle; the first request afterwards
> takes ~30s. Expected, not a bug.

## 4. Frontend — Vercel

1. Vercel → **Import** this repo, root directory `frontend`.
2. Environment variables (see `frontend/.env.local.example`):
   - the six `NEXT_PUBLIC_FIREBASE_*` values
   - `API_PROXY_ORIGIN` = the Render URL — **the important one**, see below
   - `NEXT_PUBLIC_API_URL` = the Render URL (server components only)
   - `NEXT_PUBLIC_IMAGE_HOSTNAME` = the host from `S3_PUBLIC_BASE_URL` (hostname only)
3. Deploy, note the production domain.

> **`API_PROXY_ORIGIN` is read at build time, not runtime.** Next evaluates
> `rewrites()` in `next.config.ts` while building and bakes the target into the
> output — verified by starting a build made without it and watching it proxy to
> the stale default. So: set it *before* the first deploy, and **redeploy after
> any change**. Editing it in the dashboard alone changes nothing.
>
> If it is missing at build time the app proxies to `http://127.0.0.1:8000`,
> which on Vercel is nothing — every request fails as `Failed to fetch`.

**Why the browser never calls Render directly.** All browser requests go to
`/api/v1/*` on the Vercel origin, and Next proxies them server-side. Same-origin
requests are not subject to CORS at all, so a mistyped `CORS_ORIGINS` cannot take
the app down. It also means the backend URL is not baked into the client bundle.

## 5. Close the loop

1. **Firebase console → Authentication → Settings → Authorized domains** → add
   the Vercel domain. Login fails silently without this.
2. **Render → `CORS_ORIGINS`** = the exact Vercel origin
   (`https://your-app.vercel.app`, no trailing slash). Redeploy.

---

## Smoke test (run against production)

| # | Step | Expected |
|---|---|---|
| 1 | `GET /health` | `200`, `{"status":"healthy"}` |
| 2 | Sign up / log in via the Vercel app | lands on the dashboard |
| 3 | Create a project | `201`, appears in the list |
| 4 | Create a second project, then a third | third returns **402**, upgrade modal opens |
| 5 | Submit an email in the modal | success message; row lands in `waitlist` |
| 6 | Upload an image on `/analyze` | analysis renders; image URL is on the `S3_PUBLIC_BASE_URL` host |
| 7 | Redeploy the backend, reload the analysis | image still loads (proves object storage, not local disk) |
| 8 | `POST /api/v1/waitlist` twice with one email | `201` then `200`, no duplicate row |
| 9 | Log in as a second user, `GET /api/v1/analyses` | only that user's rows — never the first user's |
| 10 | Trigger any 500 | response body has no stack trace or SQL |

Check `waitlist` count against the Phase 3 gate (25 signups) in
`docs/progress.md`.

## Troubleshooting a failed Render deploy

Render's notification reads `Deploy failed for <sha>: <commit message>`. The text
after the colon is the **commit message, not the error** — ignore it. Open
*Render → your service → Logs* and look at the last few lines before the crash.

| Log line contains | Cause | Fix |
|---|---|---|
| `CORS_ORIGINS is empty in production` | `CORS_ORIGINS` unset | Set it to your Vercel origin, no trailing slash |
| `CORS_ORIGINS contains '*'` | wildcard with credentials enabled | Use exact origins |
| `Object storage is not fully configured` | one of the four required `S3_*` vars missing | Set `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_BUCKET`, `S3_PUBLIC_BASE_URL` |
| `No AI provider configured` | no `NVIDIA_NIM_API_KEY` and Gemini disabled | Set `NVIDIA_NIM_API_KEY` |
| `Firebase credential is configured but failed to load` | malformed `FIREBASE_SERVICE_ACCOUNT_JSON` | Re-paste the whole JSON on one line, no stray newlines |
| `DATABASE_URL is not configured` | `DATABASE_URL` unset — the default points at localhost | Set the Neon string with `+asyncpg` |
| `connection to server at "localhost" ... refused` | same, on an older build predating the guard | Set `DATABASE_URL` |
| `connect() got an unexpected keyword argument 'sslmode'` | older build; asyncpg got a libpq param | Fixed in current `dev` — redeploy |
| `The asyncio extension requires an async driver` | older build; URL lacked `+asyncpg` | Fixed in current `dev` — the scheme is normalised automatically |
| `alembic ... auth failed` | wrong credentials in `DATABASE_URL` | Re-copy the Neon string |

## Troubleshooting the frontend

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to fetch` on **every** operation | `API_PROXY_ORIGIN` missing or set after the build — the proxy still targets `127.0.0.1:8000` | Set it in Vercel, then **redeploy**. A dashboard edit without a rebuild has no effect |
| `Failed to fetch` **after login**, on the dashboard, while the proxy itself works (`curl` gets 401) | a backend collection route defined with a trailing slash (`@router.get("/")`). Next strips the slash, FastAPI 307s it back **cross-origin** to the raw Render host, and the browser's follow-up fails CORS | Define collection routes slash-less (`@router.get("")`) and keep `redirect_slashes=False` on the app. Guarded by `test_no_route_ends_in_trailing_slash` |
| `Failed to fetch` on some operations only | backend asleep (free tier, ~30s cold start) | Retry after the first request wakes it |
| Login does nothing, no error | Vercel domain not in Firebase authorized domains | Firebase console → Authentication → Settings → Authorized domains |
| Analysis works, image is broken | `NEXT_PUBLIC_IMAGE_HOSTNAME` doesn't match `S3_PUBLIC_BASE_URL`'s host | Set it to the hostname only, no scheme or path, then redeploy |

`Failed to fetch` is a network-layer failure — the browser never got a readable
response. Check the Network tab: a request to `<vercel-domain>:8000` or to
`127.0.0.1:8000` means the proxy target is wrong, not the backend.

**Upgrading from an older config:** the storage variables were renamed from
`R2_*` to `S3_*`. If your Render service still has `R2_ACCOUNT_ID` etc., those
are now ignored and the boot fails the storage check. Delete them and set the
`S3_*` equivalents — `S3_ENDPOINT_URL` is
`https://<r2_account_id>.r2.cloudflarestorage.com` with `S3_REGION=auto`.

## Rollback

Render and Vercel both keep previous deploys — roll back from the dashboard.
Database changes need care: Alembic downgrades exist but are not rehearsed, so
prefer rolling forward with a fix.
