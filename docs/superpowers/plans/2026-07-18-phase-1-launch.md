# Phase 1 — Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take Director AI from a local-only app to a secured, quota-gated, waitlist-enabled product running on free-tier hosting.

**Architecture:** Keep the existing FastAPI + Next.js + Firebase Auth stack. Move image storage from local disk to Cloudflare R2 (free hosts have ephemeral disks). Move quota state to Postgres (drop Redis). Enforce free limits server-side (5 analyses/month, 2 projects) and funnel over-limit users to a Pro waitlist. Introduce Alembic for production migrations while keeping `create_all` for tests.

**Tech Stack:** FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, boto3 (R2 S3 API), Pillow, Firebase Admin, Next.js 15 / React 19, Vitest, Pytest.

## Global Constraints

- API prefix is `/api/v1`. All new backend routes mount under it via `app.include_router(..., prefix=API_V1)` in `backend/main.py`.
- Public (unauthenticated) endpoints in Phase 1: `POST /api/v1/waitlist` and `GET /health` only. Everything else requires `Depends(get_current_user)`.
- Free-tier limits (exact values): **5 analyses per calendar month, 2 projects**. Pro plan bypasses both.
- Quota is enforced server-side only. The frontend never decides limits.
- No secrets in the repo, in logs, or in `NEXT_PUBLIC_*` (except the Firebase client config, which is designed to be public).
- Backend tests run with `cd backend && PYTHONPATH=. pytest`. Tests use SQLite in-memory (`tests/conftest.py`) and must never require Postgres, Redis, R2, or network AI calls.
- Frontend tests run with `cd frontend && npm test` (Vitest).
- Quota-exceeded responses use HTTP 402 with a JSON `detail` object of shape:
  `{"error": "quota_exceeded", "resource": "analysis"|"project", "limit": int, "used": int, "message": str}`.
- User-facing upgrade copy string (verbatim, reused everywhere): **"Join the Pro waitlist for unlimited access."**

---

## File Structure

**Backend — new files:**
- `backend/services/storage_service.py` — R2 upload via boto3; replaces local-disk logic in `image_service.py`.
- `backend/services/quota_service.py` — usage counting + limit checks.
- `backend/models/waitlist.py` — `WaitlistEntry` ORM model.
- `backend/schemas/waitlist.py` — waitlist request/response schemas.
- `backend/routers/waitlist.py` — public waitlist endpoint.
- `backend/alembic.ini`, `backend/migrations/` — Alembic config + versions.
- `backend/tests/test_quota.py`, `backend/tests/test_waitlist.py`, `backend/tests/test_storage.py`, `backend/tests/test_ownership.py` — new tests.

**Backend — modified files:**
- `backend/config.py` — R2 settings, plan constants, prod CORS behavior, Firebase-from-env.
- `backend/auth/firebase.py` — load credential from env var (JSON string) or path.
- `backend/models/user.py` — add `plan` column.
- `backend/models/analysis.py` — add `share_token` column.
- `backend/services/image_service.py` — delegate persistence to `storage_service`.
- `backend/routers/analysis.py` — quota check + store R2 URL.
- `backend/routers/projects.py` — quota check on create.
- `backend/main.py` — remove `/uploads` static mount, register waitlist router.
- `backend/requirements.txt` — add `boto3`, `alembic` already present.

**Frontend — new files:**
- `frontend/src/components/UpgradeModal.tsx` — Pro waitlist modal + email capture.
- `frontend/src/components/UpgradeModal.module.css`.
- `frontend/src/components/UsageMeter.tsx` — navbar usage indicator.

**Frontend — modified files:**
- `frontend/src/lib/api.ts` — surface quota (402) errors as a typed error.
- `frontend/src/components/Navbar.tsx` — mount `UsageMeter`.
- `frontend/src/app/analyze/page.tsx` — catch quota error → open `UpgradeModal`.
- `frontend/src/app/project/new/page.tsx` — catch quota error → open `UpgradeModal`.
- `frontend/next.config.ts` — R2 image host + prod API URL.

**Deploy — new files:**
- `backend/render.yaml` — Render service definition.
- `backend/Dockerfile` — optional container build for Render.
- `docs/deploy.md` — step-by-step deploy + env var reference.

---

## Task 1: Purge and rotate committed secrets

**Files:**
- Modify: `.gitignore` (root)
- Delete from tree: `backend/director-ai-55e1e-firebase-adminsdk-fbsvc-22528e30e4.json`, `backend/firebase-service-account.json`, `backend/.env`, `.env` (root), `frontend/.env.local`

**Interfaces:**
- Produces: a repo with no committed secrets; local dev still works via untracked `.env` files.

> **This task is partly manual (key rotation cannot be automated). Do the rotation steps in a browser/console, then the git steps.**

- [ ] **Step 1: Rotate every exposed credential (manual, do first)**

Do these in the respective consoles BEFORE removing files, so the old keys are already dead if history leaks:
1. Google Cloud Console → IAM → Service Accounts → the Firebase admin SA → Keys → delete both existing keys, create a new JSON key. Save it OUTSIDE the repo (e.g. `~/secrets/director-ai-firebase.json`).
2. NVIDIA NIM dashboard → regenerate `NVIDIA_NIM_API_KEY`.
3. Google AI Studio → regenerate `GEMINI_API_KEY`.
4. Groq console → regenerate/revoke `GROQ_API_KEY` (legacy).
5. If any real Postgres password appears in the committed `.env`, change it (Neon creds are created fresh in Task 4, so this mainly applies to a live DB).

- [ ] **Step 2: Extend `.gitignore`**

Append to root `.gitignore` (create the file if missing):

```gitignore
# Secrets — never commit
.env
.env.*
!.env.example
!.env.*.example
**/firebase-service-account.json
**/*-firebase-adminsdk-*.json
backend/.env
frontend/.env.local
```

- [ ] **Step 3: Remove the secret files from git tracking (keep local copies untracked)**

