# Nexus Production Platform Deployment Guide

## 🎯 Overview

This guide provides complete instructions for deploying the production-optimized Nexus multi-channel platform with DataFlow integration, WebSocket real-time features, and comprehensive monitoring.

## 📋 Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended (2 minimum)
- **Memory**: 8GB+ recommended (4GB minimum)
- **Storage**: 50GB+ available space
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, or similar)

### Software Dependencies
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for HTTPS in production)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd nexus-production

# Copy environment template
cp .env.example .env.production

# Edit production environment variables
nano .env.production
```

### 2. Configure Environment Variables

Create `.env.production` with your production settings:

```bash
# Environment
NEXUS_ENV=production

# Server Configuration
NEXUS_API_HOST=0.0.0.0
NEXUS_API_PORT=8000
NEXUS_WEBSOCKET_PORT=8001
NEXUS_MCP_PORT=3001

# Database Configuration
DATABASE_URL=postgresql://horme_user:YOUR_SECURE_PASSWORD@postgres:5432/horme_classification_db

# Redis Configuration
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0

# Security (CHANGE THESE!)
NEXUS_JWT_SECRET=your-super-secure-jwt-secret-at-least-32-characters-long
NEXUS_JWT_REFRESH_SECRET=your-super-secure-refresh-secret-at-least-32-characters-long
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_DAYS=7

# Performance Configuration
CACHE_TTL_SECONDS=2700
MAX_CONCURRENT_REQUESTS=500
REQUEST_TIMEOUT=30
BULK_OPERATION_TIMEOUT=600
CLASSIFICATION_TIMEOUT=45
BATCH_SIZE_LIMIT=2000
ENABLE_COMPRESSION=true

# DataFlow Connection Pool
DATAFLOW_POOL_SIZE=75
DATAFLOW_MAX_OVERFLOW=150
DATAFLOW_POOL_RECYCLE=1200

# WebSocket Configuration
MAX_WEBSOCKET_CONNECTIONS=500
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_TIMEOUT=300

# Optimization Features
CACHE_WARMING_ENABLED=true
ENABLE_REQUEST_BATCHING=true
ENABLE_LOAD_BALANCING=true

# Rate Limiting
RATE_LIMIT_RPM=300
RATE_LIMIT_BURST=50

# CORS (customize for your domains)
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com,https://admin.your-domain.com
```

### 3. Deploy with Docker Compose

```bash
# Deploy core platform
docker-compose -f docker-compose.production.yml up -d

# Or deploy with monitoring (optional)
docker-compose -f docker-compose.production.yml --profile monitoring up -d

# Or deploy with load balancer (optional)
docker-compose -f docker-compose.production.yml --profile load-balancer up -d

# Deploy everything
docker-compose -f docker-compose.production.yml --profile monitoring --profile load-balancer up -d
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.production.yml ps

# Check health
curl -f http://localhost:8000/api/v2/health/comprehensive

# Check logs
docker-compose -f docker-compose.production.yml logs -f nexus-production
```

## 🔧 Detailed Configuration

### Database Optimization

The PostgreSQL instance is pre-configured with production optimizations:

- **Connection Pool**: 200 max connections
- **Memory**: 512MB shared_buffers, 2GB effective_cache_size
- **WAL**: Optimized for write performance
- **Parallel Processing**: 8 worker processes, 4 parallel workers per gather
- **Monitoring**: pg_stat_statements enabled

### Redis Cache Configuration

Redis is configured for optimal caching performance:

- **Memory**: 512MB maxmemory with LRU eviction
- **Persistence**: AOF enabled with fsync every second
- **Network**: Optimized for low latency

### Performance Targets

The platform is optimized to achieve:

- **API Response Time**: <2 seconds average
- **Bulk Operations**: 10,000+ records/second
- **Cache Hit Ratio**: >80%
- **WebSocket Connections**: Up to 500 concurrent
- **Error Rate**: <3%

## 🌐 Multi-Channel Access

### REST API
- **URL**: `http://your-domain.com/api/`
- **Authentication**: JWT with refresh tokens
- **Rate Limiting**: 300 requests/minute per IP
- **Compression**: Gzip enabled for responses >1KB

