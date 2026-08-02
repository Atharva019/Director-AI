# 🎬 Director AI

Director AI is a production-ready, cloud-native cinematography companion and shot-planning application. It acts as an AI-powered Director of Photography—helping filmmakers plan projects, organize scenes, build shot lists, and automatically reverse-engineer lighting setups, camera specs, and color palettes from reference stills using high-performance Vision AI models.

---

## ✨ Key Features

- **Multi-Provider Vision AI Pipeline**: Reverse-engineers film reference images into precise lighting setups, focal lengths, camera angles, color swatches, and set instructions using **NVIDIA NIM** (`meta/llama-3.2-90b-vision-instruct`) with automatic fallback to **Google Gemini Vision** (`gemini-2.0-flash`).
- **Interactive Visual Overlays**:
  - **Composition Grids**: Toggle a Rule-of-Thirds composition overlay on reference stills.
  - **Color Palette Extraction**: Automatically extract dominant HEX color swatches for color grading.
  - **3-Point Lighting Diagrams**: Dynamically rendered overhead lighting diagrams (Key, Fill, and Back light placement, intensity, and color temperature).
- **Project & Shot Planning**: Define scenes (interior/exterior, time-of-day, mood) and break them down into granular shot lists (camera motion, lens choice, subject framing).
- **Scene Analysis Association**: Analyze reference stills standalone or directly link analysis records to specific project scenes.
- **Call Sheet PDF Exports**: Generate formatted, print-ready production call sheets and shot list PDFs in a single click (powered by client-side jsPDF).
- **Cloud Object Storage**: Provider-agnostic S3 object storage integration (Cloudflare R2, AWS S3) for zero-data-loss image serving across ephemeral deployments.
- **Tiered Quota & Usage Enforcement**: Database-backed usage metering (Free tier: 5 analyses/month, 2 projects) with interactive upgrade modals and IP-based sliding-window rate limiting.
- **Pro Waitlist Funnel**: Built-in waitlist tracking for premium tier conversion.
- **Enterprise Security**: Firebase Auth integration (Google Sign-In, Email/Password), IDOR ownership validation, strict startup environment guards, and CORS/proxy security.
- **Automated Testing**: CI/CD-ready test suites using **Pytest** for backend API/security tests and **Vitest** for frontend component/API tests.

---

## 🏗️ Architecture Overview

Director AI is architected as a decoupled, serverless-friendly SaaS application deployed on zero-cost cloud tiers.

```
┌─────────────────┐       HTTPS       ┌───────────────────────┐
│     Vercel      │ ────────────────> │     Render (free)     │
│ Next.js 15 App  │   /api/v1 proxy   │    FastAPI Backend    │
└─────────────────┘                   └───┬───────┬───────┬───┘
                                          │       │       │
                      ┌───────────────────┘       │       └───────────────────┐
                      ▼                           ▼                           ▼
            ┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
            │   Neon Postgres   │       │   Cloudflare R2   │       │   AI Providers    │
            │ (SQLAlchemy+Async)│       │   (boto3 S3 API)  │       │ NVIDIA NIM → Gemini│
            └───────────────────┘       └───────────────────┘       └───────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router, React 19, TypeScript)
- **Styling**: Vanilla CSS Modules (Glassmorphism design system, CSS custom properties)
- **Authentication**: Firebase Auth (Google OAuth & Email/Password)
- **PDF Generation**: jsPDF & jsPDF-AutoTable
- **Testing**: Vitest, React Testing Library, JSDOM

### Backend
- **Framework**: FastAPI (Python 3.10+, fully async)
- **Database**: PostgreSQL (Neon serverless / local Docker) via `SQLAlchemy 2` & `asyncpg`
- **Database Migrations**: Alembic (version-controlled schema migrations)
- **AI Vision Pipeline**: NVIDIA NIM Vision API (Primary) with Google Gemini Vision API fallback
- **Storage**: S3-compatible Object Storage (`boto3` / Cloudflare R2) with local fallback in dev
- **Auth & Security**: Firebase Admin SDK token verification middleware & IDOR checks
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, aioSQLite

---

## 📋 Prerequisites

Before running the project locally, ensure you have:
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (v3.10+)
- [Docker](https://www.docker.com/) & Docker Compose (for local PostgreSQL)
- API Keys:
  - NVIDIA NIM API Key or Google Gemini API Key (for Vision AI analysis)
  - Firebase Project Credentials (for Authentication)

---

## 🚀 Getting Started

### 1. Start Infrastructure (Local Dev)
Launch the PostgreSQL database container from the project root:
```bash
docker-compose up -d
```

### 2. Backend Setup
Navigate to the `backend` folder, create a virtual environment, install dependencies, and configure environment variables:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Ensure your `.env` is configured with database credentials, AI provider keys (`NVIDIA_NIM_API_KEY` or `GEMINI_API_KEY`), and Firebase service account path.

Apply database migrations:
```bash
alembic upgrade head
```

Run the FastAPI development server:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
Navigate to the `frontend` folder, install dependencies, and set up environment variables:
```bash
cd frontend
npm install

# Configure environment variables
cp .env.local.example .env.local
```

Fill out `.env.local` with your Firebase web configuration (`NEXT_PUBLIC_FIREBASE_API_KEY`, etc.).

Start the Next.js development server:
```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🧪 Running Tests

### Backend Test Suite
Runs unit, integration, and security ownership tests using Pytest:
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest
```

### Frontend Test Suite
Runs unit and component integration tests using Vitest:
```bash
cd frontend
npm test
```

---

## 🚀 Deployment & Operations

For detailed production deployment instructions, environment variables, startup security guards, and the 10-step verification runbook, refer to:
- [`docs/architecture.md`](docs/architecture.md) — Production architecture design & quota model.
- [`docs/deploy.md`](docs/deploy.md) — Render & Vercel deployment runbook.
- [`docs/security.md`](docs/security.md) — Security policies & credential management.

