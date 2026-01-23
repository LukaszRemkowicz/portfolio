# portfolio-be/Dockerfile
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.3

WORKDIR /app

# Install system dependencies and Poetry in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# --- Development Stage ---
FROM base AS development

# Install all dependencies (including dev)
RUN poetry install --no-root

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/media/avatars /app/staticfiles

# Create and switch to non-root user
RUN addgroup --system appuser && adduser --system --group appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Dev command (Runserver)
# Using 'sh -c' to allow multiple commands while still maintaining shell signal handling if needed,
# though runserver handles SIGINT fine.
CMD ["sh", "-c", "python manage.py migrate && python manage.py compilemessages && python manage.py runserver 0.0.0.0:8000"]

# --- Production Stage ---
FROM base AS production

# Install only production dependencies
RUN poetry install --no-root --only main

# Create non-root user first to allow --chown
RUN addgroup --system appuser && adduser --system --group appuser

# Copy project files with correct ownership to avoid large chown layers
COPY --chown=appuser:appuser . .

# Create media and static directories with correct ownership
RUN mkdir -p /app/media/avatars /app/staticfiles && \
    chmod -R 755 /app/media /app/staticfiles && \
    chown -R appuser:appuser /app/media /app/staticfiles

USER appuser

EXPOSE 8000

# Prod command (Gunicorn)
# Use exec form to ensure Gunicorn receives signals directly (SIGTERM)
CMD ["sh", "-c", "python manage.py migrate && python manage.py compilemessages && python manage.py collectstatic --noinput && exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 4"]
