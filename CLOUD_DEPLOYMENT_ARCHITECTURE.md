# Cloud Deployment Architecture - Horme POV

## Executive Summary

This document outlines the comprehensive containerized architecture for deploying the Horme POV Enterprise AI system to cloud environments (AWS, Azure, GCP, or private cloud).

### Key Objectives
- **100% Containerized**: All services run in isolated Docker containers
- **Virtual Environment**: Python dependencies managed via UV in containers
- **Production Ready**: Security, monitoring, scaling, and high availability
- **Cloud Agnostic**: Deploy to any cloud provider or on-premises
- **Zero Downtime**: Rolling updates, health checks, auto-recovery

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     LOAD BALANCER / CDN                      │
│                    (Cloud Provider LB)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┴────────────────┐
       │                                 │
┌──────▼───────┐                 ┌──────▼───────┐
│    NGINX     │                 │   NGINX      │
│  (SSL/TLS)   │                 │  (Replica)   │
└──────┬───────┘                 └──────┬───────┘
       │                                 │
       ├─────────────┬──────────────────┤
       │             │                  │
┌──────▼───────┐ ┌──▼─────────┐ ┌─────▼────────┐
│   FRONTEND   │ │    API     │ │  WEBSOCKET   │
│  (Next.js)   │ │ (FastAPI)  │ │   (Python)   │
│              │ │            │ │              │
│ Port: 3000   │ │ Port: 8000 │ │  Port: 8001  │
└──────────────┘ └──────┬─────┘ └──────┬───────┘
                        │                │
        ┌───────────────┴────────────────┴──────────┐
        │                                            │
┌───────▼───────┐  ┌──────────┐  ┌────────────┐ ┌──▼────────┐
│  POSTGRESQL   │  │  REDIS   │  │   NEO4J    │ │  EMAIL    │
│  (Primary DB) │  │ (Cache)  │  │  (Graph)   │ │ MONITOR   │
└───────────────┘  └──────────┘  └────────────┘ └───────────┘
        │
┌───────▼───────────┐
│  POSTGRES BACKUP  │
│   (Daily Backup)  │
└───────────────────┘

VOLUMES (Persistent Storage):
- postgres_data    -> PostgreSQL data
- redis_data       -> Redis persistence
- neo4j_data       -> Neo4j graph database
- uploads          -> User uploaded files
- logs             -> Application logs
- backups          -> Database backups
```

---

## Services Breakdown

### 1. **Frontend (Next.js)**
- **Container**: `horme-frontend`
- **Base Image**: `node:20-alpine`
- **Build**: Multi-stage (build → production)
- **Port**: 3000 (internal), 80/443 (external via Nginx)
- **Environment**: Server-side rendering with API proxy
- **Replicas**: 2+ for high availability

### 2. **API Backend (FastAPI)**
- **Container**: `horme-api`
- **Base Image**: `python:3.11-slim`
- **Package Manager**: UV (10-100x faster than pip)
- **Port**: 8000 (internal), exposed via Nginx
- **Workers**: Gunicorn with 4 Uvicorn workers
- **Replicas**: 3+ with load balancing
- **Health Check**: `/api/health` endpoint

### 3. **WebSocket Server**
- **Container**: `horme-websocket`
- **Base Image**: `python:3.11-slim`
- **Port**: 8001
- **Purpose**: Real-time chat, notifications
- **Connection**: Sticky sessions via Nginx

### 4. **PostgreSQL Database**
- **Container**: `horme-postgres`
- **Version**: PostgreSQL 15
- **Features**:
  - Automatic backups (daily)
  - Point-in-time recovery
  - Replication (primary + replica)
  - Connection pooling via PgBouncer
- **Storage**: Persistent volume with daily snapshots

### 5. **Redis Cache**
- **Container**: `horme-redis`
- **Version**: Redis 7 Alpine
- **Features**:
  - Session storage
  - API response caching
  - Rate limiting
  - Background job queue
- **Persistence**: AOF (Append-Only File)

### 6. **Neo4j Knowledge Graph**
- **Container**: `horme-neo4j`
- **Version**: Neo4j 5 Community
- **Purpose**: Product relationships, recommendations
- **Storage**: Persistent volume

### 7. **Email Monitor** (Optional)
- **Container**: `horme-email-monitor`
- **Purpose**: Process incoming RFP emails
- **IMAP Connection**: Secure email polling

### 8. **Nginx Reverse Proxy**
- **Container**: `horme-nginx`
- **Features**:
  - SSL/TLS termination
  - Load balancing
  - Rate limiting
  - CORS handling
  - Static file serving
  - WebSocket upgrade support

---

## Container Network Architecture

```
Networks:
┌────────────────────────────────────────────────┐
│  frontend_network (isolated)                   │
│  - frontend ↔ nginx only                       │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  backend_network (API services)                │
│  - api ↔ postgres, redis, neo4j               │
│  - websocket ↔ postgres                       │
│  - nginx ↔ api, websocket                     │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  database_network (data services only)         │
│  - postgres ↔ backup service                   │
│  - redis ↔ api only                           │
│  - neo4j ↔ api only                           │
└────────────────────────────────────────────────┘
```

**Security Benefits**:
- Frontend cannot directly access databases
- Each service has minimal network access
- Database services isolated from external access

---

## Cloud Provider Specific Deployment

### AWS (Amazon Web Services)

```yaml
Services Used:
- ECS (Elastic Container Service) or EKS (Kubernetes)
- RDS for PostgreSQL (managed database)
- ElastiCache for Redis (managed cache)
- ALB (Application Load Balancer)
- ACM (Certificate Manager) for SSL
- S3 for file uploads and backups
- CloudWatch for monitoring
- Route 53 for DNS
- ECR (Elastic Container Registry) for Docker images

