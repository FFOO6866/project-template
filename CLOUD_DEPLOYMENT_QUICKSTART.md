# Cloud Deployment Quick Start Guide

## Overview

This guide provides step-by-step instructions to deploy the Horme POV system to any cloud environment using Docker containers with all dependencies fulfilled in virtual environments.

---

## Prerequisites

1. **Docker & Docker Compose**
   ```bash
   docker --version  # >= 24.0
   docker compose version  # >= 2.20
   ```

2. **Cloud Provider Account** (choose one):
   - AWS Account with IAM access
   - Azure Subscription
   - GCP Project
   - Or self-hosted infrastructure

3. **Domain Name** (for production)
   - SSL certificate (Let's Encrypt recommended)

---

## Step 1: Initial Setup

### Clone and Prepare Environment

```bash
# Clone repository
git clone <your-repo-url>
cd horme-pov

# Copy environment template
cp .env.example .env.production

# Generate secure secrets
python scripts/generate_production_credentials.py

# Edit .env.production with your values
nano .env.production
```

### Required Environment Variables

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# Database
POSTGRES_USER=horme_user
POSTGRES_PASSWORD=<generate-strong-password>
POSTGRES_DB=horme_db

# Redis
REDIS_PASSWORD=<generate-strong-password>

# Neo4j
NEO4J_PASSWORD=<generate-strong-password>

# JWT Secrets (generate with: openssl rand -hex 32)
JWT_SECRET=<your-jwt-secret>
NEXUS_JWT_SECRET=<your-nexus-jwt-secret>
SECRET_KEY=<your-secret-key>

# OpenAI
OPENAI_API_KEY=<your-openai-api-key>

# Email (for RFP monitoring)
EMAIL_IMAP_SERVER=mail.horme.com.sg
EMAIL_USERNAME=integrum@horme.com.sg
EMAIL_PASSWORD=<your-email-password>

# CORS (your frontend domain)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Admin
ADMIN_EMAIL=admin@your-domain.com
ADMIN_PASSWORD_HASH=<bcrypt-hash-of-admin-password>
```

---

## Step 2: Build Docker Images

### Local Build (Testing)
```bash
# Build all services
docker compose -f docker-compose.cloud.yml build --no-cache

# Verify images
docker images | grep horme
```

### Expected Output:
```
horme-frontend     latest    123MB
horme-api          latest    856MB
horme-websocket    latest    845MB
```

---

## Step 3: Deploy Locally (Testing)

### Start All Services
```bash
# Start services
docker compose -f docker-compose.cloud.yml up -d

# View logs
docker compose -f docker-compose.cloud.yml logs -f

# Check health
docker compose -f docker-compose.cloud.yml ps
```

### Verify Services
```bash
# API health check
curl http://localhost:8000/health

# Frontend access
curl http://localhost:3000

# WebSocket test
wscat -c ws://localhost:8001
```

---

## Step 4: Cloud Deployment

### Option A: AWS Deployment

#### Using AWS ECS (Elastic Container Service)

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create ECR repositories
aws ecr create-repository --repository-name horme-frontend
aws ecr create-repository --repository-name horme-api
aws ecr create-repository --repository-name horme-websocket

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag horme-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/horme-frontend:latest
docker tag horme-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/horme-api:latest

# Push images
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/horme-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/horme-api:latest

# Deploy using ECS
./scripts/deploy-aws-ecs.sh
```

#### Using AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk
eb init -p docker horme-pov --region us-east-1

# Create environment
eb create horme-prod --instance-type t3.medium --database.engine postgres

# Deploy
eb deploy

# Open in browser
eb open
```

---

### Option B: Azure Deployment

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create resource group
az group create --name horme-rg --location eastus

# Create container registry
az acr create --resource-group horme-rg --name hormeregistry --sku Basic

# Login to ACR
az acr login --name hormeregistry

# Tag and push images
docker tag horme-frontend:latest hormeregistry.azurecr.io/horme-frontend:latest
docker push hormeregistry.azurecr.io/horme-frontend:latest

# Deploy using Azure Container Instances
./scripts/deploy-azure-aci.sh

# Or deploy using Azure Kubernetes Service
./scripts/deploy-azure-aks.sh
```

---

### Option C: GCP Deployment

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Set project
gcloud config set project horme-pov

# Enable services
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com

# Tag and push to Google Container Registry
docker tag horme-frontend:latest gcr.io/horme-pov/horme-frontend:latest
docker push gcr.io/horme-pov/horme-frontend:latest

# Deploy to Cloud Run
./scripts/deploy-gcp-cloudrun.sh

# Or deploy to GKE (Kubernetes)
./scripts/deploy-gcp-gke.sh
```

---

### Option D: Self-Hosted / On-Premises

```bash
# Using Docker Compose on VM
scp docker-compose.cloud.yml user@your-server:/opt/horme/
scp .env.production user@your-server:/opt/horme/

# SSH to server
ssh user@your-server

# Start services
cd /opt/horme
docker compose -f docker-compose.cloud.yml up -d

# Set up nginx reverse proxy
sudo apt install nginx
sudo cp /opt/horme/nginx/production.conf /etc/nginx/sites-available/horme
sudo ln -s /etc/nginx/sites-available/horme /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Set up SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Step 5: Database Initialization

### Run Database Migrations
```bash
# Connect to API container
docker compose -f docker-compose.cloud.yml exec api bash

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_database.py

# Create admin user
python scripts/create_admin_user.py
```

---

## Step 6: Monitoring Setup

### Prometheus + Grafana (Recommended)

```bash
# Start monitoring stack
docker compose -f docker-compose.cloud.yml --profile monitoring up -d

# Access Grafana
http://your-domain.com:3000

# Default credentials
Username: admin
Password: admin (change immediately)

# Import dashboard
- Go to Dashboards > Import
- Upload: monitoring/grafana/horme-dashboard.json
```

### Cloud Provider Monitoring

**AWS CloudWatch**
```bash
# Enable container insights
aws ecs update-cluster-settings --cluster horme-cluster --settings name=containerInsights,value=enabled

# View logs
aws logs tail /ecs/horme-api --follow
```

**Azure Monitor**
```bash
# Enable monitoring
az monitor log-analytics workspace create --resource-group horme-rg --workspace-name horme-logs

# View logs
az monitor log-analytics query --workspace horme-logs --analytics-query "ContainerLog | limit 100"
```

**GCP Operations (formerly Stackdriver)**
```bash
# Logs automatically collected with Cloud Run

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

## Step 7: SSL/TLS Setup

### Let's Encrypt (Free SSL)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run

# Renewal cron job
sudo crontab -e
0 3 * * * certbot renew --quiet
```

### Cloud Provider SSL

**AWS Certificate Manager**
```bash
# Request certificate
aws acm request-certificate --domain-name your-domain.com --validation-method DNS

# Attach to load balancer
aws elbv2 create-listener --load-balancer-arn <lb-arn> --protocol HTTPS --port 443 --certificates CertificateArn=<cert-arn>
```

**Azure Application Gateway**
```bash
# Upload certificate
az network application-gateway ssl-cert create --gateway-name horme-gateway --resource-group horme-rg --name ssl-cert --cert-file cert.pfx --cert-password <password>
```

**GCP Load Balancer**
```bash
# Create SSL certificate
gcloud compute ssl-certificates create horme-ssl --certificate=cert.pem --private-key=key.pem

# Attach to load balancer
gcloud compute target-https-proxies create horme-https-proxy --ssl-certificates=horme-ssl --url-map=horme-url-map
```

---

## Step 8: Backup Configuration

### Automated Backups
```bash
# Create backup script
cat > /opt/horme/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/horme/backups

# Backup PostgreSQL
docker exec horme-postgres pg_dump -U horme_user horme_db > $BACKUP_DIR/db_$DATE.sql

# Backup volumes
docker run --rm -v horme_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_$DATE.tar.gz /data

# Upload to cloud storage (AWS S3 example)
aws s3 cp $BACKUP_DIR/ s3://horme-backups/ --recursive --exclude "*" --include "*$DATE*"

# Delete local backups older than 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/horme/backup.sh

# Add to cron (daily at 2 AM)
sudo crontab -e
0 2 * * * /opt/horme/backup.sh >> /var/log/horme-backup.log 2>&1
```

---

## Step 9: Scaling & High Availability

### Horizontal Scaling (Docker Compose)
```bash
# Scale API service to 3 instances
docker compose -f docker-compose.cloud.yml up -d --scale api=3 --scale websocket=2

# Verify
docker compose -f docker-compose.cloud.yml ps
```

### Kubernetes (for advanced scaling)
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Scale deployment
kubectl scale deployment horme-api --replicas=5

# Auto-scaling
kubectl autoscale deployment horme-api --min=3 --max=10 --cpu-percent=70
```

---

## Step 10: Health Checks & Alerts

### Health Check Endpoints
```bash
# API health
curl https://your-domain.com/api/health

# Response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "neo4j": "connected"
}

