# Deployment Quick Start Guide

**⚠️ ALWAYS refer to `DEPLOYMENT_AGENT.md` for complete procedures**

---

## 🚀 First Time Setup

### 1. Check Files Exist

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing

# These files should exist:
ls -la .env                      # ✓ Contains your secrets (NEVER commit to Git)
ls -la .env.example              # ✓ Template for reference
ls -la docker-compose.yml        # ✓ Reads from .env automatically
ls -la DEPLOYMENT_AGENT.md       # ✓ Complete deployment guide
ls -la .gitignore                # ✓ Ensures .env is not committed
ls -la scripts/deploy.sh         # ✓ Automated deployment script
```

### 2. Verify .env Has Critical Variables

```bash
grep OPENAI_API_KEY .env
# Should show: OPENAI_API_KEY=sk-proj-brP97...

grep ENVIRONMENT .env
# Should show: ENVIRONMENT=development (for local)
```

---

## 💻 Local Development

### Quick Start

```bash
# Start all services (docker-compose reads .env automatically)
docker-compose up -d

# Check everything is running
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Using Deployment Script

```bash
# Make script executable (first time only)
chmod +x scripts/deploy.sh

# Deploy locally
./scripts/deploy.sh local
```

---

## 🌐 Server Deployment

### Prerequisites (One-Time)

1. **Update .env with server details:**
   ```bash
   SERVER_IP=192.168.1.100         # Your server IP
   SERVER_USER=ubuntu              # SSH user
   PEM_KEY_PATH=~/.ssh/mykey.pem   # Path to SSH key
   ```

2. **Copy .env to server (FIRST TIME ONLY):**
   ```bash
   scp -i ~/.ssh/mykey.pem .env ubuntu@192.168.1.100:~/job-pricing-engine/
   ```

3. **Set ENVIRONMENT to production on server:**
   ```bash
   ssh -i ~/.ssh/mykey.pem ubuntu@192.168.1.100
   cd ~/job-pricing-engine
   sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env
   exit
   ```

### Deploy to Server

**Method 1: Using Deployment Script (Recommended)**

```bash
./scripts/deploy.sh server
```

This will:
- Commit and push your changes to Git
- SSH to server
- Pull latest code from Git
- Deploy with docker-compose
- Verify deployment

**Method 2: Manual Deployment**

```bash
# 1. Push to Git
git add .
git commit -m "your commit message"
git push origin main

# 2. SSH to server
ssh -i ~/.ssh/mykey.pem ubuntu@192.168.1.100

# 3. Update code
cd ~/job-pricing-engine
git pull origin main

# 4. Deploy
docker-compose down
docker-compose up -d --build

# 5. Verify
docker-compose ps
curl http://localhost:8000/health

# 6. Exit
exit
```

---

## 🔧 Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
```

### Restart a Service

```bash
docker-compose restart api
```

### Check Environment Variables

```bash
# Verify OPENAI_API_KEY is set
docker-compose exec api env | grep OPENAI_API_KEY

# Verify ENVIRONMENT
docker-compose exec api env | grep ENVIRONMENT
```

### Database Operations

```bash
# Run migrations
docker-compose exec api python -m alembic upgrade head

# Access database
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db
```

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY not set" Error

```bash
# Check if .env exists
ls -la .env

# Check if OPENAI_API_KEY is in .env
grep OPENAI_API_KEY .env

# If missing, add it:
echo "OPENAI_API_KEY=sk-proj-brP97..." >> .env

# Restart services
docker-compose down
docker-compose up -d

# Verify it's now set
docker-compose exec api env | grep OPENAI_API_KEY
```

### Services Not Starting

```bash
# Check logs for errors
docker-compose logs api

# Remove old containers and restart fresh
docker-compose down
docker-compose rm -f
docker-compose up -d --build
```

### Wrong Environment (Production vs Development)

```bash
# Check current ENVIRONMENT
grep ENVIRONMENT .env

# On server, should be "production"
# On local, should be "development"

# To change:
# Edit .env file and update ENVIRONMENT value
# Then restart: docker-compose down && docker-compose up -d
```

---

## ✅ Deployment Checklist

### Before Every Deployment

- [ ] Code tested locally with `docker-compose up -d`
- [ ] .env has OPENAI_API_KEY set
- [ ] Changes committed to Git
- [ ] Reviewed DEPLOYMENT_AGENT.md for full procedures

### After Every Deployment

- [ ] All services running (`docker-compose ps`)
- [ ] API health check passes (`curl http://localhost:8000/health`)
- [ ] Environment verified (development vs production)
- [ ] OPENAI_API_KEY confirmed set in container
- [ ] No errors in logs (`docker-compose logs api`)

---

## 📚 Documentation References

| Document | Purpose |
|----------|---------|
| **DEPLOYMENT_AGENT.md** | Complete deployment procedures, troubleshooting, commands |
| **DEPLOYMENT_QUICK_START.md** | This file - quick reference |
| **.env** | Environment variables (NEVER commit to Git) |
| **.env.example** | Template for .env |
| **docker-compose.yml** | Docker services configuration |
| **scripts/deploy.sh** | Automated deployment script |

---

## 🔐 Security Reminders

1. ✅ .env is in .gitignore (never committed)
2. ✅ .env contains secrets (OpenAI key, passwords)
3. ✅ Use .env.example for templates only
4. ✅ Same .env structure on local and server (only ENVIRONMENT differs)

---

## 📞 Need Help?

1. **Read DEPLOYMENT_AGENT.md first** - Comprehensive guide with all commands
2. Check troubleshooting section above
3. Review docker-compose logs: `docker-compose logs -f`
4. Verify .env file has all required variables

---

**Quick Commands Summary:**

```bash
# Local development
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f api        # View logs
docker-compose ps                 # Check status

# Deployment
./scripts/deploy.sh local         # Deploy locally
./scripts/deploy.sh server        # Deploy to server

# Git workflow
git add .                         # Stage changes
git commit -m "message"           # Commit
git push origin main              # Push to GitHub

# Server
ssh -i ~/.ssh/key.pem user@ip    # Connect to server
git pull origin main              # Update code
docker-compose up -d --build      # Deploy
```

---

**Remember**: Always use `DEPLOYMENT_AGENT.md` for complete, detailed procedures!