Architecture:
┌─────────────┐
│   Route 53  │ (DNS)
└──────┬──────┘
       │
┌──────▼──────┐
│     ALB     │ (Load Balancer with SSL)
└──────┬──────┘
       │
┌──────▼──────┐
│     ECS     │ (Container orchestration)
│             │
│  ┌────────┐ │
│  │ Tasks  │ │ (Frontend, API, WebSocket)
│  └────┬───┘ │
└───────┼─────┘
        │
    ┌───┴────┐
    │        │
┌───▼───┐ ┌──▼──┐
│  RDS  │ │Cache│
└───────┘ └─────┘
```

**Deployment Command**:
```bash
./deploy-aws.sh
```

### Azure

```yaml
Services Used:
- Azure Container Instances or AKS
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Application Gateway
- Azure Key Vault (secrets)
- Azure Blob Storage (files)
- Azure Monitor (logging)
- Azure Container Registry

Architecture:
- Similar to AWS with Azure equivalents
- Uses Azure AD for authentication
```

**Deployment Command**:
```bash
./deploy-azure.sh
```

### GCP (Google Cloud Platform)

```yaml
Services Used:
- Cloud Run or GKE (Kubernetes)
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Load Balancing
- Cloud Storage (files)
- Cloud Monitoring
- Artifact Registry (Docker images)

Architecture:
- Serverless with Cloud Run
- Auto-scaling based on traffic
```

**Deployment Command**:
```bash
./deploy-gcp.sh
```

### On-Premises / Private Cloud

```yaml
Infrastructure:
- Docker Swarm or Kubernetes cluster
- HAProxy or Traefik for load balancing
- Self-managed PostgreSQL cluster
- Self-managed Redis cluster
- NFS or Ceph for shared storage
- Prometheus + Grafana for monitoring

Minimum Requirements:
- 3 nodes for high availability
- 16 GB RAM per node
- 200 GB storage per node
- 1 Gbps network
```

---

## Environment Variables Management

### Development (.env)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost:5432/dev_db
```

### Staging (.env.staging)
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/staging_db
```

### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db:5432/prod_db

# NEVER COMMIT SECRETS - Use cloud secret managers
# AWS: AWS Secrets Manager
# Azure: Key Vault
# GCP: Secret Manager
```

