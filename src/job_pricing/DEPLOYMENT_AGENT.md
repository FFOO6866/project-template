# Deployment Agent - Dynamic Job Pricing Engine

**Version**: 1.0
**Last Updated**: 2025-01-10
**Status**: PRODUCTION-READY

---

## ⚠️ CRITICAL RULES - READ BEFORE EVERY DEPLOYMENT

1. **ALWAYS use this deployment agent** - Never deploy without following these exact steps
2. **Local → Git → Server** - NEVER use rsync, scp, or direct file copy
3. **Same .env structure** on local and server - Only ENVIRONMENT flag differs
4. **Docker Compose reads .env** - NEVER manually insert env vars in docker-compose commands
5. **Git is the source of truth** - All sync happens through Git
6. **Production flag** - Check ENVIRONMENT variable before deployment
7. **Test locally first** - Always verify locally before server deployment

---

## 🏗️ Architecture Overview

```
┌──────────────┐
│   LOCAL      │  1. Develop & Test
│  DEV MACHINE │     - Code changes
│              │     - Local docker-compose up
└──────┬───────┘
       │
       │ 2. Git Push
       ▼
┌──────────────┐
│   GITHUB     │  3. Version Control
│  REPOSITORY  │     - main branch
│              │
└──────┬───────┘
       │
       │ 4. Git Pull
       ▼
┌──────────────┐
│   SERVER     │  5. Deploy
│  PRODUCTION  │     - docker-compose up
│              │
└──────────────┘
```

---

## 📋 Pre-Deployment Checklist

### One-Time Setup (Already Done)

- [x] .env file created with all variables
- [x] .env.example template created
- [x] docker-compose.yml configured to read from .env
- [x] .gitignore includes .env
- [x] OpenAI API key stored in .env: `OPENAI_API_KEY=sk-proj-brP97...`

### Before EVERY Deployment

- [ ] All changes committed locally
- [ ] Code tested locally with `docker-compose up`
- [ ] .env file updated on server (if needed)
- [ ] ENVIRONMENT variable checked (development vs production)
- [ ] Git repository up to date

---

## 🚀 Deployment Procedures

### Procedure 1: Local Development

**Purpose**: Develop and test changes locally

```bash
# 1. Navigate to project directory
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing

# 2. Ensure .env exists and has correct values
cat .env | grep OPENAI_API_KEY
# Should output: OPENAI_API_KEY=sk-proj-brP97...

cat .env | grep ENVIRONMENT
# Should output: ENVIRONMENT=development

# 3. Start services (docker-compose reads .env automatically)
docker-compose up -d

# 4. Verify all services are running
docker-compose ps

# Expected output:
# NAME                              STATUS
# job-pricing-postgres              Up (healthy)
# job-pricing-redis                 Up (healthy)
# job-pricing-api                   Up (healthy)
# job-pricing-celery-worker         Up
# job-pricing-celery-beat           Up

# 5. Check API health
curl http://localhost:8000/health

# 6. View logs if needed
docker-compose logs -f api

# 7. Test your changes
# ... (run tests, manual testing, etc.)

# 8. Stop services when done
docker-compose down
```

**IMPORTANT**: If you see "OPENAI_API_KEY not set" error, it means:
- .env file is missing
- .env file doesn't have OPENAI_API_KEY
- docker-compose.yml not reading .env properly

**Solution**:
```bash
# Verify .env exists
ls -la .env

# Verify OPENAI_API_KEY is set
grep OPENAI_API_KEY .env

# Restart docker-compose (it will re-read .env)
docker-compose down
docker-compose up -d
```

---

### Procedure 2: Git Sync (Local → GitHub)

**Purpose**: Push local changes to GitHub

```bash
# 1. Check git status
git status

# 2. Add all changes EXCEPT .env (already in .gitignore)
git add .

# 3. Verify .env is NOT staged
git status | grep .env
# Should NOT show .env in staged files

# 4. Commit with descriptive message
git commit -m "feat: add mercer integration workflow"

# 5. Push to GitHub
git push origin main

# 6. Verify push succeeded
git log -1
```

