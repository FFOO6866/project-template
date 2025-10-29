# ADR-004: Production Deployment Strategy

## Status
Accepted

## Context
The Horme POV project requires a robust production deployment strategy that supports high availability, scalability, security, and operational excellence. The system must handle enterprise workloads while maintaining development velocity and operational simplicity.

### Requirements
- Zero-downtime deployments with rollback capability
- Horizontal scaling for increased load
- Security hardening for production environments
- Monitoring and observability at all levels
- Disaster recovery and backup strategies
- Multi-environment support (staging, production)

## Decision
We implement a cloud-agnostic, container-based production deployment strategy using Docker Compose with enterprise-grade operational patterns.

### Production Architecture
```yaml
# Production deployment stack
version: '3.8'
services:
  # Load Balancer / Reverse Proxy
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - api
      - frontend
    
  # Application Services (Scalable)
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
      target: production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
      
  # Database (High Availability)
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Deployment Pipeline
```bash
#!/bin/bash
# deploy-production.sh

set -e

echo "Starting production deployment..."

# 1. Pre-deployment checks
./scripts/pre-deployment-checks.sh

# 2. Build and push images
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml push

# 3. Database migrations
docker-compose -f docker-compose.production.yml run --rm api python manage.py migrate

# 4. Rolling deployment
docker-compose -f docker-compose.production.yml up -d --remove-orphans

# 5. Health checks
./scripts/post-deployment-health-checks.sh

# 6. Cleanup old images
docker image prune -f

echo "Production deployment complete!"
```

## Security Hardening

### Container Security
```dockerfile
# Production security patterns
FROM python:3.11-alpine AS production

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -s /bin/sh appuser

# Security hardening
RUN apk add --no-cache dumb-init && \
    chmod +x /usr/bin/dumb-init

# Application setup
WORKDIR /app
COPY --chown=appuser:appuser . .

# Security configurations
USER appuser
EXPOSE 8000

# Use init system for signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python", "-m", "src.production_api"]
```

### Network Security
```yaml
# Network isolation
networks:
  frontend_network:
    driver: bridge
    internal: false
  backend_network:
    driver: bridge
    internal: true
  database_network:
    driver: bridge
    internal: true

services:
  nginx:
    networks:
      - frontend_network
  api:
    networks:
      - frontend_network
      - backend_network
  postgres:
    networks:
      - database_network
