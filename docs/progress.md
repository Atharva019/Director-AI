# Progress

Single source of truth for where the production push stands. Update as tasks complete.

**Current phase**: Phase 1 — not started
**Live URL**: —
**Waitlist count**: 0 (Phase 3 gate: 25)

## Phase status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Launch (`phases/phase-1-launch.md`) | ⬜ Not started | Security P0 first |
| Phase 2 — Funnel (`phases/phase-2-funnel.md`) | ⬜ Blocked on Phase 1 | |
| Phase 3 — Monetize (`phases/phase-3-monetize.md`) | 🔒 Gated | Needs waitlist signal |

## Phase 1 checklist (mirror of phase doc)

- [ ] 1. Security P0: keys rotated, secrets out of repo, auth/IDOR audit
- [ ] 2. Storage on Cloudflare R2
- [ ] 3. Neon Postgres + Alembic migrations
- [ ] 4. Quotas (5 analyses/mo, 2 projects) + waitlist endpoint + upgrade UI
- [ ] 5. Deployed: Render (API) + Vercel (frontend), smoke-tested live, tests green

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
