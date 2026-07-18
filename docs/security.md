# Security

## ✅ Credential exposure — verified NOT committed (corrected 2026-07-18)

An earlier draft of this document claimed these files were committed to git. **That
was wrong.** Verified against the full history (29 commits, all branches):

```
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -iE "\.env|adminsdk|service-account|credential|secret|\.pem$|\.key$"
# -> only backend/.env.example, .env.example, frontend/.env.local.example
```

| File | On disk | In git history | Ignored by |
|---|---|---|---|
| `backend/director-ai-*-firebase-adminsdk-*.json` | yes | **never** | `backend/*.json` |
| `backend/firebase-service-account.json` | yes | **never** | `backend/*.json` |
| `backend/.env` | yes | **never** | `.env` |
| `.env` (root) | yes | **never** | `.env` |
| `frontend/.env.local` | yes | **never** | `.env*.local` |

No history rewriting is needed, and `git filter-repo` would be pure waste here.

**Still worth doing before launch**, at lower urgency:

1. **Rotate the AI provider keys** (NIM, Gemini, Groq) if they have ever been pasted
   into a chat, issue, or screen share. Cheap insurance, not incident response.
2. Keep the Firebase Admin key file local-only. Production loads it from
   `FIREBASE_SERVICE_ACCOUNT_JSON` (a JSON string env var) — implemented in
   `backend/auth/firebase.py`, which additionally **crashes at boot** rather than
   running with auth disabled when `APP_ENV=production` and the credential fails
   to load.
3. Before any `git add -A`, confirm `git status --short` shows no secret files.
   The `.gitignore` rules above already cover them, but `git add -f` bypasses them.

## Production hardening (Phase 1 scope)

- **CORS**: allowlist exactly the Vercel domain(s), not `*`.
- **Auth**: Firebase ID-token verification middleware already exists — verify it covers
  every non-public router; the only unauthenticated endpoints should be
  `POST /api/v1/waitlist` and `GET /health` (share links arrive in Phase 2).
- **Ownership checks**: every project/scene/shot/analysis query must filter by the
  authenticated `user_id` (audit existing routes for IDOR — a user must never fetch
  another user's project by guessing an ID).
- **Upload validation**: enforce content-type + magic-bytes image check and a hard size
  cap (already partially handled by Pillow compression — validate *before* processing).
  Uploads go to R2 under non-guessable keys (uuid), never user-supplied filenames.
- **Quota enforcement server-side**: limits live in the backend (Postgres), never
  trusted to the frontend.
- **Rate limiting**: keep per-IP limiting on the two public endpoints (waitlist, share)
  to prevent abuse; simple in-memory limiter is fine on a single free-tier instance
  (`rate_limiter.py` already exists — repurpose).
- **Share tokens**: `secrets.token_urlsafe(16)`+ — unguessable, revocable (nullable column).
- **Secrets in deploys**: Render/Vercel environment variable stores only. No secrets in
  build args, logs, or `NEXT_PUBLIC_*` (except the Firebase client config, which is
  designed to be public).
- **Debug off**: `APP_DEBUG=false` in production; error responses must not leak stack
  traces or SQL (the global exception handler in `main.py` should return generic 500s).

## Explicitly deferred (revisit at Phase 3 / first paying customer)

- Firebase App Check, CSP headers, dependency audit automation, pen-test level review.
- These are listed so they're deferred deliberately, not forgotten.
