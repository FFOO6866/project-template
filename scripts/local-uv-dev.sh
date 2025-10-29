#!/bin/bash
# ============================================================================
# Horme POV - Local UV Development Environment
# ============================================================================
#
# Sets up and runs local development environment with UV-based containers
#
# Usage:
#   ./scripts/local-uv-dev.sh                # Start all services
#   ./scripts/local-uv-dev.sh --rebuild      # Rebuild and start
#   ./scripts/local-uv-dev.sh --stop         # Stop all services
#   ./scripts/local-uv-dev.sh --logs api     # View API logs
#
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Configuration
# ============================================================================

COMPOSE_FILE="docker-compose.uv.yml"
ENV_FILE=".env.production"

# Parse arguments
REBUILD=false
STOP=false
LOGS=""

case "${1:-}" in
    --rebuild)
        REBUILD=true
        ;;
    --stop)
        STOP=true
        ;;
    --logs)
        LOGS="${2:-}"
        ;;
esac

# ============================================================================
# Validation
# ============================================================================

log_info "🚀 Horme POV - Local UV Development Environment"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if uv.lock exists
if [ ! -f "uv.lock" ]; then
    log_warn "uv.lock not found. Generating from pyproject.toml..."

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "UV not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    uv lock
    log_info "✅ uv.lock generated"
fi

# Check if .env.production exists
if [ ! -f "${ENV_FILE}" ]; then
    log_warn ".env.production not found. Creating from .env.example..."

    if [ -f ".env.example" ]; then
        cp .env.example .env.production
        log_warn "⚠️  Please update .env.production with real values!"
        log_warn "   Generate secrets: openssl rand -hex 32"
    else
        log_error ".env.example not found. Cannot proceed."
        exit 1
    fi
fi

# ============================================================================
# Execute Commands
# ============================================================================

if [ "${STOP}" = true ]; then
    log_info "Stopping all services..."
    docker-compose -f "${COMPOSE_FILE}" down
    log_info "✅ All services stopped"
    exit 0
fi

if [ -n "${LOGS}" ]; then
    log_info "Viewing logs for ${LOGS}..."
    docker-compose -f "${COMPOSE_FILE}" logs -f "${LOGS}"
    exit 0
fi

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build and start services
if [ "${REBUILD}" = true ]; then
    log_info "Rebuilding all services with UV..."
    docker-compose -f "${COMPOSE_FILE}" build --no-cache
fi

log_info "Starting services..."
docker-compose -f "${COMPOSE_FILE}" up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Check service status
log_info "Service Status:"
docker-compose -f "${COMPOSE_FILE}" ps

# ============================================================================
# Display Access URLs
# ============================================================================

cat <<EOF

✅ Services are running!

📡 Access URLs:
   API Server:     http://localhost:8000
   API Docs:       http://localhost:8000/docs
   Health Check:   http://localhost:8000/health
   WebSocket:      ws://localhost:8001
   Nexus Platform: http://localhost:8080
   PostgreSQL:     localhost:5433
   Redis:          localhost:6380

📊 Useful Commands:
   View logs:          ./scripts/local-uv-dev.sh --logs api
   Stop services:      ./scripts/local-uv-dev.sh --stop
   Rebuild:            ./scripts/local-uv-dev.sh --rebuild
   Docker stats:       docker stats
   Service shell:      docker exec -it horme-api-uv bash

📚 Next Steps:
   1. Test API: curl http://localhost:8000/health
   2. Check logs: docker-compose -f ${COMPOSE_FILE} logs -f
   3. Run tests: docker exec horme-api-uv pytest tests/

EOF

log_info "🎉 Local development environment ready!"
