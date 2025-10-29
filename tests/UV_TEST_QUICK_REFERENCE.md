# UV Migration Testing - Quick Reference

## Test File Locations

```
tests/
├── integration/
│   ├── test_uv_docker_build.py      # Docker build validation (15 tests)
│   └── test_uv_dependencies.py      # Dependency management (26 tests)
└── e2e/
    └── test_uv_deployment.py        # Full stack deployment (21 tests)

scripts/
└── validate_production_complete.py  # Enhanced with UV checks
```

## Quick Commands

### Run Specific Test Categories

```bash
# 1. Dependency Validation (FASTEST - No Docker required)
pytest tests/integration/test_uv_dependencies.py -v
# Validates: pyproject.toml, uv.lock, OpenAI version, no duplicates

# 2. Docker Build Validation (MEDIUM - Builds images)
pytest tests/integration/test_uv_docker_build.py -v
# Validates: Dockerfile builds, image sizes, health checks, security

# 3. Full Stack Deployment (SLOWEST - Complete E2E)
docker-compose -f docker-compose.uv.yml up -d
pytest tests/e2e/test_uv_deployment.py -v
docker-compose -f docker-compose.uv.yml down -v
# Validates: Stack startup, API endpoints, real DB/Redis, env vars
```

### Run All UV Tests

```bash
# Complete UV test suite
pytest tests/integration/test_uv_docker_build.py \
       tests/integration/test_uv_dependencies.py \
       tests/e2e/test_uv_deployment.py \
       -v --tb=short --maxfail=5
```

### Production Validation

```bash
# Enhanced validation script with UV checks
python scripts/validate_production_complete.py

# Expected sections:
# ✅ UV Configuration Check: 10/10
# ✅ UV Lockfile Check: 10/10
# ✅ UV Dockerfiles Check: 10/10
```

## Test Markers

```bash
# Run only UV-specific tests
pytest -m "uv" -v

# Run integration tests (Tier 2)
pytest -m "integration" tests/integration/test_uv_* -v

# Run E2E tests (Tier 3)
pytest -m "e2e" tests/e2e/test_uv_* -v

# Run Docker-related tests
pytest -m "docker" -v
```

## Common Test Scenarios

### 1. Pre-Commit Validation
```bash
# Quick dependency check before commit
pytest tests/integration/test_uv_dependencies.py::TestPyprojectConfiguration -v
pytest tests/integration/test_uv_dependencies.py -k "openai" -v
```

### 2. Build Verification
```bash
# Verify Docker builds succeed
pytest tests/integration/test_uv_docker_build.py::TestUVDockerBuilds -v
```

### 3. Image Size Monitoring
```bash
# Check image sizes are optimized
pytest tests/integration/test_uv_docker_build.py::TestUVImageOptimization -v
```

### 4. Security Audit
```bash
# Check security best practices
pytest tests/integration/test_uv_docker_build.py::TestUVImageSecurity -v
pytest tests/integration/test_uv_docker_build.py -k "hardcoded" -v
```

### 5. Full Stack Health Check
```bash
# Verify complete deployment
pytest tests/e2e/test_uv_deployment.py::TestUVStackDeployment -v
pytest tests/e2e/test_uv_deployment.py::TestAPIEndpoints::test_health_endpoint_responds -v
```

## Test Output Examples

### ✅ Success Output
```
test_uv_docker_build.py::TestUVDockerBuilds::test_api_dockerfile_builds_successfully PASSED
test_uv_dependencies.py::TestPyprojectConfiguration::test_openai_version_standardized PASSED
test_uv_deployment.py::TestAPIEndpoints::test_health_endpoint_responds PASSED

======== 56 passed in 245.32s ========
```

### ❌ Failure Examples

#### Hardcoded Value Detected
```
FAILED test_uv_docker_build.py::test_no_hardcoded_values_in_dockerfiles
AssertionError: Dockerfile.api.uv contains hardcoded password: ['password="secret123"']
```

#### OpenAI Version Mismatch
```
FAILED test_uv_dependencies.py::test_openai_version_standardized
AssertionError: OpenAI should be version 1.51.2, found: openai==1.40.0
```

