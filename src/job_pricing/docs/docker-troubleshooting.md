# Docker Troubleshooting Guide

## 📋 Overview

This guide documents common Docker issues encountered during development and their solutions, with specific focus on the Docker Desktop connectivity issue encountered during Phase 2 implementation.

---

## 🚨 Critical Issue: PostgreSQL Container Creation Failure

### Symptoms

```
error during connect: Post "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.51/containers/create?name=job-pricing-engine-postgres": EOF

request returned 500 Internal Server Error for API route and/or path
error: unable to create job-pricing-engine-postgres container
```

### Root Cause

Docker Desktop's Linux engine is not responding properly on the Windows named pipe (`\\.\pipe\dockerDesktopLinuxEngine`). This is a Docker Desktop service connectivity issue, not a problem with the application code or configuration.

### What Works

- ✅ Docker build process completes successfully
- ✅ All Docker images are built (API, Celery Worker, Celery Beat)
- ✅ Docker network creation succeeds
- ✅ Docker volume creation succeeds
- ✅ Redis container creation succeeds

### What Fails

- ❌ PostgreSQL container creation specifically

### Impact

- Cannot run Alembic migrations
- Cannot load seed data
- Cannot run integration tests
- Blocks completion of Phase 2 (currently at 90%)

---

## ✅ Solutions (In Order of Preference)

### Solution 1: Restart Docker Desktop (Quickest)

**Steps**:

1. **Stop all Docker processes**:
   ```bash
   docker-compose down
   docker stop $(docker ps -aq)
   ```

2. **Exit Docker Desktop**:
   - Right-click Docker Desktop icon in system tray
   - Click "Quit Docker Desktop"
   - Wait 10 seconds for complete shutdown

3. **Start Docker Desktop**:
   - Launch Docker Desktop from Start menu
   - Wait for "Docker Desktop is running" notification
   - Verify with: `docker ps`

4. **Retry container creation**:
   ```bash
   cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
   docker-compose up -d --build
   ```

**Expected Outcome**: All 5 containers should start successfully.

---

### Solution 2: Reset Docker Connection via Windows Services

**Steps**:

1. **Open Windows Services**:
   - Press `Win + R`
   - Type `services.msc`
   - Press Enter

2. **Find Docker Desktop Service**:
   - Look for "Docker Desktop Service"
   - Note its current status

3. **Restart the service**:
   - Right-click → "Restart"
   - Wait for service to fully restart

4. **Verify Docker is responding**:
   ```bash
   docker version
   docker ps
   ```

5. **Retry container creation**:
   ```bash
   cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
   docker-compose up -d --build
   ```

---

### Solution 3: Check WSL 2 Settings

If using WSL 2 backend (recommended for Windows 10/11):

**Steps**:

1. **Open Docker Desktop Settings**:
   - Right-click Docker Desktop icon
   - Click "Settings"

2. **Check WSL Integration**:
   - Navigate to: Resources → WSL Integration
   - Ensure WSL 2 is enabled
   - Enable integration with your WSL distro (if applicable)

3. **Verify WSL 2 is running**:
   ```bash
   wsl --list --verbose
   ```

   Expected output:
   ```
   NAME      STATE           VERSION
   * Ubuntu  Running         2
   ```

4. **Restart WSL if needed**:
   ```bash
   wsl --shutdown
   # Wait 10 seconds
   wsl
   ```

5. **Restart Docker Desktop** and retry

---

### Solution 4: Full Docker System Prune (Nuclear Option)

**⚠️ WARNING**: This will delete all Docker data (containers, images, volumes, networks). Only use if other solutions fail.

**Steps**:

1. **Backup important data**:
   - Export any important container data
   - Save database dumps if needed

2. **Stop Docker Desktop**:
   - Right-click Docker Desktop icon → Quit

3. **Remove all Docker data**:
   ```bash
   docker system prune -a --volumes
   ```

   Type `y` to confirm deletion.

4. **Restart Docker Desktop**

