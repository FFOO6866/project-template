# ADR-005: Monitoring and Observability Strategy

## Status
Accepted

## Context
The Horme POV production system requires comprehensive monitoring and observability to ensure system reliability, performance optimization, and rapid issue resolution. The system must provide insights across application performance, infrastructure health, business metrics, and user experience.

### Requirements
- Real-time system health monitoring
- Application performance metrics (APM)
- Business metrics and KPI tracking
- Log aggregation and analysis
- Alerting and incident response
- Performance optimization insights
- Security event monitoring

## Decision
We implement a comprehensive monitoring and observability stack using Prometheus, Grafana, and structured logging with business metrics integration.

### Monitoring Architecture
```yaml
# Monitoring stack configuration
version: '3.8'
services:
  # Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  # Visualization and Dashboards  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_COOKIE_SECURE=true
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro

  # Alerting
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
```

## Metrics Collection Strategy

### Infrastructure Metrics
```yaml
# prometheus.yml - Infrastructure monitoring
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Application metrics
  - job_name: 'horme-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  # Database metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  # Container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

### Application Metrics
```python
# Python application metrics implementation
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import psutil

# Business Metrics
QUOTATIONS_CREATED = Counter('quotations_created_total', 'Total quotations created', ['status'])
RFP_PROCESSING_TIME = Histogram('rfp_processing_seconds', 'RFP processing duration')
ACTIVE_USERS = Gauge('active_users_current', 'Current active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')

# System Metrics
CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'System memory usage in bytes')
DISK_USAGE = Gauge('system_disk_usage_percent', 'System disk usage percentage')

class MetricsCollector:
    def __init__(self):
        self.start_http_server(8001)  # Metrics endpoint
        
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        CPU_USAGE.set(psutil.cpu_percent(interval=1))
        MEMORY_USAGE.set(psutil.virtual_memory().used)
        DISK_USAGE.set(psutil.disk_usage('/').percent)
        
    def record_business_event(self, event_type: str, **labels):
        """Record business-specific events"""
        if event_type == 'quotation_created':
            QUOTATIONS_CREATED.labels(**labels).inc()
        elif event_type == 'rfp_processed':
            RFP_PROCESSING_TIME.observe(labels.get('duration', 0))