**CRITICAL**: .env should NEVER be committed to Git. It contains secrets.

---

### Procedure 3: Server Deployment (GitHub → Server)

**Purpose**: Deploy latest code to production server

#### Step 1: Connect to Server

```bash
# From your local machine
ssh -i ~/.ssh/your-key.pem ubuntu@<SERVER_IP>

# Example (replace with your actual values from .env):
# ssh -i ~/.ssh/your-key.pem ubuntu@192.168.1.100
```

#### Step 2: Update Code from Git

```bash
# On the server
cd /home/ubuntu/job-pricing-engine

# Pull latest changes from GitHub
git pull origin main

# Verify pull succeeded
git log -1
```

#### Step 3: Check/Update .env File

```bash
# Verify .env exists on server
ls -la .env

# Check ENVIRONMENT is set to production
grep ENVIRONMENT .env
# Should output: ENVIRONMENT=production

# Verify OPENAI_API_KEY is set
grep OPENAI_API_KEY .env
# Should output: OPENAI_API_KEY=sk-proj-brP97...

# If .env is missing or incorrect, copy from local (ONE TIME ONLY):
# From local machine:
scp -i ~/.ssh/your-key.pem .env ubuntu@<SERVER_IP>:/home/ubuntu/job-pricing-engine/

# Then SSH back and update ENVIRONMENT to production:
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env
```

#### Step 4: Deploy with Docker Compose

```bash
# On the server

# Stop existing containers
docker-compose down

# Pull latest images (if using remote images)
docker-compose pull

# Rebuild and start services
# NOTE: docker-compose automatically reads .env - NO manual env vars needed!
docker-compose up -d --build

# Verify all services are running
docker-compose ps

# Expected output:
# NAME                              STATUS
# job-pricing-postgres              Up (healthy)
# job-pricing-redis                 Up (healthy)
# job-pricing-api                   Up (healthy)
# job-pricing-celery-worker         Up
# job-pricing-celery-beat           Up
```

#### Step 5: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check environment is production
docker-compose exec api python -c "import os; print(os.getenv('ENVIRONMENT'))"
# Should output: production

# Check OPENAI_API_KEY is set
docker-compose exec api python -c "import os; print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
# Should output: OPENAI_API_KEY: SET

# View real-time logs
docker-compose logs -f api

# Press Ctrl+C to stop following logs
```

#### Step 6: Database Migrations (if applicable)

```bash
# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Verify migration succeeded
docker-compose exec api python -m alembic current
```

---

## 🔧 Common Commands Reference

### Docker Compose Commands

```bash
# Start all services (reads .env automatically)
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f api

# Check service status
docker-compose ps

# Rebuild services
docker-compose up -d --build

# Execute command in container
docker-compose exec api <command>

# Example: Python shell
docker-compose exec api python

# Example: Database shell
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db
```

### Git Commands

```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "message"

# Push
git push origin main

# Pull
git pull origin main

# View commit history
git log --oneline

# Check current branch
git branch
```

### Environment Variable Debugging

```bash
# Print all environment variables in container
docker-compose exec api env

# Check specific variable
docker-compose exec api env | grep OPENAI_API_KEY

# Verify .env is being read
docker-compose config
# This shows the actual configuration with env vars substituted
```

---

## 🐛 Troubleshooting Guide

### Problem 1: "OPENAI_API_KEY not set" Error

**Symptoms**:
- API returns errors about missing OpenAI key
- Workflows fail with authentication error

**Root Cause**:
- .env file missing
- .env file doesn't have OPENAI_API_KEY
- docker-compose not reading .env

**Solution**:
```bash
# Step 1: Verify .env exists
ls -la .env

# Step 2: Check OPENAI_API_KEY in .env
grep OPENAI_API_KEY .env
# Should show: OPENAI_API_KEY=sk-proj-brP97...

