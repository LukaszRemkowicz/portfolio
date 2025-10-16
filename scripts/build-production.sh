#!/bin/bash

# Portfolio Production Build Script
# Script for building production images on demand
# Run manually when you want to build new images

set -e  # Stop on error

# Configuration
PROJECT_DIR="/path/to/portfolio"  # CHANGE TO YOUR PATH!
BRANCH="main"
LOG_FILE="/var/log/portfolio-build.log"

# Colors for logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Show help if --help is provided
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Portfolio Production Build Script"
    echo ""
    echo "Usage:"
    echo "  $0                    # Build production images"
    echo "  $0 --help            # Show this help"
    echo "  $0 --no-pull         # Build without pulling code"
    echo "  $0 --frontend-only   # Build only frontend"
    echo "  $0 --backend-only    # Build only backend"
    echo ""
    echo "Options:"
    echo "  --no-pull           Skip git pull"
    echo "  --frontend-only     Build only frontend image"
    echo "  --backend-only      Build only backend image"
    echo "  --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Full build"
    echo "  $0 --no-pull --frontend-only # Frontend only without git pull"
    exit 0
fi

# Parse arguments
NO_PULL=false
FRONTEND_ONLY=false
BACKEND_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-pull)
            NO_PULL=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        *)
            error "Unknown argument: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Check conflicting options
if [ "$FRONTEND_ONLY" = true ] && [ "$BACKEND_ONLY" = true ]; then
    error "Cannot use --frontend-only and --backend-only at the same time"
    exit 1
fi

log "🏭 Starting production image build..."

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    error "Project directory does not exist: $PROJECT_DIR"
    error "Change PROJECT_DIR in the script to the correct path!"
    exit 1
fi

# Go to project directory
cd "$PROJECT_DIR" || {
    error "Cannot access directory: $PROJECT_DIR"
    exit 1
}

# Sprawdź czy to repozytorium git
if [ ! -d ".git" ]; then
    error "To nie jest repozytorium git!"
    exit 1
fi

# Sprawdź czy Docker jest dostępny
if ! command -v docker &> /dev/null; then
    error "Docker nie jest zainstalowany lub nie jest dostępny!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    error "Docker Compose nie jest dostępny!"
    exit 1
fi

# Pokaż aktualny branch
CURRENT_BRANCH=$(git branch --show-current)
log "📋 Aktualny branch: $CURRENT_BRANCH"

# Git pull (jeśli nie wyłączone)
if [ "$NO_PULL" = false ]; then
    log "📥 Pobieram najnowszy kod z branch $BRANCH..."
    
    # Przełącz na właściwy branch jeśli potrzeba
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        log "🔄 Przełączam na branch $BRANCH..."
        git checkout "$BRANCH" || {
            error "Nie można przełączyć na branch $BRANCH"
            exit 1
        }
    fi
    
    # Pobierz najnowszy kod
    git pull origin "$BRANCH" || {
        error "Nie udało się pobrać kodu z git!"
        exit 1
    }
    
    success "✅ Kod pobrany pomyślnie"
else
    info "⏭️  Pomijam git pull (--no-pull)"
fi

# Pokaż aktualny commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
log "📌 Aktualny commit: $CURRENT_COMMIT"

# Sprawdź czy pliki Dockerfile istnieją
if [ "$BACKEND_ONLY" = false ]; then
    if [ ! -f "frontend/Dockerfile" ]; then
        error "Plik frontend/Dockerfile nie istnieje!"
        exit 1
    fi
fi

if [ "$FRONTEND_ONLY" = false ]; then
    if [ ! -f "backend/Dockerfile" ]; then
        error "Plik backend/Dockerfile nie istnieje!"
        exit 1
    fi
fi

# Zatrzymaj istniejące kontenery (opcjonalnie)
log "🛑 Zatrzymuję istniejące kontenery..."
if command -v docker-compose &> /dev/null; then
    docker-compose down || warning "Nie udało się zatrzymać kontenerów (może nie były uruchomione)"
else
    docker compose down || warning "Nie udało się zatrzymać kontenerów (może nie były uruchomione)"
fi