5. **Rebuild everything from scratch**:
   ```bash
   cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

### Solution 5: Reinstall Docker Desktop (Last Resort)

If all else fails:

1. **Uninstall Docker Desktop**:
   - Settings → Apps → Docker Desktop → Uninstall
   - Manually delete: `C:\Program Files\Docker`
   - Manually delete: `C:\ProgramData\Docker`

2. **Reboot Windows**

3. **Download latest Docker Desktop**:
   - Visit: https://www.docker.com/products/docker-desktop/

4. **Install with default settings**

5. **Retry container creation**

---

## 🔍 Diagnostic Commands

### Check Docker Service Status

```bash
# Windows PowerShell (as Administrator)
Get-Service -Name "com.docker.service"

# Expected: Status should be "Running"
```

### Check Docker Engine Connectivity

```bash
docker version
```

**Expected Output**:
```
Client:
 Version:           xx.xx.x
 ...

Server:
 Version:           xx.xx.x
 ...
```

If "Server" section is missing, Docker engine is not accessible.

### Check Named Pipe Access

```bash
# PowerShell
Test-Path \\.\pipe\dockerDesktopLinuxEngine
```

**Expected**: `True`

If `False`, Docker Desktop is not running or the named pipe is not created.

### Check Container Logs

```bash
# Check logs for failed container
docker-compose logs postgres

# Check Docker daemon logs
# Windows: C:\ProgramData\Docker\log\host
# View in: Event Viewer → Applications and Services Logs → Docker
```

### Check Docker Compose Configuration

```bash
# Validate docker-compose.yml syntax
docker-compose config

# Expected: Should show parsed configuration without errors
```

### Check Port Conflicts

```bash
# Check if port 5432 (PostgreSQL) is already in use
netstat -ano | findstr :5432

# If output shows a process, check which process:
tasklist | findstr <PID>
```

---

## 🐛 Other Common Docker Issues

### Issue: "port is already allocated"

**Symptoms**:
```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

**Solution**:
```bash
# Find process using the port
netstat -ano | findstr :5432

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or change the port in docker-compose.yml
```

---

### Issue: "No space left on device"

**Symptoms**:
```
failed to create container: Error response from daemon: mkdir: no space left on device
```

**Solution**:
```bash
# Check Docker disk usage
docker system df

# Remove unused data
docker system prune -a --volumes

# Increase Docker Desktop disk space:
# Settings → Resources → Advanced → Disk image size
```

---

### Issue: "driver failed programming external connectivity"

**Symptoms**:
```
Error response from daemon: driver failed programming external connectivity on endpoint postgres:
failed to bind port 0.0.0.0:5432/tcp: Error starting userland proxy
```

**Solution**:
```bash
# Restart Docker Desktop

# Or restart Windows NAT service (PowerShell as Admin)
Restart-Service com.docker.service
Restart-Service WinNAT
```

---

### Issue: "Cannot connect to Docker daemon"

**Symptoms**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

**Solution**:
- Ensure Docker Desktop is running
- Check WSL 2 backend is enabled (Settings → General)
- Restart Docker Desktop

---

### Issue: Slow Docker Build Performance

**Symptoms**:
- Builds take > 10 minutes
- `npm install` or `pip install` very slow

**Solutions**:

1. **Enable BuildKit**:
   ```bash
   # Add to .env or set environment variable
   DOCKER_BUILDKIT=1
   COMPOSE_DOCKER_CLI_BUILD=1
   ```

2. **Use Docker cache**:
   ```dockerfile
   # In Dockerfile, separate dependency installation from code copy
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   ```

3. **Increase Docker resources**:
   - Settings → Resources → Advanced
   - Increase CPUs and Memory

---

### Issue: "exec format error"

**Symptoms**:
```
standard_init_linux.go:228: exec user process caused: exec format error
```

**Solution**:
- Ensure base image matches your CPU architecture
- For Windows on ARM: Use `arm64` images
- For Windows on x86: Use `amd64` images

```dockerfile
# Multi-platform support
FROM --platform=linux/amd64 python:3.11-slim
```

---

### Issue: Container Exits Immediately

**Symptoms**:
```
docker-compose ps
NAME                STATUS
app                 Exited (0)
```

