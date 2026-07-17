# Architecture

Target architecture for taking Director AI from local-first to a deployed, free-tier, revenue-funnel SaaS.
Approach: **Approach 2** — deploy + gate + waitlist (Phase 1), then revenue funnel (Phase 2). See `phases/`.

## Current state (what exists)

```
frontend/  Next.js 15 (App Router, TS, CSS Modules), React 19
           Firebase client auth, jsPDF call-sheet export (client-side)
           pages: / (login), /dashboard, /project/[id], /analyze, /history
backend/   FastAPI (async), SQLAlchemy 2 + asyncpg
           routers: auth, projects, scenes, shots, analysis
           services: ai_provider (NVIDIA NIM primary → Gemini fallback, Groq legacy),
                     image_service (Pillow compress/resize), scene_analyzer,
                     rate_limiter, project_service
           auth: Firebase Admin token verification middleware
           storage: local ./uploads served as static files
           db: Base.metadata.create_all at startup (no Alembic migrations in use)
infra/     docker-compose: PostgreSQL + Redis (local only)
```

## Target production topology ($0/mo)

```
┌─────────────┐     HTTPS      ┌──────────────────┐
│   Vercel    │ ─────────────▶ │  Render (free)   │
│  (frontend) │   /api proxy   │  FastAPI backend  │
└─────────────┘                └───┬─────┬────┬───┘
                                   │     │    │
                     ┌─────────────┘     │    └──────────────┐
                     ▼                   ▼                   ▼
              ┌────────────┐    ┌───────────────┐    ┌──────────────┐
              │    Neon    │    │ Cloudflare R2 │    │ AI providers │
              │  Postgres  │    │ (image store) │    │ NIM → Gemini │
              │   (free)   │    │  (10GB free)  │    │ (free tiers) │
              └────────────┘    └───────────────┘    └──────────────┘
```

| Concern | Choice | Why |
|---|---|---|
| Frontend hosting | Vercel free | Native Next.js, zero config |
| Backend hosting | Render free web service | Runs the existing FastAPI app as-is (Docker or `uvicorn` start command). Cold starts ~50s after idle — acceptable at launch |
| Database | Neon free Postgres | Already on asyncpg/SQLAlchemy; connection-string swap. 0.5GB is plenty |
| Object storage | Cloudflare R2 (S3 API via boto3) | Free hosts have **ephemeral disks** — local `./uploads` is lost on redeploy. 10GB free, no egress fees |
| Redis | **Dropped** | Only used for rate limiting. Quotas must live in Postgres anyway (they're billing state, not cache). One less service |
| AI | Keep NIM primary → Gemini fallback | Already built and free. `ai_provider.py` unchanged |
| Auth | Keep Firebase Auth | Already built. Spark plan is free |

## Key changes from current code

1. **Storage abstraction**: `image_service` writes to R2 instead of local disk; analysis
   records store the R2 public URL (or presigned URL) instead of `/uploads/...` paths.
2. **Quota enforcement**: `rate_limiter.py` becomes Postgres-backed usage tracking.
   New columns on `users`: `plan` (`free`/`pro`), monthly analysis count derived by
   counting `analyses` rows in the current month (no counter to keep in sync).
   Limits: **free = 5 analyses/month, 2 projects**. Checked in the analysis and
   project-create routes; returns 402-style JSON the frontend turns into an upgrade prompt.
3. **Waitlist**: `waitlist` table (email, created_at, source) + one public POST endpoint.
4. **Migrations**: Alembic replaces `create_all` for production DB changes
   (`create_all` stays for tests/local).
5. **Share links** (Phase 2): `share_token` column on analyses; public
   `GET /api/share/{token}` endpoint (no auth) + `/share/[token]` frontend page.
6. **Config**: all secrets via environment variables only — no JSON key files,
   no committed `.env` (see `security.md`).

## Data flow: analysis request (target)

1. User uploads reference still → frontend `POST /api/analysis` (Firebase ID token).
2. Backend middleware verifies token → quota check against Postgres (free: 5/mo).
3. `image_service` compresses (Pillow), uploads to R2, returns URL.
4. `ai_provider` calls NIM; on failure falls back to Gemini; returns structured JSON
   (lighting, focal length, palette, framing).
5. Analysis row persisted (user, project/scene link, R2 URL, JSON result, share_token).
6. Frontend renders result + overlays; share page reads the same row publicly by token.

## What is deliberately NOT built

- Team workspaces / roles / multi-tenancy — Phase 3, gated on waitlist demand.
- Payment processing — waitlist first (see `design.md`).
- Background job queue — analyses run in-request (NIM responds in seconds; fine at this scale).
- CDN/image optimization beyond R2 — add when traffic exists.
