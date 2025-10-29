# ADR-006: VM Production Readiness Architecture

## Status
Accepted

## Context

The Horme POV project requires deployment readiness for Virtual Machine (VM) environments, including cloud VMs, on-premises servers, and hybrid deployments. This extends the existing Docker-first approach (ADR-004) to provide robust VM deployment capabilities with security hardening, infrastructure compatibility, and operational excellence.

### Requirements Analysis

#### Functional Requirements
| Requirement | Description | Input | Output | Business Logic | Edge Cases | VM Mapping |
|-------------|-------------|-------|--------|----------------|------------|-----------|
| REQ-001 | VM compatibility | System specs | Deployment config | Resource validation | Limited resources | Docker Compose profiles |
| REQ-002 | Security hardening | Security policies | Hardened containers | Apply security controls | Compliance violations | Security middleware |
| REQ-003 | Infrastructure adaptation | VM environment | Optimized deployment | Environment detection | Network restrictions | Network configuration |
| REQ-004 | Monitoring integration | VM metrics | Health dashboards | Metrics collection | Resource constraints | Lightweight monitoring |

#### Non-Functional Requirements

**Performance Requirements**
- VM Compatibility: Support 2GB+ RAM, 2+ CPU cores minimum
- Boot Time: <5 minutes full stack startup
- Resource Efficiency: <80% resource utilization under normal load
- Network Latency: <100ms internal service communication

**Security Requirements**
- Container Isolation: Non-root users, capability dropping
- Network Segmentation: Internal networks, firewall rules
- Secrets Management: Environment-based secret injection
- Compliance: Industry security standards (CIS, NIST)

**Reliability Requirements**
- High Availability: 99.9% uptime with proper VM configuration
- Fault Tolerance: Service restart on failure, graceful degradation
- Backup/Recovery: Automated data backup, disaster recovery procedures
- Health Monitoring: Comprehensive health checks, alerting

### User Journey Mapping

#### System Administrator Journey
1. VM Preparation → Resource validation, OS hardening
2. Installation → Docker installation, security configuration
3. Deployment → Service deployment, network configuration
4. Monitoring → Health check setup, alerting configuration
5. Maintenance → Updates, backup validation, security audits

Success Criteria:
- Complete deployment in <30 minutes
- All services healthy within 5 minutes
- Monitoring active with alerting

Failure Points:
- Insufficient VM resources
- Network connectivity issues
- Security policy conflicts
- Service startup failures

## Decision

Implement a VM-optimized, security-hardened deployment architecture that maintains Docker containerization benefits while providing robust VM compatibility, security controls, and operational procedures.

### VM Production Architecture

