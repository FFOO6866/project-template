# VM Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Horme POV platform to Virtual Machine (VM) environments with enterprise-grade security, monitoring, and operational procedures.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB free space
- **OS**: Ubuntu 20.04+ LTS, CentOS 8+, or equivalent
- **Network**: Internet connectivity for image pulls

#### Recommended Production Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ (SSD recommended)
- **OS**: Ubuntu 22.04 LTS (preferred)
- **Network**: 1Gbps+ bandwidth

### Required Software
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Curl/wget
- OpenSSL (for SSL certificate generation)

## Phase 1: VM Environment Preparation

### 1.1 Initial VM Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    vim \
    ufw \
    fail2ban \
    logwatch \
    rkhunter \
    chkrootkit
```

### 1.2 Docker Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login to refresh group membership
```

### 1.3 Security Hardening

```bash
# Clone the repository
git clone https://github.com/your-org/horme-pov.git
cd horme-pov

# Run security hardening script
sudo ./scripts/vm-security-hardening.sh

# Verify security configuration
./scripts/vm-requirements-check.sh
```

#### Manual Security Configuration

```bash
# Configure firewall rules
sudo ufw --force enable

# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application ports (adjust based on your needs)
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # API
sudo ufw allow 3002/tcp  # MCP WebSocket
sudo ufw allow 5433/tcp  # PostgreSQL (if external access needed)
sudo ufw allow 6380/tcp  # Redis (if external access needed)
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 3001/tcp  # Grafana

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Phase 2: SSL Certificate Setup

### 2.1 Generate Self-Signed Certificates (Development/Testing)

```bash
# Create SSL directory
sudo mkdir -p /opt/horme-pov/ssl

# Generate private key
sudo openssl genrsa -out /opt/horme-pov/ssl/horme.key 2048

# Generate certificate signing request
sudo openssl req -new -key /opt/horme-pov/ssl/horme.key -out /opt/horme-pov/ssl/horme.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Department/CN=your-domain.com"

# Generate self-signed certificate
sudo openssl x509 -req -days 365 -in /opt/horme-pov/ssl/horme.csr \
    -signkey /opt/horme-pov/ssl/horme.key -out /opt/horme-pov/ssl/horme.crt

