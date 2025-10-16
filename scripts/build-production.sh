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

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
log "📋 Current branch: $CURRENT_BRANCH"

# Git pull (if not disabled)
if [ "$NO_PULL" = false ]; then
    log "📥 Pulling latest code from branch $BRANCH..."

    # Switch to correct branch if needed
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        log "🔄 Switching to branch $BRANCH..."
        git checkout "$BRANCH" || {
            error "Cannot switch to branch $BRANCH"
            exit 1
        }
    fi

    # Pull latest code
    git pull origin "$BRANCH" || {
        error "Failed to pull code from git!"
        exit 1
    }

    success "✅ Code pulled successfully"
else
    info "⏭️  Skipping git pull (--no-pull)"
fi

# Show current commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
log "📌 Current commit: $CURRENT_COMMIT"

# Check if Dockerfile files exist
if [ "$BACKEND_ONLY" = false ]; then
    if [ ! -f "frontend/Dockerfile" ]; then
        error "frontend/Dockerfile file does not exist!"
        exit 1
    fi
fi

if [ "$FRONTEND_ONLY" = false ]; then
    if [ ! -f "backend/Dockerfile" ]; then
        error "backend/Dockerfile file does not exist!"
        exit 1
    fi
fi

# Stop existing containers (optional)
log "🛑 Stopping existing containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose down || warning "Failed to stop containers (may not have been running)"
else
    docker compose down || warning "Failed to stop containers (may not have been running)"
fi

# Build images
if [ "$BACKEND_ONLY" = false ]; then
    log "🔨 Building frontend image (production)..."

    # Check if 'prod' target exists in Dockerfile
    if grep -q "target.*prod" frontend/Dockerfile; then
        BUILD_TARGET="prod"
        log "📦 Using target: $BUILD_TARGET"
    else
        BUILD_TARGET=""
        warning "No 'prod' target in Dockerfile, building default"
    fi

    if [ -n "$BUILD_TARGET" ]; then
        docker build -t portfolio-frontend:prod -t portfolio-frontend:latest -t portfolio-frontend:$CURRENT_COMMIT --target "$BUILD_TARGET" ./frontend || {
            error "Error building frontend image!"
            exit 1
        }
    else
        docker build -t portfolio-frontend:prod -t portfolio-frontend:latest -t portfolio-frontend:$CURRENT_COMMIT ./frontend || {
            error "Error building frontend image!"
            exit 1
        }
    fi

    success "✅ Frontend image built successfully"
    info "📦 Tags: portfolio-frontend:prod, portfolio-frontend:latest, portfolio-frontend:$CURRENT_COMMIT"
fi

if [ "$FRONTEND_ONLY" = false ]; then
    log "🔨 Building backend image (production)..."

    # Check if 'prod' target exists in Dockerfile
    if grep -q "target.*prod" backend/Dockerfile; then
        BUILD_TARGET="prod"
        log "📦 Using target: $BUILD_TARGET"
    else
        BUILD_TARGET=""
        warning "No 'prod' target in Dockerfile, building default"
    fi

    if [ -n "$BUILD_TARGET" ]; then
        docker build -t portfolio-backend:prod -t portfolio-backend:latest -t portfolio-backend:$CURRENT_COMMIT --target "$BUILD_TARGET" ./backend || {
            error "Error building backend image!"
            exit 1
        }
    else
        docker build -t portfolio-backend:prod -t portfolio-backend:latest -t portfolio-backend:$CURRENT_COMMIT ./backend || {
            error "Error building backend image!"
            exit 1
        }
    fi

    success "✅ Backend image built successfully"
    info "📦 Tags: portfolio-backend:prod, portfolio-backend:latest, portfolio-backend:$CURRENT_COMMIT"
fi

# Show built images
log "📋 Built images:"
docker images | grep portfolio || warning "No portfolio images found"

# Optionally run containers (ask user)
echo ""
read -p "🚀 Do you want to run production containers? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "🚀 Starting production containers..."

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

    # Check status
    sleep 3
    log "📊 Container status:"
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi

    success "✅ Containers started successfully"
else
    info "⏭️  Skipping container startup"
fi

# Show summary
echo ""
log "📊 Build summary:"
log "   - Branch: $BRANCH"
log "   - Commit: $CURRENT_COMMIT"
log "   - Date: $(date)"
log "   - Built images:"

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
success "🎉 Production image build completed successfully!"
log "📝 Log saved to: $LOG_FILE"
log ""
info "💡 Tips:"
info "   - Use 'docker images | grep portfolio' to see images"
info "   - Use 'docker run -p 80:80 portfolio-frontend:prod' to test frontend"
info "   - Use 'docker run -p 8000:8000 portfolio-backend:prod' to test backend"
