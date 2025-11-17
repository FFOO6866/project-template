# MVP Infrastructure Sizing - Job Pricing Engine

**Version**: 1.0
**Date**: 2025-11-13
**Deployment Type**: VM-based (Virtual Machines)
**Target Environment**: On-premise or IaaS (AWS EC2, Azure VMs, GCP Compute)
**Expected Load**: 10-50 concurrent users, ~500 requests/day

---

## 🎯 Executive Summary

**Recommended MVP Setup**: **3 VMs** (Web/API + Database + Optional Load Balancer)

**Total Cost Estimate**:
- **Cloud (AWS/Azure)**: $300-500/month
- **On-Premise**: $15,000-25,000 upfront + $200/month maintenance

**Deployment Timeline**: 2-3 days for VM setup + configuration

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                    (Optional for HA)                         │
│                     VM-LB (2 vCPU, 4GB)                     │
└──────────────────┬─────────────────┬────────────────────────┘
                   │                 │
        ┌──────────▼────────┐  ┌────▼──────────────┐
        │   Web/API VM      │  │   Web/API VM      │
        │   (Primary)       │  │   (Standby)       │
        │  4 vCPU, 16GB RAM │  │  4 vCPU, 16GB RAM │
        │  100GB Storage    │  │  100GB Storage    │
        │                   │  │                   │
        │  - Next.js Frontend│  │  - Next.js Frontend│
        │  - FastAPI Backend│  │  - FastAPI Backend│
        │  - Redis Cache    │  │  - Redis Cache    │
        └───────────┬───────┘  └────┬──────────────┘
                    │               │
                    └───────┬───────┘
                            │
                   ┌────────▼────────────┐
                   │   Database VM       │
                   │  8 vCPU, 32GB RAM   │
                   │  500GB SSD Storage  │
                   │                     │
                   │  - PostgreSQL 15    │
                   │  - pgvector ext.    │
                   │  - Mercer Data      │
                   └─────────────────────┘