# Detailed health
curl https://your-domain.com/api/health/detailed
```

### Alert Configuration

**Email Alerts (via scripts)**
```bash
# Add to crontab (every 5 minutes)
*/5 * * * * /opt/horme/scripts/health-check.sh
```

**Cloud Provider Alerts**

AWS CloudWatch Alarms:
```bash
aws cloudwatch put-metric-alarm --alarm-name api-high-cpu --alarm-description "API CPU > 80%" --metric-name CPUUtilization --namespace AWS/ECS --statistic Average --period 300 --threshold 80 --comparison-operator GreaterThanThreshold
```

---

## Step 11: Production Verification

### Smoke Tests
```bash
# Run production smoke tests
./scripts/smoke-tests.sh production

# Expected output:
✓ API health check passed
✓ Database connection verified
✓ Redis connection verified
✓ Frontend loading correctly
✓ File upload working
✓ WebSocket connection established
```

### Load Testing
```bash
# Install k6
brew install k6  # macOS
apt install k6   # Ubuntu

# Run load test
k6 run tests/load/api-load-test.js

# Expected metrics:
http_req_duration..........: avg=45ms   med=42ms  max=250ms
http_req_failed............: 0.00% ✓ 0
http_reqs...................: 10000
```

---

## Troubleshooting

### Common Issues

**1. Container won't start**
```bash
# Check logs
docker logs horme-api --tail=50

