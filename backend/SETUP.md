# Backend Development Setup

## Prerequisites
- Python 3.12+
- Poetry (for dependency management)

## Quick Start

### 1. Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies
```bash
cd backend
poetry install
```

### 3. Activate Virtual Environment
```bash
poetry shell
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

## Code Quality Setup

### Install Pre-commit Hooks
```bash
# Install pre-commit globally
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

### Available Commands

#### Testing
```bash
# Run all tests
poetry run python manage.py test

# Run with coverage
poetry run coverage run --source='.' manage.py test
poetry run coverage report -m
```

#### Code Formatting
```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Check formatting
poetry run black --check .
poetry run isort --check-only .
```

#### Linting
```bash
# Run Flake8
poetry run flake8 .

# Run MyPy type checking
poetry run mypy .
```

#### Security
```bash
# Check for known security vulnerabilities
poetry run pip install safety
poetry run safety check
```

## Docker Development

### Build and Run
```bash
# From project root
docker compose up --build

# Backend only
docker compose up --build portfolio-be
```

### Run Tests in Docker
```bash
docker compose exec portfolio-be python manage.py test
```

## Project Structure
```
backend/
├── astrophotography/     # Astrophotography app
├── programming/          # Programming app
├── users/               # User management app
├── inbox/               # Contact messages app
├── core/                # Core Django settings
├── manage.py            # Django management script
├── pyproject.toml       # Poetry configuration
├── .flake8              # Flake8 configuration
└── SETUP.md             # This file
```

## API Endpoints
- `/api/v1/profile/` - User profile
- `/api/v1/background/` - Background images
- `/api/v1/image/` - Astrophotography images
- `/api/v1/contact/` - Contact form submission

## Environment Variables
Create `.env` file in backend directory:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,portfolio.local,admin.portfolio.local
```