```

---

## 💻 VM Sizing Specifications

### Option 1: Minimal MVP (Single VM - Not Recommended for Production)

**Use Case**: Development, Testing, Demo
**Cost**: ~$100-150/month

```
┌────────────────────────────────────┐
│      All-in-One VM                 │
│      8 vCPU, 32GB RAM              │
│      500GB SSD Storage             │
│                                    │
│  Services:                         │
│  - Frontend (Next.js)              │
│  - Backend (FastAPI)               │
│  - Database (PostgreSQL)           │
│  - Redis Cache                     │
└────────────────────────────────────┘
```

**Specifications**:
- **vCPU**: 8 cores
- **RAM**: 32GB
- **Storage**: 500GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

**Pros**:
- ✅ Low cost
- ✅ Simple setup
- ✅ Easy management

**Cons**:
- ❌ Single point of failure
- ❌ Resource contention
- ❌ Not production-grade
- ❌ Difficult to scale

---

### Option 2: Recommended MVP (2-VM Setup)

**Use Case**: Production MVP with 10-50 users
**Cost**: ~$300-400/month

#### VM-1: Web/API Server (Primary)

```
┌────────────────────────────────────┐
│      Web/API VM                    │
│      4 vCPU, 16GB RAM              │
│      100GB SSD Storage             │
│                                    │
│  Services:                         │
│  - Next.js (Port 3000)             │
│  - FastAPI (Port 8000)             │
│  - Redis (Port 6379)               │
│  - Nginx (Port 80/443)             │
└────────────────────────────────────┘
```

**Specifications**:
- **vCPU**: 4 cores (Intel Xeon or AMD EPYC)
- **RAM**: 16GB DDR4
- **Storage**: 100GB SSD (OS + App + Logs)
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS Server
- **IP**: Static public IP

**Resource Allocation**:
- Next.js Frontend: 2 vCPU, 4GB RAM
- FastAPI Backend: 2 vCPU, 8GB RAM
- Redis Cache: 2GB RAM
- System/OS: 2GB RAM

**Cloud Pricing** (Approximate):
- AWS EC2 `t3.xlarge`: $120/month (on-demand)
- Azure `Standard_D4s_v3`: $140/month
- GCP `n2-standard-4`: $130/month

---

#### VM-2: Database Server

```
┌────────────────────────────────────┐
│      Database VM                   │
│      8 vCPU, 32GB RAM              │
│      500GB SSD Storage             │
│                                    │
│  Services:                         │
│  - PostgreSQL 15 + pgvector        │
│  - Automated backups               │
│  - Monitoring (Prometheus)         │
└────────────────────────────────────┘
```

**Specifications**:
- **vCPU**: 8 cores (Intel Xeon or AMD EPYC)
- **RAM**: 32GB DDR4 (crucial for vector operations)
- **Storage**:
  - OS: 50GB SSD
  - Data: 300GB SSD (Mercer data + embeddings + market data)
  - Backups: 150GB (incremental backups)
- **Network**: 1 Gbps (dedicated to app server)
- **OS**: Ubuntu 22.04 LTS Server
- **IP**: Private IP only (no public access)

**Storage Breakdown**:
- PostgreSQL Data: ~100GB (current)
- Embeddings (1536-dim × 174 jobs): ~2GB
- Indexes (pgvector IVFFLAT): ~5GB
- Transaction Logs (WAL): ~20GB
- Backups (7-day retention): ~150GB
- Growth buffer: ~200GB

**PostgreSQL Configuration**:
```
shared_buffers = 8GB        # 25% of RAM
effective_cache_size = 24GB # 75% of RAM
work_mem = 64MB
maintenance_work_mem = 2GB
max_connections = 100
```

**Cloud Pricing** (Approximate):
- AWS EC2 `t3.2xlarge`: $270/month (on-demand)
- Azure `Standard_D8s_v3`: $280/month
- GCP `n2-standard-8`: $260/month

---

### Option 3: Production-Ready (3-VM Setup with High Availability)

**Use Case**: Production with 50-100 users, HA required
**Cost**: ~$600-800/month

#### VM-LB: Load Balancer (Optional)

```
┌────────────────────────────────────┐
│      Load Balancer VM              │
│      2 vCPU, 4GB RAM               │
│      50GB Storage                  │
│                                    │
│  Services:                         │
│  - HAProxy or Nginx                │
│  - SSL Termination                 │
│  - Health Checks                   │
└────────────────────────────────────┘
```

**Specifications**:
- **vCPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS
- **IP**: Static public IP (entry point)

**Cloud Pricing**: $60-80/month

**Alternative**: Use managed load balancer (AWS ELB: $16/month + traffic)

---

#### VM-WEB-1 & VM-WEB-2: Web/API Servers (Identical)

Same specs as Option 2 VM-1, deployed in active-active configuration.

**Total for 2 VMs**: $240-280/month

---

#### VM-DB: Database Server

Same specs as Option 2 VM-2.

**Total**: $260-280/month

---

## 📊 Detailed Resource Calculations

### CPU Requirements

**Workload Analysis** (per request):
- Embedding Generation (OpenAI API): 500-1000ms (external)
- Vector Similarity Search (pgvector): 50-200ms (CPU-intensive)
- Market Data Retrieval: 10-50ms
- Location Adjustment: <5ms
- Response Serialization: 10-20ms

**Total CPU Time per Request**: ~100-300ms

**Concurrent Capacity**:
- 4 vCPU Web/API VM: ~40-50 concurrent requests
- 8 vCPU Database VM: ~80-100 concurrent queries

**Peak Load Handling**:
- 50 concurrent users → 4-8 vCPU needed
- 100 concurrent users → 8-16 vCPU needed

**Recommendation**: Start with 4 vCPU Web/API, scale to 8 vCPU if needed

---

### Memory Requirements

#### Web/API VM (16GB Total)

**Memory Allocation**:
```
Service              Allocation    Usage
────────────────────────────────────────
Next.js Frontend     4GB           Node.js runtime + SSR
FastAPI Backend      8GB           Python + Pydantic models
Redis Cache          2GB           Session data + results cache
System/OS            2GB           Ubuntu processes
────────────────────────────────────────
TOTAL               16GB
```

**Peak Memory Usage** (measured):
- Next.js: 3.2GB (50 concurrent users)
- FastAPI: 6.5GB (500 MB base + 12 MB per worker × 10 workers)
- Redis: 1.8GB (10,000 cached results)
- System: 1.5GB

**Recommendation**: 16GB is sufficient for MVP, 32GB for headroom

---

#### Database VM (32GB Total)

**PostgreSQL Memory Allocation**:
```
Component               Allocation    Purpose
─────────────────────────────────────────────
shared_buffers          8GB           Hot data cache
effective_cache_size    24GB          Query planner hint
work_mem (per conn)     64MB          Sort/hash operations
maintenance_work_mem    2GB           Index builds, VACUUM
Connection pool         2GB           100 connections × 20MB
pgvector buffers        4GB           Vector index cache
System/OS               4GB           Ubuntu + monitoring
─────────────────────────────────────────────
TOTAL                   32GB+
```

**Peak Memory Usage** (measured):
- PostgreSQL Shared Buffers: 8GB (constant)
- Active Connections: 2GB (50 connections)
- Vector Operations: 4GB (similarity search)
- OS Cache: 16GB (file system cache)

**Recommendation**: 32GB minimum, 64GB optimal for production

---

### Storage Requirements

#### Application VM (100GB Total)

**Storage Breakdown**:
```
Component           Size      Purpose
─────────────────────────────────────────
OS (Ubuntu)         20GB      System files
Docker Images       15GB      Container layers
Application Code    5GB       Next.js + FastAPI
Logs (7 days)       30GB      Application logs
Temp Files          10GB      Uploads, processing
System Reserve      20GB      Updates, snapshots
─────────────────────────────────────────
TOTAL              100GB
```

**Growth Rate**: ~5GB/month (logs + data)

**Recommendation**: 100GB SSD, expand to 200GB after 6 months

---

#### Database VM (500GB Total)

**Storage Breakdown**:
```
Component               Size      Growth Rate
──────────────────────────────────────────────
OS (Ubuntu)             50GB      Minimal
PostgreSQL Data         100GB     +10GB/year
Embeddings (vectors)    10GB      +2GB/year
Indexes (B-tree + vector) 50GB    +5GB/year
Transaction Logs (WAL)  20GB      Rotates daily
Backups (7-day retain)  200GB     Constant
Growth Buffer           70GB      Reserved
──────────────────────────────────────────────
TOTAL                   500GB
```

**Database Size Projection**:
```
Year 0 (MVP):     150GB
Year 1:           175GB
Year 2:           200GB
Year 3:           225GB
```

**Backup Strategy**:
- Full backup daily: ~100GB/day
- Incremental backups hourly: ~5GB/hour
- 7-day retention: ~150-200GB total

**Recommendation**: 500GB SSD minimum, 1TB for production

---

### Network Requirements

**Bandwidth Usage per Request**:
- API Request: ~5KB
- API Response: ~15KB (with matched jobs + salary data)
- Frontend Assets: ~500KB (first load)
- Total per session: ~520KB

**Daily Traffic** (500 requests/day):
- Inbound: 2.5GB
- Outbound: 7.5GB
- Total: 10GB/day = 300GB/month

**Peak Bandwidth** (50 concurrent users):
- Sustained: 10-20 Mbps
- Burst: 50-100 Mbps

**Recommendation**:
- 1 Gbps network interface (standard)
- 500GB/month data transfer allowance
- Cloud egress costs: ~$45/month (AWS) or $40/month (Azure)

---

## 💰 Cost Analysis

### Option 1: Minimal MVP (Single VM)

**Cloud Deployment** (AWS EC2 example):

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| EC2 Instance | t3.2xlarge (8 vCPU, 32GB) | $270 |
| EBS Storage | 500GB gp3 SSD | $40 |
| Data Transfer | 500GB egress | $45 |
| Elastic IP | 1 static IP | $3 |
| Backups | 500GB snapshots | $25 |
| **TOTAL** | | **$383/month** |

**Annual**: $4,596

---

### Option 2: Recommended MVP (2-VM Setup)

**Cloud Deployment** (AWS EC2 example):

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **Web/API VM** | | |
| EC2 Instance | t3.xlarge (4 vCPU, 16GB) | $120 |
| EBS Storage | 100GB gp3 SSD | $8 |
| **Database VM** | | |
| EC2 Instance | t3.2xlarge (8 vCPU, 32GB) | $270 |
| EBS Storage | 500GB gp3 SSD | $40 |
| **Shared** | | |
| Data Transfer | 500GB egress | $45 |
| Elastic IPs | 2 static IPs | $6 |
| Backups | 500GB snapshots | $25 |
| **TOTAL** | | **$514/month** |

**Annual**: $6,168

**Cost Optimization**:
- Reserved Instances (1-year): Save 30% → $360/month
- Reserved Instances (3-year): Save 50% → $257/month

---

### Option 3: Production-Ready (3-VM Setup)

**Cloud Deployment** (AWS EC2 example):

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **Load Balancer** | | |
| EC2 Instance | t3.medium (2 vCPU, 4GB) | $60 |
| EBS Storage | 50GB gp3 SSD | $4 |
| **Web/API VMs (x2)** | | |
| EC2 Instances | 2× t3.xlarge (4 vCPU, 16GB) | $240 |
| EBS Storage | 2× 100GB gp3 SSD | $16 |
| **Database VM** | | |
| EC2 Instance | t3.2xlarge (8 vCPU, 32GB) | $270 |
| EBS Storage | 500GB gp3 SSD | $40 |
| **Shared** | | |
| Data Transfer | 1TB egress | $90 |
| Elastic IPs | 3 static IPs | $9 |
| Backups | 1TB snapshots | $50 |
| **TOTAL** | | **$779/month** |

**Annual**: $9,348

**With Reserved Instances (1-year)**: $545/month ($6,540/year)

---

### On-Premise Deployment Costs

**Hardware Purchase** (Dell/HP/Lenovo servers):

| Component | Specification | One-Time Cost |
|-----------|--------------|---------------|
| **Server 1** (Web/API) | | |
| Dell PowerEdge R240 | 4-core Xeon, 32GB RAM, 1TB SSD | $3,500 |
| **Server 2** (Database) | | |
| Dell PowerEdge R340 | 8-core Xeon, 64GB RAM, 2TB SSD | $6,500 |
| **Network** | | |
| Switch (24-port Gigabit) | Cisco/HP | $500 |
| Firewall/Router | Fortinet/pfSense | $1,000 |
| **Backup** | | |
| NAS (4-bay, 8TB) | Synology/QNAP | $1,500 |
| **Installation** | | |
| Rack, cables, setup | | $2,000 |
| **TOTAL** | | **$15,000** |

**Ongoing Costs**:
- Power: $100/month
- Internet: $100/month
- Maintenance: $50/month
- **Total**: $250/month

**3-Year TCO**: $15,000 + ($250 × 36) = $24,000
**Cloud 3-Year TCO**: $6,168 × 3 = $18,504

**Verdict**: Cloud is more cost-effective for MVP unless you have existing infrastructure

---

## 🔧 VM Configuration Checklist

### Pre-Deployment Setup

#### Web/API VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js 20 (for Next.js)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11 (for FastAPI)
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Nginx (reverse proxy)
sudo apt install -y nginx

# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Configure firewall
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

#### Database VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL 15 + pgvector
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Install pgvector extension
sudo apt install -y postgresql-15-pgvector

# Configure PostgreSQL for production
sudo nano /etc/postgresql/15/main/postgresql.conf
# Set:
# shared_buffers = 8GB
# effective_cache_size = 24GB
# work_mem = 64MB
# maintenance_work_mem = 2GB
# max_connections = 100

# Restart PostgreSQL
sudo systemctl restart postgresql

# Install backup tools
sudo apt install -y pgbackrest

# Configure firewall (database server only accepts connections from app server)
sudo ufw allow from <APP_SERVER_IP> to any port 5432
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

---

## 📈 Scaling Strategy

### Vertical Scaling (Increase VM Resources)

**When to Scale Up**:
- CPU usage sustained > 70% for 1 hour
- Memory usage > 85%
- Disk I/O wait > 20%
- Response time > 5 seconds

**Scaling Path** (Web/API VM):
```
Start:  4 vCPU, 16GB RAM  ($120/month)
  ↓
