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

## 📁 Project Structure

```
backend/
├── core/                    # Django project configuration
│   ├── settings.py         # Main settings with environment config
│   ├── urls.py            # URL routing and admin configuration
│   ├── models.py          # BaseImage abstract model
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI application
├── users/                  # User management app
│   ├── models.py          # Custom User model with social fields
│   ├── views.py           # UserViewSet for profile API
│   ├── serializers.py     # User and PublicUser serializers
│   ├── urls.py            # User API endpoints
│   └── admin.py           # User admin configuration
├── astrophotography/       # Astrophotography app
│   ├── models.py          # AstroImage and BackgroundMainPage models
│   ├── views.py           # Image listing, detail, and background views
│   ├── serializers.py     # Image serializers for API responses
│   ├── urls.py            # Astrophotography API endpoints
│   └── admin.py           # Image admin configuration
├── programming/            # Programming projects app
│   ├── models.py          # Project and ProjectImage models
│   ├── views.py           # Project API views (placeholder)
│   ├── urls.py            # Programming API endpoints
│   └── admin.py           # Project admin configuration
├── manage.py              # Django management script
├── pyproject.toml         # Poetry dependencies and configuration
└── Dockerfile             # Docker container configuration
```

## 🔌 API Endpoints

### User Profile
- **`GET /api/v1/profile/`** - Public user profile data
  - Returns: username, name, bio, avatar, social links, about me images
  - Serializer: `PublicUserSerializer`

### Astrophotography
- **`GET /api/v1/image/`** - List astrophotography images
  - Query params: `?filter=<celestial_object>` (Landscape, Deep Sky, etc.)
  - Returns: Array of images with URLs and metadata
- **`GET /api/v1/image/<id>/`** - Individual image details
  - Returns: Full image metadata including equipment, processing details
- **`GET /api/v1/background/`** - Main page background image
  - Returns: Latest background image URL

### Programming (Future)
- **`GET /api/v1/programming/`** - Programming projects list
- **`GET /api/v1/programming/<id>/`** - Individual project details

## 🛠️ Development Setup

### Prerequisites
- **Python 3.11-3.12** (specified in pyproject.toml)
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
Create `.env` file in `backend/` directory:
```env
# Required
SECRET_KEY=your-super-secret-key-here
DEBUG=True

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Domain Configuration
ALLOWED_HOSTS=admin.portfolio.local,portfolio.local,localhost,127.0.0.1
```

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
- **Django Admin**: `https://admin.portfolio.local/admin/`
- **Media Files**: `https://portfolio.local/media/`

### Backend-Only Docker
```bash
cd backend
docker build -t portfolio-backend .
docker run -p 8000:8000 portfolio-backend
```

## 📊 Database Models

### User Model (Extended Django User)
```python
class User(AbstractUser):
    bio = models.TextField(max_length=10000)
    avatar = models.ImageField(upload_to='avatars/')
    about_me_image = models.ImageField(upload_to='about_me_images/')
    about_me_image2 = models.ImageField(upload_to='about_me_images/')
    website = models.URLField()
    github_profile = models.URLField()
    linkedin_profile = models.URLField()
    astrobin_url = models.URLField()
    fb_url = models.URLField()
    ig_url = models.URLField()
```

### Astrophotography Models
```python
class AstroImage(BaseImage):
    capture_date = models.DateField()
    location = models.CharField(max_length=255)
    equipment = models.TextField()
    exposure_details = models.TextField()
    processing_details = models.TextField()
    celestial_object = models.CharField(choices=CelestialObjectChoices)
    astrobin_url = models.URLField()

class BackgroundMainPage(models.Model):
    image = models.ImageField(upload_to='backgrounds/')
    created_at = models.DateTimeField(auto_now_add=True)
```

### Programming Models
```python
class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    technologies = models.TextField()
    github_url = models.URLField()
    live_url = models.URLField()

class ProjectImage(BaseImage):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_cover = models.BooleanField(default=False)
```

## 🔧 Configuration

### Django Settings Highlights
- **CORS Configuration** - Configured for frontend domains
- **Media File Handling** - Optimized for nginx serving
- **Custom Admin Interface** - Branded admin portal
- **Environment-based Configuration** - Secure settings management
- **Database Connection Pooling** - Production-ready database config

### Dependencies (pyproject.toml)
```toml
dependencies = [
    "Django>=4.2",
    "djangorestframework>=3.14",
    "django-environ>=0.11.2",
    "psycopg2-binary>=2.9.9",
    "Pillow>=10.2.0",
    "django-cors-headers>=4.3.1"
]
```

## 🧪 Testing

### Current Test Setup
- **pytest** configured for testing
- **Django test framework** integration
- **Test database** isolation

### Running Tests
```bash
poetry run python manage.py test
# or
poetry run pytest
```

## 📋 Admin Interface

### Custom Admin Features
- **Branded Interface** - Custom site header and title
- **User Management** - Extended user fields in admin
- **Image Management** - Bulk upload and organization
- **Content Management** - Easy profile and bio updates

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

- [ ] Complete Programming API endpoints
- [ ] Add comprehensive test coverage
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
- [ ] **Test Coverage** - Increase test coverage for all models and views
- [ ] **Integration Tests** - Add integration tests for API endpoints
- [ ] **Performance Tests** - Add load testing for API endpoints
- [ ] **Code Quality** - Add linting and code quality checks

### 📊 Monitoring & Logging
- [ ] **Structured Logging** - Implement structured logging with JSON format
- [ ] **Error Tracking** - Add error tracking and monitoring
- [ ] **Health Checks** - Add health check endpoints
- [ ] **Metrics Collection** - Add application metrics collection

---

For frontend setup and integration, see [Frontend README](../frontend/README.md). 