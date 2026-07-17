# Security

## 🚨 P0 — committed credentials (fix before anything else)

These files are **committed to the git repository right now**:

| File | Contents |
|---|---|
| `backend/director-ai-55e1e-firebase-adminsdk-fbsvc-22528e30e4.json` | Firebase Admin private key |
| `backend/firebase-service-account.json` | Firebase Admin private key |
| `backend/.env` | AI provider API keys (NIM/Gemini/Groq), DB creds |
| `.env` (root) | Infra creds |
| `frontend/.env.local` | Firebase client config (public-ish, but shouldn't be committed) |

Remediation order — **rotation is the real fix; history rewriting is secondary**:

1. **Rotate every secret**: generate a new Firebase service-account key and delete the
   old ones in Google Cloud Console; regenerate NIM, Gemini, and Groq API keys; change
   any DB passwords that appear.
2. Remove the files from the working tree and add to `.gitignore`
   (`*.json` service accounts, `.env*` except `*.example`).
3. Load the Firebase Admin credential from the `GOOGLE_APPLICATION_CREDENTIALS` env var
   or a `FIREBASE_SERVICE_ACCOUNT_JSON` env var (JSON string) — file path only for local dev.
4. If the repo is (or ever becomes) public: purge history with `git filter-repo`.
   If it stays private, rotation alone is sufficient — don't burn a day on history surgery.

## Production hardening (Phase 1 scope)

- **CORS**: allowlist exactly the Vercel domain(s), not `*`.
- **Auth**: Firebase ID-token verification middleware already exists — verify it covers
  every non-public router; the only unauthenticated endpoints should be
  `POST /api/waitlist`, `GET /api/share/{token}`, and health checks.
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
