# portfolio-be/Dockerfile
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.1.3

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

# --- Development Stage ---
FROM base AS development
RUN poetry install --no-root
COPY . .
RUN mkdir -p /app/media/avatars /app/staticfiles
RUN addgroup --system appuser && adduser --system --group appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Production Stage ---
FROM base AS production
RUN poetry install --no-root --only main

RUN addgroup --system appuser && adduser --system --group appuser
COPY --chown=appuser:appuser . .

RUN mkdir -p /app/media/avatars /app/staticfiles && \
    chmod -R 755 /app/media /app/staticfiles && \
    chown -R appuser:appuser /app/media /app/staticfiles

USER appuser
EXPOSE 8000

# ✅ App container should only run the web server
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4"]
