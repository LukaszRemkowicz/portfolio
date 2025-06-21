# Backend for Portfolio Page

This is the backend for the Portfolio Page project, built with Django and Django Rest Framework (DRF). It provides APIs and backend logic for the personal landing page, including subpages for Astrophotography, Programming, and Contact.

## Features
- Django 4.2+
- Django Rest Framework
- Custom User model with bio, avatar, website, and social links
- Image models for astrophotography and programming projects
- Environment variable management with django-environ
- Dockerized for easy local development
- PostgreSQL database (via Docker Compose)
- Modular apps: users, astrophotography, programming
- Integrated with nginx for static/media file serving and HTTPS

## Requirements
- Python 3.11+ (recommended: use [pyenv](https://github.com/pyenv/pyenv) to manage Python versions)
- Poetry (for dependency management)
- Docker & Docker Compose

## Setup Instructions

### 1. Install Python 3.11+
If you have multiple Python versions, use [pyenv](https://github.com/pyenv/pyenv):
```sh
pyenv install 3.11.8
pyenv local 3.11.8
```

### 2. Install Poetry
Follow the [official Poetry installation guide](https://python-poetry.org/docs/#installation):
```sh
curl -sSL https://install.python-poetry.org | python3 -
```
Make sure Poetry is in your PATH. You can check with:
```sh
poetry --version
```

### 3. Install dependencies
```sh
cd backend
poetry install
```

### 4. Configure environment variables
Create a `.env` file in the `backend/` directory. Example:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,db
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
- Never commit your `.env` file to version control.
- Use a strong, unique value for `SECRET_KEY` (you can generate one with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`).

### 5. Run migrations
```sh
poetry run python manage.py migrate
```

### 6. Run the development server
```sh
poetry run python manage.py runserver 0.0.0.0:8000
```

## Docker Usage

You can run the backend, frontend, nginx, and database using Docker Compose:

```sh
docker-compose up --build
```

- The backend will be available at `https://admin.portfolio.local/`
- The frontend will be available at `https://portfolio.local/`
- The database will be available at `localhost:5432`
- Media files are served via nginx at `/media/`

## API Endpoints

- `/api/v1/profile/` — Public user profile (bio, avatar, name, social links)
- `/api/v1/astrophotography/` — Astrophotography images (if enabled)
- `/api/v1/programming/` — Programming projects (if enabled)

## Project Structure

- `core/` - Django project settings and configuration
- `users/` - User management app
- `astrophotography/` - Astrophotography app
- `programming/` - Programming app

## Integration with Frontend
- The React frontend fetches profile and media data from the backend API.
- CORS and HTTPS are configured for local development with custom domains via nginx.

## License

MIT 