```yaml
# docker-compose.vm-production.yml
version: '3.8'

services:
  # Reverse Proxy with SSL Termination
  nginx:
    image: nginx:1.25-alpine
    container_name: horme-nginx
    ports:
      - "${NGINX_HTTP_PORT:-80}:80"
      - "${NGINX_HTTPS_PORT:-443}:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
      - ./logs/nginx:/var/log/nginx
    networks:
      - frontend_network
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    user: "101:101"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # API Service with Security Hardening
  api:
    build:
      context: .
      dockerfile: Dockerfile.api-secure
      target: production
    container_name: horme-api
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    networks:
      - frontend_network
      - backend_network
    volumes:
      - ./logs/api:/app/logs:rw
      - ./data/uploads:/app/uploads:rw
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
      - seccomp:./security/seccomp-api.json
    cap_drop:
      - ALL
    cap_add:
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp
      - /run
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # MCP Server with Enhanced Security
  mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp-secure
      target: production
    container_name: horme-mcp
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - WS_PORT=3002
      - CORS_ORIGINS=${CORS_ORIGINS}
      - AUTH_ENABLED=true
      - RATE_LIMIT_ENABLED=true
    networks:
      - backend_network
    ports:
      - "${MCP_PORT:-3002}:3002"
    volumes:
      - ./logs/mcp:/app/logs:rw
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
      - seccomp:./security/seccomp-mcp.json
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
      - /run
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "nc -z localhost 3002 || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    depends_on:
      postgres:
        condition: service_healthy

  # PostgreSQL with Security Controls
  postgres:
    image: postgres:15-alpine
    container_name: horme-postgres
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
      - POSTGRES_HOST_AUTH_METHOD=scram-sha-256
    networks:
      - database_network
      - backend_network
    ports:
      - "${POSTGRES_PORT:-5433}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
      - ./backups:/backups:rw
      - ./logs/postgres:/var/log:rw
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - SETGID
      - SETUID
      - DAC_OVERRIDE
    read_only: false
    shm_size: 256m
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s

  # Redis with Security Configuration
  redis:
    image: redis:7-alpine
    container_name: horme-redis
    ports:
      - "${REDIS_PORT:-6380}:6379"
    networks:
      - backend_network
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - ./logs/redis:/var/log/redis:rw
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  # Frontend with Security Headers
  frontend:
    build:
      context: ./fe-reference
      dockerfile: Dockerfile
      target: production
    container_name: horme-frontend
    environment:
      - NODE_ENV=production
      - API_URL=https://${DOMAIN_NAME}/api
      - WS_URL=wss://${DOMAIN_NAME}/ws
    networks:
      - frontend_network
    volumes:
      - ./logs/frontend:/var/log/nginx:rw
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache/nginx
      - /var/run
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: horme-prometheus
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    networks:
      - monitoring_network
      - backend_network
    volumes:
      - ./monitoring/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
      - ./logs/prometheus:/var/log:rw
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "65534:65534"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.2'
          memory: 512M

  grafana:
    image: grafana/grafana:latest
    container_name: horme-grafana
    ports:
      - "${GRAFANA_PORT:-3001}:3000"
    networks:
      - monitoring_network
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SECURITY_DISABLE_GRAVATAR=true
      - GF_SECURITY_COOKIE_SECURE=true
      - GF_SECURITY_COOKIE_SAMESITE=strict
      - GF_SERVER_ROOT_URL=https://${DOMAIN_NAME}/grafana/
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning:ro
      - ./logs/grafana:/var/log/grafana:rw
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "472:472"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 256M

# Network Configuration with Security
networks:
  frontend_network:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.20.1.0/24

  backend_network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.2.0/24

  database_network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.3.0/24

  monitoring_network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.4.0/24

# Persistent Volumes
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/prometheus
  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/grafana
```

### Security Hardening Implementation

#### Container Security (Dockerfile.api-secure)
```dockerfile
# Multi-stage build for security
FROM python:3.11-alpine AS builder

# Security: Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    && rm -rf /var/cache/apk/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# Production stage
FROM python:3.11-alpine AS production

# Security: Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -s /bin/sh appuser

# Security: Install only runtime dependencies
RUN apk add --no-cache \
    dumb-init \
    postgresql-client \
    curl \
    && rm -rf /var/cache/apk/*

# Security: Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Application setup
WORKDIR /app
COPY --chown=appuser:appuser . .

# Security: Set proper permissions
RUN chmod -R 755 /app && \
    chmod +x /app/entrypoint.sh

# Security: Create log directory
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs

# Security: Switch to non-root user
USER appuser

# Security: Expose minimal port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Security: Use init system for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./entrypoint.sh"]
```

#### Network Security Configuration
```nginx
# nginx/nginx-secure.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# Security: Worker process limits
worker_rlimit_nofile 65535;

events {
    worker_connections 1024;
    multi_accept on;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security: Hide server information
    server_tokens off;
    
    # Security: Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Security: Connection limits
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    
    # Security: Buffer size limits
    client_body_buffer_size 1K;
    client_header_buffer_size 1k;
    client_max_body_size 10m;
    large_client_header_buffers 2 1k;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 30;
    keepalive_requests 100;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Frontend Server
    upstream frontend {
        server frontend:3000;
    }

    # API Backend
    upstream api {
        server api:8000;
        keepalive 32;
    }

    # Main server block
    server {
        listen 80;
        server_name _;
        
        # Security: Force HTTPS redirect
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name ${DOMAIN_NAME};

        # SSL certificates
        ssl_certificate /etc/ssl/certs/horme.crt;
        ssl_certificate_key /etc/ssl/certs/horme.key;

        # Security headers
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss:; font-src 'self';" always;

        # Security: Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_conn conn_limit_per_ip 20;

        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Security: Prevent proxy header manipulation
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Server $host;
        }

        # API routes
        location /api/ {
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Security: API-specific rate limiting
            limit_req zone=api burst=50 nodelay;
            
            # Security: Timeout settings
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 30s;
        }

        # WebSocket for MCP
        location /ws/ {
            proxy_pass http://mcp:3002/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket timeouts
            proxy_connect_timeout 7d;
            proxy_send_timeout 7d;
            proxy_read_timeout 7d;
        }

        # Health check endpoint
        location /health {
            access_log off;
            add_header Content-Type text/plain;
            return 200 "healthy\n";
        }

        # Security: Block common attack patterns
        location ~* \.(env|git|svn|htaccess|htpasswd)$ {
            deny all;
        }

        location ~* \.(sql|bak|backup|log)$ {
            deny all;
        }
    }
}
```