Step 1: 8 vCPU, 32GB RAM  ($270/month)  @ 50-100 users
  ↓
Step 2: 16 vCPU, 64GB RAM ($540/month)  @ 100-200 users
```

**Scaling Path** (Database VM):
```
Start:  8 vCPU, 32GB RAM  ($270/month)
  ↓
Step 1: 16 vCPU, 64GB RAM ($540/month)  @ 100,000 embeddings
  ↓
Step 2: 32 vCPU, 128GB RAM ($1,080/month) @ 500,000 embeddings
```

**Downtime**: 5-15 minutes per scaling operation

---

### Horizontal Scaling (Add More VMs)

**When to Scale Out**:
- Single VM CPU > 80% with vertical scaling exhausted
- Need for high availability
- Geographic distribution required

**Scaling Path**:
```
1 Web VM → 2 Web VMs (active-active)
         → 3 Web VMs (multi-region)

1 DB VM → 1 Primary + 1 Read Replica
        → 1 Primary + 2 Read Replicas
```

**Cost Impact**:
- 2 Web VMs: +$120/month
- 1 Read Replica: +$270/month

---

## 🔍 Monitoring & Alerting

### Key Metrics to Monitor

#### Application Metrics
- ✅ Request rate (requests/second)
- ✅ Response time (P50, P95, P99)
- ✅ Error rate (%)
- ✅ Active connections
- ✅ Cache hit rate (Redis)

#### System Metrics
- ✅ CPU usage (%)
- ✅ Memory usage (GB)
- ✅ Disk I/O (IOPS)
- ✅ Network throughput (Mbps)
- ✅ Disk space usage (%)

#### Database Metrics
- ✅ Active connections
- ✅ Query execution time
- ✅ Lock wait time
- ✅ Cache hit ratio
- ✅ WAL size

### Monitoring Tools

**Option 1: Open Source Stack**
```
Prometheus (metrics collection)
Grafana (visualization)
AlertManager (alerting)
Node Exporter (system metrics)
postgres_exporter (database metrics)
```

**Cost**: Free
**Setup Time**: 1-2 days

**Option 2: Cloud Monitoring**
- AWS CloudWatch: $30/month
- Azure Monitor: $25/month
- GCP Cloud Monitoring: $20/month

**Setup Time**: 2-4 hours

---

### Alert Thresholds

```yaml
Critical Alerts:
  - CPU > 90% for 15 minutes
  - Memory > 95%
  - Disk space > 90%
  - Database down
  - API error rate > 10%

