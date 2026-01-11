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

## Testing

### Using `exec` (Services must be running)
Recommended for development (fastest):
```bash
docker compose exec portfolio-fe npm test    # Frontend
docker compose exec portfolio-be pytest     # Backend
```

### Using `run` (One-off isolated container)
Recommended for CI or isolated runs:
```bash
docker compose run --rm portfolio-fe npm test -- --watchAll=false
docker compose run --rm portfolio-be pytest
```


## ✅ Recently Completed

### 🎯 Major Achievements (Latest Session)

- ✅ **Full TypeScript Migration** - 100% TypeScript coverage across entire frontend
- ✅ **CI/CD Pipeline Setup** - Complete GitHub Actions workflow with testing, security scanning, and Docker builds
- ✅ **Pre-commit Hooks** - Automated code formatting and quality checks (Black, isort, Flake8, Prettier)
- ✅ **Code Quality Tools** - ESLint, Prettier, Black configured with 100-character line length
- ✅ **Security Scanning** - CodeQL integration for vulnerability detection
- ✅ **Dependency Management** - Dependabot configured for automatic updates
- ✅ **Production Deployment** - Deploy scripts for production server deployment
- ✅ **Documentation Updates** - All README files updated with current project state

## TODO - Project Improvements

### 📋 Component-Specific TODOs
- **Frontend TODOs**: See [Frontend README](frontend/README.md#-todo--future-improvements)
- **Backend TODOs**: See [Backend README](backend/README.md)