### Secrets Management

**Docker Secrets (Docker Swarm)**:
```bash
echo "db_password_here" | docker secret create postgres_password -
```

**Kubernetes Secrets**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: horme-secrets
type: Opaque
data:
  postgres-password: base64_encoded_password
  jwt-secret: base64_encoded_secret
```

**Cloud Provider Secrets**:
```bash
# AWS
aws secretsmanager create-secret --name horme/db-password --secret-string "password"

# Azure
az keyvault secret set --vault-name horme-vault --name db-password --value "password"

# GCP
echo -n "password" | gcloud secrets create db-password --data-file=-
```

---

## Deployment Workflows

### 1. Local Development
```bash
# Start all services locally
docker-compose up -d

# View logs
docker-compose logs -f api

# Run tests
docker-compose exec api pytest

# Stop services
docker-compose down
```

### 2. CI/CD Pipeline (GitHub Actions Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: docker-compose -f docker-compose.cloud.yml build

      - name: Run tests
        run: docker-compose -f docker-compose.cloud.yml run --rm api pytest

      - name: Push to registry
        run: |
          docker tag horme-api:latest ${{ secrets.REGISTRY }}/horme-api:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/horme-api:${{ github.sha }}

      - name: Deploy to cloud
        run: ./deploy-cloud.sh production
```

### 3. Blue-Green Deployment
```bash
# Deploy to "green" environment
./deploy-cloud.sh green

# Run smoke tests
./run-smoke-tests.sh green

# Switch traffic from blue to green
./switch-traffic.sh blue green

# Keep blue running for 1 hour for rollback
sleep 3600

# Shutdown old blue environment
./shutdown-environment.sh blue
```

---

## Monitoring & Observability

### Metrics (Prometheus + Grafana)
```yaml
Metrics Collected:
- API response times (p50, p95, p99)
- Database connection pool usage
- Cache hit/miss ratio
- Active WebSocket connections
- Container CPU/Memory usage
- Request rate per endpoint
- Error rate by status code
```

### Logging (ELK Stack or Cloud Provider)
```yaml
Log Aggregation:
- Application logs (JSON structured)
- Access logs (Nginx)
- Database slow queries
- Error traces with stack traces
- Security audit logs

Tools:
- Elasticsearch + Kibana
- AWS CloudWatch Logs
- Azure Monitor
- GCP Cloud Logging
```

### Alerts
```yaml
Critical Alerts:
- API response time > 5s
- Error rate > 1%
- Database connections > 80% pool
- Disk usage > 85%
- SSL certificate expiring < 30 days

Warning Alerts:
- High CPU usage > 75%
- Memory usage > 80%
- Cache hit rate < 70%
```

---

## Security Hardening

### Container Security
```dockerfile
# ✅ Use non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# ✅ Read-only root filesystem
docker run --read-only --tmpfs /tmp

# ✅ Drop capabilities
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE

# ✅ Security scanning
trivy image horme-api:latest
```

### Network Security
```yaml
Firewall Rules:
- Only ports 80/443 exposed to internet
- Database ports (5432, 6379, 7687) internal only
- API containers can't access internet
- Rate limiting: 100 req/min per IP
```

### Data Security
```yaml
Encryption:
- ✅ TLS 1.3 for all external connections
- ✅ Encrypted volumes (AES-256)
- ✅ Secrets encrypted at rest
- ✅ Database encryption enabled
- ✅ JWT tokens with RS256 signing
```

---

## Scaling Strategy

### Horizontal Scaling (Auto-scaling)
```yaml
API Service:
  min_instances: 3
  max_instances: 20
  scale_up_threshold: CPU > 70% for 2 minutes
  scale_down_threshold: CPU < 30% for 10 minutes

Frontend Service:
  min_instances: 2
  max_instances: 10
  scale_up_threshold: Requests > 1000/min

Database:
  type: Read Replicas
  replicas: 2 (read-only)
  primary: 1 (write)
```

