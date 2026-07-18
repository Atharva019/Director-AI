# Progress

Single source of truth for where the production push stands. Update as tasks complete.

**Current phase**: Phase 1 — code complete, ready to deploy
**Live URL**: — (not yet deployed)
**Waitlist count**: 0 (Phase 3 gate: 25)

## Phase status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Launch (`phases/phase-1-launch.md`) | 🟨 Code complete | Needs Neon + R2 provisioning, then deploy |
| Phase 2 — Funnel (`phases/phase-2-funnel.md`) | ⬜ Blocked on Phase 1 | |
| Phase 3 — Monetize (`phases/phase-3-monetize.md`) | 🔒 Gated | Needs waitlist signal |

## Phase 1 checklist (mirror of phase doc)

- [x] 1. Security P0 — resolved: secrets verified **never committed** and gitignored (see `security.md`)
- [x] 1b. Auth/IDOR audit — ownership regression tests in `tests/test_ownership.py`
- [x] 2. Storage on Cloudflare R2 — `services/storage_service.py`, local `/uploads` mount removed
- [x] 3. Alembic migrations — baseline + schema additions, verified on a fresh DB
- [x] 4. Quotas (5 analyses/mo, 2 projects) + waitlist endpoint + upgrade UI
- [x] 5. Deploy config written and container-verified; **live deploy pending rotation**

### Outstanding before launch

1. Provision Neon (Postgres) and Cloudflare R2 — both free tier.
2. Follow `docs/deploy.md`: Render blueprint, Vercel import, Firebase authorized
   domain, `CORS_ORIGINS`.
3. Run the 10-step smoke test in `docs/deploy.md`.
4. Optional: rotate the AI provider keys if they've ever left this machine.

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
