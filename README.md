# Portfolio Landing Page

A modern, API-driven personal portfolio web app with subpages for Astrophotography, Programming, and Contact. Built with React (frontend) and Django + Django Rest Framework (backend), fully dockerized and orchestrated with nginx for local HTTPS development.

## 🌐 LIVE

Check out the live version: **[lukaszremkowicz.com](https://lukaszremkowicz.com)**

## 📸 Screenshots

<details>
<summary><b>Click to expand screenshots</b></summary>

### Home Page
![Home Page](screenshots/homepage.jpg)

### Astrophotography Gallery
![Gallery](screenshots/gallery.jpg)

### Contact Form
![Contact](screenshots/contact.jpg)

</details>

## Quick Start

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd landingpage
```

### 2. Configure Environment (Doppler)

We use **Doppler** for secure secret management. Before starting, ensure you have the Doppler CLI installed and are logged in.

```bash
# Login to Doppler
doppler login

# Setup the project for the current directory
doppler setup
```

### 3. Start all services with Docker Compose

Always use `doppler run` to inject secrets into your Docker containers. Use the `--config` flag to specify the environment.

```bash
# For local development (default dev config)
doppler --config dev run -- docker compose up --build

# For staging
doppler --config staging run -- docker compose up --build
```

- Frontend: https://portfolio.local/
- API: https://api.portfolio.local/
- Backend Admin: https://admin.portfolio.local/

> **Note:** You may need to add these domains to your `/etc/hosts` file:
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
The project uses **Doppler** for secure secret management across all environments.
- **Local Dev**: Use `doppler setup --config dev`. Then run: `doppler run -- docker compose up`.
- **Production**: Doppler injects variables automatically. Always specify the config: `doppler --config prod run -- ./scripts/release/deploy.sh`
- Critical variables like `SECRET_KEY`, `DB_PASSWORD`, and `ALLOWED_HOSTS` are managed centrally in Doppler.

### 2. Building Images
Use the centralized build script to create production-ready Docker images.
```bash
# Build images with a specific tag (e.g., git commit hash or 'latest'). TAG is optional.
TAG=v1.0.0 doppler run -- ./scripts/release/build.sh
```
This script builds `portfolio-frontend`, `portfolio-backend`, and `portfolio-nginx` using production targets.

### 3. Deploying
The `deploy.sh` script handles the orchestration of the production stack.
```bash
# Deploy using images with a specific tag. TAG is optional.
TAG=v1.0.0 doppler run -- ./scripts/release/deploy.sh
```
**What this script does:**
- Verifies that the required images exist.
- Runs database migrations and collects static files via a temporary `release` container.
- Performs a "hot swap" of the running containers with zero-downtime.

### 4. Nginx Production Config
All config is placed in nginx/prod/TEMPLATE.conf. Environment variables are injected to configuration in build stage.

### 5. Nginx Environment Variables
Nginx configuration is handled automatically. Variables are injected by Doppler and substituted into the template at runtime.
The `docker-compose.prod.yml` uses these variables for path mapping:
- `NGINX_CONF_PATH`: Path to the production template.
- `NGINX_SSL_DIR`: Directory containing your SSL certificates.
- `NGINX_LOG_DIR`: Directory for Nginx logs.

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
