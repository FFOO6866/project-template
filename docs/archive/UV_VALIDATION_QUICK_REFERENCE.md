# UV Validation Scripts - Quick Reference

## 🚀 Quick Start

```bash
# One-command complete validation
./scripts/run-complete-validation.sh

# Individual scripts
./scripts/setup-uv-environment.sh              # Step 1: UV setup
./scripts/validate-uv-docker-build.sh          # Step 2: Docker builds
./scripts/run-complete-validation.sh           # Step 3: Everything
```

---

## 📋 Script Overview

| Script | Purpose | Time | Exit Codes |
|--------|---------|------|------------|
| `setup-uv-environment.sh` | UV installation & validation | ~15s | 0=OK, 1=UV fail, 2=pyproject, 3=lock, 4=conflicts, 5=validation |
| `validate-uv-docker-build.sh` | Docker image building & testing | ~5m | 0=OK, 1=build fail, 2=health fail, 3=security |
| `run-complete-validation.sh` | Orchestrate all validations | ~6m | 0=OK, 1=UV, 2=Docker, 3=prod, 4=config, 5=multiple |

---

## 🔧 Common Commands

### UV Setup

```bash
# Standard setup
./scripts/setup-uv-environment.sh

# Force regenerate lockfile
./scripts/setup-uv-environment.sh --force-lock

# Check only (no changes)
./scripts/setup-uv-environment.sh --check-only

# Verbose mode
./scripts/setup-uv-environment.sh --verbose
```

### Docker Build Validation

```bash
# Standard validation
./scripts/validate-uv-docker-build.sh

# No cache (clean build)
./scripts/validate-uv-docker-build.sh --no-cache

# With security scanning
./scripts/validate-uv-docker-build.sh --security-scan

# Compare UV vs pip
./scripts/validate-uv-docker-build.sh --compare-pip

# Keep images after test
./scripts/validate-uv-docker-build.sh --keep

# Full validation
./scripts/validate-uv-docker-build.sh --security-scan --compare-pip --verbose
```

### Complete Validation

```bash
# Standard full validation
./scripts/run-complete-validation.sh

# Fast mode (skip optional)
./scripts/run-complete-validation.sh --fast

# CI/CD mode
./scripts/run-complete-validation.sh --ci

# Stop on first failure
./scripts/run-complete-validation.sh --stop-on-fail

# Skip Docker builds
./scripts/run-complete-validation.sh --skip-docker

# Skip security scans
./scripts/run-complete-validation.sh --skip-security

# CI with fail-fast
./scripts/run-complete-validation.sh --ci --stop-on-fail
```

---

## 🎯 Common Scenarios

### Before Committing

```bash
./scripts/setup-uv-environment.sh --check-only
./scripts/run-complete-validation.sh --stop-on-fail
```

### After Dependency Changes

```bash
./scripts/setup-uv-environment.sh --force-lock
./scripts/validate-uv-docker-build.sh --no-cache
```

### After Dockerfile Changes

```bash
./scripts/validate-uv-docker-build.sh --no-cache --security-scan
```

### CI/CD Pipeline

```bash
./scripts/run-complete-validation.sh --ci --stop-on-fail
exit_code=$?
[ $exit_code -eq 0 ] && echo "Deploy" || echo "Block"
```

### Pre-Production

```bash
./scripts/run-complete-validation.sh --verbose --security-scan
open validation-reports/validation-*.html
```

---

## 📊 Output Files

### Locations

```
validation-reports/
├── validation-YYYYMMDD_HHMMSS.json    # Machine-readable results
├── validation-YYYYMMDD_HHMMSS.html    # Visual dashboard
├── validation-YYYYMMDD_HHMMSS.log     # Complete execution log
└── uv-docker-build-report-*.json      # Docker build metrics
```

### Quick Review

```bash
# View latest JSON report
cat validation-reports/validation-*.json | jq .

# Open latest HTML report
open validation-reports/validation-*.html  # macOS
xdg-open validation-reports/validation-*.html  # Linux

# Tail validation logs
tail -f validation-reports/validation-*.log

# Check Docker build metrics
cat uv-docker-build-report-*.json | jq '.services'
```

---

## 🔍 Validation Checklist

**UV Environment:**
- [ ] UV installed (v0.5.17)
- [ ] Python 3.11+
- [ ] pyproject.toml valid
- [ ] uv.lock generated and consistent
- [ ] No dependency conflicts
- [ ] Critical dependencies present

**Docker Builds:**
- [ ] All 3 images build successfully (api, websocket, nexus)
- [ ] Build times < 2 minutes (with cache)
- [ ] Image sizes < 1GB
- [ ] Health checks configured
- [ ] Containers start successfully
- [ ] No hardcoded localhost
- [ ] No hardcoded credentials
- [ ] No CRITICAL vulnerabilities (Trivy)

