# portfolio-be/Dockerfile
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HTTP_TIMEOUT=120

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# --- Development Stage ---
FROM base AS development

# Install all dependencies (including dev)
RUN poetry install --no-root --no-interaction

# Copy project files
COPY . .

# Create media directory and set permissions
RUN mkdir -p /app/media/avatars && \
    chmod -R 755 /app/media

# Create and switch to non-root user
RUN addgroup --system appuser && adduser --system --group appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Dev command (Runserver)
CMD python manage.py migrate && python manage.py compilemessages && python manage.py runserver 0.0.0.0:8000

# --- Production Stage ---
FROM base AS production

# Install only production dependencies
RUN poetry install --no-root --no-interaction --only main

# Copy project files
COPY . .

# Create media directory and set permissions
RUN mkdir -p /app/media/avatars && \
    chmod -R 755 /app/media

# Create and switch to non-root user
RUN addgroup --system appuser && adduser --system --group appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Prod command (Gunicorn)
CMD python manage.py migrate && python manage.py compilemessages && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 4