#### Missing uv.lock
```
SKIPPED test_uv_dependencies.py::test_uv_lock_consistent_with_pyproject
Reason: uv.lock not found, run 'uv lock' first
```

## Debugging Failed Tests

### 1. View Detailed Error
```bash
pytest tests/integration/test_uv_docker_build.py -v --tb=long
```

### 2. Run Single Test
```bash
pytest tests/integration/test_uv_dependencies.py::TestPyprojectConfiguration::test_openai_version_standardized -v
```

### 3. Enable Debug Logging
```bash
pytest tests/e2e/test_uv_deployment.py -v --log-cli-level=DEBUG
```

### 4. Keep Docker Containers Running
```bash
docker-compose -f docker-compose.uv.yml up -d
pytest tests/e2e/test_uv_deployment.py -v
# Don't run 'down' to inspect containers
docker-compose -f docker-compose.uv.yml logs api
```

## Continuous Integration

### GitHub Actions Snippet
```yaml
- name: Run UV Migration Tests
  run: |
    pytest tests/integration/test_uv_docker_build.py \
           tests/integration/test_uv_dependencies.py \
           -v --junitxml=uv-tests.xml

- name: Validate Production Standards
  run: python scripts/validate_production_complete.py
```

### Local Pre-Push Hook
```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running UV migration tests..."
pytest tests/integration/test_uv_dependencies.py -v --maxfail=3

if [ $? -ne 0 ]; then
    echo "❌ UV tests failed. Push aborted."
    exit 1
fi

echo "✅ UV tests passed!"
```

## Performance Benchmarks

| Test Category | Tests | Duration | Requirements |
|--------------|-------|----------|--------------|
| Dependency Validation | 26 | ~30s | UV installed |
| Docker Build | 15 | ~180s | Docker + 2GB RAM |
| E2E Deployment | 21 | ~240s | Docker + 4GB RAM |
| **Total** | **62** | **~450s** | **Full stack** |

## Troubleshooting

### uv.lock out of sync
```bash
Error: uv.lock is out of sync with pyproject.toml

Fix:
uv lock
git add uv.lock
git commit -m "Update uv.lock"
```

### Docker build timeout
```bash
Error: Timeout waiting for build

Fix:
pytest tests/integration/test_uv_docker_build.py --timeout=600
# Or increase timeout in test file
```

### Port conflicts
```bash
Error: Port 5433 already in use

Fix:
# Check what's using the port
lsof -i :5433
# Kill the process or use different port in .env.production
```

### Missing dependencies
```bash
Error: ModuleNotFoundError: No module named 'toml'

Fix:
pip install toml  # Or add to requirements-test.txt
```

## File Reference

### Test Files (Created)
1. `tests/integration/test_uv_docker_build.py` - Docker build validation
2. `tests/integration/test_uv_dependencies.py` - Dependency management
3. `tests/e2e/test_uv_deployment.py` - Full stack deployment

### Enhanced Files
1. `scripts/validate_production_complete.py` - Added UV checks

### Documentation
1. `UV_MIGRATION_TESTING_COMPLETE.md` - Complete guide
2. `tests/UV_TEST_QUICK_REFERENCE.md` - This file

## Production Checklist

Before deploying UV migration:

- [ ] `pytest tests/integration/test_uv_dependencies.py -v` passes
- [ ] `pytest tests/integration/test_uv_docker_build.py -v` passes
- [ ] `pytest tests/e2e/test_uv_deployment.py -v` passes
- [ ] `python scripts/validate_production_complete.py` score ≥ 75%
- [ ] `uv.lock` exists and committed to git
- [ ] OpenAI version standardized to 1.51.2
- [ ] No hardcoded values in Dockerfiles
- [ ] All images under 1.2GB
- [ ] All services use environment variables

---

**Quick Start:** `pytest tests/integration/test_uv_dependencies.py -v`
**Full Test:** `pytest tests/integration/test_uv_* tests/e2e/test_uv_* -v`
**Validate:** `python scripts/validate_production_complete.py`