### Vertical Scaling (Resource Limits)
```yaml
api:
  resources:
    limits:
      memory: 2Gi
      cpu: "1000m"
    requests:
      memory: 1Gi
      cpu: "500m"
```

---

## Backup & Disaster Recovery

### Database Backups
```bash
# Automated daily backups
0 2 * * * docker exec horme-postgres pg_dump -U postgres horme_db > backup.sql

# Backup to cloud storage
aws s3 cp backup.sql s3://horme-backups/$(date +%Y%m%d)/

# Retention: 7 daily, 4 weekly, 12 monthly
```

### Disaster Recovery Plan
```yaml
Recovery Time Objective (RTO): 1 hour
Recovery Point Objective (RPO): 24 hours (daily backups)

Procedure:
1. Provision new cloud infrastructure (via Terraform)
2. Restore database from latest backup
3. Deploy application containers
4. Run health checks
5. Switch DNS to new infrastructure
```

---

## Cost Optimization

### Cloud Cost Estimates (Monthly)

**AWS (Small Deployment)**
```
- ECS Fargate (3 tasks): $150
- RDS PostgreSQL (db.t3.medium): $70
- ElastiCache Redis (cache.t3.micro): $15
- ALB: $20
- S3 Storage (100GB): $3
- CloudWatch: $10
Total: ~$270/month
```

**AWS (Medium Deployment)**
```
- ECS Fargate (10 tasks): $500
- RDS PostgreSQL (db.r5.large with replica): $400
- ElastiCache Redis (cache.r5.large): $150
- ALB + WAF: $50
- S3 Storage (500GB): $12
- CloudWatch + X-Ray: $30
Total: ~$1,140/month
```

### Cost Saving Strategies
```yaml
1. Use Spot Instances (AWS ECS) - 70% savings
2. Auto-scaling - only pay for what you use
3. Reserved Instances - 40% discount for 1-year commit
4. CDN caching - reduce API calls
5. Compression - reduce storage costs
```

---

## Quick Deployment Commands

### Build All Images
```bash
docker-compose -f docker-compose.cloud.yml build --parallel
```

### Deploy to Cloud
```bash
# Development
./deploy-cloud.sh dev

# Staging
./deploy-cloud.sh staging

# Production (requires confirmation)
./deploy-cloud.sh production
```

### Health Check
```bash
curl https://your-domain.com/api/health
```

### View Logs
```bash
# API logs
docker-compose logs -f --tail=100 api

# All services
docker-compose logs -f
```

### Database Backup
```bash
./scripts/backup-database.sh
```

### Scale Service
```bash
docker-compose up -d --scale api=5
```

---

## Troubleshooting

### Common Issues

**Issue**: Container fails to start
```bash
# Check logs
docker logs horme-api

# Check health
docker inspect horme-api | grep Health

# Restart container
docker restart horme-api
```

**Issue**: Database connection refused
```bash
# Verify network
docker network inspect horme_backend_network

# Check database is running
docker ps | grep postgres

# Test connection
docker exec horme-api psql -h postgres -U horme_user -d horme_db
```

**Issue**: High memory usage
```bash
# Check resource usage
docker stats

# Restart service
docker-compose restart api
```

---

## Next Steps

1. ✅ Review this architecture document
2. ✅ Choose cloud provider (AWS/Azure/GCP/On-prem)
3. ✅ Set up CI/CD pipeline
4. ✅ Configure secrets management
5. ✅ Deploy to staging environment
6. ✅ Run load tests
7. ✅ Deploy to production
8. ✅ Set up monitoring and alerts

---

## Support & Documentation

- **Architecture Diagram**: See above
- **Deployment Scripts**: `./scripts/deploy-*.sh`
- **Environment Templates**: `.env.example`, `.env.production.example`
- **Docker Compose**: `docker-compose.cloud.yml`
- **Kubernetes Manifests**: `k8s/`
- **Monitoring Dashboards**: `monitoring/grafana/`

For questions or issues, contact the DevOps team or refer to the deployment guide.