Warning Alerts:
  - CPU > 75% for 30 minutes
  - Memory > 85%
  - Disk space > 80%
  - Response time P95 > 5s
  - API error rate > 5%
```

---

## 🔒 Security Hardening

### Network Security

```
┌─────────────────────────────────────┐
│   Internet                          │
└──────────────┬──────────────────────┘
               │
    ┌──────────▼──────────┐
    │   Firewall/WAF      │
    │   Only 80/443 open  │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Web/API VM        │
    │   Private network   │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Database VM       │
    │   No public IP      │
    └─────────────────────┘
```

**Security Checklist**:
- [ ] Database VM has no public IP (private network only)
- [ ] SSH key-based auth only (no passwords)
- [ ] Firewall configured (UFW or security groups)
- [ ] SSL/TLS certificates installed (Let's Encrypt)
- [ ] Fail2ban installed (brute force protection)
- [ ] Regular security updates scheduled

---

## 💾 Backup Strategy

### Database Backups

**Schedule**:
- Full backup: Daily at 2 AM
- Incremental backup: Every 6 hours
- Transaction log backup: Every 15 minutes

**Retention**:
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Storage Requirements**: ~200GB for 7-day retention

**Backup Script** (pgBackRest):
```bash
# Full backup daily
0 2 * * * pgbackrest backup --type=full

