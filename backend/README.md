# Portfolio Backend

Django REST API backend for a personal portfolio showcasing astrophotography and programming projects. Built with Django 6.0+ and Django REST Framework, featuring custom user models, image management, and comprehensive API endpoints.

## 🚀 Features

### Core Functionality
- **Custom User Model** - Singleton admin user with bio, avatar, social links, and specific about me images.
- **Image Management** - `BaseImage` abstract model with automatic **thumbnail generation** and consistent scaling.
- **Persona Profiles** - Support for niche-specific content (Programming vs. Astrophotography) for the same user.
- **Astrophotography Gallery** - Complete image gallery with metadata, tags, and category filtering.
- **Contact System** - Secure contact form with bot protection (honeypot), duplicate detection, and email notifications.
- **Background Management** - Dynamic main page background images.

## 🛡️ Security Architecture

We implement a **Defense in Depth** strategy using several specialized tools and libraries:

### 1. Brute Force Protection (**Django Axes**)
We use [Django Axes](https://github.com/jazzband/django-axes) to protect the admin portal and API from brute-force attacks.
- Locked-out users are tracked by IP and username.
- Configurable cool-off periods and failure limits.

### 2. API Abuse Prevention (**DRF Throttling**)
Granular rate limiting is enforced across all endpoints:
- **Anonymous Throttling**: Limits unauthenticated users.
- **Contact Form Throttling**: Specialized 5-per-hour limit to prevent spam.
- **Method Restriction**: Critical ViewSets (like Contact/Users) explicitly restrict HTTP verbs to the bare minimum (e.g., POST-only or GET-only).

### 3. Dependency Scanning (**Safety**)
We use [Safety](https://github.com/pyupio/safety) to scan our dependencies for known vulnerabilities.
- Integrated into the CI/CD pipeline and available via `poetry run security`.

### 4. Infrastructure Security
- **Non-Root Execution**: Docker containers run under a restricted `appuser`.
- **Environment Isolation**: Secure configuration via `django-environ`.
- **Docker-Locked Environment**: Verified multi-stage builds and restricted `.dockerignore`.

### Technical & Security Features
- **Modern Stack** - Python 3.13, Django 6.0, and Poetry for dependency management.
- **Caching** - **Redis-backed** caching for Django Select2 and internal performance.
- **Security Hardening** - HSTS, secure cookies, and non-root execution in Docker.
- **Defense in Depth** - Advanced API rate limiting (**Django Axes** + DRF Throttling), payload size limits, and restricted HTTP verbs.
- **Internationalization (i18n)** - Multi-language support (EN/PL) with automatic message compilation.
- **Docker Integration** - Optimized multi-stage builds with automated static collection.

## 🛠️ Development Setup

### Prerequisites
- **Python 3.13**
- **Poetry**
- **Docker & Docker Compose**

### Local Quick Start

1. **Install Dependencies**
   ```bash
   poetry install
   ```

2. **Environment Configuration (Recommended: Doppler)**
   We use **Doppler** for secure secret management.
   ```bash
   doppler login
   doppler setup
   # No manual .env files needed!
   ```
   *Note: For legacy setups, you can still copy `DEFAULT.env` to `.env`.*

3. **Database & Translations**
   ```bash
   # Using Doppler to inject secrets
   doppler run -- poetry run python manage.py migrate
   doppler run -- poetry run python manage.py compilemessages
   ```

4. **Run Server**
   ```bash
   doppler run -- poetry run python manage.py runserver
   ```

## 🧪 Testing & Quality

We provide several **Poetry scripts** to streamline testing and security audits.

### Automated Scripts
These wrappers handle the complex Docker commands for you:

```bash
# Run all tests (automatically starts/stops portfolio-test container)
poetry run test

# Run tests with coverage report
poetry run test-cov

# Run security scan on local dependencies
poetry run security
```

### Manual Commands
If you need more control or want to run tools individually on your host:

```bash
# Run pytest with specific arguments
poetry run pytest -v

# Run linters and formatters (pre-commit)
pre-commit run --all-files
```

## 🐳 Docker Integration (Recommended)

### Pro Deployment (Recommended: Doppler)
```bash
# Run from the project root with centralized secrets
doppler run -- docker compose up --build
```

### Standard Deployment
```bash
# Legacy method using local .env files
docker compose up --build
```

#### Host File Configuration (Required for Docker)
To access the project via custom domains, add the following to your `/etc/hosts` (Mac/Linux) or `C:\Windows\System32\drivers\etc\hosts` (Windows):
```text
127.0.0.1 portfolio.local
127.0.0.1 admin.portfolio.local
```

- **Backend API**: `https://admin.portfolio.local/api/v1/`
- **Django Admin**: `https://admin.portfolio.local/admin/`
- **Media Files**: `https://portfolio.local/media/`

### Run Tests in Docker
```bash
# Isolated test execution
docker compose run --rm portfolio-test

# Fast check if already running
docker compose exec portfolio-be pytest
```

## 🗄️ Database Maintenance

We provide specialized "God-Tier" scripts for automated database backups and restore verification.

- **Atomic Backups**: `scripts/db_backup/backup_db.sh` creates validated, timestamped dumps with overlap protection.
- **Restore Verification**: `scripts/db_backup/test_restore.sh` automatically verifies that backups are healthy by performing a full restore in a temporary container.

> [!TIP]
> For detailed instructions on configuration (Doppler/Env), retention policies, and restore procedures, see the [Database Maintenance Guide](../scripts/db_backup/MAINTENANCE.md).

## 📅 TODO - Backend Improvements

## � TODO - Backend Improvements

### 📸 Features & Processing
- [ ] Implement image optimization pipeline (WebP conversion)
- [ ] Prettify email messages (add HTML template)
- [x] Singleton User & UUID migration for all models
- [x] Contact form with throttling and honeypot
- [x] Automatic thumbnail generation

### 🚀 API & Reliability
- [ ] **API Documentation** - Add OpenAPI/Swagger documentation
- [ ] **Structured Logging** - Implement JSON structured logs for production
- [x] **Rate Limiting** - Multi-layer DDoS protection implemented
- [x] **Health Checks** - Django health endpoint configured

### 🗄️ Database & Performance
- [x] **Backup** - Atomic DB backup and "God-Tier" restore verification scripts
- [x] **Redis Caching** - Configured for Select2 and select views
- [x] **Automated Migrations** - Integrated into Docker startup

### 🔒 Security
- [x] **Harden Container** - Non-root user with minimal permissions
- [x] **Dependency Scanning** - GitHub Actions with Safety & Dependabot
- [x] **ViewSet Hardening** - Minimalist ViewSets with strict method enforcement