```bash
cd "/home/atharvakakdam/MONO/projects/Director AI"
git rm --cached backend/director-ai-55e1e-firebase-adminsdk-fbsvc-22528e30e4.json \
                backend/firebase-service-account.json \
                backend/.env .env frontend/.env.local
```

Then move the (now untracked) Firebase JSON out of `backend/` so it can't be re-added by accident; point local dev at it via env var in Task 2.

- [ ] **Step 4: Verify nothing secret remains staged/tracked**

Run: `git ls-files | grep -E '\.env$|firebase.*\.json|adminsdk' || echo "CLEAN"`
Expected: `CLEAN`

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "security: remove committed secrets, ignore env and service-account files"
```

> Note on history: if this repo is or will be public, purge history with `git filter-repo` in a separate follow-up. If it stays private, the rotation in Step 1 is the real fix — do not block launch on history rewriting.

---

## Task 2: Load Firebase credential from env; harden config for production

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/auth/firebase.py`
- Test: `backend/tests/test_config.py` (create)

**Interfaces:**
- Consumes: `Settings` from `config.get_settings()`.
- Produces: `Settings.FIREBASE_SERVICE_ACCOUNT_JSON: str`, `Settings.plan_free_analyses: int`, `Settings.plan_free_projects: int`, R2 settings (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_BASE_URL`). `initialize_firebase()` reads JSON from env when set.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_config.py`:

```python
from config import Settings


def test_cors_regex_disabled_in_production():
    s = Settings(APP_ENV="production", CORS_ORIGINS="https://app.example.com")
    assert s.cors_origin_list == ["https://app.example.com"]
    assert s.is_production is True


def test_cors_regex_flag_in_development():
    s = Settings(APP_ENV="development")
    assert s.is_production is False


def test_free_plan_limits_present():
    s = Settings()
    assert s.plan_free_analyses == 5
    assert s.plan_free_projects == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_config.py -v`
Expected: FAIL (`AttributeError: 'Settings' object has no attribute 'is_production'`).

- [ ] **Step 3: Implement config changes**

In `backend/config.py`, inside `Settings`, add these fields (after the existing Firebase field) and properties:

```python
    # ── Firebase Auth ─────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    # JSON string of the service account (preferred in production). If set,
    # takes precedence over FIREBASE_CREDENTIALS_PATH.
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""

    # ── Cloudflare R2 (S3-compatible object storage) ──────────────────────
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_BASE_URL: str = ""  # e.g. https://pub-xxxx.r2.dev or a custom domain

    # ── Plan limits ───────────────────────────────────────────────────────
    plan_free_analyses: int = 5
    plan_free_projects: int = 2
```

Add these properties to `Settings`:

```python
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def r2_enabled(self) -> bool:
        return bool(self.R2_ACCOUNT_ID and self.R2_ACCESS_KEY_ID and self.R2_BUCKET)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && PYTHONPATH=. pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Load Firebase credential from env in `auth/firebase.py`**

Open `backend/auth/firebase.py`, find `initialize_firebase()`, and make it prefer the JSON env var. Replace the credential-loading block with:

```python
import json
from firebase_admin import credentials

def _load_credential():
    settings = get_settings()
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip():
        info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        return credentials.Certificate(info)
    return credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
```

Use `_load_credential()` where the code currently builds `credentials.Certificate(...)`. (Read the existing function first; keep its guard that skips init if already initialized.)

- [ ] **Step 6: Harden CORS in `main.py`**

In `backend/main.py`, change the CORS middleware `allow_origin_regex` line to key off the new property:

```python
    allow_origin_regex=r"https?://.*" if not settings.is_production else None,
```

- [ ] **Step 7: Commit**

```bash
git add backend/config.py backend/auth/firebase.py backend/main.py backend/tests/test_config.py
git commit -m "security: load firebase creds from env, harden prod CORS, add plan/R2 config"
```

---

## Task 3: Audit auth coverage and ownership (IDOR)

**Files:**
- Test: `backend/tests/test_ownership.py` (create)
- Modify (only if the test finds a gap): `backend/routers/analysis.py`

**Interfaces:**
- Consumes: `client` and `test_user` fixtures from `tests/conftest.py`.
- Produces: a regression test proving a user cannot read another user's analysis.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_ownership.py`. It seeds an analysis owned by a *different* user, then asserts the API returns 404 for the authenticated `test_user`:

```python
import uuid
import pytest
from models.analysis import SceneAnalysis
from models.user import User


@pytest.mark.asyncio
async def test_cannot_read_other_users_analysis(client, db_session, test_user):
    other = User(id=uuid.uuid4(), firebase_uid="other_uid", email="other@example.com")
    db_session.add(other)
    await db_session.flush()

    foreign = SceneAnalysis(
        id=uuid.uuid4(), user_id=other.id, image_path="https://r2/x.jpg",
        analysis_result={}, model_used="test", confidence_score=0.5,
    )
    db_session.add(foreign)
    await db_session.commit()

    res = await client.get(f"/api/v1/analyses/{foreign.id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses_only_returns_own(client, db_session, test_user):
    other = User(id=uuid.uuid4(), firebase_uid="other2", email="o2@example.com")
    db_session.add(other)
    await db_session.flush()
    db_session.add(SceneAnalysis(
        id=uuid.uuid4(), user_id=other.id, image_path="https://r2/y.jpg",
        analysis_result={}, model_used="test", confidence_score=0.5,
    ))
    await db_session.commit()

    res = await client.get("/api/v1/analyses")
    assert res.status_code == 200
    assert res.json() == []
```

- [ ] **Step 2: Run the test**

Run: `cd backend && PYTHONPATH=. pytest tests/test_ownership.py -v`
Expected: PASS — the existing `get_analysis` and `list_analyses` already filter by `user_id`. If either FAILS, fix the offending query in `routers/analysis.py` to add `SceneAnalysis.user_id == current_user.id`, then re-run until green. (This task's value is locking that behavior with a regression test; projects/scenes/shots already route ownership through `ProjectService`.)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_ownership.py backend/routers/analysis.py
git commit -m "test: lock analysis ownership (IDOR) with regression tests"
```

---

## Task 4: Alembic setup + baseline migration

**Files:**
- Create: `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/`
- Modify: `backend/main.py` (leave `create_all` for local/test; add a comment that prod uses Alembic)

**Interfaces:**
- Produces: `alembic upgrade head` builds the current schema on a fresh Postgres DB.

- [ ] **Step 1: Initialize Alembic**

```bash
cd backend
alembic init migrations
```

- [ ] **Step 2: Point Alembic at async models**

Edit `backend/migrations/env.py`:
- Import metadata and settings:
  ```python
  from config import get_settings
  from db.database import Base
  import models  # registers all models on Base.metadata  # noqa: F401
  target_metadata = Base.metadata
  ```
- Set the URL from settings (convert asyncpg URL to sync psycopg for migrations, or use async). Simplest for free tier — use a sync driver just for migrations:
  ```python
  url = get_settings().DATABASE_URL.replace("+asyncpg", "")
  config.set_main_option("sqlalchemy.url", url)
  ```
- Add `psycopg2-binary` to `requirements.txt` (migration-time only).

- [ ] **Step 3: Generate the baseline migration**

Requires a reachable Postgres (local docker-compose is fine):

```bash
cd backend
docker-compose -f ../docker-compose.yml up -d   # if not already running
alembic revision --autogenerate -m "baseline: users, projects, scenes, shots, scene_analyses"
```

- [ ] **Step 4: Apply and verify**

Run: `cd backend && alembic upgrade head`
Expected: no error; `alembic current` shows the baseline revision.

- [ ] **Step 5: Add prod-vs-test note in `main.py`**

In `backend/main.py` lifespan, above the `create_all` call, add:

```python
    # NOTE: create_all is for local dev and the SQLite test suite only.
    # Production schema changes go through Alembic (`alembic upgrade head`).
```

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/migrations backend/requirements.txt backend/main.py
git commit -m "feat(db): add Alembic with baseline migration"
```

---

## Task 5: Add `plan` column to users

**Files:**
- Modify: `backend/models/user.py`
- Create: `backend/migrations/versions/<hash>_add_user_plan.py` (autogenerated)

**Interfaces:**
- Produces: `User.plan: str` defaulting to `"free"` (values: `"free"` | `"pro"`).

- [ ] **Step 1: Add the column to the model**

In `backend/models/user.py`, add after `avatar_url`:

```python
    plan: Mapped[str] = mapped_column(String(16), nullable=False, default="free")
```

- [ ] **Step 2: Generate migration**

```bash
cd backend && alembic revision --autogenerate -m "add user plan column"
```

Verify the generated file adds the `plan` column with a server default. If autogenerate omits a server default (existing rows), edit the migration `upgrade()` to:

```python
    op.add_column("users", sa.Column("plan", sa.String(length=16), nullable=False, server_default="free"))
```

- [ ] **Step 3: Apply and verify**

Run: `cd backend && alembic upgrade head`
Expected: no error.

- [ ] **Step 4: Verify tests still pass (create_all path)**

Run: `cd backend && PYTHONPATH=. pytest -q`
Expected: PASS (SQLite schema now includes `plan`).

- [ ] **Step 5: Commit**

```bash
git add backend/models/user.py backend/migrations/versions
git commit -m "feat(db): add user.plan column (free/pro)"
```

---

## Task 6: Add `share_token` column to scene_analyses

**Files:**
- Modify: `backend/models/analysis.py`
- Create: `backend/migrations/versions/<hash>_add_analysis_share_token.py`

**Interfaces:**
- Produces: `SceneAnalysis.share_token: str | None`, unique, nullable (populated by Phase 2 share feature).

- [ ] **Step 1: Add the column**

In `backend/models/analysis.py`, add after `confidence_score`:

```python
    share_token: Mapped[str | None] = mapped_column(
        String(48), unique=True, nullable=True, index=True
    )
```

- [ ] **Step 2: Generate, apply, verify**

```bash
cd backend && alembic revision --autogenerate -m "add analysis share_token" && alembic upgrade head
PYTHONPATH=. pytest -q
```
Expected: migration applies; tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/models/analysis.py backend/migrations/versions
git commit -m "feat(db): add scene_analyses.share_token (Phase 2 share links)"
```

---

## Task 7: Waitlist model, schema, and migration

**Files:**
- Create: `backend/models/waitlist.py`, `backend/schemas/waitlist.py`
- Modify: `backend/models/__init__.py` (register model)
- Create: `backend/migrations/versions/<hash>_add_waitlist.py`

**Interfaces:**
- Produces: `WaitlistEntry` ORM (`id`, `email` unique, `source`, `created_at`); `WaitlistCreate` schema (`email: EmailStr`, `source: str = "app"`), `WaitlistResponse` (`email`, `created_at`).

- [ ] **Step 1: Create the model**

`backend/models/waitlist.py`:

```python
"""Waitlist entry ORM model — captures Pro-tier interest."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="app")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<WaitlistEntry {self.email}>"
```

- [ ] **Step 2: Register the model**

In `backend/models/__init__.py`, add `from models.waitlist import WaitlistEntry` alongside the other model imports (so `create_all` and Alembic autogenerate see it).

- [ ] **Step 3: Create schemas**

`backend/schemas/waitlist.py`:

```python
"""Pydantic schemas for the waitlist."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class WaitlistCreate(BaseModel):
    email: EmailStr
    source: str = "app"


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: str
    created_at: datetime
```

Add `pydantic[email]` (or `email-validator`) to `requirements.txt`.

- [ ] **Step 4: Migration**

```bash
cd backend && alembic revision --autogenerate -m "add waitlist table" && alembic upgrade head
```

- [ ] **Step 5: Commit**

```bash
git add backend/models/waitlist.py backend/models/__init__.py backend/schemas/waitlist.py backend/requirements.txt backend/migrations/versions
git commit -m "feat(db): add waitlist model, schema, migration"
```

---

## Task 8: R2 storage service

**Files:**
- Create: `backend/services/storage_service.py`
- Test: `backend/tests/test_storage.py`
- Modify: `backend/requirements.txt` (add `boto3`)

**Interfaces:**
- Produces:
  - `build_object_key(ext: str) -> str` — returns `f"analyses/{uuid4().hex}{ext}"`.
  - `StorageService.upload_bytes(data: bytes, ext: str, content_type: str) -> str` — puts the object in R2 and returns the public URL `f"{R2_PUBLIC_BASE_URL}/{key}"`.
- Consumes: `get_settings()` for R2 credentials.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_storage.py` (mocks boto3 — no network):

```python
from unittest.mock import MagicMock
import pytest
from services import storage_service
from services.storage_service import StorageService, build_object_key


def test_build_object_key_uses_extension():
    key = build_object_key(".jpg")
    assert key.startswith("analyses/")
    assert key.endswith(".jpg")
    assert len(key) > len("analyses/.jpg")


def test_upload_bytes_puts_object_and_returns_url(monkeypatch):
    fake_client = MagicMock()
    svc = StorageService()
    monkeypatch.setattr(svc, "_client", fake_client)
    monkeypatch.setattr(svc, "_bucket", "test-bucket")
    monkeypatch.setattr(svc, "_public_base_url", "https://pub.example.r2.dev")

    url = svc.upload_bytes(b"imagedata", ".png", "image/png")

    fake_client.put_object.assert_called_once()
    kwargs = fake_client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Body"] == b"imagedata"
    assert kwargs["ContentType"] == "image/png"
    assert url.startswith("https://pub.example.r2.dev/analyses/")
    assert url.endswith(".png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_storage.py -v`
Expected: FAIL (`ModuleNotFoundError: services.storage_service`).

- [ ] **Step 3: Implement the service**

`backend/services/storage_service.py`:

```python
"""Cloudflare R2 object storage (S3-compatible) via boto3."""

import logging
import uuid
from functools import lru_cache

import boto3
from botocore.config import Config

from config import get_settings

logger = logging.getLogger(__name__)


def build_object_key(ext: str) -> str:
    """Non-guessable object key under the analyses/ prefix."""
    return f"analyses/{uuid.uuid4().hex}{ext}"


class StorageService:
    """Uploads image bytes to Cloudflare R2 and returns a public URL."""

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.R2_BUCKET
        self._public_base_url = settings.R2_PUBLIC_BASE_URL.rstrip("/")
        self._endpoint = (
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            if settings.R2_ACCOUNT_ID else None
        )
        self._access_key = settings.R2_ACCESS_KEY_ID
        self._secret_key = settings.R2_SECRET_ACCESS_KEY
        self._client = None  # lazy

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._client

    def upload_bytes(self, data: bytes, ext: str, content_type: str) -> str:
        key = build_object_key(ext)
        self._get_client().put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
        )
        url = f"{self._public_base_url}/{key}"
        logger.info("Uploaded object to R2: %s", key)
        return url


@lru_cache()
def get_storage_service() -> StorageService:
    return StorageService()
```

Add `boto3` to `backend/requirements.txt`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && PYTHONPATH=. pytest tests/test_storage.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/storage_service.py backend/tests/test_storage.py backend/requirements.txt
git commit -m "feat(storage): add Cloudflare R2 upload service"
```

---

## Task 9: Route uploads through R2; remove local static serving

**Files:**
- Modify: `backend/services/image_service.py`
- Modify: `backend/main.py` (remove `/uploads` mount + upload-dir creation)
- Test: `backend/tests/test_storage.py` (extend)

**Interfaces:**
- Consumes: `StorageService.upload_bytes`, `build_object_key`, existing Pillow helpers.
- Produces: `ImageService.save_upload(file) -> str` now returns a public R2 URL (same signature, new meaning).

- [ ] **Step 1: Write the failing test**

Extend `backend/tests/test_storage.py`:

```python
import io
from unittest.mock import MagicMock
import pytest
from PIL import Image
from starlette.datastructures import UploadFile, Headers
from services.image_service import ImageService


def _png_upload():
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), (10, 20, 30)).save(buf, format="PNG")
    buf.seek(0)
    return UploadFile(file=buf, filename="ref.png", headers=Headers({"content-type": "image/png"}))