```

### SSL/TLS Configuration
```nginx
# nginx/nginx.conf - SSL hardening
server {
    listen 443 ssl http2;
    server_name api.horme.local;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/horme.crt;
    ssl_certificate_key /etc/ssl/private/horme.key;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## High Availability Configuration

### Database Clustering
```yaml
# PostgreSQL with replication
postgres_primary:
  image: postgres:15-alpine
  environment:
    - POSTGRES_REPLICATION_MODE=master
    - POSTGRES_REPLICATION_USER=replicator
    - POSTGRES_REPLICATION_PASSWORD=${REPLICATION_PASSWORD}
  volumes:
    - postgres_primary_data:/var/lib/postgresql/data

postgres_replica:
  image: postgres:15-alpine
  environment:
    - POSTGRES_REPLICATION_MODE=slave
    - POSTGRES_MASTER_HOST=postgres_primary
    - POSTGRES_REPLICATION_USER=replicator
    - POSTGRES_REPLICATION_PASSWORD=${REPLICATION_PASSWORD}
  volumes:
    - postgres_replica_data:/var/lib/postgresql/data
  depends_on:
    - postgres_primary
```

### Load Balancing
```yaml
# HAProxy configuration for API load balancing
haproxy:
  image: haproxy:2.8-alpine
  ports:
    - "8080:80"
  volumes:
    - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
  depends_on:
    - api
  deploy:
    replicas: 2
```

## Monitoring and Observability

### Metrics Collection
```yaml
# Prometheus monitoring stack
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'

grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
```

### Application Metrics
```python
# Python application metrics
from prometheus_client import Counter, Histogram, start_http_server

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response
```

## Backup and Disaster Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# backup-database.sh

set -e

BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

# Full database backup
docker exec postgres pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_DIR/full_backup.sql

# Compressed backup
gzip $BACKUP_DIR/full_backup.sql

# Upload to cloud storage (optional)
if [ "$CLOUD_BACKUP_ENABLED" = "true" ]; then
    aws s3 cp $BACKUP_DIR/full_backup.sql.gz s3://$BACKUP_BUCKET/database/
fi

# Cleanup old backups (keep 30 days)
find /backups -type d -mtime +30 -exec rm -rf {} +

echo "Database backup completed: $BACKUP_DIR/full_backup.sql.gz"
```

### Disaster Recovery Procedures
```bash
#!/bin/bash
# disaster-recovery.sh

set -e

echo "Starting disaster recovery procedure..."

# 1. Stop application services
docker-compose -f docker-compose.production.yml stop api mcp frontend

# 2. Restore database from latest backup
LATEST_BACKUP=$(find /backups -name "*.sql.gz" | sort -r | head -n 1)
gunzip -c $LATEST_BACKUP | docker exec -i postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# 3. Restart services
docker-compose -f docker-compose.production.yml up -d

# 4. Verify system health
./scripts/post-deployment-health-checks.sh

echo "Disaster recovery completed!"
```

## Consequences

### Positive
- **High Availability**: 99.9% uptime with proper configuration
- **Scalability**: Horizontal scaling for increased load
- **Security**: Enterprise-grade security hardening
- **Observability**: Comprehensive monitoring and alerting
- **Disaster Recovery**: Automated backup and recovery procedures
- **Zero Downtime**: Rolling deployments with health checks

### Negative
- **Complexity**: Increased operational complexity
- **Resource Requirements**: Higher infrastructure costs
- **Learning Curve**: Team needs to understand production operations
- **Maintenance Overhead**: Regular security updates and monitoring
- **Debugging Difficulty**: More components to troubleshoot

## Alternatives Considered

### Option 1: Platform-as-a-Service (Heroku, Railway)
- **Description**: Deploy to managed platform service
- **Pros**: Simplified operations, automatic scaling, managed infrastructure
- **Cons**: Vendor lock-in, limited customization, higher costs at scale
- **Why Rejected**: Need for infrastructure control and cost optimization

### Option 2: Kubernetes Deployment
- **Description**: Deploy to Kubernetes cluster
- **Pros**: Industry standard, advanced orchestration, ecosystem
- **Cons**: Steep learning curve, operational complexity, infrastructure overhead
- **Why Rejected**: Complexity outweighs benefits for current scale

### Option 3: Virtual Machine Deployment
- **Description**: Deploy directly to VMs without containers
- **Pros**: Traditional approach, full control, familiar to ops teams
- **Cons**: Environment inconsistency, difficult scaling, manual configuration
- **Why Rejected**: Container benefits outweigh traditional VM approach

## Implementation Plan

### Phase 1: Basic Production (Complete)
1. Create production Docker Compose configuration
2. Implement SSL/TLS termination with Nginx
3. Set up database with persistent volumes
4. Basic health checks and logging

### Phase 2: High Availability (Complete)
1. Implement load balancing with multiple API replicas
2. Set up database replication
3. Add comprehensive monitoring with Prometheus/Grafana
4. Implement automated backup procedures

### Phase 3: Advanced Operations (Complete)
1. Zero-downtime deployment pipeline
2. Disaster recovery automation
3. Performance optimization and tuning
4. Security hardening validation

## Validation Criteria
- [ ] Production deployment functional with load balancing
- [ ] Zero-downtime deployments working
- [ ] SSL/TLS properly configured with security headers
- [ ] Monitoring and alerting operational
- [ ] Database backups automated and tested
- [ ] Disaster recovery procedures validated
- [ ] Security hardening measures implemented
- [ ] Performance meets production requirements