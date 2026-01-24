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
- API: https://api.portfolio.local/
- Backend Admin: https://admin.portfolio.local/
- Media files: https://api.portfolio.local/media/

> **Note:** You may need to add `portfolio.local`, `api.portfolio.local`, and `admin.portfolio.local` to your `/etc/hosts` file:
> ```
> 127.0.0.1 portfolio.local api.portfolio.local admin.portfolio.local
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

The project uses a standalone production configuration to ensure zero-downtime deployments and environment isolation.

### 1. Environment Secrets (Doppler)
On production, move all variables from `backend/.env` to a **Doppler** project.
- Use the Doppler CLI to inject variables: `doppler run -- ./scripts/release/deploy.sh`
- Ensure critical variables like `SECRET_KEY`, `DB_PASSWORD`, and `ALLOWED_HOSTS` are properly set in the Doppler production config.

### 2. Building Images
Use the centralized build script to create production-ready Docker images.
```bash
# Build images with a specific tag (e.g., git commit hash or 'latest')
TAG=v1.0.0 ./scripts/release/build.sh
```
This script builds both `portfolio-frontend` and `portfolio-backend` using production targets.

### 3. Deploying
The `deploy.sh` script handles the orchestration of the production stack.
```bash
# Deploy using images with a specific tag
TAG=v1.0.0 ./scripts/release/deploy.sh
```
**What this script does:**
- Verifies that the required images exist.
- Runs database migrations and collects static files via a temporary `release` container.
- Performs a "hot swap" of the running containers with zero-downtime.

### 4. Nginx Production Config
Before your first deployment, you **must** configure [nginx/prod/nginx.conf](nginx/prod/nginx.conf):
- **Server Names**: Update `server_name` to your real domains (e.g., `example.com`).
- **SSL Certificates**: Point `ssl_certificate` paths to your actual Certbot/LetsEncrypt certificates (usually mounted to `/etc/nginx/ssl/`).
- **CORS/CSRF**: Ensure the domains in Nginx match your `CORS_ALLOWED_ORIGINS` in Doppler/Env.

---

## 💾 Database Backup & Maintenance

Database maintenance scripts are located in `scripts/db_backup/`.

### 1. Manual Backup
Create a compressed SQL dump of the production database:
```bash
./scripts/db_backup/backup_db.sh
```
The backup will be stored in `scripts/db_backup/backups/`.

### 2. Testing Restores
Always verify your backups by running a test restore:
```bash
./scripts/db_backup/test_restore.sh
```
This script creates a temporary container and verifies that the SQL dump is valid and can be fully imported.

See [Backup Maintenance Guide](file:///Users/lukaszremkowicz/Projects/landingpage/scripts/db_backup/MAINTENANCE.md) for more details.

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

---

## 🔄 Release Lifecycle

To ensure version traceability and zero-downtime, follow this mandatory flow for all new features and fixes:

### 1. Development to Dev
- **Merge Request**: Create an MR from your feature branch to `dev`.
- **Squash & Delete**: Perform a **Squash and Merge** and delete the feature branch to keep history clean.

### 2. Versioning (Tags)
- **Tag the Commit**: Once code is on `dev`, tag it with a version (e.g., `v1.2.0`).
- **Push Tag**: `git push origin v1.2.0`
- **Automatic Detection**: The `build.sh` and `deploy.sh` scripts automatically detect this tag and use it as the Docker image reference.

### 3. Promotion to Main
- **Merge Request**: Merge `dev` into `main`.
- **Production Anchor**: This ensures `main` always stable and aligned with a specific Git tag.

### 4. Direct Deployment
On your production server, simply run:
```bash
# TAG is auto-detected from the Git tag on main
./scripts/release/deploy.sh
```

> [!IMPORTANT]
> **Production Requirement**: Deployments **must** use a Git tag as the reference. This allows for instant rollbacks by just changing the `TAG` variable.

---

## 📋 Component-Specific TODOs
- **Frontend TODOs**: See [Frontend README](frontend/README.md#-todo--future-improvements)
- **Backend TODOs**: See [Backend README](backend/README.md)
