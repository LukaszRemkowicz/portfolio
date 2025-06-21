# Portfolio Landing Page

A modern, API-driven personal portfolio web app with subpages for Astrophotography, Programming, and Contact. Built with React (frontend) and Django + Django Rest Framework (backend), fully dockerized and orchestrated with nginx for local HTTPS development.

## Features
- One-page React frontend with subpages (Astrophotography, Programming, Contact)
- Dynamic profile, bio, and media content loaded from backend API
- Custom user model and image models in Django
- Modular, maintainable codebase
- Docker Compose for full-stack local development
- nginx for HTTPS, static/media file serving, and domain routing

## Quick Start

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd landingpage
```

### 2. Start all services with Docker Compose
```sh
docker-compose up --build
```
- Frontend: https://portfolio.local/
- Backend: https://admin.portfolio.local/
- Media files: https://portfolio.local/media/

> **Note:** You may need to add `portfolio.local` and `admin.portfolio.local` to your `/etc/hosts` file:
> ```
> 127.0.0.1 portfolio.local admin.portfolio.local
> ```

### 3. Access Django Admin
- Go to https://admin.portfolio.local/admin/
- Log in with your superuser credentials (create one if needed)
- Update your profile, bio, and avatar in the Users section

## Project Structure
- `frontend/` — React app (see [frontend/README.md](frontend/README.md))
- `backend/` — Django + DRF API (see [backend/README.md](backend/README.md))
- `nginx/` — nginx config, SSL, and logs
- `docker-compose.yml` — Orchestration for all services

## API Endpoints
- `/api/v1/profile/` — Public user profile (bio, avatar, name, social links)
- `/media/` — Media files (avatars, images)

## More Info
- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)

## License
MIT 