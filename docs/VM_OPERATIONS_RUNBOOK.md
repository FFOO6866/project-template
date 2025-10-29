# VM Operations Runbook

## Overview

This operations runbook provides comprehensive procedures for managing the Horme POV platform in Virtual Machine (VM) production environments. It covers day-to-day operations, monitoring, incident response, maintenance procedures, and emergency recovery.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Daily Operations](#daily-operations)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Incident Response](#incident-response)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Backup and Recovery](#backup-and-recovery)
7. [Security Operations](#security-operations)
8. [Performance Management](#performance-management)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Emergency Procedures](#emergency-procedures)

## System Architecture Overview

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Horme POV VM Stack                   │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  Nginx (Reverse Proxy & SSL)       │
│  Port: 3000          │  Ports: 80, 443                    │
├─────────────────────────────────────────────────────────────┤
│  API Service         │  MCP Server                         │
│  Port: 8000         │  Port: 3002                         │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL          │  Redis                              │
│  Port: 5433         │  Port: 6380                         │
├─────────────────────────────────────────────────────────────┤
│  Prometheus          │  Grafana                            │
│  Port: 9090         │  Port: 3001                         │
└─────────────────────────────────────────────────────────────┘
```

### Key File Locations

```
/opt/horme-pov/
├── docker-compose.vm-production.yml    # Main orchestration file
├── .env.production                     # Environment configuration
├── data/                              # Persistent data volumes
│   ├── postgres/                      # Database data
│   ├── redis/                        # Redis data
│   ├── prometheus/                   # Metrics data
│   └── grafana/                      # Dashboard data
├── logs/                             # Application logs
│   ├── nginx/                        # Web server logs
│   ├── api/                         # API service logs
│   ├── mcp/                         # MCP server logs
│   └── postgres/                    # Database logs
├── backups/                          # Backup storage
├── ssl/                             # SSL certificates
├── config/                          # Configuration files
└── scripts/                         # Operational scripts
    ├── health-check-vm.sh           # Health monitoring
    ├── backup-database-vm.sh        # Database backup
    ├── disaster-recovery.sh         # Recovery procedures
    └── system-update.sh            # Update procedures
```

## Daily Operations

### Morning Health Check Routine

```bash
#!/bin/bash
# Daily morning health check routine

echo "🌅 Starting daily health check routine..."
echo "Date: $(date)"
echo "=========================================="

# 1. Check overall system health
echo "1. System Health Check:"
./scripts/health-check-vm.sh

# 2. Check service status
echo "2. Service Status:"
docker-compose -f docker-compose.vm-production.yml ps

# 3. Check resource usage
echo "3. Resource Usage:"
echo "Memory:"
free -h
echo "Disk:"
df -h | grep -E "(/$|/opt)"
echo "CPU Load:"
uptime

# 4. Check recent errors in logs
echo "4. Recent Errors (last 24 hours):"
find /opt/horme-pov/logs -name "*.log" -mtime -1 -exec grep -l "ERROR\|CRITICAL\|FATAL" {} \; | head -5

# 5. Check backup status
echo "5. Backup Status:"
ls -la /opt/horme-pov/backups/ | tail -3

# 6. Check SSL certificate expiry
echo "6. SSL Certificate Status:"
openssl x509 -in /opt/horme-pov/ssl/horme.crt -noout -dates | grep "notAfter"

# 7. Check security status
echo "7. Security Status:"
sudo fail2ban-client status
sudo ufw status | head -5

echo "=========================================="
echo "✅ Daily health check completed at $(date)"
```

### Service Status Monitoring

#### Check Service Health
```bash
# Quick service health check
curl -f https://your-domain.com/health
curl -f https://your-domain.com/api/health

# WebSocket health check
echo "Testing WebSocket connection..." | websocat ws://your-domain.com/ws --exit-on-eof

# Database connectivity check
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

#### Monitor Resource Usage
```bash
# Container resource usage
docker stats --no-stream

# System resource usage
htop -n 1
iostat -x 1 3
netstat -i
```

### Log Management

#### Daily Log Review
```bash
#!/bin/bash
# Daily log review script

LOG_DIR="/opt/horme-pov/logs"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

echo "📋 Daily Log Summary for $YESTERDAY"
echo "=================================="

# Check for errors across all services
for service in nginx api mcp frontend postgres redis; do
    if [ -d "$LOG_DIR/$service" ]; then
        echo "Service: $service"
        error_count=$(grep -c "ERROR\|CRITICAL\|FATAL" $LOG_DIR/$service/*.log 2>/dev/null || echo "0")
        warn_count=$(grep -c "WARN" $LOG_DIR/$service/*.log 2>/dev/null || echo "0")
        echo "  Errors: $error_count, Warnings: $warn_count"
        
        # Show recent critical errors
        if [ "$error_count" -gt 0 ]; then
            echo "  Recent errors:"
            grep "ERROR\|CRITICAL\|FATAL" $LOG_DIR/$service/*.log 2>/dev/null | tail -3 | sed 's/^/    /'
        fi
        echo ""
    fi
done

# Check log file sizes
echo "Log File Sizes:"
du -sh $LOG_DIR/*/ 2>/dev/null | sort -hr
```

## Monitoring and Alerting

### Prometheus Monitoring Setup

#### Key Metrics to Monitor
```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: system.rules
    rules:
      # System resource alerts
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}% for more than 5 minutes"

      - alert: HighCPUUsage
        expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}% for more than 10 minutes"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 20
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk space is {{ $value }}% full"

  - name: application.rules
    rules:
      # Application service alerts
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "Service has been down for more than 2 minutes"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time for {{ $labels.instance }}"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count / pg_settings_max_connections * 100 > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL connection pool nearly exhausted"
          description: "{{ $value }}% of connections are in use"

  - name: security.rules
    rules:
      # Security alerts
      - alert: FailedLoginAttempts
        expr: increase(failed_login_attempts[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High number of failed login attempts"
          description: "{{ $value }} failed login attempts in the last 5 minutes"

      - alert: SSLCertificateExpiring
        expr: ssl_certificate_expiry_days < 30
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate expires in {{ $value }} days"
```

### Grafana Dashboard Configuration

#### System Overview Dashboard
```json
{
  "dashboard": {
    "title": "Horme POV System Overview",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"horme-api\"}",
            "legendFormat": "API"
          },
          {
            "expr": "up{job=\"horme-mcp\"}",
            "legendFormat": "MCP"
          },
          {
            "expr": "up{job=\"postgres\"}",
            "legendFormat": "Database"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "http_request_duration_seconds{quantile=\"0.95\"}",
            "legendFormat": "95th Percentile"
          },
          {
            "expr": "http_request_duration_seconds{quantile=\"0.50\"}",
            "legendFormat": "Median"
          }
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)",
            "legendFormat": "Memory %"
          },
          {
            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU %"
          }
        ]
      }
    ]
  }
}
```

### Alert Notification Setup

```bash
# Setup email notifications via SMTP
cat > /opt/horme-pov/monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'smtp.your-email.com:587'
  smtp_from: 'alerts@your-domain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'ops-team@your-domain.com'
    subject: 'Horme POV Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF
```

## Incident Response

### Incident Response Process

#### Severity Levels
- **Critical (P1)**: Complete service outage, data loss, security breach
- **High (P2)**: Major functionality impaired, performance severely degraded
- **Medium (P3)**: Minor functionality issues, moderate performance impact
- **Low (P4)**: Cosmetic issues, minimal impact

#### Incident Response Workflow
```
1. Detection → 2. Assessment → 3. Response → 4. Resolution → 5. Post-Mortem
```

### Critical Incident Response (P1)

#### Service Outage Response
```bash
#!/bin/bash
# Critical incident response for service outage

echo "🚨 CRITICAL INCIDENT: Service Outage Response"
echo "Incident started at: $(date)"

# 1. Immediate assessment
echo "1. Checking service status..."
docker-compose -f docker-compose.vm-production.yml ps

# 2. Check system resources
echo "2. System resource check..."
free -h
df -h
uptime

# 3. Check recent logs for errors
echo "3. Recent error analysis..."
find /opt/horme-pov/logs -name "*.log" -mtime -0.1 -exec grep -l "ERROR\|CRITICAL\|FATAL" {} \;

# 4. Attempt service recovery
echo "4. Attempting service recovery..."
docker-compose -f docker-compose.vm-production.yml restart

# 5. Wait and verify recovery
echo "5. Verifying service recovery..."
sleep 30
curl -f https://your-domain.com/health

# 6. Document incident
echo "6. Documenting incident..."
echo "Incident: Service Outage" >> /opt/horme-pov/incidents.log
echo "Time: $(date)" >> /opt/horme-pov/incidents.log
echo "Resolution: Service restart" >> /opt/horme-pov/incidents.log
echo "---" >> /opt/horme-pov/incidents.log

echo "✅ Critical incident response completed at: $(date)"
```

#### Database Emergency Response
```bash
#!/bin/bash
# Database emergency response

echo "🚨 DATABASE EMERGENCY RESPONSE"

# 1. Check database status
echo "1. Database status check..."
docker-compose -f docker-compose.vm-production.yml exec postgres pg_isready -U $POSTGRES_USER -d $POSTGRES_DB

# 2. Check database connections
echo "2. Active connections check..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Check for locks
echo "3. Lock analysis..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM pg_locks WHERE NOT granted;"

# 4. Emergency backup
echo "4. Emergency backup creation..."
./scripts/backup-database-vm.sh

# 5. If database is corrupted, initiate recovery
if ! docker-compose -f docker-compose.vm-production.yml exec postgres pg_isready; then
    echo "5. Database recovery required - initiating disaster recovery..."
    ./scripts/disaster-recovery.sh
fi
```

### Security Incident Response

#### Security Breach Response
```bash
#!/bin/bash
# Security incident response

echo "🔒 SECURITY INCIDENT RESPONSE"
echo "Security incident started at: $(date)"

# 1. Immediate containment
echo "1. Immediate containment..."
# Block suspicious IPs (example)
sudo ufw deny from 192.168.1.100
sudo fail2ban-client set sshd banip 192.168.1.100

# 2. Collect evidence
echo "2. Evidence collection..."
# Capture current system state
ps aux > /opt/horme-pov/security/incident-$(date +%s)-processes.log
netstat -tulpn > /opt/horme-pov/security/incident-$(date +%s)-network.log
last -n 50 > /opt/horme-pov/security/incident-$(date +%s)-logins.log

# 3. Analyze logs for attack patterns
echo "3. Log analysis..."
grep -E "(ATTACK|BREACH|UNAUTHORIZED)" /opt/horme-pov/logs/*/*.log > /opt/horme-pov/security/incident-$(date +%s)-attacks.log

# 4. Change critical passwords (if needed)
echo "4. Security hardening..."
# This would involve rotating JWT secrets, database passwords, etc.

# 5. Notify security team
echo "5. Security team notification..."
echo "Security incident detected at $(date)" | mail -s "SECURITY ALERT: Horme POV" security-team@your-domain.com
```

## Maintenance Procedures

### Scheduled Maintenance

#### Weekly Maintenance Routine
```bash
#!/bin/bash
# Weekly maintenance routine (Sundays at 2 AM)

echo "🔧 Weekly Maintenance Routine"
echo "Started at: $(date)"

# 1. System updates
echo "1. System package updates..."
sudo apt update && sudo apt upgrade -y

# 2. Docker cleanup
echo "2. Docker cleanup..."
docker system prune -f
docker volume prune -f

# 3. Log rotation
echo "3. Log rotation..."
sudo logrotate -f /etc/logrotate.d/horme-pov

# 4. Database maintenance
echo "4. Database maintenance..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# 5. SSL certificate check
echo "5. SSL certificate validation..."
openssl x509 -in /opt/horme-pov/ssl/horme.crt -noout -checkend $((30*24*3600)) || \
  echo "WARNING: SSL certificate expires within 30 days"

# 6. Security scan
echo "6. Security scan..."
./scripts/security-audit.sh

# 7. Performance baseline check
echo "7. Performance check..."
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/api/health

echo "✅ Weekly maintenance completed at: $(date)"
```

#### Monthly Maintenance Routine
```bash
#!/bin/bash
# Monthly maintenance routine (First Sunday of month)

echo "🗓️ Monthly Maintenance Routine"
echo "Started at: $(date)"

# 1. Full system backup
echo "1. Full system backup..."
./scripts/backup-volumes.sh
./scripts/backup-database-vm.sh

# 2. Update Docker images
echo "2. Docker image updates..."
docker-compose -f docker-compose.vm-production.yml pull
docker-compose -f docker-compose.vm-production.yml up -d

# 3. Database optimization
echo "3. Database optimization..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "REINDEX DATABASE $POSTGRES_DB;"

# 4. Certificate renewal (if using Let's Encrypt)
echo "4. Certificate renewal..."
sudo certbot renew --post-hook "docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml restart nginx"

# 5. Comprehensive health check
echo "5. Comprehensive health check..."
./scripts/validate-vm-deployment.sh

# 6. Performance benchmark
echo "6. Performance benchmarking..."
# Run performance tests and compare with baselines

echo "✅ Monthly maintenance completed at: $(date)"
```

### Emergency Maintenance

#### Hotfix Deployment
```bash
#!/bin/bash
# Emergency hotfix deployment procedure

echo "🚀 Emergency Hotfix Deployment"
echo "Deployment started at: $(date)"

# 1. Create backup before deployment
echo "1. Pre-deployment backup..."
./scripts/backup-database-vm.sh

# 2. Pull latest changes
echo "2. Pulling hotfix..."
git fetch origin
git checkout main
git pull origin main

# 3. Build and deploy with zero downtime
echo "3. Zero-downtime deployment..."
# Build new images
docker-compose -f docker-compose.vm-production.yml build

# Rolling restart
for service in api mcp frontend; do
    echo "Restarting $service..."
    docker-compose -f docker-compose.vm-production.yml up -d --no-deps $service
    sleep 30
    
    # Health check
    curl -f https://your-domain.com/health || {
        echo "Health check failed for $service"
        # Rollback if needed
        exit 1
    }
done

# 4. Post-deployment validation
echo "4. Post-deployment validation..."
./scripts/validate-vm-deployment.sh

echo "✅ Emergency hotfix deployment completed at: $(date)"
```

## Backup and Recovery

### Backup Strategy

#### Automated Daily Backup
```bash
#!/bin/bash
# Automated daily backup script (runs at 2 AM daily)
# /opt/horme-pov/scripts/daily-backup.sh

set -e

BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/opt/horme-pov/backups/$BACKUP_DATE"
mkdir -p $BACKUP_DIR

echo "📦 Starting daily backup for $BACKUP_DATE"

# 1. Database backup
echo "1. Database backup..."
docker-compose -f /opt/horme-pov/docker-compose.vm-production.yml exec postgres \
  pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > $BACKUP_DIR/database.sql.gz

# 2. Configuration backup
echo "2. Configuration backup..."
tar -czf $BACKUP_DIR/config.tar.gz \
  /opt/horme-pov/.env.production \
  /opt/horme-pov/ssl/ \
  /opt/horme-pov/config/

# 3. Application data backup
echo "3. Application data backup..."
tar -czf $BACKUP_DIR/data.tar.gz /opt/horme-pov/data/

# 4. Verify backup integrity
echo "4. Backup verification..."
gzip -t $BACKUP_DIR/database.sql.gz
tar -tzf $BACKUP_DIR/config.tar.gz > /dev/null
tar -tzf $BACKUP_DIR/data.tar.gz > /dev/null

# 5. Upload to cloud storage (if configured)
if [ "$CLOUD_BACKUP_ENABLED" = "true" ]; then
    echo "5. Cloud backup upload..."
    # Example for AWS S3
    aws s3 sync $BACKUP_DIR s3://$BACKUP_BUCKET/$BACKUP_DATE/
fi

# 6. Cleanup old backups (keep 30 days)
echo "6. Cleanup old backups..."
find /opt/horme-pov/backups -type d -mtime +30 -exec rm -rf {} +

echo "✅ Daily backup completed: $BACKUP_DIR"
```

### Recovery Procedures

#### Database Recovery
```bash
#!/bin/bash
# Database recovery procedure

echo "🔄 Database Recovery Procedure"

# 1. Stop application services
echo "1. Stopping application services..."
docker-compose -f docker-compose.vm-production.yml stop api mcp frontend

# 2. Select backup to restore
echo "2. Available backups:"
find /opt/horme-pov/backups -name "database.sql.gz" | sort -r | head -5

read -p "Enter full path to backup file: " BACKUP_FILE

# 3. Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found!"
    exit 1
fi

# 4. Create current database backup before restore
echo "4. Creating safety backup..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > /opt/horme-pov/backups/pre-restore-$(date +%s).sql.gz

# 5. Drop and recreate database
echo "5. Recreating database..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"

docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;"

# 6. Restore from backup
echo "6. Restoring database..."
gunzip -c $BACKUP_FILE | docker-compose -f docker-compose.vm-production.yml exec -T postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB

# 7. Restart services
echo "7. Restarting services..."
docker-compose -f docker-compose.vm-production.yml up -d

# 8. Wait for services and validate
echo "8. Validating recovery..."
sleep 30
./scripts/validate-vm-deployment.sh

echo "✅ Database recovery completed successfully"
```

#### Full System Recovery
```bash
#!/bin/bash
# Full system disaster recovery

echo "🆘 Full System Disaster Recovery"

# 1. System preparation
echo "1. System preparation..."
sudo systemctl stop docker
sudo umount /opt/horme-pov/data/* 2>/dev/null || true

# 2. Select recovery point
echo "2. Available recovery points:"
ls -la /opt/horme-pov/backups/

read -p "Enter backup date (YYYY-MM-DD): " BACKUP_DATE
BACKUP_DIR="/opt/horme-pov/backups/$BACKUP_DATE"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: Backup directory not found!"
    exit 1
fi

# 3. Restore configuration
echo "3. Restoring configuration..."
tar -xzf $BACKUP_DIR/config.tar.gz -C /

# 4. Restore data volumes
echo "4. Restoring data volumes..."
rm -rf /opt/horme-pov/data/*
tar -xzf $BACKUP_DIR/data.tar.gz -C /

# 5. Start Docker and services
echo "5. Starting services..."
sudo systemctl start docker
cd /opt/horme-pov
docker-compose -f docker-compose.vm-production.yml up -d

# 6. Wait for database to be ready
echo "6. Waiting for database..."
sleep 60

# 7. Restore database
echo "7. Restoring database..."
gunzip -c $BACKUP_DIR/database.sql.gz | docker-compose -f docker-compose.vm-production.yml exec -T postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB

# 8. Final validation
echo "8. System validation..."
sleep 30
./scripts/validate-vm-deployment.sh

echo "✅ Full system recovery completed"
```

## Security Operations

### Daily Security Checks

```bash
#!/bin/bash
# Daily security monitoring routine

echo "🔒 Daily Security Check"
echo "Date: $(date)"

# 1. Check failed login attempts
echo "1. Failed login attempts (last 24 hours):"
sudo journalctl --since "24 hours ago" | grep -i "failed\|invalid\|authentication failure" | wc -l

# 2. Check fail2ban status
echo "2. Fail2ban status:"
sudo fail2ban-client status

# 3. Check firewall status
echo "3. Firewall status:"
sudo ufw status numbered | head -10

# 4. Check SSL certificate expiry
echo "4. SSL certificate expires:"
openssl x509 -in /opt/horme-pov/ssl/horme.crt -noout -dates | grep notAfter

# 5. Check for suspicious processes
echo "5. Suspicious processes:"
ps aux | grep -E "(nc|netcat|wget|curl)" | grep -v grep | head -5

# 6. Check disk usage for log files
echo "6. Log disk usage:"
du -sh /opt/horme-pov/logs/* | sort -hr | head -5

# 7. Check container security
echo "7. Container security status:"
docker inspect horme-api --format='{{.HostConfig.ReadonlyRootfs}}'
docker inspect horme-api --format='{{.Config.User}}'

echo "✅ Daily security check completed"
```

### Security Incident Detection

```bash
#!/bin/bash
# Automated security incident detection

echo "🕵️ Security Incident Detection"

# 1. Check for brute force attacks
FAILED_LOGINS=$(sudo journalctl --since "1 hour ago" | grep -c "authentication failure")
if [ $FAILED_LOGINS -gt 50 ]; then
    echo "ALERT: Possible brute force attack detected ($FAILED_LOGINS failed logins)"
    # Trigger incident response
fi

# 2. Check for unusual network activity
HIGH_CONNECTIONS=$(netstat -an | grep ":443" | wc -l)
if [ $HIGH_CONNECTIONS -gt 1000 ]; then
    echo "ALERT: Unusually high number of connections ($HIGH_CONNECTIONS)"
fi

# 3. Check for file system changes in critical directories
find /opt/horme-pov/config -type f -mmin -60 | while read file; do
    echo "ALERT: Critical file modified: $file"
done

# 4. Check for new user accounts
NEW_USERS=$(awk -F: '$3 >= 1000 {print $1}' /etc/passwd | wc -l)
if [ -f /tmp/user_count ]; then
    OLD_COUNT=$(cat /tmp/user_count)
    if [ $NEW_USERS -gt $OLD_COUNT ]; then
        echo "ALERT: New user account created"
    fi
fi
echo $NEW_USERS > /tmp/user_count

# 5. Check for unauthorized sudo usage
sudo grep -i "sudo.*COMMAND" /var/log/auth.log | tail -5
```

## Performance Management

### Performance Monitoring

```bash
#!/bin/bash
# Performance monitoring and baseline validation

echo "📊 Performance Monitoring"

# 1. API response time check
echo "1. API Response Times:"
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/api/health
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/api/products

# 2. Database performance
echo "2. Database Performance:"
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
    SELECT 
      schemaname,
      tablename,
      attname,
      n_distinct,
      correlation 
    FROM pg_stats 
    WHERE schemaname = 'public' 
    ORDER BY n_distinct DESC 
    LIMIT 5;"

# 3. System performance metrics
echo "3. System Metrics:"
echo "Load Average:"
uptime

echo "Memory Usage:"
free -h

echo "Disk I/O:"
iostat -x 1 3

# 4. Container performance
echo "4. Container Performance:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# 5. Network performance
echo "5. Network Performance:"
ss -tuln | grep -E ":80|:443|:8000|:3002" | wc -l
```

### Performance Optimization

```bash
#!/bin/bash
# Performance optimization procedures

echo "⚡ Performance Optimization"

# 1. Database optimization
echo "1. Database optimization..."
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
    -- Update statistics
    ANALYZE;
    
    -- Reindex if needed
    REINDEX DATABASE $POSTGRES_DB;
    
    -- Check for slow queries
    SELECT query, calls, total_time, mean_time 
    FROM pg_stat_statements 
    ORDER BY mean_time DESC 
    LIMIT 5;"

# 2. Docker optimization
echo "2. Docker optimization..."
# Clean up unused resources
docker system prune -f

# Optimize Docker daemon settings
sudo systemctl restart docker

# 3. System optimization
echo "3. System optimization..."
# Clear page cache if memory usage is high
if [ $(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}') -gt 85 ]; then
    echo "High memory usage detected, clearing cache..."
    sync && echo 3 > /proc/sys/vm/drop_caches
fi

# 4. Log cleanup
echo "4. Log cleanup..."
find /opt/horme-pov/logs -name "*.log" -size +100M -exec truncate -s 10M {} \;

echo "✅ Performance optimization completed"
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Service Won't Start
```bash
# Diagnosis
echo "🔍 Service startup troubleshooting"

# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose -f docker-compose.vm-production.yml logs [service-name]

# Check resource availability
free -h
df -h

# Check port conflicts
netstat -tlnp | grep -E "(80|443|8000|3002|5433|6380)"

# Solutions
# 1. Restart Docker daemon
sudo systemctl restart docker

# 2. Clean up resources
docker system prune -f

# 3. Check configuration
docker-compose -f docker-compose.vm-production.yml config
```

#### Issue: Database Connection Failed
```bash
# Diagnosis
echo "🔍 Database connection troubleshooting"

# Check database status
docker-compose -f docker-compose.vm-production.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.vm-production.yml logs postgres

# Check connection settings
grep -E "(DATABASE|POSTGRES)" .env.production

# Test connectivity
docker-compose -f docker-compose.vm-production.yml exec api ping postgres

# Solutions
# 1. Restart database
docker-compose -f docker-compose.vm-production.yml restart postgres

# 2. Check authentication
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# 3. Reset database if corrupted
./scripts/disaster-recovery.sh
```

#### Issue: High Resource Usage
```bash
# Diagnosis
echo "🔍 High resource usage troubleshooting"

# Check resource usage
htop
iostat -x 1 5
docker stats --no-stream

# Check for memory leaks
ps aux --sort=-%mem | head -10

# Check disk usage
du -sh /opt/horme-pov/* | sort -hr

# Solutions
# 1. Restart memory-hungry services
docker-compose -f docker-compose.vm-production.yml restart api

# 2. Clean up logs
find /opt/horme-pov/logs -name "*.log" -size +100M -delete

# 3. Optimize database
docker-compose -f docker-compose.vm-production.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM FULL;"
```

#### Issue: SSL Certificate Problems
```bash
# Diagnosis
echo "🔍 SSL certificate troubleshooting"

# Check certificate validity
openssl x509 -in /opt/horme-pov/ssl/horme.crt -text -noout

# Check certificate expiry
openssl x509 -in /opt/horme-pov/ssl/horme.crt -noout -dates

# Check certificate chain
openssl verify -CAfile /opt/horme-pov/ssl/horme.crt /opt/horme-pov/ssl/horme.crt

# Solutions
# 1. Regenerate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/horme-pov/ssl/horme.key \
  -out /opt/horme-pov/ssl/horme.crt \
  -subj "/CN=your-domain.com"

# 2. Renew Let's Encrypt certificate
sudo certbot renew

# 3. Restart nginx
docker-compose -f docker-compose.vm-production.yml restart nginx
```

## Emergency Procedures

### Complete System Failure Recovery

```bash
#!/bin/bash
# Emergency system recovery procedure

echo "🆘 EMERGENCY SYSTEM RECOVERY"
echo "Recovery started at: $(date)"

# 1. Assess the situation
echo "1. System assessment..."
systemctl status docker
docker ps -a
df -h
free -h

# 2. If Docker is down, restart it
if ! systemctl is-active --quiet docker; then
    echo "2. Restarting Docker daemon..."
    sudo systemctl start docker
    sleep 10
fi

# 3. Try to start services
echo "3. Attempting to start services..."
cd /opt/horme-pov
docker-compose -f docker-compose.vm-production.yml up -d

# 4. Wait and check
sleep 60
if curl -f https://your-domain.com/health; then
    echo "✅ System recovered successfully!"
    exit 0
fi

# 5. If still failing, initiate disaster recovery
echo "5. System not responding, initiating disaster recovery..."
./scripts/disaster-recovery.sh

echo "✅ Emergency recovery procedure completed at: $(date)"
```

### Data Loss Recovery

```bash
#!/bin/bash
# Data loss recovery procedure

echo "💾 Data Loss Recovery Procedure"

# 1. Stop all services immediately
echo "1. Stopping all services..."
docker-compose -f docker-compose.vm-production.yml down

# 2. Assess data loss extent
echo "2. Assessing data loss..."
ls -la /opt/horme-pov/data/postgres/
ls -la /opt/horme-pov/backups/

# 3. Find most recent backup
LATEST_BACKUP=$(find /opt/horme-pov/backups -name "database.sql.gz" | sort -r | head -1)
echo "3. Latest backup: $LATEST_BACKUP"

# 4. Restore from backup
echo "4. Restoring from backup..."
if [ -n "$LATEST_BACKUP" ]; then
    # Start only database
    docker-compose -f docker-compose.vm-production.yml up -d postgres
    sleep 30
    
    # Restore database
    gunzip -c $LATEST_BACKUP | docker-compose -f docker-compose.vm-production.yml exec -T postgres \
      psql -U $POSTGRES_USER -d $POSTGRES_DB
    
    # Start all services
    docker-compose -f docker-compose.vm-production.yml up -d
    
    echo "✅ Data recovery completed"
else
    echo "❌ No backup found - data may be permanently lost"
    exit 1
fi
```

### Security Breach Response

```bash
#!/bin/bash
# Emergency security breach response

echo "🚨 SECURITY BREACH RESPONSE"

# 1. Immediate isolation
echo "1. Immediate system isolation..."
# Block all incoming traffic except SSH
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable

# 2. Stop compromised services
echo "2. Stopping potentially compromised services..."
docker-compose -f docker-compose.vm-production.yml down

# 3. Collect forensic evidence
echo "3. Collecting forensic evidence..."
mkdir -p /opt/horme-pov/security/incident-$(date +%s)
INCIDENT_DIR="/opt/horme-pov/security/incident-$(date +%s)"

# Copy logs
cp -r /opt/horme-pov/logs $INCIDENT_DIR/
cp /var/log/auth.log $INCIDENT_DIR/
cp /var/log/syslog $INCIDENT_DIR/

# System state
ps aux > $INCIDENT_DIR/processes.log
netstat -tulpn > $INCIDENT_DIR/network.log
lsof > $INCIDENT_DIR/files.log

# 4. Change all passwords and secrets
echo "4. Rotating security credentials..."
# This would involve changing database passwords, JWT secrets, etc.
# In a real scenario, you'd have specific procedures for this

# 5. Notify security team
echo "5. Notifying security team..."
echo "SECURITY BREACH DETECTED at $(date)" | mail -s "CRITICAL: Security Breach" security@your-domain.com

echo "🔒 System secured - manual investigation required"
```

## Contact Information

### Emergency Contacts

```
Primary On-Call: +1-555-0001
Secondary On-Call: +1-555-0002
Security Team: security@your-domain.com
Operations Team: ops@your-domain.com

Escalation Matrix:
Level 1: On-call engineer
Level 2: Team lead
Level 3: Engineering manager
Level 4: CTO
```

### Vendor Contacts

```
Cloud Provider Support: 1-800-XXX-XXXX
SSL Certificate Provider: support@ssl-provider.com
DNS Provider: support@dns-provider.com
Monitoring Service: support@monitoring.com
```

## Documentation Maintenance

This runbook should be reviewed and updated:
- **Monthly**: Update procedures and contact information
- **Quarterly**: Review and test all emergency procedures
- **After incidents**: Update based on lessons learned
- **After changes**: Update when system architecture changes

Last updated: [Date]
Reviewed by: [Name]
Next review date: [Date + 1 month]

---

Remember: This runbook is a living document. Keep it updated with your actual environment configurations, contact information, and procedures. Test all procedures regularly in a safe environment before relying on them in production.