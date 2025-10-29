#!/bin/bash

# Production MCP Server Deployment Script
# Deploys containerized MCP server with full production features

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.mcp-production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Production MCP Server Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    deploy      Deploy the production MCP server stack
    update      Update running services with zero downtime
    rollback    Rollback to previous version
    stop        Stop all services gracefully
    restart     Restart all services
    status      Show status of all services
    logs        Show logs from all services
    health      Check health of all services
    backup      Create backup of persistent data
    restore     Restore from backup
    cleanup     Clean up unused containers and volumes

Options:
    -h, --help              Show this help message
    -e, --env-file FILE     Use custom environment file (default: .env.production)
    -f, --compose-file FILE Use custom compose file
    --no-backup            Skip backup during update/rollback
    --force                Force operation without confirmation
    --verbose              Enable verbose logging
    --dry-run              Show what would be done without executing

Examples:
    $0 deploy                    # Deploy production stack
    $0 update --no-backup        # Update without backup
    $0 rollback                  # Rollback to previous version
    $0 health                    # Check all service health
    $0 logs mcp-server-1         # Show logs for specific service

EOF
}

# Parse command line arguments
COMMAND=""
ENV_FILE_OVERRIDE=""
COMPOSE_FILE_OVERRIDE=""
NO_BACKUP=false
FORCE=false
VERBOSE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env-file)
            ENV_FILE_OVERRIDE="$2"
            shift 2
            ;;
        -f|--compose-file)
            COMPOSE_FILE_OVERRIDE="$2"
            shift 2
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$COMMAND" ]]; then
                COMMAND="$1"
            else
                # Additional arguments for commands like logs
                EXTRA_ARGS="$*"
                break
            fi
            shift
            ;;
    esac
done

# Use overrides if provided
if [[ -n "$ENV_FILE_OVERRIDE" ]]; then
    ENV_FILE="$ENV_FILE_OVERRIDE"
fi

if [[ -n "$COMPOSE_FILE_OVERRIDE" ]]; then
    COMPOSE_FILE="$COMPOSE_FILE_OVERRIDE"
fi

# Verbose logging
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Environment file not found: $ENV_FILE"
        log_info "Creating default environment file..."
        create_default_env_file
    fi
    
    log_success "Prerequisites check passed"
}

# Create default environment file
create_default_env_file() {
    cat > "$ENV_FILE" << EOF
# Production MCP Server Environment Configuration
# SECURITY: Change all default passwords and secrets!

# Database
POSTGRES_PASSWORD=secure-password-change-in-production
POSTGRES_REPLICATION_PASSWORD=replication-password-change-in-production

# Message Queue
RABBITMQ_USER=mcpuser
RABBITMQ_PASSWORD=secure-rabbitmq-password-change-in-production

# MCP Server
MCP_JWT_SECRET=your-production-jwt-secret-change-this-$(openssl rand -hex 32)

# Monitoring
GRAFANA_PASSWORD=admin-change-in-production

# Project
COMPOSE_PROJECT_NAME=mcp-production

# Scaling
MCP_SERVER_REPLICAS=2
POSTGRES_REPLICA_COUNT=1
REDIS_REPLICA_COUNT=1
EOF
    
    log_warning "Default environment file created at: $ENV_FILE"
    log_warning "IMPORTANT: Review and update all passwords and secrets before deployment!"
}

# Wait for service to be healthy
wait_for_service() {
    local service="$1"
    local timeout="${2:-300}"  # Default 5 minutes
    local interval="${3:-10}"   # Default 10 seconds
    
    log_info "Waiting for service '$service' to be healthy..."
    
    local elapsed=0
    while [[ $elapsed -lt $timeout ]]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "healthy"; then
            log_success "Service '$service' is healthy"
            return 0
        fi
        
        log_info "Waiting for '$service'... (${elapsed}s/${timeout}s)"
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    
    log_error "Service '$service' did not become healthy within ${timeout} seconds"
    return 1
}

