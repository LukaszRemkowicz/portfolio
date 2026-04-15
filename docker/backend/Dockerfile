# syntax=docker/dockerfile:1.7

# portfolio-be/Dockerfile
FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

# Install shared runtime dependencies
# libpq5 is always needed for psycopg2
# gosu is needed to drop privileges from root to appuser after permission fixes
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    gosu \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appuser && adduser --system --group appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    VIRTUAL_ENV=/venv \
    UV_PROJECT_ENVIRONMENT=/venv \
    UV_LINK_MODE=copy \
    TZ=Europe/Warsaw

# Add virtualenv to PATH
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- Builder Stage ---
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into virtualenv
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Pre-compile translations at build time for production
COPY backend/ .

# --- Development Stage ---
FROM base AS development

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Reuse builder venv to avoid re-installing main deps
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Install ALL dependencies (including dev)
COPY backend/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN mkdir -p /app/media /app/staticfiles

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Production Stage ---
FROM base AS production

# Note: gettext NOT needed here because messages were compiled in builder
RUN mkdir -p /app/media /app/staticfiles && \
    chown -R appuser:appuser /app

# Copy virtualenv and app (already compiled) with correct ownership
COPY --from=builder --chown=appuser:appuser $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder --chown=appuser:appuser /app /app

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 8000

ENV WEB_CONCURRENCY=2 \
    GUNICORN_THREADS=1

# Note: We do NOT use 'USER appuser' here because the entrypoint.sh
# needs root privileges to fix permissions on mounted volumes.
# entrypoint.sh will drop privileges to appuser using 'gosu' at the end.

# Use sh -c to expand environment variables for workers and threads
CMD ["sh", "-c", "gunicorn settings.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY} --threads ${GUNICORN_THREADS} --keep-alive 60 --log-level info"]