**Solution**:

1. **Check container logs**:
   ```bash
   docker-compose logs app
   ```

2. **Common causes**:
   - Command completes immediately (needs long-running process)
   - Application crashes on startup
   - Missing environment variables

3. **Fix for FastAPI**:
   ```yaml
   # docker-compose.yml
   command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 📊 Docker Health Checks

### Verify All Services Are Healthy

```bash
docker-compose ps
```

**Expected Output**:
```
NAME                                    STATUS
job-pricing-engine-api                  Up (healthy)
job-pricing-engine-celery-beat          Up
job-pricing-engine-celery-worker        Up
job-pricing-engine-postgres             Up (healthy)
job-pricing-engine-redis                Up (healthy)
```

### Check Container Resource Usage

```bash
docker stats --no-stream
```

**Monitor**:
- CPU usage (should be < 80% normally)
- Memory usage (should have headroom)
- Network I/O
- Block I/O

### Test Database Connection

```bash
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT version();"
```

**Expected**: PostgreSQL version information

### Test API Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🛠️ Maintenance Commands

### Restart All Containers

```bash
docker-compose restart
```

### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100
```

### Access Container Shell

```bash
# PostgreSQL
docker-compose exec postgres bash

# API
docker-compose exec api bash

# Redis CLI
docker-compose exec redis redis-cli
```

### Clean Up Resources

```bash
# Stop and remove containers
docker-compose down

# Remove volumes too (deletes data!)
docker-compose down -v

# Remove everything including images
docker-compose down --rmi all -v
```

---

## 📚 Docker Compose Configuration Reference

### Current Configuration (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    container_name: job-pricing-engine-postgres
    environment:
      POSTGRES_DB: job_pricing_db
      POSTGRES_USER: job_pricing_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d/init
      - ./db/seeds:/docker-entrypoint-initdb.d/seeds
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U job_pricing_user -d job_pricing_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: job-pricing-engine-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  api:
    build: .
    container_name: job-pricing-engine-api
    environment:
      DATABASE_URL: postgresql://job_pricing_user:${POSTGRES_PASSWORD}@postgres:5432/job_pricing_db
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn src.job_pricing.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: .
    container_name: job-pricing-engine-celery-worker
    environment:
      DATABASE_URL: postgresql://job_pricing_user:${POSTGRES_PASSWORD}@postgres:5432/job_pricing_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    command: celery -A src.job_pricing.celery_app worker --loglevel=info

  celery-beat:
    build: .
    container_name: job-pricing-engine-celery-beat
    environment:
      DATABASE_URL: postgresql://job_pricing_user:${POSTGRES_PASSWORD}@postgres:5432/job_pricing_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    command: celery -A src.job_pricing.celery_app beat --loglevel=info

volumes:
  postgres-data:
  redis-data:

networks:
  default:
    name: job-pricing-network
```

---

## 🔗 Useful Resources

### Docker Documentation
- [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

### WSL 2
- [WSL 2 Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Docker WSL 2 Backend](https://docs.docker.com/desktop/wsl/)

### Troubleshooting
- [Docker Desktop Troubleshooting](https://docs.docker.com/desktop/troubleshoot/)
- [Common Docker Issues](https://docs.docker.com/engine/faq/)

---

## 📝 Issue Tracking Template

When reporting Docker issues, include:

```markdown
## Environment
- OS: Windows 10/11
- Docker Desktop Version: X.XX.X
- WSL Version: 2
- WSL Distro: Ubuntu 22.04

## Issue Description
[Describe the problem]

## Steps to Reproduce
1. Run: `docker-compose up -d --build`
2. Observe: [error message]

## Error Message
```
[Paste full error message]
```

## Diagnostic Output
```bash
docker version
docker ps
docker-compose ps
docker-compose logs [service]
```

## What I've Tried
- [x] Restarted Docker Desktop
- [ ] Checked WSL 2 settings
- [ ] Ran docker system prune
```

---

*Last Updated: 2025-11-11*
*Related: Phase 2 completion blocked by Docker connectivity issue*
