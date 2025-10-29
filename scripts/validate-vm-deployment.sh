#!/bin/bash
# VM Infrastructure Validation Script
# Comprehensive validation for VM deployment with database connectivity testing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}Horme POV VM Infrastructure Validation${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""

# Global counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Logging functions
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASSED_CHECKS++)); }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; ((FAILED_CHECKS++)); }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARNING_CHECKS++)); }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_check() { echo -e "${CYAN}[CHECK]${NC} $1"; ((TOTAL_CHECKS++)); }

# 1. Docker Infrastructure Validation
echo -e "${CYAN}1. DOCKER INFRASTRUCTURE VALIDATION${NC}"
echo "=================================================="

log_check "Docker daemon status"
if docker info >/dev/null 2>&1; then
    log_success "Docker daemon is running"
else
    log_error "Docker daemon is not running"
fi

log_check "Docker Compose availability"
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    log_success "Docker Compose v1 available: $(docker-compose --version)"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    log_success "Docker Compose v2 available: $(docker compose version)"
else
    log_error "Docker Compose not found"
    COMPOSE_CMD=""
fi

log_check "Docker network configuration"
if docker network ls | grep -q "horme-isolated-network\|horme_network"; then
    log_success "Horme Docker network exists"
else
    log_warning "Horme Docker network not found - will be created during deployment"
fi

echo ""

# 2. Container Status Validation
echo -e "${CYAN}2. CONTAINER STATUS VALIDATION${NC}"
echo "============================================="

containers=("horme-postgres-vm" "horme-redis-vm" "horme-api-vm" "horme-mcp-vm" "horme-nexus-vm" "horme-frontend-vm")
required_images=("postgres:15-alpine" "redis:7-alpine" "horme-api:latest" "horme-mcp:latest" "horme-nexus:latest" "horme-frontend:latest")

for container in "${containers[@]}"; do
    log_check "Container $container status"
    if docker ps | grep -q "$container"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
        if [[ "$status" == "running" ]]; then
            log_success "Container $container is running"
        else
            log_error "Container $container exists but not running (status: $status)"
        fi
    else
        log_warning "Container $container not found"
    fi
done

echo ""

# 3. Database Connectivity Validation (Critical for VM)
echo -e "${CYAN}3. DATABASE CONNECTIVITY VALIDATION${NC}"
echo "================================================="

# Load environment variables if available
if [[ -f ".env.production" ]]; then
    source .env.production
fi

# Set defaults if not provided
POSTGRES_USER=${POSTGRES_USER:-horme_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-nexus_secure_password_2025}
POSTGRES_DB=${POSTGRES_DB:-horme_db}
POSTGRES_PORT=${POSTGRES_PORT:-5434}

log_check "PostgreSQL container health"
if docker ps | grep -q "horme-postgres"; then
    if docker exec horme-postgres-vm pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
        log_success "PostgreSQL is healthy and accepting connections"
    else
        log_error "PostgreSQL container exists but not accepting connections"
    fi
else
    log_error "PostgreSQL container not found or not running"
fi

log_check "Database connection from host"
if command -v psql >/dev/null 2>&1; then
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Direct database connection from host successful"
    else
        log_error "Cannot connect to database from host"
    fi
else
    log_warning "psql not available for host connection test"
fi

