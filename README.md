# Portfolio Landing Page

A modern, API-driven personal portfolio web app with subpages for Astrophotography, Programming, and Contact. Built with React (frontend) and Django + Django Rest Framework (backend), fully dockerized and orchestrated with nginx for local HTTPS development.

## Quick Start

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd landingpage
```

### 2. Start all services with Docker Compose
```sh
# For newer Docker versions (Docker Compose V2)
docker compose up --build

# For older Docker versions (Docker Compose V1)
docker-compose up --build
```

> **Note**: Docker Compose V2 uses `docker compose` (space), while V1 uses `docker-compose` (hyphen). Check your Docker version with `docker --version`.
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

## Development

### Frontend Development
```bash
cd frontend
npm install
npm start          # Development server
npm test           # Run test suite
npm run build      # Production build
```

### Backend Development
```bash
cd backend
poetry install
poetry shell
python manage.py runserver
```

### Docker Development
```bash
# For newer Docker versions (Docker Compose V2)
docker compose up --build    # Start all services

# For older Docker versions (Docker Compose V1)
docker-compose up --build    # Start all services
docker-compose exec portfolio-fe npm test    # Run frontend tests
```


## 🚀 Production Deployment

### 1. Build and Run
Use the `docker-compose.prod.yml` override to enable production mode (optimized assets, no hot-reloading, security hardening).

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 2. Deployment Checklist
- [ ] **SSL Certificates**: Replace the local dev certificates in `./nginx/ssl/certs` with valid ones (e.g., Let's Encrypt).
- [ ] **Environment Variables**: Update `backend/.env`:
    - `DEBUG=False`
    - `SECRET_KEY=<strong-random-string>`
    - `DJANGO_ALLOWED_HOSTS=<your-domain.com>`
- [ ] **Data Backup**: Ensure the `postgres_data` volume is backed up.

## Testing

### Backend (Dedicated Service)
The backend tests now run in a dedicated, isolated environment using Docker Compose Profiles. This inherits your development configuration but remains isolated.

```bash
docker compose run --rm portfolio-test
```

### Frontend
```bash
docker compose exec portfolio-fe npm test    # Local development (fastest)
docker compose run --rm portfolio-fe npm test -- --watchAll=false  # Isolated
```

## TODO - Project Improvements

### 📋 Component-Specific TODOs
- **Frontend TODOs**: See [Frontend README](frontend/README.md#-todo--future-improvements)
- **Backend TODOs**: See [Backend README](backend/README.md)
