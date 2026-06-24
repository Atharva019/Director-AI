# 🎬 Director AI

Director AI is a powerful, local-first cinematography companion application. It acts as your AI-powered Director of Photography—helping filmmakers plan projects, organize scenes, build shot lists, and automatically reverse-engineer lighting and camera settings from reference images using local Vision AI models.

## ✨ Key Features

- **Project Management**: Create and organize filmmaking projects with dynamic statuses, genres, and rich descriptions. Search and filter projects straight from your dashboard.
- **Scene & Shot Planning**: Define scenes (interior/exterior, time of day, mood) and break them down into highly specific shots (camera angles, movements, and focal lengths).
- **AI Cinematography Analysis**: Upload any reference film still, and local AI (powered by Ollama and `gemma3:4b` or `llava`) will break down the exact lighting setup, focal length, framing, color palettes, and practical set instructions.
- **Visual Enhancements**:
  - **Composition Overlays**: Toggle a Rule-of-Thirds grid over your analyzed images.
  - **Color Palettes**: Automatically extract and display the dominant color swatches for color-grading references.
  - **Lighting Diagrams**: Dynamically generated 3-point overhead lighting diagrams (Key, Fill, Back light) based on the AI's analysis of the scene.
- **Call Sheet Exports**: Export your entire project's shot list into a beautifully formatted, print-ready PDF with a single click.
- **Beautiful UI**: A highly responsive, premium dark-themed interface built using glassmorphism, vanilla CSS modules, and Next.js.
- **Fully Tested**: Automated CI/CD-ready test suites using **Pytest** for the backend and **Vitest** for the frontend.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js (App Router, TypeScript)
- **Styling**: Vanilla CSS Modules (Glassmorphism, CSS Custom Properties)
- **Authentication**: Firebase Auth (Google Sign-In, Email/Password)
- **Testing**: Vitest, React Testing Library
- **PDF Generation**: jsPDF, jsPDF-AutoTable

### Backend
- **Framework**: FastAPI (Python, fully async)
- **Database**: PostgreSQL (via `asyncpg` & SQLAlchemy)
- **AI Integration**: Ollama (Running local vision models)
- **Storage**: Local static file serving
- **Caching**: Redis
- **Testing**: Pytest, Pytest-Asyncio, HTTPX, aioSQLite

---

## 📋 Prerequisites

Before you start, make sure you have the following installed:
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.10+)
- [Docker](https://www.docker.com/) & Docker Compose
- [Ollama](https://ollama.ai/) running locally (with a vision model pulled, e.g., `ollama run llava` or `gemma3:4b`)

---

## 🚀 Getting Started

### 1. Database & Infrastructure
Start the PostgreSQL and Redis services from the project root using Docker:
```bash
docker-compose up -d
```

### 2. Backend Setup
Navigate to the `backend` directory, set up your Python environment, and start the API:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```
Ensure your `OLLAMA_DEFAULT_MODEL` is set in `.env` and your `firebase-service-account.json` is correctly linked.

Start the FastAPI development server:
```bash
uvicorn main:app --reload
```

### 3. Frontend Setup
Navigate to the `frontend` directory, install dependencies, and start the UI:
```bash
cd frontend
npm install

# Configure Firebase environment variables
cp .env.local.example .env.local
```
*(Ensure you fill out `.env.local` with your Firebase project credentials.)*

Start the Next.js development server:
```bash
npm run dev
```

Visit `http://localhost:3000` and start directing!

---

## 🧪 Running Tests

Director AI is built to be production-ready and includes full testing suites for both the backend API and frontend components.

**Run Backend Tests:**
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest
```

**Run Frontend Tests:**
```bash
cd frontend
npm test
```