### VM Infrastructure Requirements

#### Minimum System Requirements
```bash
# System Requirements Validation Script
#!/bin/bash
# vm-requirements-check.sh

set -e

echo "🔍 Validating VM requirements for Horme POV deployment..."

# CPU Check
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -lt 2 ]; then
    echo "❌ ERROR: Minimum 2 CPU cores required (found: $CPU_CORES)"
    exit 1
fi
echo "✅ CPU cores: $CPU_CORES"

# Memory Check
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$MEMORY_GB" -lt 4 ]; then
    echo "❌ ERROR: Minimum 4GB RAM required (found: ${MEMORY_GB}GB)"
    exit 1
fi
echo "✅ Memory: ${MEMORY_GB}GB"

# Disk Space Check
DISK_SPACE_GB=$(df -BG / | awk 'NR==2{sub(/G/,"",$4); print $4}')
if [ "$DISK_SPACE_GB" -lt 20 ]; then
    echo "❌ ERROR: Minimum 20GB free space required (found: ${DISK_SPACE_GB}GB)"
    exit 1
fi
echo "✅ Disk space: ${DISK_SPACE_GB}GB"

# Docker Check
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker not installed"
    exit 1
fi
echo "✅ Docker installed: $(docker --version)"

# Docker Compose Check
if ! command -v docker-compose &> /dev/null; then
    echo "❌ ERROR: Docker Compose not installed"
    exit 1
fi
echo "✅ Docker Compose installed: $(docker-compose --version)"

# Network Connectivity Check
if ! curl -sSf https://index.docker.io > /dev/null 2>&1; then
    echo "⚠️  WARNING: Cannot reach Docker Hub (may need proxy configuration)"
else
    echo "✅ Network connectivity: OK"
fi

echo ""
echo "🎉 VM requirements validation complete!"
echo ""
echo "Recommended specifications:"
echo "  - CPU: 4+ cores for production workloads"
echo "  - RAM: 8GB+ for optimal performance"
echo "  - Storage: 50GB+ for logs and data retention"
echo "  - Network: 1Gbps+ for high throughput"
```

#### Operating System Hardening
```bash
#!/bin/bash
# vm-security-hardening.sh

set -e

echo "🔒 Applying VM security hardening..."

# Firewall Configuration
echo "Configuring firewall rules..."
ufw --force enable

# Allow SSH (adjust port as needed)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow application ports
ufw allow 3000/tcp  # Frontend
ufw allow 8000/tcp  # API
ufw allow 3002/tcp  # MCP WebSocket
ufw allow 5433/tcp  # PostgreSQL (external access)
ufw allow 6380/tcp  # Redis (external access)
ufw allow 9090/tcp  # Prometheus
ufw allow 3001/tcp  # Grafana

# Deny all other traffic by default
ufw default deny incoming
ufw default allow outgoing

# System Security Updates
echo "Applying security updates..."
apt update && apt upgrade -y

# Install security tools
apt install -y \
    fail2ban \
    unattended-upgrades \
    logwatch \
    rkhunter \
    chkrootkit

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[ssh]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure automatic security updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
systemctl enable unattended-upgrades

# Kernel parameter hardening
cat >> /etc/sysctl.conf << EOF
# Network security
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
EOF

sysctl -p

echo "✅ VM security hardening complete!"
```

## Implementation Strategy

### Phase 1: VM Infrastructure Setup (Complete)
1. ✅ Create VM-optimized Docker Compose configuration
2. ✅ Implement security-hardened Dockerfiles
3. ✅ Set up network security with proper isolation
4. ✅ Configure SSL/TLS with security headers

### Phase 2: Security Hardening (Complete)
1. ✅ Implement container security controls (non-root users, capability dropping)
2. ✅ Set up network segmentation with internal networks
3. ✅ Configure comprehensive security headers and policies
4. ✅ Implement rate limiting and DDoS protection

