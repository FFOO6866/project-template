#!/bin/bash
# VM Infrastructure Monitoring Script
# Continuous monitoring for VM deployment with alerting capabilities

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MONITOR_INTERVAL=${MONITOR_INTERVAL:-30}  # seconds
ALERT_THRESHOLD=${ALERT_THRESHOLD:-3}     # consecutive failures before alert
LOG_FILE=${LOG_FILE:-"./logs/vm-monitor.log"}
EMAIL_ALERTS=${EMAIL_ALERTS:-false}
WEBHOOK_URL=${WEBHOOK_URL:-""}

# State tracking
declare -A failure_counts
declare -A last_status
declare -A alert_sent

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() { 
    echo -e "${GREEN}[OK]${NC} $1"
    log_with_timestamp "[OK] $1"
}

log_error() { 
    echo -e "${RED}[ERROR]${NC} $1"
    log_with_timestamp "[ERROR] $1"
}

log_warning() { 
    echo -e "${YELLOW}[WARN]${NC} $1"
    log_with_timestamp "[WARN] $1"
}

log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1"
    log_with_timestamp "[INFO] $1"
}

# Alert functions
send_alert() {
    local service="$1"
    local message="$2"
    local severity="$3"
    
    log_error "ALERT: $service - $message"
    
    # Webhook alert
    if [[ -n "$WEBHOOK_URL" ]]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 Horme VM Alert [$severity]: $service - $message\"}" \
            >/dev/null 2>&1 || true
    fi
    
    # Email alert (if configured)
    if [[ "$EMAIL_ALERTS" == "true" ]] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Horme VM Alert: $service" "$EMAIL_RECIPIENT" || true
    fi
    
    alert_sent["$service"]=true
}

send_recovery_alert() {
    local service="$1"
    local message="$2"
    
    log_success "RECOVERY: $service - $message"
    
    # Webhook recovery notification
    if [[ -n "$WEBHOOK_URL" ]]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"✅ Horme VM Recovery: $service - $message\"}" \
            >/dev/null 2>&1 || true
    fi
    
    alert_sent["$service"]=false
}

