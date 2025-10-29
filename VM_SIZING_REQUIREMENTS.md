# Horme POV - VM Sizing Requirements

## 📊 Executive Summary

**Recommended Minimum VM Configuration:**
- **vCPUs**: 4 cores (8 cores recommended for production)
- **RAM**: 10 GB minimum (16 GB recommended)
- **Storage**: 200 GB SSD (500 GB recommended for growth)
- **Network**: 1 Gbps connection
- **OS**: Ubuntu 20.04+ LTS, CentOS 8+, or equivalent Linux distribution

---

## 🖥️ Detailed Resource Breakdown

### 1. CPU Requirements

| Service | Allocated CPUs | Priority | Notes |
|---------|----------------|----------|-------|
| PostgreSQL | 1.0 vCPU | **Critical** | Database operations, vector search |
| Neo4j | 1.0 vCPU | **Critical** | Knowledge graph queries |
| API (FastAPI) | 0.5 vCPU | **Critical** | Main backend API |
| Redis | 0.25 vCPU | High | Caching & sessions |
| WebSocket | 0.25 vCPU | High | Real-time chat |
| Frontend (Next.js) | 0.25 vCPU | High | Static serving |
| Email Monitor | 0.25 vCPU | High | Email processing |
| Prometheus | 0.5 vCPU | Medium | Metrics collection |
| Grafana | 0.25 vCPU | Medium | Visualization |
| Node Exporter | 0.1 vCPU | Low | System metrics |
| **TOTAL (Limits)** | **4.35 vCPUs** | | |
| **Recommended** | **8 vCPUs** | | For headroom & bursting |

**CPU Sizing Logic:**
- **4 vCPUs**: Minimum for basic operation (all services at limit)
- **6 vCPUs**: Recommended for light production (50% headroom)
- **8 vCPUs**: Recommended for production (100% headroom + bursting)
- **12+ vCPUs**: Heavy load/high concurrency scenarios

---

### 2. Memory (RAM) Requirements

| Service | Allocated RAM | Actual Usage | Notes |
|---------|---------------|--------------|-------|
| **Core Services** | | | |
| PostgreSQL | 2048 MB | ~1.5-2 GB | Shared buffers: 512MB, cache: 2GB |
| Neo4j | 2048 MB | ~1-1.5 GB | Heap: 512MB, page cache: 256MB |
| Redis | 1024 MB | ~200-500 MB | Max memory: 512MB configured |
| **Application Services** | | | |
| API (FastAPI) | 1024 MB | ~300-600 MB | Gunicorn workers, AI models |
| WebSocket | 512 MB | ~150-300 MB | Real-time connections |
| Frontend (Next.js) | 512 MB | ~100-200 MB | Static file serving |
| Email Monitor | 512 MB | ~150-300 MB | Document processing |
| **Monitoring** | | | |
| Prometheus | 1024 MB | ~300-500 MB | 30 days retention |
| Grafana | 512 MB | ~100-200 MB | Dashboards |
| Node Exporter | 128 MB | ~30-50 MB | Lightweight metrics |
| **System Overhead** | ~1024 MB | ~1 GB | OS, Docker daemon |
| **TOTAL** | **~10 GB** | **~6-8 GB** | At typical load |
| **Recommended** | **16 GB** | | For safety & growth |

**Memory Sizing Logic:**
- **8 GB**: Absolute minimum (may cause OOM under load)
- **10 GB**: Minimum for stable operation
- **16 GB**: Recommended for production
- **32 GB**: High-traffic production with large datasets

---

### 3. Storage Requirements

#### A. Docker Images (~75 GB)