**Production Standards:**
- [ ] No in-memory storage
- [ ] Database integration present
- [ ] No localhost URLs in production code
- [ ] No hardcoded credentials
- [ ] Environment-based configuration
- [ ] No fallback data patterns
- [ ] Mock data limited to tests

**Configuration:**
- [ ] Environment variables set
- [ ] Secrets are strong (32+ chars)
- [ ] URLs use service names (not localhost)
- [ ] CORS configured correctly
- [ ] OpenAI API key valid

**UV-Specific:**
- [ ] uv.lock exists and current
- [ ] No pip requirements.txt files
- [ ] Dockerfiles use ghcr.io/astral-sh/uv
- [ ] No hardcoded values in Dockerfiles
- [ ] OpenAI version standardized (1.51.2)

---

## 🚨 Troubleshooting Quick Fixes

### UV Not Installed

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Lock File Issues

```bash
# Regenerate
./scripts/setup-uv-environment.sh --force-lock

# Manual fix
uv lock --upgrade
```

### Docker Build Fails

```bash
# Clean rebuild
docker system prune -a
./scripts/validate-uv-docker-build.sh --no-cache

# Check disk space
df -h

# Check Docker daemon
sudo systemctl status docker
```

### Hardcoded Values Found

```bash
# Find localhost references
grep -r "localhost" src/ --include="*.py" | grep -v "__pycache__"

# Find credentials
grep -r "password\s*=" src/ --include="*.py"

# Fix: Replace with environment variables
from src.core.config import config
database_url = config.DATABASE_URL  # Not "localhost"
```

### Health Check Fails

```bash
# Check container logs
docker logs <container-name>

# Test endpoint manually
docker exec <container-name> curl -f http://localhost:8000/health

# Check environment
docker exec <container-name> env | grep DATABASE_URL
```

---

## 📈 Performance Expectations

| Metric | Expected | Warning | Critical |
|--------|----------|---------|----------|
| UV setup time | < 20s | 20-60s | > 60s |
| Docker build (cached) | < 2m | 2-5m | > 5m |
| Docker build (clean) | < 10m | 10-15m | > 15m |
| Image size (api) | < 900MB | 900MB-1.2GB | > 1.2GB |
| Image size (websocket) | < 800MB | 800MB-1GB | > 1GB |
| Image size (nexus) | < 1GB | 1-1.5GB | > 1.5GB |
| Total validation | < 8m | 8-15m | > 15m |

---

## 🔐 Security Standards

**Required Checks:**
- ✅ No hardcoded localhost
- ✅ No hardcoded passwords
- ✅ No hardcoded API keys
- ✅ Environment-based secrets
- ✅ Strong passwords (32+ chars)
- ✅ HTTPS-only CORS origins
- ✅ No CRITICAL Trivy vulnerabilities

**Commands:**
```bash
# Security scan
./scripts/validate-uv-docker-build.sh --security-scan

# Manual Trivy scan
trivy image --severity HIGH,CRITICAL horme-api:latest

# Check hardcoded values
grep -r "password.*=.*['\"]" src/ --include="*.py"
grep -r "localhost" src/production_*.py
```

---

## 🎓 Exit Code Reference

### setup-uv-environment.sh
- **0**: Success
- **1**: UV installation failed
- **2**: pyproject.toml invalid
- **3**: Lock generation/validation failed
- **4**: Dependency conflicts
- **5**: Validation failed

### validate-uv-docker-build.sh
- **0**: All builds successful
- **1**: Build failed
- **2**: Health check failed
- **3**: Security issues found

### run-complete-validation.sh
- **0**: All validations passed
- **1**: UV setup failed
- **2**: Docker build failed
- **3**: Production validation failed
- **4**: Configuration validation failed
- **5**: Multiple failures

---

## 📞 Support

**Documentation:**
- Full guide: `UV_VALIDATION_AUTOMATION_GUIDE.md`
- Production standards: `CLAUDE.md`
- Production readiness: `PRODUCTION_READINESS_PLAN.md`

**Common Issues:**
1. UV installation → See troubleshooting section
2. Dependency conflicts → Check pyproject.toml constraints
3. Docker build fails → Check logs, disk space, daemon
4. Health check fails → Verify environment variables
5. Hardcoded values → Use config module

**Help Commands:**
```bash
./scripts/setup-uv-environment.sh --help
./scripts/validate-uv-docker-build.sh --help
./scripts/run-complete-validation.sh --help
```

---

## 📝 Notes

- All scripts are cross-platform (Windows Git Bash/WSL, Linux, macOS)
- All scripts follow CLAUDE.md production standards
- All scripts produce machine-readable JSON output
- All scripts support CI/CD integration
- All scripts have comprehensive error handling

**Last Updated:** 2025-10-18
**Version:** 1.0.0