# Service check functions
check_container_health() {
    local container="$1"
    
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
        local running_status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        
        if [[ "$running_status" != "running" ]]; then
            return 1
        elif [[ "$health_status" == "healthy" ]] || [[ "$health_status" == "no-health-check" ]]; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

check_service_endpoint() {
    local service="$1"
    local url="$2"
    local timeout="${3:-5}"
    
    if curl -f -s -S --max-time "$timeout" "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_database_connectivity() {
    # Load environment variables
    if [[ -f ".env.production" ]]; then
        source .env.production
    fi
    
    local user="${POSTGRES_USER:-horme_user}"
    local password="${POSTGRES_PASSWORD:-nexus_secure_password_2025}"
    local db="${POSTGRES_DB:-horme_db}"
    
    if docker exec horme-postgres-vm pg_isready -U "$user" >/dev/null 2>&1; then
        # Test actual connection with a simple query
        if docker exec horme-postgres-vm psql -U "$user" -d "$db" -c "SELECT 1;" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

check_redis_connectivity() {
    # Load environment variables
    if [[ -f ".env.production" ]]; then
        source .env.production
    fi
    
    local password="${REDIS_PASSWORD:-redis_secure_password_2025}"
    
    if docker exec horme-redis-vm redis-cli --no-auth-warning -a "$password" ping >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Resource monitoring
check_system_resources() {
    local memory_threshold=85  # 85%
    local disk_threshold=85    # 85%
    
    # Memory check
    if command -v free >/dev/null 2>&1; then
        local memory_usage=$(free | awk '/^Mem:/ {printf("%.0f", $3/$2*100)}')
        if [[ $memory_usage -ge $memory_threshold ]]; then
            return 1
        fi
    fi
    
    # Disk check
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df . | awk 'NR==2 {print substr($5,1,length($5)-1)}')
        if [[ $disk_usage -ge $disk_threshold ]]; then
            return 1
        fi
    fi
    
    return 0
}

# Network monitoring
check_network_connectivity() {
    # Check Docker network
    if ! docker network ls | grep -q "horme"; then
        return 1
    fi
    
    # Check inter-container communication
    if docker ps | grep -q "horme-api-vm"; then
        if ! docker exec horme-api-vm ping -c 1 postgres >/dev/null 2>&1; then
            return 1
        fi
        
        if ! docker exec horme-api-vm ping -c 1 redis >/dev/null 2>&1; then
            return 1
        fi
    fi
    
    return 0
}

# Performance monitoring
collect_performance_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local metrics_file="./logs/vm-metrics.log"
    
    # System metrics
    if command -v free >/dev/null 2>&1; then
        local memory_info=$(free -m | awk '/^Mem:/ {printf "memory_total=%d memory_used=%d memory_available=%d", $2, $3, $7}')
    fi
    
    if command -v df >/dev/null 2>&1; then
        local disk_info=$(df -h . | awk 'NR==2 {printf "disk_total=%s disk_used=%s disk_available=%s disk_usage=%s", $2, $3, $4, $5}')
    fi
    
    # Docker metrics
    local running_containers=$(docker ps --format "{{.Names}}" | grep "horme-" | wc -l)
    
    # Database metrics (if available)
    local db_connections=""
    if [[ -f ".env.production" ]]; then
        source .env.production
        local user="${POSTGRES_USER:-horme_user}"
        local db="${POSTGRES_DB:-horme_db}"
        
        if check_database_connectivity; then
            db_connections=$(docker exec horme-postgres-vm psql -U "$user" -d "$db" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tr -d ' ' || echo "0")
        fi
    fi
    
    # Write metrics to log
    echo "$timestamp containers_running=$running_containers db_active_connections=${db_connections:-0} $memory_info $disk_info" >> "$metrics_file"
}

# Update service status and handle alerting
update_service_status() {
    local service="$1"
    local current_status="$2"  # 0 = healthy, 1 = unhealthy
    
    local previous_status="${last_status[$service]:-0}"
    last_status["$service"]=$current_status
    
    if [[ $current_status -eq 0 ]]; then
        # Service is healthy
        failure_counts["$service"]=0
        
        # Send recovery alert if we previously sent an alert
        if [[ "${alert_sent[$service]}" == "true" ]]; then
            send_recovery_alert "$service" "Service has recovered and is now healthy"
        fi
    else
        # Service is unhealthy
        local failures=${failure_counts["$service"]:-0}
        ((failures++))
        failure_counts["$service"]=$failures
        
        # Send alert if we've reached the threshold and haven't already sent one
        if [[ $failures -ge $ALERT_THRESHOLD ]] && [[ "${alert_sent[$service]}" != "true" ]]; then
            send_alert "$service" "Service has failed $failures consecutive health checks" "HIGH"
        fi
    fi
}

# Main monitoring loop
monitor_services() {
    local iteration=0
    
    log_info "Starting VM infrastructure monitoring (interval: ${MONITOR_INTERVAL}s)"
    log_info "Alert threshold: $ALERT_THRESHOLD consecutive failures"
    log_info "Monitoring log: $LOG_FILE"
    
    while true; do
        ((iteration++))
        echo ""
        echo -e "${CYAN}===============================================${NC}"
        echo -e "${CYAN}VM Infrastructure Check #$iteration$(NC}"
        echo -e "${CYAN}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo -e "${CYAN}===============================================${NC}"
        
        # Container health checks
        services=(
            "horme-postgres-vm:Database"
            "horme-redis-vm:Redis"
            "horme-api-vm:API"
            "horme-mcp-vm:MCP"
            "horme-nexus-vm:Nexus"
            "horme-frontend-vm:Frontend"
        )
        
        for service_info in "${services[@]}"; do
            container="${service_info%:*}"
            name="${service_info#*:}"
            
            if check_container_health "$container"; then
                log_success "$name container is healthy"
                update_service_status "$name" 0
            else
                log_error "$name container is unhealthy"
                update_service_status "$name" 1
            fi
        done
        
        # Database connectivity check
        if check_database_connectivity; then
            log_success "Database connectivity verified"
            update_service_status "DatabaseConnectivity" 0
        else
            log_error "Database connectivity failed"
            update_service_status "DatabaseConnectivity" 1
        fi
        
        # Redis connectivity check
        if check_redis_connectivity; then
            log_success "Redis connectivity verified"
            update_service_status "RedisConnectivity" 0
        else
            log_error "Redis connectivity failed"
            update_service_status "RedisConnectivity" 1
        fi
        
        # Service endpoint checks
        endpoints=(
            "API:http://localhost:8002/health"
            "MCP:http://localhost:3004/health"
            "Nexus:http://localhost:8090/health"
            "Frontend:http://localhost:3010"
        )
        
        for endpoint_info in "${endpoints[@]}"; do
            service="${endpoint_info%:*}"
            url="${endpoint_info#*:}"
            
            if check_service_endpoint "$service" "$url"; then
                log_success "$service endpoint is responding"
                update_service_status "${service}Endpoint" 0
            else
                log_error "$service endpoint is not responding"
                update_service_status "${service}Endpoint" 1
            fi
        done
        
        # System resource check
        if check_system_resources; then
            log_success "System resources are within normal limits"
            update_service_status "SystemResources" 0
        else
            log_warning "System resources are at high utilization"
            update_service_status "SystemResources" 1
        fi
        
        # Network connectivity check
        if check_network_connectivity; then
            log_success "Network connectivity is healthy"
            update_service_status "NetworkConnectivity" 0
        else
            log_error "Network connectivity issues detected"
            update_service_status "NetworkConnectivity" 1
        fi
        
        # Collect performance metrics
        collect_performance_metrics
        
        # Summary
        local healthy_services=0
        local total_services=${#last_status[@]}
        for status in "${last_status[@]}"; do
            if [[ $status -eq 0 ]]; then
                ((healthy_services++))
            fi
        done
        
        if [[ $total_services -gt 0 ]]; then
            local health_percentage=$((healthy_services * 100 / total_services))
            echo ""
            echo -e "${CYAN}Health Summary: $healthy_services/$total_services services healthy (${health_percentage}%)${NC}"
        fi
        
        # Wait for next iteration
        sleep "$MONITOR_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log_info "Monitoring stopped by user"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Usage information
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --interval SECONDS    Monitoring interval (default: 30)"
    echo "  -t, --threshold COUNT     Alert threshold (default: 3)"
    echo "  -l, --log-file PATH       Log file path (default: ./logs/vm-monitor.log)"
    echo "  -w, --webhook URL         Webhook URL for alerts"
    echo "  -e, --email               Enable email alerts"
    echo "  -h, --help                Show this help"
    echo ""
    echo "Environment variables:"
    echo "  MONITOR_INTERVAL          Monitoring interval in seconds"
    echo "  ALERT_THRESHOLD          Consecutive failures before alert"
    echo "  LOG_FILE                 Path to log file"
    echo "  WEBHOOK_URL             Webhook URL for alerts"
    echo "  EMAIL_ALERTS            Enable email alerts (true/false)"
    echo "  EMAIL_RECIPIENT         Email address for alerts"
    echo ""
    echo "Examples:"
    echo "  $0                                      # Start monitoring with defaults"
    echo "  $0 -i 60 -t 5                         # 60s interval, 5 failure threshold"
    echo "  $0 -w https://hooks.slack.com/...     # With Slack webhook"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        -t|--threshold)
            ALERT_THRESHOLD="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -w|--webhook)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL_ALERTS=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Validate numeric parameters
if ! [[ "$MONITOR_INTERVAL" =~ ^[0-9]+$ ]] || [[ $MONITOR_INTERVAL -lt 10 ]]; then
    echo "Error: Monitor interval must be a number >= 10"
    exit 1
fi

if ! [[ "$ALERT_THRESHOLD" =~ ^[0-9]+$ ]] || [[ $ALERT_THRESHOLD -lt 1 ]]; then
    echo "Error: Alert threshold must be a positive number"
    exit 1
fi

# Start monitoring
monitor_services