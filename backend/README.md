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

### Installation

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

## 🐳 Docker Integration

### With Docker Compose (Recommended)
```bash
# From project root
# Docker Compose V2 (newer versions)
docker compose up --build

# Docker Compose V1 (older versions)
docker-compose up --build
```
- **Backend API**: `https://admin.portfolio.local/api/v1/`
- **Django Admin**: `https://admin.portfolio.local/`
- **Media Files**: `https://portfolio.local/media/`

### Backend-Only Docker
```bash
cd backend
docker build -t portfolio-backend .
docker run -p 8000:8000 portfolio-backend
```

## 🧪 Testing

### Current Test Setup
- **pytest** configured for testing
- **Test database** isolation

### Running Tests
```bash
poetry run python manage.py test
# or
poetry run pytest
```

## 📋 Admin Interface

### Admin Access
1. Create superuser: `poetry run python manage.py createsuperuser`
2. Access admin: `https://admin.portfolio.local/admin/`
3. Configure profile, upload images, manage content

## 🚀 Production Considerations

### Security
- Environment-based SECRET_KEY
- CORS properly configured
- Media file serving through nginx
- Database connection security

### Performance
- Database query optimization
- Media file CDN ready
- Static file serving optimization
- Docker container optimization

### Monitoring
- Django logging configuration
- Error tracking ready
- Health check endpoints available

## 📋 TODO / Known Issues

- [ ] Implement image optimization pipeline
- [ ] Add API documentation (Swagger/OpenAPI)
- [ ] Implement caching for frequently accessed data
- [ ] Add backup and restore functionality

## 🔗 Integration

### Frontend Integration
- **CORS configured** for frontend domains
- **API endpoints** designed for React consumption
- **Media URLs** optimized for frontend display
- **Error responses** formatted for frontend handling

### nginx Integration
- **Media file serving** through nginx
- **HTTPS configuration** for local development
- **Domain-based routing** (admin vs. frontend)
- **Static file optimization**

## ✅ Recently Completed

### 🎯 Backend Improvements (Latest Session)

- ✅ **Code Quality Setup** - Pre-commit hooks, Black, isort, Flake8 configured
- ✅ **Line Length Standardization** - Updated to 100 characters for better readability
- ✅ **Python 3.13 Support** - Updated from Python 3.12 to 3.13
- ✅ **Black Integration** - Latest Black v25.9.0 with Python 3.13 support
- ✅ **Django Migrations** - Fixed long lines with noqa comments
- ✅ **Import Organization** - Fixed import order issues with isort
- ✅ **Django 5.2 Upgrade** - Upgraded to latest LTS version
- ✅ **Security Hardening** - DEBUG=False, stricter permissions, kill switch
- ✅ **Astrophotography Refactor** - Migrated to ViewSets and Routers
- ✅ **Testing** - comprehensive test suite with 100% pass rate

## 📋 TODO - Backend Improvements

### 🚀 API & Documentation
- [ ] **API Documentation** - Add OpenAPI/Swagger documentation with interactive docs
- [ ] **API Versioning** - Implement proper API versioning strategy
- [ ] **Response Standardization** - Standardize API response formats
- [ ] **API Testing** - Add comprehensive API endpoint tests

### 🗄️ Database & Performance
- [ ] **Database Optimization** - Query optimization, indexing, connection pooling
- [ ] **Caching Strategy** - Implement Redis caching for better performance
- [ ] **Database Migrations** - Optimize migration strategy for production
- [ ] **Performance Monitoring** - Add database query monitoring

### 🔒 Security & Authentication
- [ ] **JWT Authentication** - Add JWT authentication for admin endpoints
- [ ] **Rate Limiting** - Implement API rate limiting and DDoS protection
- [ ] **Input Validation** - Enhanced input validation and sanitization
- [ ] **Security Headers** - Add security headers and CSRF protection

### 📸 Image Processing
- [ ] **Image Processing** - Add image compression, resizing, and optimization
- [ ] **Multiple Image Formats** - Support for WebP, AVIF formats
- [ ] **Thumbnail Generation** - Automatic thumbnail generation
- [ ] **Image Metadata** - Extract and store EXIF data

### 🧪 Testing & Quality
- [x] **Test Coverage** - High coverage for Core, Users, Astrophotography, and Inbox apps
- [ ] **Integration Tests** - Add integration tests for API endpoints
- [ ] **Performance Tests** - Add load testing for API endpoints
- [x] **Code Quality** - ✅ Pre-commit hooks, Black, isort, Flake8 configured with 100-character line length

### 📊 Monitoring & Logging
- [ ] **Structured Logging** - Implement structured logging with JSON format
- [ ] **Error Tracking** - Add error tracking and monitoring
- [ ] **Health Checks** - Add health check endpoints
- [ ] **Metrics Collection** - Add application metrics collection

---

For frontend setup and integration, see [Frontend README](../frontend/README.md).
