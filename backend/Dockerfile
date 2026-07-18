FROM python:3.11-slim

WORKDIR /app

# Install deps first so code changes don't invalidate the dependency layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000 \
    PYTHONUNBUFFERED=1

# Migrations run at boot — Render's free tier gives us no release phase, and
# `alembic upgrade head` is a no-op when the schema is already current.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