@pytest.mark.asyncio
async def test_save_upload_returns_r2_url(monkeypatch):
    svc = ImageService()
    fake_storage = MagicMock()
    fake_storage.upload_bytes.return_value = "https://pub.example.r2.dev/analyses/abc.png"
    monkeypatch.setattr(svc, "_storage", fake_storage)

    url = await svc.save_upload(_png_upload())
    assert url == "https://pub.example.r2.dev/analyses/abc.png"
    fake_storage.upload_bytes.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_storage.py::test_save_upload_returns_r2_url -v`
Expected: FAIL (`ImageService` still writes to disk / has no `_storage`).

- [ ] **Step 3: Refactor `image_service.py`**

Change `ImageService` to keep all validation + Pillow resize logic but persist via R2. Replace `__init__` and the save/persist section:

```python
    def __init__(self) -> None:
        settings = get_settings()
        self.max_bytes = settings.max_upload_bytes
        from services.storage_service import get_storage_service
        self._storage = get_storage_service()
```

Replace steps 4–5 of `save_upload` (the Pillow save-to-disk block) with an in-memory buffer + R2 upload:

```python
        # ── 4. Open with Pillow, resize if needed ────────────────────────
        from io import BytesIO
        img = Image.open(BytesIO(contents))
        img = self._ensure_rgb(img)
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        # ── 5. Serialize and upload to R2 ────────────────────────────────
        fmt = self._pil_format(ext)
        out = BytesIO()
        img.save(out, format=fmt, quality=90)
        out.seek(0)
        content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(fmt, "image/jpeg")
        return self._storage.upload_bytes(out.getvalue(), ext, content_type)
