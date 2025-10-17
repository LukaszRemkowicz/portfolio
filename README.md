# Portfolio Landing Page

A modern, API-driven personal portfolio web app with subpages for Astrophotography, Programming, and Contact. Built with React (frontend) and Django + Django Rest Framework (backend), fully dockerized and orchestrated with nginx for local HTTPS development.

## Features

### Frontend (React)
- **Multi-page React app** with subpages (Astrophotography, Programming, Contact)
- **Dynamic content** - profile, bio, and media loaded from backend API
- **Responsive design** with mobile-first approach
- **Professional CSS architecture** - organized styles with CSS modules and design system
- **Comprehensive testing** - 18 tests covering all components with full documentation
- **Modern tooling** - Webpack 5, Jest, React Testing Library
- **SEO-friendly** with React Router v6

### Backend (Django + DRF)
- **Custom user model** with profile management
- **Image models** for astrophotography gallery
- **RESTful API** with Django Rest Framework
- **Admin interface** for content management
- **Media file handling** with proper serving

### DevOps & Infrastructure
- **Docker Compose** for full-stack local development
- **nginx** for HTTPS, static/media file serving, and domain routing
- **SSL certificates** for local HTTPS development
- **Environment-based configuration** for different deployment stages

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

## Project Structure

```
landingpage/
├── frontend/                    # React application
│   ├── src/
│   │   ├── __tests__/          # Comprehensive test suite (18 tests)
│   │   ├── styles/             # Organized CSS architecture
│   │   │   ├── global/         # Global styles and reset
│   │   │   ├── components/     # Component-specific styles
│   │   │   └── themes/         # CSS variables and utilities
│   │   ├── components/         # React components
│   │   ├── api/               # API integration layer
│   │   └── data/              # Static data and configuration
│   ├── public/                # Static assets
│   └── README.md              # Frontend documentation
├── backend/                    # Django + DRF API
│   ├── astrophotography/      # Image gallery models
│   ├── users/                 # Custom user model
│   ├── programming/           # Programming projects
│   └── README.md              # Backend documentation
├── nginx/                     # nginx configuration and SSL
└── docker-compose.yml         # Full-stack orchestration
```

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
docker compose exec portfolio-fe npm test    # Run frontend tests

# For older Docker versions (Docker Compose V1)
docker-compose up --build    # Start all services
docker-compose exec portfolio-fe npm test    # Run frontend tests
```

## Testing
- **Frontend**: 18 comprehensive tests covering all components
- **Backend**: Django test framework
- **Coverage**: Component rendering, user interactions, API integration, error handling

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

### 🚀 DevOps & Infrastructure
- [x] **CI/CD Pipeline** - ✅ GitHub Actions workflow with automated testing, security scanning, and Docker builds
- [x] **Production Deployment** - ✅ Deploy script (deploy.sh) for production server deployment
- [ ] **Environment Management** - Set up staging and production environments
- [ ] **Container Orchestration** - Consider Kubernetes or Docker Swarm for production
- [ ] **Monitoring & Logging** - Add application monitoring
- [ ] **Backup Strategy** - Implement database and media file backups
- [x] **Security Hardening** - ✅ CodeQL security analysis, vulnerability scanning, dependency audits

### 📊 Project Management
- [x] **Code Quality** - ✅ Pre-commit hooks, Black, isort, Flake8, ESLint, Prettier configured
- [x] **Dependency Management** - ✅ Dependabot configured for automatic dependency updates
- [ ] **Documentation** - API documentation, deployment guides, troubleshooting
- [ ] **Performance Testing** - Load testing and performance benchmarks


### 📋 Component-Specific TODOs
- **Frontend TODOs**: See [Frontend README](frontend/README.md#-todo--future-improvements)
- **Backend TODOs**: See [Backend README](backend/README.md) for API documentation, database optimization, caching, image processing, rate limiting, and authentication improvements

## More Info
- [Frontend README](frontend/README.md) - Detailed React app documentation
- [Backend README](backend/README.md) - Django API documentation

## License
MIT
