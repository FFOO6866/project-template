#!/bin/bash

# ==============================================================================
# Deployment Script - Dynamic Job Pricing Engine
# ==============================================================================
# Usage: ./scripts/deploy.sh [local|server]
# ==============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env_file() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env file not found!"
        log_info "Please copy .env.example to .env and fill in the values"
        exit 1
    fi

    # Check critical variables
    if ! grep -q "OPENAI_API_KEY=sk-" "$PROJECT_DIR/.env"; then
        log_error "OPENAI_API_KEY not set in .env!"
        exit 1
    fi

    log_info "✓ .env file found and valid"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found! Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found! Please install Docker Compose first."
        exit 1
    fi

    log_info "✓ Docker and Docker Compose found"
}

deploy_local() {
    log_info "================================================"
    log_info "Deploying to LOCAL environment"
    log_info "================================================"

    cd "$PROJECT_DIR"

    # Check prerequisites
    check_env_file
    check_docker

    # Verify environment is set to development
    ENV_VAR=$(grep "^ENVIRONMENT=" .env | cut -d '=' -f2)
    if [ "$ENV_VAR" != "development" ]; then
        log_warning "ENVIRONMENT is set to '$ENV_VAR' but should be 'development' for local"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_info "Stopping existing containers..."
    docker-compose down

    log_info "Building and starting services..."
    docker-compose up -d --build

    log_info "Waiting for services to be healthy..."
    sleep 10

    log_info "Checking service status..."
    docker-compose ps

    log_info "Running health check..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "✓ API is healthy!"
    else
        log_error "✗ API health check failed!"
        log_info "Check logs with: docker-compose logs -f api"
        exit 1
    fi

    log_info "================================================"
    log_info "✓ LOCAL deployment complete!"
    log_info "================================================"
    log_info "API: http://localhost:8000"
    log_info "Docs: http://localhost:8000/docs"
    log_info "Logs: docker-compose logs -f"
}

deploy_server() {
    log_info "================================================"
    log_info "Deploying to SERVER environment"
    log_info "================================================"

    cd "$PROJECT_DIR"

    # Check prerequisites
    check_env_file

    # Read server details from .env
    SERVER_IP=$(grep "^SERVER_IP=" .env | cut -d '=' -f2)
    SERVER_USER=$(grep "^SERVER_USER=" .env | cut -d '=' -f2)
    PEM_KEY_PATH=$(grep "^PEM_KEY_PATH=" .env | cut -d '=' -f2)

    # Expand ~ to home directory
    PEM_KEY_PATH="${PEM_KEY_PATH/#\~/$HOME}"

    if [ -z "$SERVER_IP" ] || [ "$SERVER_IP" = "your_server_ip_here" ]; then
        log_error "SERVER_IP not set in .env!"
        exit 1
    fi

    if [ ! -f "$PEM_KEY_PATH" ]; then
        log_error "PEM key file not found at: $PEM_KEY_PATH"
        exit 1
    fi

    log_info "Server: $SERVER_USER@$SERVER_IP"
    log_info "PEM Key: $PEM_KEY_PATH"

    # Step 1: Push to Git
    log_info "Step 1: Pushing to Git..."
    git add .
    git status

    read -p "Commit and push changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " COMMIT_MSG
        git commit -m "$COMMIT_MSG" || log_warning "No changes to commit"
        git push origin main
        log_info "✓ Pushed to Git"
    else
        log_warning "Skipping git push. Make sure code is up to date on server!"
    fi

    # Step 2: Deploy to server
    log_info "Step 2: Deploying to server..."

    ssh -i "$PEM_KEY_PATH" "$SERVER_USER@$SERVER_IP" <<'ENDSSH'
        set -e

        echo "[INFO] Navigating to project directory..."
        cd ~/job-pricing-engine || { echo "[ERROR] Project directory not found!"; exit 1; }

        echo "[INFO] Pulling latest changes from Git..."
        git pull origin main

        echo "[INFO] Checking .env file..."
        if [ ! -f .env ]; then
            echo "[ERROR] .env file not found on server!"
            echo "[INFO] Please copy .env from local machine first:"
            echo "  scp -i ~/.ssh/your-key.pem .env ubuntu@<SERVER_IP>:~/job-pricing-engine/"
            exit 1
        fi

        # Verify ENVIRONMENT is production
        ENV_VAR=$(grep "^ENVIRONMENT=" .env | cut -d '=' -f2)
        if [ "$ENV_VAR" != "production" ]; then
            echo "[WARNING] ENVIRONMENT is '$ENV_VAR', should be 'production'"
        fi

        # Verify OPENAI_API_KEY is set
        if ! grep -q "OPENAI_API_KEY=sk-" .env; then
            echo "[ERROR] OPENAI_API_KEY not set in .env!"
            exit 1
        fi

        echo "[INFO] Stopping existing containers..."
        docker-compose down

        echo "[INFO] Building and starting services..."
        docker-compose up -d --build

        echo "[INFO] Waiting for services to start..."
        sleep 15

        echo "[INFO] Checking service status..."
        docker-compose ps

        echo "[INFO] Verifying environment variables in container..."
        docker-compose exec -T api python -c "
import os
print('ENVIRONMENT:', os.getenv('ENVIRONMENT'))
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
print('DATABASE_URL:', 'SET' if os.getenv('DATABASE_URL') else 'NOT SET')
"

        echo "[INFO] Running database migrations..."
        docker-compose exec -T api python -m alembic upgrade head || echo "[WARNING] Migrations failed or not configured yet"

        echo "[INFO] Server deployment complete!"
ENDSSH

    log_info "================================================"
    log_info "✓ SERVER deployment complete!"
    log_info "================================================"
    log_info "SSH to server: ssh -i $PEM_KEY_PATH $SERVER_USER@$SERVER_IP"
    log_info "Check logs: docker-compose logs -f"
}

show_usage() {
    echo "Usage: $0 [local|server]"
    echo ""
    echo "Commands:"
    echo "  local   - Deploy to local development environment"
    echo "  server  - Deploy to production server"
    echo ""
    echo "Examples:"
    echo "  $0 local"
    echo "  $0 server"
}

# Main script
if [ $# -eq 0 ]; then
    log_error "No deployment target specified!"
    show_usage
    exit 1
fi

case "$1" in
    local)
        deploy_local
        ;;
    server)
        deploy_server
        ;;
    *)
        log_error "Invalid deployment target: $1"
        show_usage
        exit 1
        ;;
esac
