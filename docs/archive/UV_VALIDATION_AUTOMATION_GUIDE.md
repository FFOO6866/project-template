# UV Migration Validation Automation Guide

## Overview

This guide documents the comprehensive automation scripts for validating UV package manager migration and Docker builds. These scripts ensure production-ready deployments with zero hardcoded values, no mock data, and complete environment-based configuration.

**Created:** 2025-10-18
**Version:** 1.0.0
**Scripts:** 3 production-ready automation scripts

---

## Table of Contents

1. [Scripts Overview](#scripts-overview)
2. [Script 1: UV Environment Setup](#script-1-uv-environment-setup)
3. [Script 2: Docker Build Validation](#script-2-docker-build-validation)
4. [Script 3: Complete Validation Orchestrator](#script-3-complete-validation-orchestrator)
5. [Usage Examples](#usage-examples)
6. [Integration with CI/CD](#integration-with-cicd)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Scripts Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  run-complete-validation.sh (Orchestrator)                 │
│  ├── Phase 1: UV Environment Setup                         │
│  │   └── setup-uv-environment.sh                           │
│  ├── Phase 2: Docker Build Validation                      │
│  │   └── validate-uv-docker-build.sh                       │
│  ├── Phase 3: Production Validation                        │
│  │   └── validate_production_complete.py                   │
│  ├── Phase 4: Config Validation                            │
│  │   └── validate_config.py                                │
│  └── Phase 5: UV-Specific Tests                            │
│      └── Custom UV validation checks                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Features (All Scripts)

✅ **NO Hardcoded Values** - All configuration from environment variables
✅ **NO Mock Data** - Real validation against actual infrastructure
✅ **Production-Ready** - Follows CLAUDE.md standards strictly
✅ **Cross-Platform** - Works on Windows (Git Bash/WSL), Linux, macOS
✅ **CI/CD Friendly** - Proper exit codes and machine-readable output
✅ **Comprehensive Reporting** - JSON, HTML, and text reports
✅ **Error Handling** - Rollback support and detailed error messages
✅ **Performance Metrics** - Build times, image sizes, efficiency tracking

---

## Script 1: UV Environment Setup

**File:** `scripts/setup-uv-environment.sh`
**Purpose:** Automated UV installation, validation, and lockfile generation
**Lines:** 741
**Size:** 22KB

### Features

1. **UV Installation Check & Auto-Install**
   - Detects if UV is installed
   - Auto-installs on Linux/macOS
   - Provides installation instructions for Windows
   - Version validation (compares with recommended 0.5.17)

2. **Python Version Validation**
   - Checks for Python 3.11+ (minimum requirement)
   - Validates Python is in PATH
   - Cross-platform version checking

3. **pyproject.toml Validation**
   - Syntax validation with UV
   - Required sections check ([project], [project.dependencies])
   - Hardcoded credential detection
   - TOML structure verification

4. **uv.lock Generation & Validation**
   - Generates uv.lock if missing
   - Validates existing lockfile consistency
   - Creates backups before modifications
   - Rollback on failure

5. **Dependency Conflict Detection**
   - Analyzes dependency tree
   - Identifies version conflicts
   - Reports incompatible packages

6. **Critical Dependency Validation**
   - Verifies presence of required packages:
     - fastapi, uvicorn, asyncpg
     - redis, neo4j, openai
   - Ensures no missing core dependencies

7. **Environment Configuration Validation**
   - Checks UV cache directory
   - Validates UV environment variables
   - Recommends best practices

8. **Installation Verification**
   - Dry-run installation test
   - Dependency statistics
   - Pre-deployment verification

### Usage

```bash
# Standard setup and validation
./scripts/setup-uv-environment.sh

# Force regenerate lockfile
./scripts/setup-uv-environment.sh --force-lock

# Validation only (no modifications)
./scripts/setup-uv-environment.sh --check-only

# Verbose mode with debugging
./scripts/setup-uv-environment.sh --verbose

# Help and options
./scripts/setup-uv-environment.sh --help
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - Environment ready |
| 1 | UV installation failed |
| 2 | pyproject.toml invalid |
| 3 | Lock generation/validation failed |
| 4 | Dependency conflicts detected |
| 5 | General validation failure |

### Output Example

```
============================================================================
UV Environment Setup v1.0.0
============================================================================

==> Step 1: Checking UV installation
    ✓ UV is installed (version: 0.5.17)
    ✓ UV version matches recommended (0.5.17)

==> Step 2: Validating Python version
    ✓ Python is installed (version: 3.11.5)
    ✓ Python version meets minimum requirement (>=3.11)

==> Step 3: Validating pyproject.toml
    ✓ pyproject.toml exists
    ✓ pyproject.toml is readable
    ✓ pyproject.toml syntax is valid
    ✓ Section [project] exists
    ✓ Section [project.dependencies] exists
    ✓ No hardcoded credentials in pyproject.toml

==> Step 4: Generating/updating uv.lock
    ✓ Lock file generated successfully
    ✓ Lock file is consistent with pyproject.toml

==> Step 5: Checking for dependency conflicts
    ✓ No dependency conflicts detected

==> Step 6: Validating critical dependencies
    ✓ Critical dependency 'fastapi' is present
    ✓ Critical dependency 'uvicorn' is present
    ✓ Critical dependency 'asyncpg' is present
    ✓ Critical dependency 'redis' is present
    ✓ Critical dependency 'neo4j' is present
    ✓ Critical dependency 'openai' is present

==> Step 7: Validating UV environment configuration
    ✓ UV cache directory exists (size: 2.1GB)

==> Step 8: Verifying complete installation
    ✓ Installation verification passed

============================================================================
VALIDATION SUMMARY
============================================================================
Total Checks:    18
Passed:          18
Failed:          0
Warnings:        0
Success Rate:    100%
============================================================================

✅ UV ENVIRONMENT SETUP COMPLETE

Next steps:
  1. Build Docker images: ./scripts/validate-uv-docker-build.sh
  2. Run complete validation: ./scripts/run-complete-validation.sh
  3. Deploy: docker-compose -f docker-compose.production.yml up -d
```

---

## Script 2: Docker Build Validation

**File:** `scripts/validate-uv-docker-build.sh`
**Purpose:** Comprehensive Docker build validation with performance metrics
**Lines:** 805
**Size:** 25KB

### Features

1. **Multi-Image Build Validation**
   - Builds all 3 UV Dockerfiles:
     - `Dockerfile.api.uv` → horme-api:uv-test
     - `Dockerfile.websocket.uv` → horme-websocket:uv-test
     - `Dockerfile.nexus.uv` → horme-nexus:uv-test
   - BuildKit optimization support
   - Cache management
   - Progress tracking

2. **Build Time Metrics**
   - Measures build duration for each image
   - Incremental vs. clean build comparison
   - Cache hit rate analysis
   - Build performance tracking

3. **Image Size Analysis**
   - Calculates compressed and uncompressed sizes
   - Layer-by-layer size breakdown
   - Identifies largest layers
   - Size optimization recommendations

4. **Health Check Validation**
   - Extracts health check configuration
   - Validates health check commands
   - Tests health endpoints
   - Timeout and interval verification

5. **Container Startup Testing**
   - Starts containers with test environment
   - Validates initialization
   - Checks runtime stability
   - Collects startup logs

6. **Security Scanning**
   - **Hardcoded Value Detection:**
     - Scans for localhost URLs
     - Detects hardcoded credentials
     - Finds hardcoded API keys
   - **Trivy Integration (optional):**
     - Vulnerability scanning
     - HIGH/CRITICAL severity filtering
     - Dependency audit

7. **Performance Comparison (optional)**
   - UV vs. pip build time comparison
   - Image size comparison
   - Speedup calculation
   - Efficiency metrics

8. **Comprehensive Reporting**
   - JSON report with metrics
   - Build summary with statistics
   - Performance recommendations
   - Security findings

### Usage

```bash
# Standard validation (with cache)
./scripts/validate-uv-docker-build.sh

# Clean build (no cache)
./scripts/validate-uv-docker-build.sh --no-cache

# With security scanning (requires Trivy)
./scripts/validate-uv-docker-build.sh --security-scan

# Compare with pip-based builds
./scripts/validate-uv-docker-build.sh --compare-pip

# Keep images after testing
./scripts/validate-uv-docker-build.sh --keep

# Verbose output
./scripts/validate-uv-docker-build.sh --verbose

# Full validation
./scripts/validate-uv-docker-build.sh --security-scan --compare-pip --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All builds successful |
| 1 | Build failed |
| 2 | Health check failed |
| 3 | Security issues found |

### Output Example

```
============================================================================
UV Docker Build Validator v1.0.0
============================================================================

==> Checking Docker availability
[SUCCESS] Docker is available (version: 24.0.7)
[INFO] BuildKit enabled for optimized builds

==> Validating Dockerfile existence
[SUCCESS] Found: Dockerfile.api.uv
[SUCCESS] Found: Dockerfile.websocket.uv
[SUCCESS] Found: Dockerfile.nexus.uv

==> Building Docker image: api
    → Dockerfile: Dockerfile.api.uv
    → Image name: horme-api:uv-test
    → Build mode: WITH CACHE
    → Starting build...
[SUCCESS] Build completed in 1m 12s
    📊 Image size: 845MB
    📊 Raw size: 845234567

==> Validating image layers: api
    📊 Total layers: 18
    → Largest layers:
      342MB   RUN uv sync --frozen --no-dev
      156MB   COPY src/ ./src/
      98MB    apt-get install -y gcc g++ libpq-dev
      45MB    python:3.11-slim base
      12MB    COPY --from=builder /app/.venv

==> Checking health check configuration: api
[SUCCESS] Health check configured
    → Configuration: {"Test":["CMD","curl","-f","http://localhost:8000/health"]}
    📊 Test: "Test":["CMD","curl","-f","http://localhost:8000/health"]

==> Testing container startup: api
    → Starting container: test-api-12345
[SUCCESS] Container started successfully
    → Waiting for container initialization...
[SUCCESS] Container is running healthy
    → Container logs (last 10 lines):
        INFO:     Started server process
        INFO:     Waiting for application startup.
        INFO:     Application startup complete.
        INFO:     Uvicorn running on http://0.0.0.0:8000

==> Scanning for hardcoded values: api
    → Extracting image contents...
    → Scanning for localhost URLs...
[SUCCESS] No localhost URLs found
    → Scanning for hardcoded credentials...
[SUCCESS] No obvious hardcoded credentials found
[SUCCESS] Security scan passed - no hardcoded values found

==> Running Trivy security scan: api (optional)
    → Scanning for vulnerabilities...
[SUCCESS] No HIGH or CRITICAL vulnerabilities found

==> Comparing UV vs pip build performance: api (optional)
    → Building pip-based image...
    📊 Build time comparison:
    📊   UV:  1m 12s
    📊   Pip: 8m 45s
[SUCCESS] UV is 726% faster (saved 7m 33s)
    📊 Image size comparison:
    📊   UV:  845MB
    📊   Pip: 1.2GB

... (repeats for websocket and nexus services)

============================================================================
BUILD SUMMARY
============================================================================
Total builds:      3
Successful:        3
Failed:            0
Warnings:          0

Build Performance:
  api: 1m 12s (845MB)
  websocket: 58s (723MB)
  nexus: 1m 34s (912MB)

Report: /path/to/uv-docker-build-report-20251018_103045.json
============================================================================

✅ ALL DOCKER BUILDS VALIDATED SUCCESSFULLY

Next steps:
  1. Review report: cat /path/to/uv-docker-build-report-20251018_103045.json
  2. Run complete validation: ./scripts/run-complete-validation.sh
  3. Deploy images to registry: docker push ...
```

---

## Script 3: Complete Validation Orchestrator

**File:** `scripts/run-complete-validation.sh`
**Purpose:** Master orchestrator for all validation phases
**Lines:** 849
**Size:** 28KB

### Features

1. **Multi-Phase Validation Pipeline**
   - **Phase 1:** UV Environment Setup
   - **Phase 2:** Docker Build Validation
   - **Phase 3:** Production Completeness Validation
   - **Phase 4:** Configuration Validation
   - **Phase 5:** UV-Specific Tests

2. **Intelligent Execution**
   - Sequential execution with dependency management
   - Parallel execution where safe
   - Phase skipping options
   - Fail-fast mode support

3. **Progress Tracking**
   - Real-time status updates
   - Phase timing metrics
   - Success/failure tracking
   - Overall progress percentage

4. **Comprehensive Reporting**
   - **JSON Report:** Machine-readable metrics
   - **HTML Report:** Visual dashboard with charts
   - **Log File:** Complete execution trace
   - All reports timestamped and archived

5. **CI/CD Integration**
   - Minimal output mode for pipelines
   - Proper exit codes for automation
   - JSON output for downstream processing
   - Build metrics export

6. **Error Handling**
   - Graceful degradation
   - Detailed error messages
   - Phase isolation (failures don't cascade)
   - Optional stop-on-fail mode

### Usage

```bash
# Standard full validation
./scripts/run-complete-validation.sh

# Fast mode (skip optional checks)
./scripts/run-complete-validation.sh --fast

# CI/CD mode (minimal output)
./scripts/run-complete-validation.sh --ci

# Stop on first failure
./scripts/run-complete-validation.sh --stop-on-fail

# Skip Docker builds
./scripts/run-complete-validation.sh --skip-docker

# Skip security scans
./scripts/run-complete-validation.sh --skip-security

# Verbose mode
./scripts/run-complete-validation.sh --verbose

# Combined options
./scripts/run-complete-validation.sh --ci --stop-on-fail
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | UV setup failed |
| 2 | Docker build failed |
| 3 | Production validation failed |
| 4 | Configuration validation failed |
| 5 | Multiple failures |

### Phase Breakdown

#### Phase 1: UV Environment Setup
- Runs `setup-uv-environment.sh`
- Validates UV installation
- Checks pyproject.toml
- Generates/validates uv.lock
- Checks for dependency conflicts

#### Phase 2: Docker Build Validation
- Runs `validate-uv-docker-build.sh`
- Builds all UV Docker images
- Validates image layers and sizes
- Tests health checks
- Scans for hardcoded values
- Optional security scanning
- Optional performance comparison

#### Phase 3: Production Completeness
- Runs `validate_production_complete.py`
- Checks for in-memory storage
- Validates database integration
- Scans for localhost URLs
- Detects hardcoded credentials
- Checks fallback patterns
- Scans for mock data

#### Phase 4: Configuration Validation
- Runs `validate_config.py`
- Validates environment settings
- Checks security configuration
- Validates service URLs
- Checks CORS configuration
- Tests service connectivity (optional)

#### Phase 5: UV-Specific Tests
- Verifies uv.lock exists and is current
- Checks for pip artifacts
- Validates Dockerfile UV integration
- Scans for hardcoded values in Dockerfiles
- Verifies OpenAI version consistency

### Output Example

```
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  Complete Validation Orchestrator                                     ║
║  Version 1.0.0                                                         ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝

Timestamp: 2025-10-18 10:35:42
Project:   /path/to/horme-pov
Mode:      Interactive

╔════════════════════════════════════════════════════════════════════════╗
║ PHASE 1: UV Environment Setup                                         ║
╚════════════════════════════════════════════════════════════════════════╝

    → Executing: run_uv_setup

... (UV setup output) ...

[SUCCESS] UV Environment Setup completed successfully in 15s

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║ PHASE 2: Docker Build Validation                                      ║
╚════════════════════════════════════════════════════════════════════════╝

    → Executing: run_docker_build

... (Docker build output) ...

[SUCCESS] Docker Build Validation completed successfully in 4m 32s

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║ PHASE 3: Production Completeness                                      ║
╚════════════════════════════════════════════════════════════════════════╝

... (Production validation output) ...

[SUCCESS] Production Completeness completed successfully in 8s

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║ PHASE 4: Configuration Validation                                     ║
╚════════════════════════════════════════════════════════════════════════╝

... (Config validation output) ...

[SUCCESS] Configuration Validation completed successfully in 12s

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║ PHASE 5: UV-Specific Tests                                            ║
╚════════════════════════════════════════════════════════════════════════╝

... (UV-specific test output) ...

[SUCCESS] UV-Specific Tests completed successfully in 6s

────────────────────────────────────────────────────────────────────────

==> Generating comprehensive validation report
[SUCCESS] JSON report: /path/to/validation-reports/validation-20251018_103542.json
[SUCCESS] HTML report: /path/to/validation-reports/validation-20251018_103542.html

╔════════════════════════════════════════════════════════════════════════╗
║                     VALIDATION SUMMARY                                 ║
╚════════════════════════════════════════════════════════════════════════╝

Overall Statistics:
  Total Phases:  5
  Passed:        5
  Failed:        0
  Skipped:       0

Success Rate: 100%

Phase Results:
  ✅ UV Environment Setup             15s
  ✅ Docker Build Validation          4m 32s
  ✅ Production Completeness          8s
  ✅ Configuration Validation         12s
  ✅ UV-Specific Tests                6s

Reports Generated:
  JSON:  /path/to/validation-reports/validation-20251018_103542.json
  HTML:  /path/to/validation-reports/validation-20251018_103542.html
  Logs:  /path/to/validation-reports/validation-20251018_103542.log

════════════════════════════════════════════════════════════════════════

╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  ✅ ALL VALIDATIONS PASSED                                            ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝

Total validation time: 5m 13s

Next steps:
  1. Review reports in: /path/to/validation-reports
  2. Deploy to production: docker-compose -f docker-compose.production.yml up -d
  3. Monitor deployment: docker-compose -f docker-compose.production.yml logs -f
```

---

## Usage Examples

### Quick Start

```bash
# 1. Run UV setup (first time or after dependency changes)
./scripts/setup-uv-environment.sh

# 2. Validate Docker builds
./scripts/validate-uv-docker-build.sh --security-scan

# 3. Run complete validation
./scripts/run-complete-validation.sh
```

### Development Workflow

```bash
# After modifying dependencies
./scripts/setup-uv-environment.sh --force-lock

# After modifying Dockerfiles
./scripts/validate-uv-docker-build.sh --no-cache

# Before committing changes
./scripts/run-complete-validation.sh --stop-on-fail
```

### CI/CD Pipeline

```bash
# .github/workflows/validate.yml or similar
./scripts/run-complete-validation.sh --ci --stop-on-fail

# Parse results
exit_code=$?
if [ $exit_code -eq 0 ]; then
  echo "Validation passed - proceeding with deployment"
else
  echo "Validation failed - blocking deployment"
  exit $exit_code
fi
```

### Pre-Production Validation

```bash
# Full validation with all optional checks
./scripts/run-complete-validation.sh \
  --verbose \
  --stop-on-fail

# Review reports
cat validation-reports/validation-*.json | jq .
open validation-reports/validation-*.html
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: UV Migration Validation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Run Complete Validation
        run: ./scripts/run-complete-validation.sh --ci --stop-on-fail

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-reports
          path: validation-reports/

      - name: Post Results
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('validation-reports/validation-latest.json'));
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ❌ Validation Failed\n\nFailed Phases: ${report.failed}`
            });
```

### GitLab CI Example

```yaml
stages:
  - validate
  - build
  - deploy

uv-validation:
  stage: validate
  image: python:3.11-slim
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.cargo/bin:$PATH"
  script:
    - ./scripts/run-complete-validation.sh --ci --stop-on-fail
  artifacts:
    when: always
    paths:
      - validation-reports/
    reports:
      junit: validation-reports/validation-*.json
  only:
    - main
    - develop
    - merge_requests
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    stages {
        stage('UV Validation') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.cargo/bin:$PATH"
                    ./scripts/run-complete-validation.sh --ci --stop-on-fail
                '''
            }
        }

        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'validation-reports',
                    reportFiles: 'validation-*.html',
                    reportName: 'Validation Report'
                ])

                archiveArtifacts artifacts: 'validation-reports/**/*'
            }
        }
    }

    post {
        failure {
            emailext (
                subject: "UV Validation Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}",
                body: "Check validation reports: ${env.BUILD_URL}Validation_20Report/",
                to: "dev-team@example.com"
            )
        }
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. UV Installation Fails

**Problem:** `curl -LsSf https://astral.sh/uv/install.sh | sh` fails

**Solution:**
```bash
# Check internet connectivity
curl -I https://astral.sh

# Try manual download
wget https://github.com/astral-sh/uv/releases/download/0.5.17/uv-x86_64-unknown-linux-gnu.tar.gz
tar -xzf uv-x86_64-unknown-linux-gnu.tar.gz
sudo mv uv /usr/local/bin/

# Verify installation
uv --version
```

#### 2. uv.lock Generation Fails

**Problem:** `uv lock` reports dependency conflicts

**Solution:**
```bash
# Check specific conflict
uv lock --verbose

# Update conflicting dependency
# Edit pyproject.toml to resolve version constraints

# Force regenerate
./scripts/setup-uv-environment.sh --force-lock
```

#### 3. Docker Build Fails

**Problem:** Docker build fails with "permission denied"

**Solution:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Restart Docker
sudo systemctl restart docker
```

#### 4. Health Check Fails

**Problem:** Container health check keeps failing

**Solution:**
```bash
# Check container logs
docker logs <container-name>

# Test health endpoint manually
docker exec <container-name> curl -f http://localhost:8000/health

# Verify environment variables
docker exec <container-name> env | grep -E "(DATABASE|REDIS|NEO4J|OPENAI)"
```

#### 5. Security Scan Issues

**Problem:** Trivy not found or security scan fails

**Solution:**
```bash
# Install Trivy
# Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Or run without security scan
./scripts/validate-uv-docker-build.sh --skip-security
```

#### 6. Hardcoded Value Detected

**Problem:** Scripts detect hardcoded localhost or credentials

**Solution:**
```bash
# Find hardcoded values
grep -r "localhost" src/ --include="*.py" | grep -v "__pycache__"

# Replace with environment variables
# Before:
database_url = "postgresql://user:pass@localhost:5432/db"

# After:
from src.core.config import config
database_url = config.DATABASE_URL

# Update .env.production
echo "DATABASE_URL=postgresql://user:pass@postgres:5432/db" >> .env.production
```

### Performance Issues

#### Slow Docker Builds

**Problem:** Docker builds taking too long (>5 minutes per image)

**Solutions:**
```bash
# 1. Enable BuildKit
export DOCKER_BUILDKIT=1

# 2. Use --no-cache only when necessary
./scripts/validate-uv-docker-build.sh  # Uses cache

# 3. Prune unused images and build cache
docker system prune -a

# 4. Check disk space
df -h

# 5. Optimize Docker daemon
# Edit /etc/docker/daemon.json
{
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 10
}
sudo systemctl restart docker
```

#### Memory Issues

**Problem:** Build fails with "out of memory"

**Solutions:**
```bash
# Check Docker memory limit
docker info | grep -i memory

# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory → Set to 8GB+

# Build images sequentially
./scripts/validate-uv-docker-build.sh  # Already sequential

# Reduce concurrent builds (if modified)
# In validate-uv-docker-build.sh, build one at a time
```

---

## Best Practices

### 1. Pre-Commit Validation

**Always run before committing:**
```bash
# Quick check
./scripts/setup-uv-environment.sh --check-only

# Full validation before major commits
./scripts/run-complete-validation.sh --stop-on-fail
```

### 2. Dependency Management

**When adding dependencies:**
```bash
# Add to pyproject.toml (not requirements.txt)
uv add fastapi==0.109.0

# Update lockfile
uv lock

# Validate
./scripts/setup-uv-environment.sh --force-lock
```

### 3. Docker Image Optimization

**Keep images lean:**
```bash
# Review layer sizes
./scripts/validate-uv-docker-build.sh --verbose

# Check for largest layers
docker history horme-api:uv-test --no-trunc | head -10

# Combine RUN commands to reduce layers
# Before: RUN apt-get update
#         RUN apt-get install -y gcc
# After:  RUN apt-get update && apt-get install -y gcc
```

### 4. Security Hardening

**Regular security scans:**
```bash
# Weekly security scans
./scripts/validate-uv-docker-build.sh --security-scan

# Update dependencies monthly
uv lock --upgrade

# Review security reports
trivy image --severity HIGH,CRITICAL horme-api:latest
```

### 5. Report Archival

**Maintain validation history:**
```bash
# Archive old reports
mkdir -p validation-reports/archive/$(date +%Y-%m)
mv validation-reports/validation-*.* validation-reports/archive/$(date +%Y-%m)/

# Keep last 30 days
find validation-reports/archive -mtime +30 -delete
```

### 6. CI/CD Integration

**Optimize pipeline execution:**
```bash
# Use fast mode for feature branches
./scripts/run-complete-validation.sh --fast --ci

# Full validation for main/production branches
./scripts/run-complete-validation.sh --ci --security-scan

# Cache UV dependencies in CI
# GitHub Actions: uses: actions/cache@v3
#   with:
#     path: ~/.cache/uv
#     key: uv-${{ hashFiles('uv.lock') }}
```

### 7. Documentation

**Keep documentation updated:**
```bash
# Update after script changes
# Document new flags, options, exit codes

# Include examples for common scenarios
# Add troubleshooting for new issues
```

---

## Production Deployment Checklist

Before deploying to production, ensure:

- [ ] All validation scripts pass
- [ ] No hardcoded values detected
- [ ] No mock data in production code
- [ ] uv.lock is committed and up-to-date
- [ ] Docker images built successfully
- [ ] Health checks configured and passing
- [ ] Security scans show no CRITICAL vulnerabilities
- [ ] Environment variables configured in .env.production
- [ ] Database migrations tested
- [ ] Backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented

---

## Conclusion

These three automation scripts provide comprehensive validation for UV migration and production deployment. They enforce CLAUDE.md standards, prevent common mistakes, and ensure reproducible, secure builds.

**Key Achievements:**

✅ Zero hardcoded values
✅ Zero mock data
✅ Complete environment-based configuration
✅ Automated validation pipeline
✅ Comprehensive reporting
✅ CI/CD ready
✅ Production-grade quality

**Support:**

For issues, questions, or contributions:
1. Check this guide's troubleshooting section
2. Review script output and error messages
3. Check validation reports in `validation-reports/`
4. Refer to CLAUDE.md for production standards

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-18
**Maintainer:** Horme POV Team