| Image | Size | Purpose |
|-------|------|---------|
| horme-pov-api | 11 GB | FastAPI backend (includes ML models) |
| horme-api-uv | 9.25 GB | API with uv package manager |
| horme-websocket-uv | 9.25 GB | WebSocket with uv |
| horme-postgres (pgvector) | 628 MB | PostgreSQL with vector extension |
| horme-pov-email-monitor | 371 MB | Email processing service |
| horme-pov-websocket | 316 MB | WebSocket service |
| horme-pov-frontend | 233 MB | Next.js frontend |
| Neo4j (5.15) | ~500 MB | Knowledge graph database |
| Redis (7-alpine) | ~50 MB | Caching layer |
| Nginx (alpine) | ~40 MB | Reverse proxy |
| Prometheus | ~250 MB | Metrics collection |
| Grafana | ~350 MB | Visualization |
| **TOTAL** | **~32 GB** | Active images |
| **With cache/layers** | **~75 GB** | Build cache included |

#### B. Docker Volumes (~16 GB current, grows over time)

| Volume | Purpose | Initial Size | Growth Rate |
|--------|---------|--------------|-------------|
| **Database Volumes** | | | |
| `postgres_data` | Main database | ~2 GB | **~1-5 GB/month** |
| `postgres_backups` | Database backups | ~500 MB | **~2-10 GB/month** |
| `postgres_logs` | Database logs | ~100 MB | ~500 MB/month |
| `neo4j_data` | Knowledge graph | ~500 MB | **~500 MB - 2 GB/month** |
| `neo4j_logs` | Neo4j logs | ~50 MB | ~100 MB/month |
| `neo4j_import` | Import staging | ~100 MB | Variable |
| `neo4j_plugins` | APOC plugins | ~50 MB | Stable |
| `redis_data` | Cache persistence | ~100 MB | ~200 MB/month |
| `redis_logs` | Redis logs | ~20 MB | ~50 MB/month |
| **Application Volumes** | | | |
| `email_attachments` | RFQ documents | ~1 GB | **~5-20 GB/month** ⚠️ |
| `uploads` | User uploads | ~500 MB | **~2-10 GB/month** |
| `api_logs` | API logs | ~200 MB | ~1 GB/month |
| `email_monitor_logs` | Email logs | ~50 MB | ~200 MB/month |
| `websocket_logs` | WebSocket logs | ~50 MB | ~200 MB/month |
| **Monitoring Volumes** | | | |
| `prometheus_data` | Metrics (30 days) | ~2 GB | ~500 MB/month |
| `grafana_data` | Dashboards | ~100 MB | ~100 MB/month |
| **TOTAL** | | **~16 GB** | **~15-50 GB/month** |

#### C. Storage Sizing Recommendations

| Duration | Minimum Storage | Recommended | Notes |
|----------|----------------|-------------|-------|
| **Initial Setup** | 120 GB | 200 GB | Images + volumes + OS |
| **3 Months** | 180 GB | 300 GB | With typical growth |
| **6 Months** | 240 GB | 400 GB | With attachments |
| **12 Months** | 360 GB | **500 GB** | **Recommended** |
| **Heavy Usage (12 mo)** | 600 GB | 1 TB | High email volume |

**Storage Type:**
- **SSD Required**: PostgreSQL, Neo4j, Redis need low-latency I/O
- **NVMe Recommended**: For production performance
- **IOPS**: Minimum 3,000 IOPS, recommended 10,000+ IOPS

---

## 🌐 Network Requirements

### Bandwidth
- **Minimum**: 100 Mbps
- **Recommended**: 1 Gbps
- **Optimal**: 10 Gbps (for multi-tenant/high-traffic)

### Network Traffic Estimates

| Component | Ingress | Egress | Notes |
|-----------|---------|--------|-------|
| Frontend | ~50 MB/day | ~500 MB/day | Static assets |
| API Requests | ~100 MB/day | ~200 MB/day | JSON responses |
| Email Attachments | **~1-10 GB/day** | ~100 MB/day | RFQ documents ⚠️ |
| OpenAI API | ~50 MB/day | **~500 MB - 2 GB/day** | AI processing |
| Database Backups | ~100 MB/day | ~2-10 GB/day | Off-site backups |
| **TOTAL** | **~2-12 GB/day** | **~3-15 GB/day** | Varies by usage |

### Port Requirements

