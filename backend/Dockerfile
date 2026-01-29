# portfolio-be/Dockerfile
FROM python:3.13-slim AS base

# Install shared runtime dependencies
# libpq5 is always needed for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.1.3 \
    VIRTUAL_ENV=/venv \
    POETRY_VIRTUALENVS_CREATE=false

# Add virtualenv to PATH
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# --- Builder Stage ---
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into virtualenv
COPY pyproject.toml poetry.lock ./
RUN python -m venv $VIRTUAL_ENV && \
    poetry install --no-root --only main

# Pre-compile translations at build time for production
COPY . .

# --- Development Stage ---
FROM base AS development

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && rm -rf /var/lib/apt/lists/*

# Reuse builder venv to avoid re-installing main deps
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Install ALL dependencies (including dev)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .
RUN mkdir -p /app/media /app/staticfiles

RUN addgroup --system appuser && adduser --system --group appuser && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Production Stage ---
FROM base AS production

# Note: gettext NOT needed here because messages were compiled in builder
RUN addgroup --system appuser && adduser --system --group appuser && \
    mkdir -p /app/media /app/staticfiles && \
    chown -R appuser:appuser /app

# Copy virtualenv and app (already compiled) with correct ownership
COPY --from=builder --chown=appuser:appuser $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser
EXPOSE 8000

# Provide environment variables with defaults for Gunicorn
ENV WEB_CONCURRENCY=2 \
    GUNICORN_THREADS=1

# Use sh -c to expand environment variables for workers and threads
CMD ["sh", "-c", "gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY} --threads ${GUNICORN_THREADS} --log-level info"]
