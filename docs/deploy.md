# Deploy runbook — Phase 1

Target: **$0/mo**. Neon (Postgres) + Cloudflare R2 (images) + Render free (API) +
Vercel (frontend). No Redis, no billing, no job queue.

> **Blocker — do this first.** The repo still tracks live credentials
> (`backend/firebase-service-account.json`, `backend/director-ai-*-firebase-adminsdk-*.json`,
> `backend/.env`, root `.env`, `frontend/.env.local`). Rotate every one of those
> keys in its console, then `git rm --cached` the files, before anything is
> deployed. See `docs/security.md`. Nothing below is safe until that is done.

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

## 2. Image storage — Cloudflare R2

1. Cloudflare dashboard → **R2** → *Create bucket* (e.g. `director-ai-images`).
2. Bucket → **Settings** → enable **Public access**, copy the public URL
   (`https://pub-xxxxxxxx.r2.dev`).
3. **R2 → Manage API Tokens** → *Create token*, scoped **Object Read & Write** on
   that bucket only. Copy the Access Key ID and Secret — the secret is shown once.
4. You now have all five values:

   | Variable | Where it comes from |
   |---|---|
   | `R2_ACCOUNT_ID` | Cloudflare dashboard URL / R2 overview |
   | `R2_ACCESS_KEY_ID` | the API token |
   | `R2_SECRET_ACCESS_KEY` | the API token |
   | `R2_BUCKET` | bucket name |
   | `R2_PUBLIC_BASE_URL` | the `pub-*.r2.dev` URL (no trailing slash) |

Object keys are `analyses/<uuid4-hex><ext>` — unguessable, since a public bucket
means the key is the only access control.

## 3. Backend — Render

1. Render → **New → Blueprint**, point it at this repo. It picks up
   `backend/render.yaml` (Docker runtime, free plan, health check on `/health`).
2. Fill in every `sync: false` variable in the dashboard:
   - `DATABASE_URL` — from step 1
   - `NVIDIA_NIM_API_KEY`, `GEMINI_API_KEY` — freshly rotated keys
   - `FIREBASE_SERVICE_ACCOUNT_JSON` — the entire service-account JSON, one line
   - the five `R2_*` values from step 2
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
   - `NEXT_PUBLIC_R2_HOSTNAME` = `pub-xxxxxxxx.r2.dev` (hostname only)
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
| 6 | Upload an image on `/analyze` | analysis renders; image URL is the `pub-*.r2.dev` host |
| 7 | Redeploy the backend, reload the analysis | image still loads (proves R2, not local disk) |
| 8 | `POST /api/v1/waitlist` twice with one email | `201` then `200`, no duplicate row |
| 9 | Log in as a second user, `GET /api/v1/analyses` | only that user's rows — never the first user's |
| 10 | Trigger any 500 | response body has no stack trace or SQL |

Check `waitlist` count against the Phase 3 gate (25 signups) in
`docs/progress.md`.

## Rollback

Render and Vercel both keep previous deploys — roll back from the dashboard.
Database changes need care: Alembic downgrades exist but are not rehearsed, so
prefer rolling forward with a fix.