```

Remove the `self.upload_dir` attribute and its `mkdir`. Remove now-unused imports (`Path`, `uuid`) if nothing else uses them.

- [ ] **Step 4: Remove local static serving from `main.py`**

In `backend/main.py`:
- Delete the line `app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")`.
- Delete the `from fastapi.staticfiles import StaticFiles` import.
- Delete the lifespan block that creates `upload_dir` (steps under "3. Create upload directory").

- [ ] **Step 5: Run tests**

Run: `cd backend && PYTHONPATH=. pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/image_service.py backend/main.py backend/tests/test_storage.py
git commit -m "feat(storage): upload analysis images to R2, drop local disk serving"
```

---

## Task 10: Quota service

**Files:**
- Create: `backend/services/quota_service.py`
- Test: `backend/tests/test_quota.py`

**Interfaces:**
- Produces:
  - `async def count_analyses_this_month(db, user_id: uuid.UUID) -> int`
  - `async def count_projects(db, user_id: uuid.UUID) -> int`
  - `async def enforce_analysis_quota(db, user: User) -> None` — raises `HTTPException(402, detail=<quota dict>)` for free users at/over limit; no-op for pro.
  - `async def enforce_project_quota(db, user: User) -> None` — same shape for projects.
- The quota `detail` dict matches the Global Constraints shape.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_quota.py`:

```python
import uuid
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException
from models.user import User
from models.analysis import SceneAnalysis
from models.project import Project
from services import quota_service