| Port | Service | Protocol | Public? |
|------|---------|----------|---------|
| 80 | Nginx HTTP | TCP | ✅ Yes |
| 443 | Nginx HTTPS | TCP | ✅ Yes |
| 8002 | Backend API | TCP | Internal |
| 8001 | WebSocket | TCP/WS | Internal |
| 3010 | Frontend | TCP | Internal |
| 5432 | PostgreSQL | TCP | ❌ No |
| 6379 | Redis | TCP | ❌ No |
| 7474 | Neo4j HTTP | TCP | ❌ No |
| 7687 | Neo4j Bolt | TCP | ❌ No |
| 9090 | Prometheus | TCP | Internal |
| 3001 | Grafana | TCP | Internal |

---

## 💻 Recommended VM Configurations

### Option 1: Cloud VM (AWS/Azure/GCP)

#### AWS EC2
**Minimum:**
- **Instance Type**: `t3.xlarge`
- **vCPUs**: 4
- **RAM**: 16 GB
- **Storage**: 200 GB gp3 SSD (3,000 IOPS)
- **Cost**: ~$140/month

**Recommended:**
- **Instance Type**: `t3.2xlarge` or `c6i.2xlarge`
- **vCPUs**: 8
- **RAM**: 32 GB
- **Storage**: 500 GB gp3 SSD (10,000 IOPS)
- **Cost**: ~$280-400/month

#### Azure
**Minimum:**
- **Instance Type**: `Standard_D4s_v3`
- **vCPUs**: 4
- **RAM**: 16 GB
- **Storage**: 200 GB Premium SSD
- **Cost**: ~$150/month

**Recommended:**
- **Instance Type**: `Standard_D8s_v3`
- **vCPUs**: 8
- **RAM**: 32 GB
- **Storage**: 500 GB Premium SSD
- **Cost**: ~$300-450/month

#### Google Cloud
**Minimum:**
- **Instance Type**: `n2-standard-4`
- **vCPUs**: 4
- **RAM**: 16 GB
- **Storage**: 200 GB SSD
- **Cost**: ~$160/month

**Recommended:**
- **Instance Type**: `n2-standard-8`
- **vCPUs**: 8
- **RAM**: 32 GB
- **Storage**: 500 GB SSD
- **Cost**: ~$320-480/month

---

### Option 2: On-Premise/Bare Metal

**Minimum Server Specs:**
```
CPU: Intel Xeon E5-2640 v4 (10 cores, 2.4 GHz) or AMD EPYC 7302P
RAM: 32 GB DDR4 ECC
Storage: 500 GB NVMe SSD (or 1TB RAID10 SSD)
Network: 1 Gbps NIC
```

**Recommended Server Specs:**
```
CPU: Intel Xeon Gold 6248R (24 cores, 3.0 GHz) or AMD EPYC 7542
RAM: 64 GB DDR4 ECC
Storage: 1 TB NVMe SSD (or 2TB RAID10 SSD)
Network: 10 Gbps NIC
RAID: RAID10 for redundancy
UPS: Yes, for data protection
```

---

## 📈 Scaling Guidelines

### Horizontal Scaling Trigger Points

| Metric | Scale Up When | Add Resources |
|--------|---------------|---------------|
| **CPU** | >70% sustained | +2 vCPUs or add API replicas |
| **Memory** | >80% | +8 GB or add API replicas |
| **Storage** | >80% | +100-200 GB |
| **IOPS** | >70% | Upgrade to faster SSD |
| **Network** | >70% | Upgrade bandwidth |
| **API Latency** | >500ms p95 | Add API replicas (load balancer) |
| **DB Connections** | >150/200 | Add read replicas |

### Growth Projections

| Users/Requests | vCPUs | RAM | Storage | Monthly Growth |
|----------------|-------|-----|---------|----------------|
| **100 emails/day** | 4 | 10 GB | 200 GB | ~5 GB/month |
| **500 emails/day** | 8 | 16 GB | 500 GB | ~20 GB/month |
| **2,000 emails/day** | 12 | 32 GB | 1 TB | ~80 GB/month |
| **5,000 emails/day** | 16-24 | 64 GB | 2 TB | ~200 GB/month |

---

## 🔍 Monitoring & Alerting

### Key Metrics to Monitor

