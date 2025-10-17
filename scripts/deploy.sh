#!/bin/bash

# Portfolio Deployment Script
# Automatic deployment to production server
# Run by cron every 10-15 minutes

set -e  # Stop on error

# Configuration
PROJECT_DIR="/path/to/portfolio"  # CHANGE TO YOUR PATH!
BRANCH="main"
LOG_FILE="/var/log/portfolio-deploy.log"

# Colors for logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Sprawdź czy katalog projektu istnieje
if [ ! -d "$PROJECT_DIR" ]; then
    error "Project directory does not exist: $PROJECT_DIR"
    error "Change PROJECT_DIR in the script to the correct path!"
    exit 1
fi

log "🚀 Starting portfolio deployment..."

# Go to project directory
cd "$PROJECT_DIR" || {
    error "Cannot access directory: $PROJECT_DIR"
    exit 1
}

# Check if this is a git repository
if [ ! -d ".git" ]; then
    error "This is not a git repository!"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not available!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    error "Docker Compose is not available!"
    exit 1
fi

# Check if there is new code to pull
log "📥 Checking for new changes..."
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "✅ Code is up to date, no changes to deploy"
    exit 0
fi

log "📥 Found new changes, pulling code..."

# Pull latest code
git pull origin $BRANCH || {
    error "Failed to pull code from git!"
    exit 1
}

success "✅ Code pulled successfully"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml file does not exist!"
    exit 1
fi

# Stop existing containers
log "🛑 Stopping existing containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose down || warning "Failed to stop containers (may not have been running)"
else
    docker compose down || warning "Failed to stop containers (may not have been running)"
fi

# Build new images
log "🔨 Building new Docker images..."
if command -v docker-compose &> /dev/null; then
    docker-compose build --no-cache || {
        error "Error building Docker images!"
        exit 1
    }
else
    docker compose build --no-cache || {
        error "Error building Docker images!"
        exit 1
    }
fi

success "✅ Docker images built successfully"

# Start containers
log "🚀 Starting new containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d || {
        error "Error starting containers!"
        exit 1
    }
else
    docker compose up -d || {
        error "Error starting containers!"
        exit 1
    }
fi

success "✅ Containers started successfully"

# Check if containers are running
log "🔍 Checking container status..."
sleep 5  # Give time to start

if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        success "✅ Containers are running correctly"
    else
        error "❌ Containers are not running correctly!"
        docker-compose ps
        exit 1
    fi
else
    if docker compose ps | grep -q "Up"; then
        success "✅ Containers are running correctly"
    else
        error "❌ Containers are not running correctly!"
        docker compose ps
        exit 1
    fi
fi

# Clean old images (optional)
log "🧹 Cleaning old Docker images..."
docker system prune -f || warning "Failed to clean old images"

# Show summary
log "📊 Deployment summary:"
log "   - Code pulled from branch: $BRANCH"
log "   - Commit: $(git rev-parse --short HEAD)"
log "   - Date: $(date)"
log "   - Container status:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

success "🎉 Deployment completed successfully!"
log "📝 Log saved to: $LOG_FILE"