# Create backup
create_backup() {
    if [[ "$NO_BACKUP" == "true" ]]; then
        log_info "Skipping backup (--no-backup specified)"
        return 0
    fi
    
    local backup_dir="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    log_info "Creating backup in: $backup_dir"
    
    # Backup PostgreSQL
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps postgres-primary | grep -q "running"; then
        log_info "Backing up PostgreSQL database..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres-primary pg_dumpall -U mcpuser > "$backup_dir/postgres_backup.sql"
    fi
    
    # Backup Redis
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps redis-master | grep -q "running"; then
        log_info "Backing up Redis data..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis-master redis-cli BGSAVE
        sleep 5
        docker cp "$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps -q redis-master):/data/dump.rdb" "$backup_dir/redis_backup.rdb"
    fi
    
    # Backup application data
    log_info "Backing up application data..."
    docker run --rm -v "$(docker volume ls -q | grep mcp_server_1_data)":/source -v "$backup_dir":/backup alpine tar czf /backup/mcp_server_1_data.tar.gz -C /source .
    docker run --rm -v "$(docker volume ls -q | grep mcp_server_2_data)":/source -v "$backup_dir":/backup alpine tar czf /backup/mcp_server_2_data.tar.gz -C /source .
    
    log_success "Backup created successfully: $backup_dir"
    echo "$backup_dir" > "${PROJECT_ROOT}/.last_backup"
}

# Deploy command
cmd_deploy() {
    log_info "Deploying production MCP server stack..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would execute: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d"
        return 0
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Build custom images
    log_info "Building MCP server image..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres-primary redis-master rabbitmq
    
    # Wait for infrastructure to be ready
    wait_for_service "postgres-primary" 120
    wait_for_service "redis-master" 60
    wait_for_service "rabbitmq" 120
    
    # Start remaining services
    log_info "Starting all services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for MCP servers to be ready
    wait_for_service "mcp-server-1" 180
    wait_for_service "mcp-server-2" 180
    
    log_success "Production MCP server stack deployed successfully!"
    
    # Show status
    cmd_status
    
    # Show access information
    log_info "Access Information:"
    echo "  MCP Server (Load Balanced): http://localhost"
    echo "  HAProxy Stats: http://localhost:8404/stats"
    echo "  Grafana Dashboard: http://localhost:3000 (admin/admin)"
    echo "  Prometheus: http://localhost:9090"
    echo "  Jaeger Tracing: http://localhost:16686"
    echo "  RabbitMQ Management: http://localhost:15672"
}

# Update command with zero downtime
cmd_update() {
    log_info "Updating production MCP server stack with zero downtime..."
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "This will update the production stack. Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Update cancelled"
            exit 0
        fi
    fi
    
    # Create backup
    create_backup
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would perform rolling update"
        return 0
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Build custom images
    log_info "Building updated MCP server image..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
    
    # Rolling update strategy for MCP servers
    log_info "Performing rolling update of MCP servers..."
    
    # Update server 2 first
    log_info "Updating mcp-server-2..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps mcp-server-2
    wait_for_service "mcp-server-2" 180
    
    # Update server 1
    log_info "Updating mcp-server-1..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps mcp-server-1
    wait_for_service "mcp-server-1" 180
    
    # Update other services
    log_info "Updating supporting services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    log_success "Zero-downtime update completed successfully!"
    cmd_status
}