async def _make_user(db, plan="free"):
    u = User(id=uuid.uuid4(), firebase_uid=f"u{uuid.uuid4().hex[:6]}",
             email=f"{uuid.uuid4().hex[:6]}@t.com", plan=plan)
    db.add(u)
    await db.flush()
    return u


@pytest.mark.asyncio
async def test_free_user_under_limit_passes(db_session):
    u = await _make_user(db_session)
    await quota_service.enforce_analysis_quota(db_session, u)  # no raise


@pytest.mark.asyncio
async def test_free_user_at_analysis_limit_raises_402(db_session):
    u = await _make_user(db_session)
    for _ in range(5):
        db_session.add(SceneAnalysis(
            id=uuid.uuid4(), user_id=u.id, image_path="https://r2/x.jpg",
            analysis_result={}, model_used="t", confidence_score=0.1,
        ))
    await db_session.flush()
    with pytest.raises(HTTPException) as exc:
        await quota_service.enforce_analysis_quota(db_session, u)
    assert exc.value.status_code == 402
    assert exc.value.detail["error"] == "quota_exceeded"
    assert exc.value.detail["resource"] == "analysis"


@pytest.mark.asyncio
async def test_pro_user_bypasses_limit(db_session):
    u = await _make_user(db_session, plan="pro")
    for _ in range(10):
        db_session.add(SceneAnalysis(
            id=uuid.uuid4(), user_id=u.id, image_path="https://r2/x.jpg",
            analysis_result={}, model_used="t", confidence_score=0.1,
        ))
    await db_session.flush()
    await quota_service.enforce_analysis_quota(db_session, u)  # no raise