log_check "Database schema validation"
if docker exec horme-postgres-vm psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" >/dev/null 2>&1; then
    table_count=$(docker exec horme-postgres-vm psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    if [[ "$table_count" -gt 0 ]]; then
        log_success "Database schema initialized ($table_count tables found)"
    else
        log_warning "Database schema appears empty (0 tables found)"
    fi
else
    log_error "Cannot access database schema"
fi

echo ""

# 4. Redis Connectivity Validation
echo -e "${CYAN}4. REDIS CONNECTIVITY VALIDATION${NC}"
echo "============================================"

REDIS_PASSWORD=${REDIS_PASSWORD:-redis_secure_password_2025}
REDIS_PORT=${REDIS_PORT:-6381}

log_check "Redis container health"
if docker ps | grep -q "horme-redis"; then
    if docker exec horme-redis-vm redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping >/dev/null 2>&1; then
        log_success "Redis is healthy and responding to PING"
    else
        log_error "Redis container exists but not responding"
    fi
else
    log_error "Redis container not found or not running"
fi

log_check "Redis memory usage"
if docker ps | grep -q "horme-redis"; then
    memory_usage=$(docker exec horme-redis-vm redis-cli --no-auth-warning -a "$REDIS_PASSWORD" info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r\n')
    if [[ -n "$memory_usage" ]]; then
        log_success "Redis memory usage: $memory_usage"
    else
        log_warning "Cannot determine Redis memory usage"
    fi
fi

echo ""

# 5. Service Health Validation
echo -e "${CYAN}5. SERVICE HEALTH VALIDATION${NC}"
echo "========================================"

services=(
    "API:http://localhost:8002/health"
    "MCP:http://localhost:3004/health" 
    "Nexus:http://localhost:8090/health"
    "Frontend:http://localhost:3010"
)

for service in "${services[@]}"; do
    name="${service%:*}"
    url="${service#*:}"
    
    log_check "$name service health"
    
    # Wait up to 30 seconds for service to respond
    max_attempts=6
    attempt=1
    success=false
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s -S --max-time 5 "$url" >/dev/null 2>&1; then
            log_success "$name service is responding"
            success=true
            break
        else
            if [[ $attempt -eq $max_attempts ]]; then
                log_error "$name service not responding after $max_attempts attempts"
            else
                sleep 5
                ((attempt++))
            fi
        fi
    done
done

echo ""

# 6. Port Accessibility Validation
echo -e "${CYAN}6. PORT ACCESSIBILITY VALIDATION${NC}"
echo "============================================"

ports=(
    "API:8002"
    "MCP:3004"
    "Nexus:8090"
    "Frontend:3010"
    "PostgreSQL:5434"
    "Redis:6381"
)

for port_info in "${ports[@]}"; do
    name="${port_info%:*}"
    port="${port_info#*:}"
    
    log_check "$name port $port accessibility"
    
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_success "Port $port is bound and accessible"
        else
            log_error "Port $port is not accessible"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            log_success "Port $port is bound and accessible"
        else
            log_error "Port $port is not accessible"
        fi
    else
        log_warning "Cannot check port $port (no netstat/ss available)"
    fi
done

echo ""

# 7. Resource Usage Validation (VM-Specific)
echo -e "${CYAN}7. RESOURCE USAGE VALIDATION${NC}"
echo "====================================="

log_check "Memory usage assessment"
if command -v free >/dev/null 2>&1; then
    memory_info=$(free -m)
    total_memory=$(echo "$memory_info" | awk '/^Mem:/ {print $2}')
    used_memory=$(echo "$memory_info" | awk '/^Mem:/ {print $3}')
    available_memory=$(echo "$memory_info" | awk '/^Mem:/ {print $7}')
    
    memory_usage_percent=$((used_memory * 100 / total_memory))
    
    if [[ $memory_usage_percent -lt 80 ]]; then
        log_success "Memory usage: ${memory_usage_percent}% (${used_memory}MB/${total_memory}MB)"
    elif [[ $memory_usage_percent -lt 90 ]]; then
        log_warning "High memory usage: ${memory_usage_percent}% (${used_memory}MB/${total_memory}MB)"
    else
        log_error "Critical memory usage: ${memory_usage_percent}% (${used_memory}MB/${total_memory}MB)"
    fi
else
    log_warning "Cannot assess memory usage (free command not available)"
fi

log_check "Disk usage assessment"
if command -v df >/dev/null 2>&1; then
    disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    disk_available=$(df -h . | awk 'NR==2 {print $4}')
    
    if [[ $disk_usage -lt 80 ]]; then
        log_success "Disk usage: ${disk_usage}% (${disk_available} available)"
    elif [[ $disk_usage -lt 90 ]]; then
        log_warning "High disk usage: ${disk_usage}% (${disk_available} available)"
    else
        log_error "Critical disk usage: ${disk_usage}% (${disk_available} available)"
    fi
else
    log_warning "Cannot assess disk usage (df command not available)"
fi

log_check "Docker resource usage"
if docker system df >/dev/null 2>&1; then
    docker_df=$(docker system df)
    log_info "Docker resource usage:"
    echo "$docker_df" | while read -r line; do
        echo "    $line"
    done
    log_success "Docker resource information retrieved"
else
    log_warning "Cannot get Docker resource usage"
fi

echo ""

# 8. Configuration Validation
echo -e "${CYAN}8. CONFIGURATION VALIDATION${NC}"
echo "==================================="

log_check "Environment configuration"
if [[ -f ".env.production" ]]; then
    log_success ".env.production file exists"
    
    # Check critical environment variables
    required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.production; then
            log_success "Required variable $var is set"
        else
            log_error "Required variable $var is missing"
        fi
    done
else
    log_error ".env.production file not found"
fi

log_check "Docker compose configuration"
if [[ -f "docker-compose.vm-optimized.yml" ]]; then
    log_success "VM-optimized docker-compose configuration exists"
else
    log_warning "VM-optimized configuration not found, using default"
fi

echo ""

# 9. Integration Testing
echo -e "${CYAN}9. INTEGRATION TESTING${NC}"
echo "============================"

if [[ -n "$COMPOSE_CMD" ]] && docker ps | grep -q "horme-"; then
    log_check "Service interdependency validation"
    
    # Test API -> Database connection
    if curl -f -s -S --max-time 10 "http://localhost:8002/health/database" >/dev/null 2>&1; then
        log_success "API -> Database connection working"
    else
        log_error "API -> Database connection failed"
    fi
    
    # Test API -> Redis connection  
    if curl -f -s -S --max-time 10 "http://localhost:8002/health/redis" >/dev/null 2>&1; then
        log_success "API -> Redis connection working"
    else
        log_error "API -> Redis connection failed"
    fi
    
    # Test end-to-end health
    if curl -f -s -S --max-time 15 "http://localhost:8002/health/detailed" >/dev/null 2>&1; then
        log_success "End-to-end health check passed"
    else
        log_error "End-to-end health check failed"
    fi
else
    log_warning "Skipping integration tests (services not running)"
fi

echo ""

# Summary
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}VALIDATION SUMMARY${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""
echo -e "Total Checks: ${TOTAL_CHECKS}"
echo -e "${GREEN}Passed: ${PASSED_CHECKS}${NC}"
echo -e "${YELLOW}Warnings: ${WARNING_CHECKS}${NC}"
echo -e "${RED}Failed: ${FAILED_CHECKS}${NC}"
echo ""

# Calculate success rate
if [[ $TOTAL_CHECKS -gt 0 ]]; then
    success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "Success Rate: ${success_rate}%"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo -e "${GREEN}✅ VM DEPLOYMENT VALIDATION PASSED${NC}"
        echo ""
        echo -e "${CYAN}Your Horme POV system is ready for use!${NC}"
        echo ""
        echo -e "${CYAN}Access points:${NC}"
        echo -e "  🌐 Frontend: http://localhost:3010"
        echo -e "  🔗 API: http://localhost:8002"  
        echo -e "  📡 MCP Server: ws://localhost:3004"
        echo -e "  🔀 Nexus Platform: http://localhost:8090"
        echo -e "  🗄️  Database Admin: http://localhost:8091 (if admin profile enabled)"
        echo ""
        exit 0
    elif [[ $FAILED_CHECKS -le 2 ]]; then
        echo -e "${YELLOW}⚠️  VM DEPLOYMENT VALIDATION COMPLETED WITH WARNINGS${NC}"
        echo -e "${YELLOW}Some non-critical issues detected but system should be functional${NC}"
        exit 1
    else
        echo -e "${RED}❌ VM DEPLOYMENT VALIDATION FAILED${NC}"
        echo -e "${RED}Critical issues detected - please review and fix before using${NC}"
        exit 2
    fi
else
    echo -e "${RED}❌ NO VALIDATION CHECKS COMPLETED${NC}"
    exit 3
fi