# Rollback command
cmd_rollback() {
    log_info "Rolling back production MCP server stack..."
    
    if [[ ! -f "${PROJECT_ROOT}/.last_backup" ]]; then
        log_error "No backup information found. Cannot rollback."
        exit 1
    fi
    
    local backup_dir
    backup_dir=$(cat "${PROJECT_ROOT}/.last_backup")
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "This will rollback to backup from $backup_dir. Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback from: $backup_dir"
        return 0
    fi
    
    # Stop services
    log_info "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # Restore data
    log_info "Restoring data from backup..."
    
    # Restore PostgreSQL
    if [[ -f "$backup_dir/postgres_backup.sql" ]]; then
        log_info "Restoring PostgreSQL database..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres-primary
        wait_for_service "postgres-primary" 120
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres-primary psql -U mcpuser -d postgres < "$backup_dir/postgres_backup.sql"
    fi
    
    # Restore Redis
    if [[ -f "$backup_dir/redis_backup.rdb" ]]; then
        log_info "Restoring Redis data..."
        # Stop redis to restore data
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop redis-master
        docker cp "$backup_dir/redis_backup.rdb" "$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps -q redis-master):/data/dump.rdb"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" start redis-master
    fi
    
    # Restore application data
    if [[ -f "$backup_dir/mcp_server_1_data.tar.gz" ]]; then
        log_info "Restoring application data..."
        docker run --rm -v "$(docker volume ls -q | grep mcp_server_1_data)":/target -v "$backup_dir":/backup alpine tar xzf /backup/mcp_server_1_data.tar.gz -C /target
        docker run --rm -v "$(docker volume ls -q | grep mcp_server_2_data)":/target -v "$backup_dir":/backup alpine tar xzf /backup/mcp_server_2_data.tar.gz -C /target
    fi
    
    # Start all services
    log_info "Starting all services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    log_success "Rollback completed successfully!"
    cmd_status
}

# Status command
cmd_status() {
    log_info "Production MCP server stack status:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    echo
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Health command
cmd_health() {
    log_info "Checking health of all services..."
    
    local unhealthy_services=()
    
    # Check each service
    while IFS= read -r service; do
        if [[ -n "$service" ]]; then
            local health_status
            health_status=$(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" --format "{{.Status}}")
            
            if [[ "$health_status" == *"healthy"* ]]; then
                log_success "$service: healthy"
            elif [[ "$health_status" == *"unhealthy"* ]]; then
                log_error "$service: unhealthy"
                unhealthy_services+=("$service")
            else
                log_warning "$service: $health_status"
            fi
        fi
    done < <(docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config --services)
    
    if [[ ${#unhealthy_services[@]} -gt 0 ]]; then
        log_error "Unhealthy services detected: ${unhealthy_services[*]}"
        return 1
    else
        log_success "All services are healthy!"
        return 0
    fi
}

# Logs command
cmd_logs() {
    local service="${EXTRA_ARGS:-}"
    if [[ -n "$service" ]]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$service"
    else
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
    fi
}

# Stop command
cmd_stop() {
    log_info "Stopping production MCP server stack..."
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "This will stop all production services. Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stop cancelled"
            exit 0
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would stop all services"
        return 0
    fi
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    log_success "All services stopped"
}

# Restart command
cmd_restart() {
    log_info "Restarting production MCP server stack..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would restart all services"
        return 0
    fi
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
    log_success "All services restarted"
    cmd_status
}

# Cleanup command
cmd_cleanup() {
    log_info "Cleaning up unused containers and volumes..."
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "This will remove unused containers, networks, and volumes. Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cleanup cancelled"
            exit 0
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would clean up unused resources"
        return 0
    fi
    
    # Clean up Docker resources
    docker system prune -f
    docker volume prune -f
    
    # Clean up old backup files (keep last 10)
    if [[ -d "${PROJECT_ROOT}/backups" ]]; then
        log_info "Cleaning up old backup files..."
        ls -1dt "${PROJECT_ROOT}/backups/"*/ | tail -n +11 | xargs -r rm -rf
    fi
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    # Check if command is provided
    if [[ -z "$COMMAND" ]]; then
        log_error "No command specified"
        show_help
        exit 1
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Execute command
    case "$COMMAND" in
        deploy)
            cmd_deploy
            ;;
        update)
            cmd_update
            ;;
        rollback)
            cmd_rollback
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs
            ;;
        health)
            cmd_health
            ;;
        backup)
            create_backup
            ;;
        cleanup)
            cmd_cleanup
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"