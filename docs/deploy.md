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

1. Create a project at [neon.tech](https://neon.tech) (free tier).
2. Copy the **pooled** connection string.
3. Swap the driver for asyncpg — the app is fully async:

   ```
   postgresql://user:pw@host/db      ->  postgresql+asyncpg://user:pw@host/db
   ```

4. Keep it for `DATABASE_URL` in step 3.

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
2. Fill in every `sync: false` variable in the dashboard:
   - `DATABASE_URL` — from step 1
   - `NVIDIA_NIM_API_KEY`, `GEMINI_API_KEY` — freshly rotated keys
   - `FIREBASE_SERVICE_ACCOUNT_JSON` — the entire service-account JSON, one line
   - the six `S3_*` values from step 2
   - `CORS_ORIGINS` — leave blank for now, set in step 5
3. Deploy. Confirm `https://<service>.onrender.com/health` returns
   `{"status":"healthy",...}`.

`APP_ENV=production` is set in the blueprint, which turns on two hardening
behaviours: the permissive CORS regex is disabled, and a misconfigured Firebase
credential crashes the boot instead of silently disabling auth.

> Free-tier Render spins down after ~15 min idle; the first request afterwards
> takes ~30s. Expected, not a bug.

## 4. Frontend — Vercel

1. Vercel → **Import** this repo, root directory `frontend`.
2. Environment variables (see `frontend/.env.local.example`):
   - the six `NEXT_PUBLIC_FIREBASE_*` values
   - `NEXT_PUBLIC_API_URL` = the Render URL
   - `API_PROXY_ORIGIN` = the Render URL
   - `NEXT_PUBLIC_IMAGE_HOSTNAME` = the host from `S3_PUBLIC_BASE_URL` (hostname only)
3. Deploy, note the production domain.

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

## Rollback

Render and Vercel both keep previous deploys — roll back from the dashboard.
Database changes need care: Alembic downgrades exist but are not rehearsed, so
prefer rolling forward with a fix.
