# Phase 3 — Monetize + teams (GATED — do not start yet)

**Trigger** (from `../design.md`): ≥25 waitlist emails OR 3 direct "can I pay you" requests.
Until then, this phase does not get planned in detail. Building billing and multi-tenancy
for zero customers is the failure mode this gate exists to prevent.

## Rough shape (to be re-planned when triggered)

1. **Billing**: Razorpay subscriptions (Stripe India is invite-only) → `users.plan = pro`.
   Manual UPI + admin flag-flip is an acceptable v0 for the first handful of customers.
2. **Pro tier delivery**: lift quotas, clean PDF exports — already wired via `plan`,
   so Pro "turns on" with a column update. Phase 1/2 made this phase small on purpose.
3. **Teams (the actual $50–200/mo product)**: workspaces, member invites, shared
   projects, roles. Requires real multi-tenancy design — own spec when the time comes.
4. **Ops maturity**: paid backend tier (kill cold starts), error monitoring, backups.

## Signals to collect meanwhile (already in Phase 1–2)
- Waitlist emails + sources, quota-hit frequency, share-link conversion.