# Set proper permissions
sudo chown root:root /opt/horme-pov/ssl/*
sudo chmod 600 /opt/horme-pov/ssl/horme.key
sudo chmod 644 /opt/horme-pov/ssl/horme.crt
```

### 2.2 Let's Encrypt Certificates (Production)

```bash
# Install certbot
sudo apt install -y certbot

# Generate certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to application directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/horme-pov/ssl/horme.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/horme-pov/ssl/horme.key

# Set up automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet --post-hook "docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml restart nginx"
```

## Phase 3: Application Deployment

### 3.1 Environment Configuration

```bash
# Create production environment file
cp .env.production.template .env.production

# Edit configuration (replace with your values)
nano .env.production
```

#### Essential Environment Variables

```env
# Domain Configuration
DOMAIN_NAME=your-domain.com

# Database Configuration
POSTGRES_DB=horme_production
POSTGRES_USER=horme_user
POSTGRES_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_PASSWORD=your_redis_password_here

# Application Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# SSL Configuration
SSL_CERT_PATH=/opt/horme-pov/ssl/horme.crt
SSL_KEY_PATH=/opt/horme-pov/ssl/horme.key

# Port Configuration
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
API_PORT=8000
MCP_PORT=3002
FRONTEND_PORT=3000
POSTGRES_PORT=5433
REDIS_PORT=6380
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Monitoring Configuration
GRAFANA_PASSWORD=your_grafana_admin_password
PROMETHEUS_RETENTION_DAYS=30

# Log Configuration
LOG_LEVEL=info
LOG_MAX_SIZE=100m
LOG_MAX_FILES=10

# Security Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
RATE_LIMIT_ENABLED=true
AUTH_ENABLED=true
```

### 3.2 Create Required Directories

```bash
# Create data directories
sudo mkdir -p /opt/horme-pov/data/{postgres,redis,prometheus,grafana}
sudo mkdir -p /opt/horme-pov/logs/{nginx,api,mcp,frontend,postgres,redis,prometheus,grafana}
sudo mkdir -p /opt/horme-pov/backups
sudo mkdir -p /opt/horme-pov/config

# Set proper ownership
sudo chown -R 1001:1001 /opt/horme-pov/data
sudo chown -R 1001:1001 /opt/horme-pov/logs
sudo chown -R root:root /opt/horme-pov/backups
sudo chown -R root:root /opt/horme-pov/config

# Set proper permissions
sudo chmod 755 /opt/horme-pov/data
sudo chmod 755 /opt/horme-pov/logs
sudo chmod 700 /opt/horme-pov/backups
```

### 3.3 Deploy Production Stack

```bash
# Build and deploy production stack
./deploy-vm-production.sh

# Alternative: Manual deployment
docker-compose -f docker-compose.vm-production.yml build --no-cache
docker-compose -f docker-compose.vm-production.yml up -d

# Verify deployment
docker-compose -f docker-compose.vm-production.yml ps
```

### 3.4 Database Initialization

```bash
# Wait for database to be ready
sleep 30

# Run database migrations (if applicable)
docker-compose -f docker-compose.vm-production.yml exec api python manage.py migrate

# Create initial admin user (if applicable)
docker-compose -f docker-compose.vm-production.yml exec api python manage.py createsuperuser

# Verify database connection
docker-compose -f docker-compose.vm-production.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\l"
```

## Phase 4: Validation and Testing

### 4.1 Health Checks

```bash
# Run comprehensive health check
./scripts/validate-vm-deployment.sh

# Manual health checks
curl -k https://your-domain.com/health
curl -k https://your-domain.com/api/health
```

#### Expected Health Check Results

```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "mcp": "healthy"
  },
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 4.2 Security Validation

```bash
# SSL/TLS validation
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Security headers check
curl -I https://your-domain.com

# Firewall status
sudo ufw status verbose

# Fail2ban status
sudo fail2ban-client status
```

### 4.3 Performance Testing

```bash
# Simple load test
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/api/health

# Resource usage monitoring
docker stats

# System resource check
htop
df -h
free -h
```

### 4.4 Monitoring Validation

```bash
# Access monitoring dashboards
echo "Prometheus: http://your-domain.com:9090"
echo "Grafana: http://your-domain.com:3001 (admin/your_grafana_password)"

# Check metrics collection
curl http://your-domain.com:9090/api/v1/targets
```

## Phase 5: Backup and Recovery Setup

### 5.1 Database Backup Configuration

```bash
# Create backup script
sudo tee /opt/horme-pov/scripts/backup-database.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/horme-pov/backups/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

# Source environment variables
source /opt/horme-pov/.env.production

# Create database backup
docker exec horme-postgres pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_DIR/database_$(date +%H%M%S).sql

# Compress backup
gzip $BACKUP_DIR/database_*.sql

# Remove backups older than 30 days
find /opt/horme-pov/backups -type d -mtime +30 -exec rm -rf {} +

echo "Database backup completed: $BACKUP_DIR"
EOF

# Make script executable
sudo chmod +x /opt/horme-pov/scripts/backup-database.sh

# Set up automated backups (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/horme-pov/scripts/backup-database.sh") | crontab -
```

### 5.2 Volume Backup Configuration

```bash
# Create volume backup script
sudo tee /opt/horme-pov/scripts/backup-volumes.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/horme-pov/backups/volumes/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

# Backup data volumes
tar -czf $BACKUP_DIR/data_volumes_$(date +%H%M%S).tar.gz /opt/horme-pov/data

# Backup configuration
tar -czf $BACKUP_DIR/config_$(date +%H%M%S).tar.gz /opt/horme-pov/config

# Remove old volume backups (keep 7 days)
find /opt/horme-pov/backups/volumes -type d -mtime +7 -exec rm -rf {} +

echo "Volume backup completed: $BACKUP_DIR"
EOF

# Make script executable
sudo chmod +x /opt/horme-pov/scripts/backup-volumes.sh

# Set up automated volume backups (daily at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/horme-pov/scripts/backup-volumes.sh") | crontab -
```

### 5.3 Disaster Recovery Procedures

```bash
# Create disaster recovery script
sudo tee /opt/horme-pov/scripts/disaster-recovery.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting disaster recovery procedure..."

# Stop application services
docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml stop api mcp frontend

# Find latest database backup
LATEST_DB_BACKUP=$(find /opt/horme-pov/backups -name "*.sql.gz" | sort -r | head -n 1)

if [ -z "$LATEST_DB_BACKUP" ]; then
    echo "ERROR: No database backup found!"
    exit 1
fi

echo "Restoring database from: $LATEST_DB_BACKUP"

# Restore database
gunzip -c $LATEST_DB_BACKUP | docker exec -i horme-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Restart services
docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml up -d

# Wait for services to be ready
sleep 60

# Verify system health
/opt/horme-pov/scripts/validate-vm-deployment.sh

echo "Disaster recovery completed!"
EOF

# Make script executable
sudo chmod +x /opt/horme-pov/scripts/disaster-recovery.sh
```

## Phase 6: Monitoring and Alerting

### 6.1 Grafana Dashboard Setup

```bash
# Import Horme POV dashboard
curl -X POST \
  http://admin:${GRAFANA_PASSWORD}@your-domain.com:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/dashboards/horme-overview.json
```

### 6.2 Alert Configuration

```bash
# Configure Prometheus alerting rules
sudo tee /opt/horme-pov/monitoring/prometheus/alerts.yml << 'EOF'
groups:
  - name: horme.rules
    rules:
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 80% for more than 5 minutes"

      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "Service {{ $labels.instance }} has been down for more than 2 minutes"

      - alert: DatabaseConnectionsFull
        expr: pg_stat_activity_count / pg_settings_max_connections * 100 > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL connection pool nearly exhausted"
          description: "More than 90% of PostgreSQL connections are in use"
EOF
```

### 6.3 Log Management

```bash
# Configure log rotation
sudo tee /etc/logrotate.d/horme-pov << 'EOF'
/opt/horme-pov/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 1001 1001
    postrotate
        docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml restart nginx api mcp
    endscript
}
EOF

# Set up centralized logging (optional)
# Configure rsyslog to forward logs to external log management system
```

## Phase 7: Maintenance Procedures

### 7.1 Regular Updates

```bash
# Create update script
sudo tee /opt/horme-pov/scripts/system-update.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting system maintenance..."

# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml pull

# Restart services with new images
docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml up -d

# Clean up unused Docker resources
docker system prune -f

# Verify system health
/opt/horme-pov/scripts/validate-vm-deployment.sh

echo "System maintenance completed!"
EOF

# Make script executable
sudo chmod +x /opt/horme-pov/scripts/system-update.sh

# Schedule monthly updates (first Sunday of each month at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 1-7 * 0 /opt/horme-pov/scripts/system-update.sh") | crontab -
```

### 7.2 Security Auditing

```bash
# Create security audit script
sudo tee /opt/horme-pov/scripts/security-audit.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting security audit..."

# Update security tools
apt update
apt install --only-upgrade rkhunter chkrootkit

# Run rootkit scanner
rkhunter --check --sk

# Run chkrootkit
chkrootkit

# Check for failed login attempts
grep "Failed password" /var/log/auth.log | tail -20

# Check fail2ban status
fail2ban-client status

# Check for security updates
apt list --upgradable | grep -i security

# Scan for vulnerable containers
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL horme-api:latest

echo "Security audit completed!"
EOF

# Make script executable
sudo chmod +x /opt/horme-pov/scripts/security-audit.sh

# Schedule weekly security audits (Sundays at 1 AM)
(crontab -l 2>/dev/null; echo "0 1 * * 0 /opt/horme-pov/scripts/security-audit.sh") | crontab -
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Services Won't Start

```bash
# Check Docker daemon status
sudo systemctl status docker

# Check container logs
docker-compose -f docker-compose.vm-production.yml logs [service_name]

# Check available disk space
df -h

# Check memory usage
free -h

# Restart Docker daemon if needed
sudo systemctl restart docker
```

#### 2. SSL/TLS Certificate Issues

```bash
# Verify certificate validity
openssl x509 -in /opt/horme-pov/ssl/horme.crt -text -noout

# Check certificate expiration
openssl x509 -in /opt/horme-pov/ssl/horme.crt -noout -dates

# Regenerate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/horme-pov/ssl/horme.key \
  -out /opt/horme-pov/ssl/horme.crt \
  -subj "/CN=your-domain.com"
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL container status
docker-compose -f docker-compose.vm-production.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.vm-production.yml logs postgres

# Connect to database manually
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check connection settings
grep -E "(DATABASE_URL|POSTGRES)" .env.production
```

#### 4. High Resource Usage

```bash
# Check container resource usage
docker stats --no-stream

# Check system resource usage
htop
iotop
nethogs

# Optimize Docker resources
docker system prune -a
docker volume prune
```

#### 5. Network Connectivity Issues

```bash
# Check firewall status
sudo ufw status verbose

# Check port availability
netstat -tlnp | grep -E "(80|443|3000|8000|3002|5433|6380)"

# Test internal container communication
docker-compose -f docker-compose.vm-production.yml exec api ping postgres
docker-compose -f docker-compose.vm-production.yml exec api ping redis
```

### Emergency Recovery Procedures

#### Complete System Recovery

```bash
# 1. Stop all services
docker-compose -f docker-compose.vm-production.yml down

# 2. Backup current state
sudo cp -r /opt/horme-pov/data /opt/horme-pov/data.backup.$(date +%Y%m%d)

# 3. Run disaster recovery
sudo /opt/horme-pov/scripts/disaster-recovery.sh

# 4. Verify system health
/opt/horme-pov/scripts/validate-vm-deployment.sh
```

#### Rollback Deployment

```bash
# Pull previous version from git
git checkout [previous_commit_hash]

# Rebuild and redeploy
docker-compose -f docker-compose.vm-production.yml build --no-cache
docker-compose -f docker-compose.vm-production.yml up -d

# Verify rollback
/opt/horme-pov/scripts/validate-vm-deployment.sh
```

## Security Checklist

### Pre-Deployment Security Validation

- [ ] VM OS hardened and updated
- [ ] Firewall configured with minimal necessary ports
- [ ] SSL certificates generated and properly configured
- [ ] Strong passwords set for all services
- [ ] Non-root users configured for all containers
- [ ] Security monitoring tools installed and configured
- [ ] Backup procedures tested and validated
- [ ] Access controls properly configured
- [ ] Security headers validated in web responses
- [ ] Container vulnerability scanning completed

### Post-Deployment Security Monitoring

- [ ] Regular security audits scheduled
- [ ] Log monitoring and alerting configured
- [ ] Intrusion detection system active
- [ ] Automated security updates enabled
- [ ] Access log monitoring implemented
- [ ] Certificate expiration monitoring setup
- [ ] Security incident response procedures documented
- [ ] Backup integrity verification scheduled

## Performance Optimization

### Resource Optimization

```bash
# Optimize Docker daemon settings
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

sudo systemctl restart docker
```

### Database Performance Tuning

```bash
# PostgreSQL configuration optimization
sudo tee /opt/horme-pov/config/postgresql.conf << 'EOF'
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 2
max_parallel_workers = 8
max_parallel_maintenance_workers = 2
EOF
```

### Monitoring Performance Metrics

- CPU utilization per container
- Memory usage and swap activity
- Disk I/O and space utilization
- Network throughput and latency
- Application response times
- Database query performance
- SSL handshake performance

## Conclusion

This deployment guide provides a comprehensive approach to deploying the Horme POV platform in VM environments with enterprise-grade security, monitoring, and operational procedures. Regular maintenance, monitoring, and security auditing are essential for maintaining a robust production environment.

For additional support or questions, refer to:
- [ADR-006: VM Production Readiness](docs/adr/ADR-006-vm-production-readiness.md)
- [Operations Runbook](docs/VM_OPERATIONS_RUNBOOK.md)
- [Testing Strategy](docs/VM_TESTING_STRATEGY.md)

Remember to customize configuration values, domain names, and security settings according to your specific environment requirements.