### WebSocket Real-Time
- **URL**: `ws://your-domain.com/ws/{user_id}`
- **Features**: Real-time notifications, progress updates, heartbeat
- **Max Connections**: 500 concurrent

### CLI Access
```bash
# Inside container
docker exec -it nexus-production nexus --help

# Production status
docker exec -it nexus-production nexus production-status

# Performance metrics
docker exec -it nexus-production nexus performance-report

# Cache management
docker exec -it nexus-production nexus warm-cache
```

### MCP Integration
- **URL**: `http://your-domain.com:3001`
- **Tools**: DataFlow operations, bulk processing, system health
- **AI Agent Compatible**: Full MCP specification support

## 📊 Monitoring & Observability

### Health Checks

```bash
# Comprehensive health check
curl -X GET http://localhost:8000/api/v2/health/comprehensive

# Quick health check
curl -X GET http://localhost:8000/health

# Metrics endpoint (requires authentication)
curl -X GET http://localhost:8000/api/v2/metrics/production \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Prometheus Metrics (Optional)

If deployed with monitoring profile:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

Key metrics tracked:
- Request latency and throughput
- Cache hit ratios
- Database connection pool usage
- WebSocket connection counts
- Bulk operation performance
- Error rates and types

### Log Aggregation

Logs are available through Docker:

```bash
# Platform logs
docker-compose logs -f nexus-production

# Database logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# All logs
docker-compose logs -f
```

## 🔒 Security Configuration

### Authentication Flow

1. **Login**: POST `/api/auth/login` → Returns access + refresh tokens
2. **API Access**: Include `Authorization: Bearer <access_token>` header
3. **Token Refresh**: POST `/api/auth/refresh` with refresh token
4. **Logout**: POST `/api/auth/logout` → Invalidates session

### SSL/HTTPS Setup

For production HTTPS, uncomment and configure the SSL server block in `config/nginx.conf`:

```bash
# Generate SSL certificates (example with Let's Encrypt)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem config/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem config/ssl/key.pem

# Update nginx.conf to enable HTTPS server block
# Restart nginx
docker-compose restart nginx
```

### Firewall Configuration

Recommended firewall rules:

```bash
# Allow SSH
ufw allow 22

# Allow HTTP/HTTPS (if using Nginx)
ufw allow 80
ufw allow 443

# Allow direct API access (if not using Nginx)
ufw allow 8000

# Allow WebSocket (if not using Nginx)
ufw allow 8001

# Enable firewall
ufw enable
```

## 🚀 Performance Optimization

### Cache Warming

Warm caches on startup and periodically:

```bash
# Warm all caches
docker exec -it nexus-production nexus warm-cache

# Warm specific model cache
docker exec -it nexus-production nexus warm-cache --model Customer

# Check cache statistics
docker exec -it nexus-production nexus cache-stats
```

### Connection Pool Tuning

Monitor and adjust based on load:

```bash
# Check current pool status
docker exec -it nexus-production nexus production-status

# Monitor database connections
docker exec -it nexus-postgres psql -U horme_user -d horme_classification_db -c "
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity 
WHERE datname = 'horme_classification_db';
"
```

### Bulk Operation Optimization

For high-volume data processing:

```python
# Use optimized bulk endpoints
POST /api/v2/bulk/create
{
    "model": "ProductClassification",
    "data": [...],  # Up to 2000 records
    "batch_size": 1000
}
```

## 📈 Scaling Strategies

### Horizontal Scaling

Add more Nexus instances:

```yaml
# In docker-compose.production.yml
nexus-production-2:
  <<: *nexus-service-template
  container_name: nexus-production-2
  
nexus-production-3:
  <<: *nexus-service-template  
  container_name: nexus-production-3
```

Update Nginx upstream:

```nginx
upstream nexus_backend {
    least_conn;
    server nexus-production:8000;
    server nexus-production-2:8000;
    server nexus-production-3:8000;
}
```

### Database Scaling

For high load scenarios:

1. **Read Replicas**: Configure PostgreSQL streaming replication
2. **Connection Pooling**: Use PgBouncer for connection pooling
3. **Partitioning**: Partition large tables by date/category

### Cache Scaling

For better cache performance:

1. **Redis Cluster**: Deploy Redis in cluster mode
2. **Cache Warming**: Implement scheduled cache warming
3. **CDN**: Use CDN for static content and API responses

## 🛠️ Maintenance Tasks

### Daily Tasks

```bash
# Check system health
docker exec -it nexus-production nexus production-status

