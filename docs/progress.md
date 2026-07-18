# Progress

Single source of truth for where the production push stands. Update as tasks complete.

**Current phase**: Phase 1 — backend **deployed on Render**, boots clean against Neon
**Live URL**: backend up; frontend + smoke test still outstanding
**Waitlist count**: 0 (Phase 3 gate: 25)

## Phase status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Launch (`phases/phase-1-launch.md`) | 🟨 Backend live | Frontend deploy + smoke test remain |
| Phase 2 — Funnel (`phases/phase-2-funnel.md`) | ⬜ Blocked on Phase 1 | |
| Phase 3 — Monetize (`phases/phase-3-monetize.md`) | 🔒 Gated | Needs waitlist signal |

## Phase 1 checklist (mirror of phase doc)

- [x] 1. Security P0 — resolved: secrets verified **never committed** and gitignored (see `security.md`)
- [x] 1b. Auth/IDOR audit — ownership regression tests in `tests/test_ownership.py`
- [x] 2. Storage on any S3-compatible provider — `services/storage_service.py`, local `/uploads` mount removed
- [x] 3. Alembic migrations — baseline + schema additions, applied to Neon at boot
- [x] 4. Quotas (5 analyses/mo, 2 projects) + waitlist endpoint + upgrade UI
- [x] 5a. Backend deployed on Render, migrations applied, `/health` green
- [ ] 5b. Frontend deployed on Vercel
- [ ] 5c. 10-step smoke test in `docs/deploy.md` passed against production

### Outstanding before launch

1. Deploy the frontend on Vercel (step 4 of `docs/deploy.md`).
2. Firebase console → Authentication → Authorized domains → add the Vercel
   domain. **Login fails silently without this** — no error, just no session.
3. Set Render's `CORS_ORIGINS` to the real Vercel origin if it differs from the
   value guessed at deploy time.
4. Run the 10-step smoke test.

> **Startup guards check presence, not validity.** The boot succeeding proves
> `S3_*` and `FIREBASE_SERVICE_ACCOUNT_JSON` are *set*, not that the credentials
> work — a placeholder passes the guard and then fails on first upload or first
> login. Smoke steps 2 and 6 are what actually exercise them.

## Phase 2 checklist

- [ ] 1. Landing page at `/`, login moved to `/login`
- [ ] 2. Public share links (`/share/[token]`)
- [ ] 3. Watermarked free-tier PDF exports
- [ ] 4. Minimal analytics / source tracking

## Decisions log

| Date | Decision |
|---|---|
| 2026-07-18 | Target: B2B production houses via indie-filmmaker freemium funnel |
| 2026-07-18 | $0/mo infra: Vercel + Render free + Neon + R2; Redis dropped |
| 2026-07-18 | No billing at launch — free tier + Pro waitlist; Phase 3 gated on 25 signups |