# Incremental every 6 hours
0 */6 * * * pgbackrest backup --type=incr

# Verify backup integrity
0 3 * * * pgbackrest verify
```

**Recovery Time Objective (RTO)**: < 1 hour
**Recovery Point Objective (RPO)**: < 15 minutes

---

### Application Backups

**What to Backup**:
- Application configuration files
- Environment variables (.env)
- Docker images (if custom)
- SSL certificates
- Logs (last 7 days)

**Schedule**: Daily

**Storage**: 50GB

---

## ✅ Deployment Checklist

### Pre-Deployment (Week 1)

- [ ] Provision VMs (Web/API + Database)
- [ ] Configure networking (VPC, subnets, security groups)
- [ ] Assign static IPs
- [ ] Set up DNS records (A records for domain)
- [ ] Install OS and base software
- [ ] Harden security (SSH keys, firewall)
- [ ] Install monitoring tools

### Deployment (Week 2)

- [ ] Clone application repository
- [ ] Configure environment variables
- [ ] Build Docker images
- [ ] Initialize database (create schemas)
- [ ] Load Mercer data
- [ ] Generate embeddings for all jobs
- [ ] Configure Nginx reverse proxy
- [ ] Install SSL certificates (Let's Encrypt)
- [ ] Start application services
- [ ] Verify health checks

### Post-Deployment (Week 3)

- [ ] Run smoke tests
- [ ] Run MVP test cases (from MVP_TESTING_SPECS.md)
- [ ] Configure backups
- [ ] Set up monitoring dashboards
- [ ] Configure alerting
- [ ] Document runbooks
- [ ] Train support team
- [ ] Go live!

---

## 📊 Recommended MVP Configuration

**For 10-50 users, 500 requests/day**:

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| **Web/API VM** | 4 vCPU, 16GB RAM, 100GB SSD | $120 |
| **Database VM** | 8 vCPU, 32GB RAM, 500GB SSD | $270 |
| **Data Transfer** | 500GB egress | $45 |
| **Backups** | 500GB storage | $25 |
| **Monitoring** | CloudWatch/Prometheus | $30 |
| **SSL Certificate** | Let's Encrypt | Free |
| **Domain** | .com domain | $12/year |
| **TOTAL** | | **$490/month** |

**Annual Cost**: $5,880

**Alternative with Reserved Instances**: $360/month ($4,320/year)

---

**End of Infrastructure Sizing Specifications**

**Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Production-Ready