# Check performance metrics
docker exec -it nexus-production nexus performance-report

# Clean up expired sessions
docker exec -it nexus-postgres psql -U horme_user -d horme_classification_db -c "
SELECT nexus_production.cleanup_expired_sessions();
"
```

### Weekly Tasks

```bash
# Update cache statistics
docker exec -it nexus-production nexus warm-cache

# Check disk usage
docker system df

# Rotate logs (if not using log rotation)
docker-compose logs --no-log-prefix nexus-production > logs/nexus-$(date +%Y%m%d).log
```

### Monthly Tasks

```bash
# Database maintenance
docker exec -it nexus-postgres psql -U horme_user -d horme_classification_db -c "
VACUUM ANALYZE;
REINDEX DATABASE horme_classification_db;
"

# Update dependencies
docker-compose pull
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services if needed
docker-compose restart nexus-production
```

#### Database Connection Issues
```bash
# Check database connectivity
docker exec -it nexus-postgres pg_isready -U horme_user

# Check connection pool
docker exec -it nexus-postgres psql -U horme_user -d horme_classification_db -c "
SELECT * FROM pg_stat_activity WHERE datname = 'horme_classification_db';
"
```

#### WebSocket Connection Issues
```bash
# Check WebSocket connections
docker exec -it nexus-production nexus websocket-stats

# Restart for WebSocket issues
docker-compose restart nexus-production
```

#### Cache Issues
```bash
# Check Redis connectivity
docker exec -it nexus-redis redis-cli ping

# Clear cache if needed
docker exec -it nexus-redis redis-cli FLUSHALL
```

### Performance Debugging

```bash
# Run performance benchmark
docker exec -it nexus-production nexus performance-benchmark

# Check slow queries
docker exec -it nexus-postgres psql -U horme_user -d horme_classification_db -c "
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

## 🔄 Backup & Recovery

### Database Backup

```bash
# Create backup
docker exec -it nexus-postgres pg_dump -U horme_user horme_classification_db > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i nexus-postgres psql -U horme_user horme_classification_db < backup_20250804.sql
```

### Configuration Backup

```bash
# Backup all configuration
tar -czf nexus-config-backup-$(date +%Y%m%d).tar.gz config/ .env.production docker-compose.production.yml
```

## 📞 Support & Monitoring

### Health Check Endpoints

- **Basic Health**: `GET /health`
- **Comprehensive Health**: `GET /api/v2/health/comprehensive`
- **Metrics**: `GET /api/v2/metrics/production`

### Alert Thresholds

The platform monitors these critical metrics:

- **Response Time**: >2s average triggers alert
- **Error Rate**: >3% triggers alert  
- **Cache Hit Ratio**: <80% triggers alert
- **Memory Usage**: >4GB triggers alert
- **Database Connections**: >160 (80% of pool) triggers alert

### Production Checklist

Before going live:

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database optimized and tested
- [ ] Cache warming configured
- [ ] Monitoring setup and tested
- [ ] Backup procedures tested
- [ ] Load testing completed
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Team trained on operations

## 🎯 Success Metrics

Target KPIs for production deployment:

- **Uptime**: >99.9%
- **API Response Time**: <2s average, <5s P95
- **Bulk Throughput**: >10,000 records/second
- **Cache Hit Ratio**: >80%
- **Error Rate**: <3%
- **WebSocket Availability**: >99%
- **Database Performance**: <100ms query average

---

## 📚 Additional Resources

- [DataFlow Optimization Guide](dataflow_production_optimizations.py)
- [WebSocket Integration Examples](nexus_production_platform.py)
- [Performance Benchmarking](validate_dataflow_optimizations.py)
- [Security Best Practices](../docs/security/)
- [API Documentation](../docs/api/)

For additional support or questions, refer to the platform logs and monitoring dashboards.