# Step 3: If missing, add it:

# Step 4: Restart services
docker-compose down
docker-compose up -d

# Step 5: Verify it's now set
docker-compose exec api env | grep OPENAI_API_KEY
```

---

### Problem 2: Wrong Environment (Development vs Production)

**Symptoms**:
- Production server has DEBUG=true
- Using wrong database
- Test data appearing in production

**Root Cause**:
- ENVIRONMENT variable not set correctly in .env

**Solution**:
```bash
# On SERVER only:
# Step 1: Check current ENVIRONMENT
grep ENVIRONMENT .env

# Step 2: If it says "development", change to "production"
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env

# Step 3: Also set DEBUG to false
sed -i 's/DEBUG=true/DEBUG=false/' .env

# Step 4: Restart services
docker-compose down
docker-compose up -d

# Step 5: Verify
docker-compose exec api python -c "import os; print('ENV:', os.getenv('ENVIRONMENT'), 'DEBUG:', os.getenv('DEBUG'))"
# Should output: ENV: production DEBUG: false
```

---

### Problem 3: Services Not Starting

**Symptoms**:
- `docker-compose ps` shows services as "Exited"
- Health checks failing

**Solution**:
```bash
# Step 1: Check logs for error messages
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis

# Step 2: Check if ports are already in use
netstat -tulpn | grep 8000
netstat -tulpn | grep 5432
netstat -tulpn | grep 6379

# Step 3: If ports in use, stop conflicting services
docker-compose down
docker ps -a  # Check for other containers

# Step 4: Remove old containers if needed
docker-compose rm -f

# Step 5: Restart fresh
docker-compose up -d --build

# Step 6: Monitor startup
docker-compose logs -f
```

---

### Problem 4: Database Connection Error

**Symptoms**:
- "could not connect to server"
- "database does not exist"

**Solution**:
```bash
# Step 1: Check postgres is running
docker-compose ps postgres

# Step 2: Check postgres logs
docker-compose logs postgres

# Step 3: Verify DATABASE_URL in .env
grep DATABASE_URL .env

# Step 4: Test database connection
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT 1;"

# Step 5: If database doesn't exist, recreate:
docker-compose down -v  # Warning: This deletes all data!
docker-compose up -d
```

---

### Problem 5: Git Sync Issues

**Symptoms**:
- "fatal: not a git repository"
- Merge conflicts
- Can't push/pull

**Solution**:
```bash
# Check if in git repository
git status

# If not a git repo, initialize:
git init
git remote add origin <your-repo-url>

# If merge conflicts:
git status  # See conflicting files
# Manually resolve conflicts in files
git add .
git commit -m "resolve conflicts"

# If can't pull due to local changes:
git stash  # Save local changes
git pull origin main
git stash pop  # Restore local changes

# If completely stuck, backup and reclone:
cp -r . ../backup
cd ..
git clone <your-repo-url> job-pricing-engine-new
cd job-pricing-engine-new
# Copy .env from backup
cp ../backup/.env .
```

---

## 📊 Health Checks

### After Every Deployment

```bash
# 1. Check all services are up
docker-compose ps

# 2. Check API health endpoint
curl http://localhost:8000/health

# 3. Check environment variables
docker-compose exec api env | grep -E "ENVIRONMENT|OPENAI_API_KEY|DATABASE_URL"

# 4. Check database connection
docker-compose exec api python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('✓ Database connected')
conn.close()
"

# 5. Check Redis connection
docker-compose exec api python -c "
import redis
import os
r = redis.from_url(os.getenv('REDIS_URL'))
r.ping()
print('✓ Redis connected')
"