@pytest.mark.asyncio
async def test_free_user_at_project_limit_raises_402(db_session):
    u = await _make_user(db_session)
    for i in range(2):
        db_session.add(Project(id=uuid.uuid4(), user_id=u.id, title=f"P{i}"))
    await db_session.flush()
    with pytest.raises(HTTPException) as exc:
        await quota_service.enforce_project_quota(db_session, u)
    assert exc.value.status_code == 402
    assert exc.value.detail["resource"] == "project"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_quota.py -v`
Expected: FAIL (`ModuleNotFoundError: services.quota_service`).

- [ ] **Step 3: Implement the service**

`backend/services/quota_service.py`:

```python
"""Free-tier usage limits, enforced against Postgres (no Redis)."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.analysis import SceneAnalysis
from models.project import Project
from models.user import User

UPGRADE_COPY = "Join the Pro waitlist for unlimited access."


def _month_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def count_analyses_this_month(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(SceneAnalysis).where(
        SceneAnalysis.user_id == user_id,
        SceneAnalysis.created_at >= _month_start(),
    )
    return int((await db.execute(stmt)).scalar_one())


async def count_projects(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Project).where(Project.user_id == user_id)
    return int((await db.execute(stmt)).scalar_one())


def _quota_error(resource: str, limit: int, used: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "error": "quota_exceeded",
            "resource": resource,
            "limit": limit,
            "used": used,
            "message": f"You've reached the free limit of {limit} {resource}s. {UPGRADE_COPY}",
        },
    )


async def enforce_analysis_quota(db: AsyncSession, user: User) -> None:
    if user.plan == "pro":
        return
    limit = get_settings().plan_free_analyses
    used = await count_analyses_this_month(db, user.id)
    if used >= limit:
        raise _quota_error("analysis", limit, used)


async def enforce_project_quota(db: AsyncSession, user: User) -> None:
    if user.plan == "pro":
        return
    limit = get_settings().plan_free_projects
    used = await count_projects(db, user.id)
    if used >= limit:
        raise _quota_error("project", limit, used)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && PYTHONPATH=. pytest tests/test_quota.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/quota_service.py backend/tests/test_quota.py
git commit -m "feat(quota): Postgres-backed free-tier limits (5 analyses/mo, 2 projects)"
```

---

## Task 11: Wire quota enforcement into routers

**Files:**
- Modify: `backend/routers/analysis.py`, `backend/routers/projects.py`
- Test: `backend/tests/test_quota_routes.py` (create)

**Interfaces:**
- Consumes: `quota_service.enforce_analysis_quota`, `enforce_project_quota`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_quota_routes.py` — the `test_user` fixture is free plan; seed it to the project limit and assert create returns 402:

```python
import uuid
import pytest
from models.project import Project


@pytest.mark.asyncio
async def test_create_project_over_limit_returns_402(client, db_session, test_user):
    # Ensure the user row exists (client fixture adds it on first auth override call)
    await client.get("/api/v1/projects/")
    for i in range(2):
        db_session.add(Project(id=uuid.uuid4(), user_id=test_user.id, title=f"P{i}"))
    await db_session.commit()

    res = await client.post("/api/v1/projects/", json={"title": "Third"})
    assert res.status_code == 402
    assert res.json()["detail"]["error"] == "quota_exceeded"
    assert res.json()["detail"]["resource"] == "project"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_quota_routes.py -v`
Expected: FAIL (create returns 201).

- [ ] **Step 3: Enforce in `projects.py`**

In `backend/routers/projects.py`, import and call at the top of `create_project`:

```python
from services import quota_service
```
```python
async def create_project(...):
    """Create a new filmmaking project."""
    await quota_service.enforce_project_quota(db, current_user)
    project = await _svc.create_project(...)
```

- [ ] **Step 4: Enforce in `analysis.py`**

In `backend/routers/analysis.py`, import `from services import quota_service` and call at the very start of `analyze_image` (before saving the upload — never spend an AI call the user isn't entitled to):

```python
async def analyze_image(...):
    await quota_service.enforce_analysis_quota(db, current_user)
    # 1. Save and validate the upload
    ...
```

- [ ] **Step 5: Run tests**

Run: `cd backend && PYTHONPATH=. pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/projects.py backend/routers/analysis.py backend/tests/test_quota_routes.py
git commit -m "feat(quota): enforce free limits on project + analysis creation"
```

---

## Task 12: Public waitlist endpoint

**Files:**
- Create: `backend/routers/waitlist.py`
- Modify: `backend/routers/__init__.py` (export `waitlist_router`), `backend/main.py` (register)
- Test: `backend/tests/test_waitlist.py`

**Interfaces:**
- Consumes: `WaitlistCreate`, `WaitlistResponse`, `WaitlistEntry`, `get_db`.
- Produces: `POST /api/v1/waitlist` (public, no auth) → 201 with `WaitlistResponse`; duplicate email → 200 idempotent (returns existing).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_waitlist.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_join_waitlist_creates_entry(client):
    res = await client.post("/api/v1/waitlist", json={"email": "a@b.com", "source": "landing"})
    assert res.status_code == 201
    assert res.json()["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_join_waitlist_is_idempotent(client):
    await client.post("/api/v1/waitlist", json={"email": "dup@b.com"})
    res = await client.post("/api/v1/waitlist", json={"email": "dup@b.com"})
    assert res.status_code in (200, 201)
    assert res.json()["email"] == "dup@b.com"


@pytest.mark.asyncio
async def test_join_waitlist_rejects_bad_email(client):
    res = await client.post("/api/v1/waitlist", json={"email": "not-an-email"})
    assert res.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_waitlist.py -v`
Expected: FAIL (404 — route not registered).

- [ ] **Step 3: Implement the router**

`backend/routers/waitlist.py`:

```python
"""Public Pro-tier waitlist endpoint (no authentication)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.waitlist import WaitlistEntry
from schemas.waitlist import WaitlistCreate, WaitlistResponse

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(
    payload: WaitlistCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> WaitlistResponse:
    existing = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == payload.email)
    )
    entry = existing.scalar_one_or_none()
    if entry is None:
        entry = WaitlistEntry(email=payload.email, source=payload.source)
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK
    return WaitlistResponse.model_validate(entry)
```

- [ ] **Step 4: Register the router**

In `backend/routers/__init__.py`, add `from routers.waitlist import router as waitlist_router` and include it in `__all__` if that list exists.
In `backend/main.py`, add to imports and register:

```python
from routers import (auth_router, projects_router, scenes_router, shots_router, analysis_router, waitlist_router)
```
```python
app.include_router(waitlist_router, prefix=API_V1)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_waitlist.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/waitlist.py backend/routers/__init__.py backend/main.py backend/tests/test_waitlist.py
git commit -m "feat(waitlist): public POST /api/v1/waitlist endpoint"
```

---

## Task 13: Frontend — surface quota errors as a typed error

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Test: `frontend/src/lib/__tests__/api.test.ts` (create)

**Interfaces:**
- Produces: `QuotaError` class (extends `Error`) with `.quota: {error, resource, limit, used, message}`; `handleResponse` throws it on 402 with a `quota_exceeded` detail object.

- [ ] **Step 1: Write the failing test**

`frontend/src/lib/__tests__/api.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { QuotaError, __parseError } from "@/lib/api";