# Check health
docker inspect horme-api | grep Health
```

**2. Database connection refused**
```bash
# Verify database is running
docker ps | grep postgres

# Test connection from API container
docker exec horme-api psql -h postgres -U horme_user -d horme_db -c "SELECT 1"
```

**3. Out of memory**
```bash
# Check container memory
docker stats

# Increase memory limits in docker-compose.cloud.yml
deploy:
  resources:
    limits:
      memory: 2G  # Increase this
```

**4. SSL certificate issues**
```bash
# Verify certificate
openssl s_client -connect your-domain.com:443

# Renew certificate
sudo certbot renew --force-renewal
```

---

## Maintenance

### Regular Tasks

**Daily**
- Monitor error logs
- Check disk usage
- Verify backups completed

**Weekly**
- Review security logs
- Update packages in containers
- Performance review

**Monthly**
- Rotate secrets
- Security scanning
- Cost optimization review

### Update Deployment
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker compose -f docker-compose.cloud.yml build

# Rolling update (zero downtime)
docker compose -f docker-compose.cloud.yml up -d --no-deps --build api

# Verify
docker compose -f docker-compose.cloud.yml ps
```

---

## Cost Optimization

### Development vs Production

**Development** (~$50/month):
- Smallest instance sizes
- Single region
- No redundancy

**Production** (~$300-500/month):
- Multi-AZ deployment
- Auto-scaling
- Database replicas
- CDN for frontend

### Cost Reduction Tips
1. Use spot instances for non-critical workloads (70% savings)
2. Reserved instances for production (40% savings)
3. Auto-scaling to match demand
4. CDN caching to reduce API calls
5. Compression for storage

---

## Next Steps

1. ✅ Deploy to staging environment
2. ✅ Run full test suite
3. ✅ Configure monitoring and alerts
4. ✅ Set up automated backups
5. ✅ Deploy to production
6. ✅ Monitor for 24 hours
7. ✅ Hand off to operations team

---

## Support

For deployment issues:
- Check CLOUD_DEPLOYMENT_ARCHITECTURE.md
- Review logs: `docker compose logs -f`
- Contact DevOps team

For application issues:
- Check application logs
- Review error tracking dashboard
- Contact development team