1. **CPU Usage**: Alert at >80% for 10 minutes
2. **Memory Usage**: Alert at >85%
3. **Disk Space**: Alert at >75%
4. **Disk IOPS**: Alert at >80% capacity
5. **PostgreSQL Connections**: Alert at >180/200
6. **Neo4j Heap**: Alert at >90%
7. **Redis Memory**: Alert at >450MB/512MB
8. **Email Attachment Volume**: Monitor growth rate

### Recommended Tools
- **Built-in**: Prometheus + Grafana (included in docker-compose)
- **Cloud**: CloudWatch (AWS), Azure Monitor, Cloud Monitoring (GCP)
- **Third-party**: Datadog, New Relic, Grafana Cloud

---

## ⚠️ Critical Considerations

### 1. Email Attachments Storage ⚠️
**Highest Growth Area:**
- Average attachment size: ~2-5 MB per email
- 500 emails/day × 3 MB = **~45 GB/month**
- **Recommendation**: Implement attachment archiving/cleanup policy
- **Alternative**: Use S3/Azure Blob/GCS for attachments (cheaper long-term storage)

### 2. Database Backups
**Current Setup:**
- Backups stored in Docker volume
- **Risk**: If VM fails, backups lost
- **Recommendation**: Off-site backup storage (S3, Azure Blob, GCS)
- **Frequency**: Daily backups, 30-day retention

### 3. OpenAI API Costs
**Not VM cost, but important:**
- Document processing: ~$0.01-0.05 per email
- 500 emails/day = **~$5-25/day** = **$150-750/month**
- **Recommendation**: Budget separately for AI API costs

### 4. SSL/TLS Certificates
- Let's Encrypt (free, auto-renewal)
- Wildcard cert recommended for subdomains

---

## 📋 Pre-Deployment Checklist

### VM Preparation
- [ ] Ubuntu 20.04+ LTS or equivalent installed
- [ ] Docker 24.0+ installed
- [ ] Docker Compose v2.20+ installed
- [ ] Firewall configured (ports 80, 443 open)
- [ ] SSH access configured
- [ ] Non-root user with sudo privileges
- [ ] Swap space configured (8-16 GB)
- [ ] Time synchronization (NTP) enabled

### Storage Configuration
- [ ] SSD/NVMe storage confirmed
- [ ] Minimum 200 GB available
- [ ] Automatic volume expansion enabled (cloud VMs)
- [ ] Backup destination configured
- [ ] Monitoring for disk space set up

### Network Configuration
- [ ] Static IP assigned (or Elastic IP)
- [ ] DNS records configured
- [ ] SSL certificate obtained
- [ ] Firewall rules configured
- [ ] Security groups configured (cloud)

### Security
- [ ] SSH key-based auth only
- [ ] Fail2ban installed
- [ ] UFW/iptables configured
- [ ] Automatic security updates enabled
- [ ] Secrets in `.env.production` (not in git)
- [ ] Strong passwords for all services

---

## 🚀 Quick Sizing Decision Matrix

**Choose Your Tier:**

| Use Case | vCPUs | RAM | Storage | Monthly Cost |
|----------|-------|-----|---------|--------------|
| **Development/Testing** | 2-4 | 8 GB | 100 GB | $50-100 |
| **Small Production (<100 emails/day)** | 4 | 16 GB | 200 GB | $140-180 |
| **Medium Production (100-500 emails/day)** | 8 | 32 GB | 500 GB | $280-400 |
| **Large Production (500-2000 emails/day)** | 12-16 | 64 GB | 1 TB | $500-800 |
| **Enterprise (>2000 emails/day)** | 16-24 | 128 GB | 2 TB | $1000+ |

---

## 📞 Support & Documentation

- **Deployment Guide**: See `docs/VM_PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Security Guide**: See `SECURITY_CHECKLIST.md`
- **Monitoring Setup**: See `deployment/monitoring/README.md`
- **Backup Strategy**: See `scripts/backup.sh`

---

**Last Updated**: 2025-10-27
**Version**: 1.0
**Reviewed By**: Claude Code Assistant
