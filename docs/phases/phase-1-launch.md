# Phase 1 — Get it live, gate it, waitlist it

**Goal**: a stranger can use the real product at a public URL; free limits funnel to a waitlist.
**Done when**: all success criteria in `../design.md` except share links hold on the live URL.

## Tasks (in order)

### 1. Security P0 (blocks everything — see `../security.md`)
- [ ] Rotate Firebase service-account key, NIM/Gemini/Groq API keys, DB passwords
- [ ] Remove committed secret files; extend `.gitignore`
- [ ] Load Firebase Admin credential from env var
- [ ] Audit all routers for auth coverage + user-ownership (IDOR) checks

### 2. Storage → Cloudflare R2
- [ ] R2 bucket + API token (free tier)
- [ ] `image_service` uploads to R2 via boto3 (S3 API), uuid keys
- [ ] Analysis records store R2 URLs; remove local static file serving from `main.py`
- [ ] Upload validation: magic-bytes check + size cap before Pillow processing

### 3. Database → Neon + Alembic
- [ ] Neon free project; `DATABASE_URL` swap
- [ ] Alembic init + initial migration matching current models
- [ ] Migration for new columns/tables: `users.plan`, `analyses.share_token`, `waitlist`

### 4. Quotas + waitlist
- [ ] Server-side checks: free = 5 analyses/month (count `analyses` rows per calendar
      month), 2 projects. Enforced in analysis + project-create routes → structured
      `quota_exceeded` error response
- [ ] `POST /api/waitlist` (public, rate-limited): email + source
- [ ] Frontend: navbar usage meter, upgrade modal on quota errors → waitlist email capture
- [ ] Drop Redis dependency (quotas are Postgres; keep in-memory limiter for public endpoints)

### 5. Deploy
- [ ] Backend on Render free (env vars, health check endpoint, CORS allowlist)
- [ ] Frontend on Vercel (API rewrite → Render URL, Firebase env vars)
- [ ] Firebase Auth: add production domains to authorized domains
- [ ] Smoke test the full loop live: signup → project → analyze → shot list → PDF
- [ ] Run backend pytest + frontend vitest suites; fix anything the changes broke

## Risks / notes
- Render free cold start (~50s after 15min idle): acceptable; add a friendly frontend
  loading state for the first request. Do NOT add keep-alive pingers (ToS-gray, wasteful).
- NIM/Gemini free-tier rate limits are the real ceiling; the 5/month quota also protects us.