# Middleware for automatic metric collection
@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record request metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response
```

## Dashboard Configuration

### System Health Dashboard
```json
{
  "dashboard": {
    "title": "Horme System Health",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])",
            "legendFormat": "Average Response Time"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec - {{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"4..|5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### Business Metrics Dashboard
```json
{
  "dashboard": {
    "title": "Horme Business Metrics",
    "panels": [
      {
        "title": "Quotations Created",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(quotations_created_total[1h])",
            "legendFormat": "Last Hour"
          }
        ]
      },
      {
        "title": "RFP Processing Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rfp_processing_seconds_bucket[5m]))",
            "legendFormat": "95th Percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(rfp_processing_seconds_bucket[5m]))",
            "legendFormat": "50th Percentile"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "active_users_current",
            "legendFormat": "Current Active Users"
          }
        ]
      }
    ]
  }
}
```

## Alerting Configuration

### Alert Rules
```yaml
# monitoring/rules/horme-alerts.yml
groups:
  - name: horme-system-alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"
          
      # High response time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
          
      # Database connection issues
      - alert: DatabaseConnectionHigh
        expr: database_connections_active > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
          description: "Database connections: {{ $value }}"
          
      # System resource alerts
      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
          
      - alert: HighMemoryUsage
        expr: system_memory_usage_bytes / (1024^3) > 3.5  # 3.5GB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}GB"
```

### AlertManager Configuration
```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@horme.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      
    - match:
        severity: warning  
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://api:8000/webhooks/alerts'
        
  - name: 'critical-alerts'
    email_configs:
      - to: 'ops-team@horme.local'
        subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
    webhook_configs:
      - url: 'http://api:8000/webhooks/critical-alerts'
        
  - name: 'warning-alerts'
    email_configs:
      - to: 'dev-team@horme.local'
        subject: 'Warning: {{ .GroupLabels.alertname }}'
```

## Logging Strategy

### Structured Logging
```python
# Structured logging implementation
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        
        # Configure structured handler
        handler = logging.StreamHandler()
        handler.setFormatter(self.StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'service': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add extra fields if present
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            if hasattr(record, 'request_id'):
                log_entry['request_id'] = record.request_id
            if hasattr(record, 'business_event'):
                log_entry['business_event'] = record.business_event
                
            return json.dumps(log_entry)
    
    def log_business_event(self, event_type: str, **kwargs):
        """Log business-specific events with structured data"""
        extra = {'business_event': {'type': event_type, 'data': kwargs}}
        self.logger.info(f"Business event: {event_type}", extra=extra)

# Usage in application
logger = StructuredLogger('horme-api')

@app.middleware('http')
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log request start
    logger.logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={'request_id': request_id, 'method': request.method, 'path': request.url.path}
    )
    
    response = await call_next(request)
    
    # Log request completion
    duration = time.time() - start_time
    logger.logger.info(
        f"Request completed: {response.status_code}",
        extra={
            'request_id': request_id,
            'status_code': response.status_code,
            'duration': duration
        }
    )
    
    return response
```

## Performance Monitoring

### Application Performance Monitoring
```python
# APM integration
import time
from functools import wraps

def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record success metrics
                duration = time.time() - start_time
                OPERATION_DURATION.labels(
                    operation=operation_name,
                    status='success'
                ).observe(duration)
                
                logger.log_business_event('operation_completed', 
                    operation=operation_name,
                    duration=duration,
                    status='success'
                )
                
                return result
                
            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                OPERATION_DURATION.labels(
                    operation=operation_name,
                    status='error'
                ).observe(duration)
                
                logger.logger.error(f"Operation failed: {operation_name}",
                    extra={'operation': operation_name, 'error': str(e), 'duration': duration}
                )
                
                raise
                
        return wrapper
    return decorator

# Usage
@monitor_performance('rfp_analysis')
async def analyze_rfp(rfp_content: str) -> dict:
    # RFP analysis logic
    pass

@monitor_performance('quotation_generation')
async def generate_quotation(requirements: dict) -> dict:
    # Quotation generation logic
    pass
```

## Consequences

### Positive
- **Proactive Issue Detection**: Alerts before user impact
- **Performance Optimization**: Data-driven performance improvements  
- **Business Insights**: Real-time business metrics and KPIs
- **Incident Response**: Faster issue resolution with detailed metrics
- **Capacity Planning**: Resource usage trends for scaling decisions
- **Compliance**: Audit trails and security event monitoring

### Negative
- **Resource Overhead**: Monitoring infrastructure requires resources
- **Complexity**: Additional systems to maintain and troubleshoot
- **Data Volume**: Large amounts of metrics and logs to manage
- **Alert Fatigue**: Risk of too many alerts reducing effectiveness
- **Storage Costs**: Long-term metrics retention requires storage

## Alternatives Considered

### Option 1: SaaS Monitoring (DataDog, New Relic)
- **Description**: Use external SaaS monitoring platform
- **Pros**: Managed service, advanced features, minimal setup
- **Cons**: Vendor lock-in, ongoing costs, data privacy concerns
- **Why Rejected**: Cost and data control requirements

### Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Description**: Use ELK stack for logging and monitoring
- **Pros**: Powerful search, log analysis, visualization
- **Cons**: Resource intensive, complex setup, maintenance overhead
- **Why Rejected**: Higher resource requirements than Prometheus/Grafana

### Option 3: Minimal Monitoring (Basic Health Checks)
- **Description**: Only basic uptime monitoring
- **Pros**: Simple, minimal resource usage
- **Cons**: Limited insights, reactive instead of proactive
- **Why Rejected**: Insufficient for production system requirements

## Implementation Plan

### Phase 1: Core Monitoring (Complete)
1. Deploy Prometheus and Grafana stack
2. Implement basic application metrics
3. Create system health dashboards
4. Set up basic alerting rules

### Phase 2: Business Metrics (Complete)
1. Implement business-specific metrics collection
2. Create business metrics dashboards
3. Add structured logging with business events
4. Set up business metric alerts

### Phase 3: Advanced Observability (Complete)
1. Implement distributed tracing
2. Add performance profiling
3. Create advanced alerting rules
4. Implement automated incident response

## Validation Criteria
- [ ] Prometheus collecting metrics from all services
- [ ] Grafana dashboards operational with system and business metrics
- [ ] Alerting rules functional with appropriate thresholds
- [ ] Structured logging implemented across all services
- [ ] Performance monitoring providing actionable insights
- [ ] Business metrics tracking key KPIs
- [ ] Incident response procedures tested and functional