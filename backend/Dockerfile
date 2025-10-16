# portfolio-be/Dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install system dependencies for building Python packages and PostgreSQL support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction

# Create media directory with proper permissions
RUN mkdir -p /app/media/avatars && \
    chown -R www-data:www-data /app/media && \
    chmod -R 755 /app/media

# Copy project files
COPY . .

# Ensure media directory permissions are maintained after copy
RUN chown -R www-data:www-data /app/media && \
    chmod -R 755 /app/media

EXPOSE 8000

# Run migrations and start server
CMD poetry run python manage.py migrate && poetry run python manage.py runserver 0.0.0.0:8000
