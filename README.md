# Director AI 🎬

Director AI is a powerful cinematography companion application that helps filmmakers plan, manage, and analyze scenes and shots. It leverages AI vision models to analyze reference images and provide insights on lighting, camera settings, composition, and mood.

## Features ✨

- **Project Management**: Create and manage filmmaking projects with genres and production statuses.
- **Scene & Shot Planning**: Define scenes (time of day, location, mood) and break them down into specific shots (camera angles, movements, lenses).
- **AI Cinematography Analysis**: Upload reference images or film stills and get AI-powered breakdowns of lighting setups, focal lengths, framing, color palettes, and setup instructions using local models via Ollama.
- **Analysis History & Attachments**: Save AI analyses directly to your scenes and review your history over time.
- **Beautiful UI**: Modern, glassmorphic, and highly responsive dark-themed user interface built with Vanilla CSS modules and Next.js.

## Tech Stack 🛠️

### Frontend
- **Framework**: Next.js (App Router, TypeScript)
- **Styling**: Vanilla CSS Modules (Glassmorphism, CSS Variables)
- **Authentication**: Firebase Auth (Google Sign-In / Email)

### Backend
- **Framework**: FastAPI (Python, async)
- **Database**: PostgreSQL (with asyncpg & SQLAlchemy)
- **AI Integration**: Ollama (Running local models like `gemma3:4b` for vision tasks)
- **Storage**: Local file system (or configurable cloud storage)
- **Caching**: Redis

## Prerequisites 📋

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.10+)
- [Docker](https://www.docker.com/) & Docker Compose
- [Ollama](https://ollama.ai/) installed locally (with `gemma3:4b` or your preferred vision model pulled)

## Getting Started 🚀

### 1. Backend Setup

Navigate to the `backend` directory and set up your Python environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Start the Postgres and Redis services using Docker Compose from the project root:
```bash
cd ..
docker-compose up -d
```

Copy the example environment file and configure it:
```bash
cd backend
cp .env.example .env
```
Ensure your `OLLAMA_DEFAULT_MODEL` is set correctly in `.env` (e.g., `gemma3:4b`) and your Firebase admin SDK JSON file is placed at the correct path.

Run the FastAPI development server:
```bash
uvicorn main:app --reload
```

### 2. Frontend Setup

Navigate to the `frontend` directory:

```bash
cd frontend
npm install
```

Create a `.env.local` file and add your Firebase client configuration:
```env
NEXT_PUBLIC_FIREBASE_API_KEY="your-api-key"
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="your-auth-domain"
NEXT_PUBLIC_FIREBASE_PROJECT_ID="your-project-id"
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="your-storage-bucket"
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="your-sender-id"
NEXT_PUBLIC_FIREBASE_APP_ID="your-app-id"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

Start the Next.js development server:
```bash
npm run dev
```

Visit `http://localhost:3000` to start directing!