# 6. Check OpenAI API key works
docker-compose exec api python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
# If no error, key is valid
print('✓ OpenAI API key valid')
"
```

---

## 📝 Deployment Checklist

Use this checklist for EVERY deployment:

### Pre-Deployment

- [ ] Code changes committed locally
- [ ] Tests pass locally
- [ ] `docker-compose up -d` works locally
- [ ] .env file has all required variables
- [ ] OPENAI_API_KEY verified in .env
- [ ] Changes pushed to GitHub (`git push origin main`)

### Deployment

- [ ] SSH to server
- [ ] Navigate to project directory
- [ ] Pull latest code (`git pull origin main`)
- [ ] Verify .env exists on server
- [ ] Verify ENVIRONMENT=production in .env
- [ ] Verify OPENAI_API_KEY set in .env
- [ ] Stop services (`docker-compose down`)
- [ ] Start services (`docker-compose up -d --build`)
- [ ] Check services status (`docker-compose ps`)

### Post-Deployment

- [ ] API health check passes
- [ ] Environment verified as "production"
- [ ] OPENAI_API_KEY confirmed set in container
- [ ] Database connection works
- [ ] Redis connection works
- [ ] API responds to test request
- [ ] Logs show no errors
- [ ] Monitor for 5 minutes

---

## 🔐 Security Reminders

1. **NEVER commit .env to Git**
   - Already in .gitignore
   - Contains secrets (OpenAI key, passwords)

2. **NEVER expose .env publicly**
   - Keep it on local machine and server only
   - Use .env.example for templates

3. **Use strong passwords**
   - Database password
   - Redis password
   - JWT secret

4. **Rotate secrets regularly**
   - OpenAI API key every 90 days
   - Database passwords every 180 days

5. **Monitor API usage**
   - OpenAI API costs
   - Unusual activity

---

## 📞 Emergency Procedures

### If Production is Down

```bash
# 1. Check what's down
docker-compose ps

# 2. View logs immediately
docker-compose logs --tail=100 api

# 3. Quick restart
docker-compose restart api

# 4. If that doesn't work, full restart
docker-compose down
docker-compose up -d

# 5. If still down, check .env
grep -E "ENVIRONMENT|OPENAI_API_KEY|DATABASE_URL" .env

# 6. Last resort: rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Rollback to Previous Version

```bash
# 1. Check git log for last working commit
git log --oneline

# 2. Revert to specific commit
git checkout <commit-hash>

# 3. Restart services
docker-compose down
docker-compose up -d --build

# 4. If rollback permanent:
git revert <bad-commit-hash>
git push origin main
```

---

## 📚 Reference: All Environment Variables

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `ENVIRONMENT` | ✅ Yes | `production` | MUST be "production" on server |
| `OPENAI_API_KEY` | ✅ Yes | `sk-proj-brP97...` | From your OpenAI account |
| `DATABASE_URL` | ✅ Yes | `postgresql://...` | Auto-constructed from other vars |
| `REDIS_URL` | ✅ Yes | `redis://:pass@...` | Auto-constructed from other vars |
| `JWT_SECRET_KEY` | ✅ Yes | `random_string` | Long random string |
| `POSTGRES_PASSWORD` | ✅ Yes | `secure_pass` | Strong password |
| `REDIS_PASSWORD` | ✅ Yes | `redis_pass` | Strong password |
| `MERCER_API_KEY` | ⚠️ Optional | `mercer_key` | If using Mercer API |
| `GLASSDOOR_EMAIL` | ⚠️ Optional | `email@company.com` | For web scraping |
| `GLASSDOOR_PASSWORD` | ⚠️ Optional | `password` | For web scraping |

**Full list**: See `.env.example`

---

## ✅ Summary: The Golden Rules

1. **Always use this deployment agent** ✅
2. **Local → Git → Server** (never rsync/scp) ✅
3. **docker-compose reads .env automatically** (no manual env vars) ✅
4. **Check ENVIRONMENT flag** (development vs production) ✅
5. **Verify OPENAI_API_KEY always set** ✅
6. **Test locally before deploying** ✅
7. **Use git for all file syncing** ✅

---

**Last Updated**: 2025-01-10
**Maintained By**: Development Team
**Questions**: Refer to this document FIRST, then escalate if needed