describe("quota error parsing", () => {
  it("returns a QuotaError for a 402 quota_exceeded body", () => {
    const body = { detail: { error: "quota_exceeded", resource: "analysis", limit: 5, used: 5, message: "limit hit" } };
    const err = __parseError(402, body);
    expect(err).toBeInstanceOf(QuotaError);
    expect((err as QuotaError).quota.resource).toBe("analysis");
    expect(err.message).toBe("limit hit");
  });

  it("returns a plain Error for a string detail", () => {
    const err = __parseError(400, { detail: "bad request" });
    expect(err).not.toBeInstanceOf(QuotaError);
    expect(err.message).toBe("bad request");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- api.test`
Expected: FAIL (`QuotaError`/`__parseError` not exported).

- [ ] **Step 3: Implement in `api.ts`**

Add near the top of `frontend/src/lib/api.ts`:

```ts
export interface QuotaDetail {
  error: "quota_exceeded";
  resource: "analysis" | "project";
  limit: number;
  used: number;
  message: string;
}

export class QuotaError extends Error {
  quota: QuotaDetail;
  constructor(quota: QuotaDetail) {
    super(quota.message);
    this.name = "QuotaError";
    this.quota = quota;
  }
}

// Exported for unit testing; builds the Error a failed response should throw.
export function __parseError(status: number, body: { detail?: unknown }): Error {
  const detail = body?.detail;
  if (
    status === 402 &&
    detail && typeof detail === "object" &&
    (detail as QuotaDetail).error === "quota_exceeded"
  ) {
    return new QuotaError(detail as QuotaDetail);
  }
  if (Array.isArray(detail)) {
    const message = detail
      .map((e: { loc?: string[]; msg?: string }) => `${e.loc?.slice(-1)[0] ?? "field"}: ${e.msg ?? "invalid"}`)
      .join(", ");
    return new Error(message);
  }
  if (typeof detail === "string") return new Error(detail);
  return new Error(`HTTP ${status}`);
}
```

Replace the body of `handleResponse`'s error branch to use it:

```ts
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw __parseError(res.status, body);
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- api.test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/lib/__tests__/api.test.ts
git commit -m "feat(frontend): typed QuotaError from 402 responses"
```

---

## Task 14: Frontend — upgrade modal, usage meter, quota handling

**Files:**
- Create: `frontend/src/components/UpgradeModal.tsx`, `frontend/src/components/UpgradeModal.module.css`, `frontend/src/components/UsageMeter.tsx`
- Modify: `frontend/src/components/Navbar.tsx`, `frontend/src/app/analyze/page.tsx`, `frontend/src/app/project/new/page.tsx`

**Interfaces:**
- Consumes: `QuotaError`, `apiPost` from `@/lib/api`.
- Produces: `<UpgradeModal open reason onClose />` (posts email to `/api/v1/waitlist`); `<UsageMeter />` (best-effort display).

- [ ] **Step 1: Build `UpgradeModal.tsx`**

Create `frontend/src/components/UpgradeModal.tsx`:

```tsx
"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import styles from "./UpgradeModal.module.css";

export function UpgradeModal({
  open, reason, onClose,
}: { open: boolean; reason?: string; onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (!open) return null;

  async function join(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await apiPost("/api/v1/waitlist", { email, source: "upgrade-modal" });
      setDone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2>Upgrade to Pro</h2>
        {reason && <p className={styles.reason}>{reason}</p>}
        {done ? (
          <p className={styles.success}>You're on the list — we'll email you when Pro launches.</p>
        ) : (
          <form onSubmit={join}>
            <input
              type="email" required placeholder="you@studio.com"
              value={email} onChange={(e) => setEmail(e.target.value)}
              className={styles.input}
            />
            <button type="submit" disabled={busy} className={styles.cta}>
              {busy ? "Joining…" : "Join the Pro waitlist"}
            </button>
            {err && <p className={styles.error}>{err}</p>}
          </form>
        )}
        <button className={styles.close} onClick={onClose}>Maybe later</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Build `UpgradeModal.module.css`**

Create `frontend/src/components/UpgradeModal.module.css` matching the existing dark glassmorphism (reuse CSS custom properties already defined globally; check `globals.css` for variable names like `--surface`, `--accent`):

```css
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  display: grid; place-items: center; z-index: 1000; }
.modal { background: var(--surface, #16181d); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 2rem; width: min(90vw, 420px); box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.reason { color: var(--muted, #9aa0a6); margin: 0.5rem 0 1rem; }
.input { width: 100%; padding: 0.75rem 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04); color: inherit; margin-bottom: 0.75rem; }
.cta { width: 100%; padding: 0.75rem 1rem; border: none; border-radius: 10px; cursor: pointer;
  background: var(--accent, #e0a24a); color: #1a1205; font-weight: 600; }
.cta:disabled { opacity: 0.6; cursor: default; }
.success { color: #7ddf8f; }
.error { color: #ff6b6b; margin-top: 0.5rem; }
.close { margin-top: 1rem; background: none; border: none; color: var(--muted, #9aa0a6);
  cursor: pointer; width: 100%; }
```

- [ ] **Step 3: Wire the modal into `analyze/page.tsx`**

In `frontend/src/app/analyze/page.tsx`: import `QuotaError` and `UpgradeModal`, add state `const [quotaReason, setQuotaReason] = useState<string | null>(null)`, and in the analyze submit `catch`:

```tsx
} catch (e) {
  if (e instanceof QuotaError) { setQuotaReason(e.quota.message); }
  else { /* existing error handling */ }
}
```

Render at the end of the component:

```tsx
<UpgradeModal open={quotaReason !== null} reason={quotaReason ?? undefined} onClose={() => setQuotaReason(null)} />
```

- [ ] **Step 4: Wire the modal into `project/new/page.tsx`**

Apply the identical pattern to the project-create submit handler in `frontend/src/app/project/new/page.tsx`.

- [ ] **Step 5: Build `UsageMeter.tsx` and mount in Navbar**

Create `frontend/src/components/UsageMeter.tsx`. It computes usage from analyses the user already fetches, or does a lightweight count via `apiGet`. Keep it best-effort — never block render:

```tsx
"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

export function UsageMeter() {
  const [count, setCount] = useState<number | null>(null);
  useEffect(() => {
    apiGet<unknown[]>("/api/v1/analyses")
      .then((rows) => setCount(Array.isArray(rows) ? rows.length : null))
      .catch(() => setCount(null));
  }, []);
  if (count === null) return null;
  return <span title="Analyses this month">{Math.min(count, 5)}/5 analyses</span>;
}
```

> ponytail: counts total analyses client-side, not this-month. Good enough for a nav hint; the server enforces the real monthly limit. Upgrade to a `/api/v1/me/usage` endpoint if the number needs to be exact.

Mount it in `frontend/src/components/Navbar.tsx` where the authed user's info renders.

- [ ] **Step 6: Verify frontend build + tests**

Run: `cd frontend && npm test && npm run build`
Expected: tests PASS, build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/UpgradeModal.tsx frontend/src/components/UpgradeModal.module.css \
        frontend/src/components/UsageMeter.tsx frontend/src/components/Navbar.tsx \
        frontend/src/app/analyze/page.tsx frontend/src/app/project/new/page.tsx
git commit -m "feat(frontend): upgrade modal + usage meter + quota-aware error handling"
```

---

## Task 15: Frontend — R2 image host + production API URL

**Files:**
- Modify: `frontend/next.config.ts`

**Interfaces:**
- Produces: images from the R2 public host render via `next/image`; API calls in production target `NEXT_PUBLIC_API_URL`.

- [ ] **Step 1: Add the R2 host to `images.remotePatterns`**

In `frontend/next.config.ts`, add an entry (replace `pub-xxxx.r2.dev` with the real R2 public hostname from Task 8's bucket):

```ts
      {
        protocol: "https",
        hostname: "pub-xxxx.r2.dev",
      },
```

- [ ] **Step 2: Make the API rewrite environment-driven**

Replace the hardcoded `destination` so production points at the Render backend:

```ts
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/v1/:path*", destination: `${api}/api/v1/:path*` }];
  },
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/next.config.ts
git commit -m "chore(frontend): R2 image host + env-driven API rewrite"
```

---

## Task 16: Deploy configuration + docs

**Files:**
- Create: `backend/render.yaml`, `backend/Dockerfile`, `docs/deploy.md`
- Create/update: `backend/.env.example`, `frontend/.env.local.example`

**Interfaces:**
- Produces: reproducible deploy steps and a complete env var reference. No secrets committed.

- [ ] **Step 1: Backend Dockerfile**

`backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
```

- [ ] **Step 2: Render service definition**

`backend/render.yaml`:

```yaml
services:
  - type: web
    name: director-ai-api
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    plan: free
    healthCheckPath: /health
    envVars:
      - key: APP_ENV
        value: production
      - key: APP_DEBUG
        value: "false"
      - key: DATABASE_URL
        sync: false
      - key: NVIDIA_NIM_API_KEY
        sync: false
      - key: GEMINI_ENABLED
        value: "true"
      - key: GEMINI_API_KEY
        sync: false
      - key: FIREBASE_SERVICE_ACCOUNT_JSON
        sync: false
      - key: R2_ACCOUNT_ID
        sync: false
      - key: R2_ACCESS_KEY_ID
        sync: false
      - key: R2_SECRET_ACCESS_KEY
        sync: false
      - key: R2_BUCKET
        sync: false
      - key: R2_PUBLIC_BASE_URL
        sync: false
      - key: CORS_ORIGINS
        sync: false
```

- [ ] **Step 3: Update `.env.example` files**

Update `backend/.env.example` to list every variable (no values): `DATABASE_URL`, `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_DEFAULT_MODEL`, `GEMINI_ENABLED`, `GEMINI_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_CREDENTIALS_PATH`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_BASE_URL`, `CORS_ORIGINS`, `APP_ENV`, `APP_DEBUG`.
Create `frontend/.env.local.example` with the `NEXT_PUBLIC_FIREBASE_*` keys and `NEXT_PUBLIC_API_URL`.

- [ ] **Step 4: Write `docs/deploy.md`**

Document, in order: (1) create Neon project → copy `DATABASE_URL` (append `+asyncpg`); (2) create R2 bucket + API token + enable public access → copy the 5 R2 vars; (3) deploy backend on Render from `render.yaml`, paste secret env vars, confirm `/health`; (4) deploy frontend on Vercel, set `NEXT_PUBLIC_*` + `NEXT_PUBLIC_API_URL`=Render URL; (5) Firebase console → Authentication → add the Vercel domain to Authorized domains; (6) set backend `CORS_ORIGINS` to the Vercel domain; (7) run the live smoke test below.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/render.yaml backend/.env.example frontend/.env.local.example docs/deploy.md
git commit -m "chore(deploy): Render + Vercel config and deploy runbook"
```

---

## Task 17: Full-suite verification + live smoke test

**Files:** none (verification only)

- [ ] **Step 1: Backend suite**

Run: `cd backend && PYTHONPATH=. pytest -q`
Expected: all tests PASS (including new quota, waitlist, storage, ownership, config tests).

- [ ] **Step 2: Frontend suite + build**

Run: `cd frontend && npm test && npm run build`
Expected: PASS + successful build.

- [ ] **Step 3: Live smoke test (after deploy)**

On the live Vercel URL, manually verify the full loop: sign up → create a project → upload a still and get an analysis → add a scene + shot → export the PDF. Then create until you hit the 3rd project / 6th analysis and confirm the upgrade modal appears and the waitlist email is captured (check the `waitlist` table in Neon).

- [ ] **Step 4: Update progress docs**

Mark Phase 1 items complete in `docs/progress.md` and set "Current phase" to "Phase 2 — ready to start". Commit:

```bash
git add docs/progress.md
git commit -m "docs: Phase 1 complete — live, secured, gated, waitlisted"
```

---

## Self-Review Notes

- **Spec coverage**: every Phase 1 checklist item in `docs/phases/phase-1-launch.md` maps to a task — security P0 (T1–T3), R2 storage (T8–T9), Neon+Alembic (T4), new columns/tables (T5–T7), quotas (T10–T11), waitlist (T12), frontend upgrade funnel (T13–T15), deploy (T16), verification (T17).
- **Redis drop**: satisfied implicitly — quota uses `quota_service` (Postgres); `rate_limiter.py` is left for the two public endpoints' abuse protection but is no longer on the quota path. No new Redis dependency is introduced.
- **Type consistency**: `enforce_analysis_quota` / `enforce_project_quota`, `QuotaError.quota`, `build_object_key`, `StorageService.upload_bytes`, `WaitlistCreate`/`WaitlistResponse` names are used identically across producing and consuming tasks.
- **Known simplification**: `UsageMeter` counts all-time analyses client-side, flagged with a `ponytail:` note and an upgrade path; the authoritative monthly limit is server-enforced in T10.
