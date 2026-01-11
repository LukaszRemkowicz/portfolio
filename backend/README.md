# Portfolio Backend

Django REST API backend for a personal portfolio showcasing astrophotography and programming projects. Built with Django 5.2+ and Django REST Framework, featuring custom user models, image management, and comprehensive API endpoints.

## 🚀 Features

### Core Functionality
- **Custom User Model** - Extended Django user with bio, avatar, social links, and about me images
- **Image Management** - BaseImage abstract model for consistent image handling
- **Astrophotography Gallery** - Complete image gallery with metadata and filtering
- **Programming Projects** - Project showcase with images and technology stacks
- **Background Management** - Dynamic main page background images
- **Admin Interface** - Customized Django admin for content management

### Technical Features
- **Django REST Framework** - RESTful API with ViewSets and serializers
- **PostgreSQL Database** - Production-ready database with migrations
- **Poetry Dependency Management** - Modern Python dependency management
- **Environment Configuration** - django-environ for secure configuration
- **CORS Support** - Configured for frontend integration
- **Media File Serving** - Optimized static and media file handling
- **Docker Integration** - Containerized deployment ready

## 🛠️ Development Setup

### Prerequisites
- **Python 3.13** (specified in pyproject.toml)
- **Poetry** for dependency management
- **PostgreSQL** (or Docker for containerized setup)
- **Docker** (for containerized development)

> **Docker Compose Version**: Check your Docker version with `docker --version`. Use `docker compose` (V2) or `docker-compose` (V1) accordingly.

### 快速开始 (Quick Start)

#### 1. Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
# Add to PATH: export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Install Dependencies
```bash
cd backend
poetry install
```

#### 3. Environment Configuration
Copy the default environment template:
```bash
cp DEFAULT.env .env
```
Then edit `.env` with your secure credentials.

#### 4. Database Setup
```bash
# Run migrations
poetry run python manage.py migrate

# Create superuser (optional)
poetry run python manage.py createsuperuser
```

#### 5. Development Server
```bash
poetry run python manage.py runserver 0.0.0.0:8000
```

## 🧪 Testing & Quality

### Running Tests
```bash
# Run all tests with pytest
poetry run pytest

# Run with coverage
poetry run pytest --cov=. --cov-report=term-missing
```

### Code Quality Tools
```bash
# Run Flake8 linting
poetry run flake8 .

# Run MyPy type checking
poetry run mypy .

# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .
```

### Security Scanning
```bash
# Run security scan for vulnerabilities
poetry run safety scan
```

## 🐳 Docker Integration

### With Docker Compose (Recommended)
```bash
# From project root
docker compose up --build
```
- **Backend API**: `https://admin.portfolio.local/api/v1/`
- **Django Admin**: `https://admin.portfolio.local/admin/`
- **Media Files**: `https://portfolio.local/media/`

### Run Tests in Docker
```bash
# Run backend tests inside the container
docker compose exec portfolio-be pytest
```

## 📋 API Endpoints
- `/api/v1/profile/` - User profile
- `/api/v1/background/` - Background images
- `/api/v1/image/` - Astrophotography images
- `/api/v1/contact/` - Contact form submission

## 🚀 Production Considerations

### Security
- Environment-based SECRET_KEY
- CORS properly configured
- Media file serving through nginx
- Database connection security
- Non-root user execution in Docker

### Performance
- Gunicorn WSGI server for production
- Database query optimization
- Media file CDN ready
- Static file serving optimization

## 📋 TODO - Backend Improvements

- [ ] Implement image optimization pipeline
- [ ] Implement caching for frequently accessed data
- [ ] Printify email messages (add html template)

### 🚀 API & Documentation
- [ ] **API Documentation** - Add OpenAPI/Swagger documentation with interactive docs
- [ ] **API Versioning** - Implement proper API versioning strategy
- [ ] **Response Standardization** - Standardize API response formats
- [x] **API Testing** - Add comprehensive API endpoint tests

### 🗄️ Database & Performance
- [ ] **Database Optimization** - Query optimization, indexing, connection pooling
- [ ] **Caching Strategy** - Implement Redis caching for better performance
- [x] **Database Migrations** - Automated production-ready migrations in Docker
- [ ] **Performance Monitoring** - Add database query monitoring
- [ ] **Backup** - Add backup and restore functionality

### 🔒 Security & Authentication
- [x] **Rate Limiting** - Implement API rate limiting and DDoS protection
- [ ] **Input Validation** - Enhanced input validation and sanitization
- [x] **Security Headers** - Add security headers and CSRF protection
- [x] **Security Hardening** - Container hardening (non-root) and HSTS implementation
- [x] **Dependency Scanning** - Automated vulnerability checks (Dependabot, Safety)

### 📸 Image Processing
- [ ] **Image Processing** - Add image compression, resizing, and optimization
- [ ] **Thumbnail Generation** - Automatic thumbnail generation

### 🧪 Testing & Quality
- [x] **Test Coverage** - High coverage for Core, Users, Astrophotography, and Inbox apps
- [ ] **Integration Tests** - Add integration tests for API endpoints
- [ ] **Performance Tests** - Add load testing for API endpoints
- [x] **Code Quality** - ✅ Pre-commit hooks, Black, isort, Flake8 configured with 100-character line length

### 📊 Monitoring & Logging
- [ ] **Structured Logging** - Implement structured logging with JSON format
- [ ] **Error Tracking** - Add error tracking and monitoring (sentry)
- [x] **Health Checks** - Add health check endpoints
- [ ] **Metrics Collection** - Add application metrics collection

### Devops
- [x] **Production Server** - Gunicorn WSGI server implementation
- [ ] ***Container orchestration*** - Docker Swarm or Kubernetes

---

For frontend setup and integration, see [Frontend README](../frontend/README.md).
