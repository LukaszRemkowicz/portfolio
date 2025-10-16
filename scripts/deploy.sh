#!/bin/bash

# Portfolio Deployment Script
# Automatyczny deployment na serwer produkcyjny
# Uruchamiany przez cron co 10-15 minut

set -e  # Zatrzymaj przy błędzie

# Konfiguracja
PROJECT_DIR="/path/to/portfolio"  # ZMIEŃ NA SWOJĄ ŚCIEŻKĘ!
BRANCH="main"
LOG_FILE="/var/log/portfolio-deploy.log"

# Kolory dla logów
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcja logowania
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

# Sprawdź czy katalog projektu istnieje
if [ ! -d "$PROJECT_DIR" ]; then
    error "Katalog projektu nie istnieje: $PROJECT_DIR"
    error "Zmień PROJECT_DIR w skrypcie na właściwą ścieżkę!"
    exit 1
fi

log "🚀 Rozpoczynam deployment portfolio..."

# Przejdź do katalogu projektu
cd "$PROJECT_DIR" || {
    error "Nie można przejść do katalogu: $PROJECT_DIR"
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

# Sprawdź czy jest nowy kod do pobrania
log "📥 Sprawdzam czy są nowe zmiany..."
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "✅ Kod jest aktualny, brak zmian do deployowania"
    exit 0
fi

log "📥 Znaleziono nowe zmiany, pobieram kod..."

# Pobierz najnowszy kod
git pull origin $BRANCH || {
    error "Nie udało się pobrać kodu z git!"
    exit 1
}

success "✅ Kod pobrany pomyślnie"

# Sprawdź czy docker-compose.yml istnieje
if [ ! -f "docker-compose.yml" ]; then
    error "Plik docker-compose.yml nie istnieje!"
    exit 1
fi

# Zatrzymaj istniejące kontenery
log "🛑 Zatrzymuję istniejące kontenery..."
if command -v docker-compose &> /dev/null; then
    docker-compose down || warning "Nie udało się zatrzymać kontenerów (może nie były uruchomione)"
else
    docker compose down || warning "Nie udało się zatrzymać kontenerów (może nie były uruchomione)"
fi

# Zbuduj nowe obrazy
log "🔨 Buduję nowe obrazy Docker..."
if command -v docker-compose &> /dev/null; then
    docker-compose build --no-cache || {
        error "Błąd podczas budowania obrazów Docker!"
        exit 1
    }
else
    docker compose build --no-cache || {
        error "Błąd podczas budowania obrazów Docker!"
        exit 1
    }
fi

success "✅ Obrazy Docker zbudowane pomyślnie"

# Uruchom kontenery
log "🚀 Uruchamiam nowe kontenery..."
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

success "✅ Kontenery uruchomione pomyślnie"

# Sprawdź czy kontenery działają
log "🔍 Sprawdzam status kontenerów..."
sleep 5  # Daj czas na uruchomienie

if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        success "✅ Kontenery działają poprawnie"
    else
        error "❌ Kontenery nie działają poprawnie!"
        docker-compose ps
        exit 1
    fi
else
    if docker compose ps | grep -q "Up"; then
        success "✅ Kontenery działają poprawnie"
    else
        error "❌ Kontenery nie działają poprawnie!"
        docker compose ps
        exit 1
    fi
fi

# Wyczyść stare obrazy (opcjonalnie)
log "🧹 Czyszczę stare obrazy Docker..."
docker system prune -f || warning "Nie udało się wyczyścić starych obrazów"

# Pokaż podsumowanie
log "📊 Podsumowanie deployment:"
log "   - Kod pobrany z branch: $BRANCH"
log "   - Commit: $(git rev-parse --short HEAD)"
log "   - Data: $(date)"
log "   - Status kontenerów:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

success "🎉 Deployment zakończony pomyślnie!"
log "📝 Log zapisany w: $LOG_FILE"