### Phase 3: Monitoring and Operations (Complete)
1. ✅ Set up Prometheus/Grafana monitoring stack
2. ✅ Implement comprehensive health checks
3. ✅ Configure automated backup procedures
4. ✅ Set up log aggregation and rotation

## Risk Assessment

### High Probability, High Impact (Critical)
1. **Resource Exhaustion**
   - Risk: VM runs out of memory/CPU under load
   - Mitigation: Resource limits, monitoring, auto-scaling alerts
   - Prevention: Proper sizing, load testing

2. **Security Breach**
   - Risk: Container escape or network infiltration
   - Mitigation: Security hardening, network isolation, monitoring
   - Prevention: Regular security audits, updates

### Medium Risk (Monitor)
1. **Service Dependencies**
   - Risk: Database or Redis failure cascading
   - Mitigation: Health checks, restart policies, data backup
   - Prevention: High availability configuration

2. **Certificate Expiration**
   - Risk: SSL certificates expire causing downtime
   - Mitigation: Monitoring, automated renewal
   - Prevention: Let's Encrypt integration

### Low Risk (Accept)
1. **Log Storage Growth**
   - Risk: Logs consume excessive disk space
   - Mitigation: Log rotation, retention policies
   - Prevention: Monitoring disk usage

## Consequences

### Positive
- **VM Compatibility**: Supports wide range of VM environments (cloud, on-premises)
- **Security Hardening**: Enterprise-grade security controls and isolation
- **Operational Excellence**: Comprehensive monitoring, logging, and health checks
- **Infrastructure Flexibility**: Adaptable to various deployment scenarios
- **Cost Optimization**: Efficient resource utilization with defined limits
- **Compliance Ready**: Security controls meet industry standards

### Negative
- **Complexity**: Increased configuration and operational complexity
- **Resource Overhead**: Security controls add some performance overhead
- **Maintenance Burden**: Regular security updates and monitoring required
- **Learning Curve**: Operations team needs container security expertise
- **Debugging Challenges**: Multiple security layers can complicate troubleshooting

## Alternatives Considered

### Option 1: Kubernetes Deployment
- **Description**: Deploy to Kubernetes cluster for orchestration
- **Pros**: Industry standard, advanced orchestration, built-in security policies
- **Cons**: Higher complexity, resource overhead, learning curve
- **Why Rejected**: Docker Compose provides sufficient orchestration with lower complexity

### Option 2: Traditional VM Deployment (No Containers)
- **Description**: Deploy directly to VMs without containerization
- **Pros**: Traditional approach, full system control, familiar operations
- **Cons**: Environment inconsistency, difficult scaling, manual configuration
- **Why Rejected**: Containers provide superior consistency and deployment benefits

### Option 3: Serverless Architecture
- **Description**: Deploy as serverless functions (Lambda, Cloud Functions)
- **Pros**: Automatic scaling, no infrastructure management, cost efficiency
- **Cons**: Cold start latency, vendor lock-in, limited runtime control
- **Why Rejected**: Real-time requirements and state management needs

## Validation Criteria

### Security Validation
- [ ] All containers run as non-root users
- [ ] Network segmentation properly isolates services
- [ ] Security headers implemented and tested
- [ ] Rate limiting and DDoS protection functional
- [ ] SSL/TLS configuration meets security standards
- [ ] Container image vulnerability scanning passes

### Performance Validation
- [ ] Resource limits prevent system exhaustion
- [ ] Health checks respond within SLA timeouts
- [ ] Service startup times meet requirements (<5 minutes)
- [ ] Network latency between services <100ms
- [ ] System handles expected load without degradation

### Operational Validation
- [ ] Monitoring dashboards show all metrics
- [ ] Log aggregation captures all service logs
- [ ] Backup procedures tested and validated
- [ ] Disaster recovery procedures functional
- [ ] Security incident response procedures tested
- [ ] Documentation complete and accurate

## Migration Strategy

### From Development to VM Production
1. **Environment Preparation**
   - VM provisioning with security hardening
   - Docker and Docker Compose installation
   - Network and firewall configuration

2. **Service Migration**
   - Deploy database with data migration
   - Deploy API and MCP services
   - Configure load balancer and SSL termination
   - Deploy frontend and monitoring stack

3. **Validation and Testing**
   - Execute comprehensive test suite
   - Validate security controls
   - Perform load testing
   - Test backup and recovery procedures

4. **Go-Live Procedures**
   - DNS cutover to production
   - Monitor system health and performance
   - Execute post-deployment validation
   - Document operational procedures