# Buduj obrazy
if [ "$BACKEND_ONLY" = false ]; then
    log "🔨 Buduję obraz frontend (produkcja)..."
    
    # Sprawdź czy target 'prod' istnieje w Dockerfile
    if grep -q "target.*prod" frontend/Dockerfile; then
        BUILD_TARGET="prod"
        log "📦 Używam target: $BUILD_TARGET"
    else
        BUILD_TARGET=""
        warning "Brak target 'prod' w Dockerfile, buduję domyślny"
    fi
    
    if [ -n "$BUILD_TARGET" ]; then
        docker build -t portfolio-frontend:prod -t portfolio-frontend:latest -t portfolio-frontend:$CURRENT_COMMIT --target "$BUILD_TARGET" ./frontend || {
            error "Błąd podczas budowania obrazu frontend!"
            exit 1
        }
    else
        docker build -t portfolio-frontend:prod -t portfolio-frontend:latest -t portfolio-frontend:$CURRENT_COMMIT ./frontend || {
            error "Błąd podczas budowania obrazu frontend!"
            exit 1
        }
    fi
    
    success "✅ Obraz frontend zbudowany pomyślnie"
    info "📦 Tagi: portfolio-frontend:prod, portfolio-frontend:latest, portfolio-frontend:$CURRENT_COMMIT"
fi

if [ "$FRONTEND_ONLY" = false ]; then
    log "🔨 Buduję obraz backend (produkcja)..."
    
    # Sprawdź czy target 'prod' istnieje w Dockerfile
    if grep -q "target.*prod" backend/Dockerfile; then
        BUILD_TARGET="prod"
        log "📦 Używam target: $BUILD_TARGET"
    else
        BUILD_TARGET=""
        warning "Brak target 'prod' w Dockerfile, buduję domyślny"
    fi
    
    if [ -n "$BUILD_TARGET" ]; then
        docker build -t portfolio-backend:prod -t portfolio-backend:latest -t portfolio-backend:$CURRENT_COMMIT --target "$BUILD_TARGET" ./backend || {
            error "Błąd podczas budowania obrazu backend!"
            exit 1
        }
    else
        docker build -t portfolio-backend:prod -t portfolio-backend:latest -t portfolio-backend:$CURRENT_COMMIT ./backend || {
            error "Błąd podczas budowania obrazu backend!"
            exit 1
        }
    fi
    
    success "✅ Obraz backend zbudowany pomyślnie"
    info "📦 Tagi: portfolio-backend:prod, portfolio-backend:latest, portfolio-backend:$CURRENT_COMMIT"
fi

# Pokaż zbudowane obrazy
log "📋 Zbudowane obrazy:"
docker images | grep portfolio || warning "Brak obrazów portfolio"

# Opcjonalnie uruchom kontenery (zapytaj użytkownika)
echo ""
read -p "🚀 Czy chcesz uruchomić kontenery produkcyjne? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "🚀 Uruchamiam kontenery produkcyjne..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d || {
            error "Błąd podczas uruchamiania kontenerów!"
            exit 1
        }
    else
        docker compose up -d || {
            error "Błąd podczas uruchamiania kontenerów!"
            exit 1
        }
    fi
    
    # Sprawdź status
    sleep 3
    log "📊 Status kontenerów:"
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    success "✅ Kontenery uruchomione pomyślnie"
else
    info "⏭️  Pomijam uruchamianie kontenerów"
fi

# Pokaż podsumowanie
echo ""
log "📊 Podsumowanie budowania:"
log "   - Branch: $BRANCH"
log "   - Commit: $CURRENT_COMMIT"
log "   - Data: $(date)"
log "   - Zbudowane obrazy:"

if [ "$BACKEND_ONLY" = false ]; then
    log "     ✅ portfolio-frontend:prod"
    log "     ✅ portfolio-frontend:latest"
    log "     ✅ portfolio-frontend:$CURRENT_COMMIT"
fi

if [ "$FRONTEND_ONLY" = false ]; then
    log "     ✅ portfolio-backend:prod"
    log "     ✅ portfolio-backend:latest"
    log "     ✅ portfolio-backend:$CURRENT_COMMIT"
fi

log ""
success "🎉 Budowanie obrazów produkcyjnych zakończone pomyślnie!"
log "📝 Log zapisany w: $LOG_FILE"
log ""
info "💡 Wskazówki:"
info "   - Użyj 'docker images | grep portfolio' aby zobaczyć obrazy"
info "   - Użyj 'docker run -p 80:80 portfolio-frontend:prod' aby przetestować frontend"
info "   - Użyj 'docker run -p 8000:8000 portfolio-backend:prod' aby przetestować backend"
