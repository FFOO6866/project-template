# UV Migration Validation Checklist
## Pre-Migration, During-Migration, and Post-Migration Validation

**Purpose**: Ensure UV migration is successful and production-ready
**Updated**: 2025-10-18

---

## Pre-Migration Validation

### Environment Preparation

- [ ] **UV installed globally**
  ```bash
  pip install uv
  uv --version  # Should show v0.1.x or higher
  ```

- [ ] **Backup created**
  ```bash
  mkdir -p .migration-backup/$(date +%Y%m%d)
  cp requirements*.txt .migration-backup/$(date +%Y%m%d)/
  cp src/*/requirements*.txt .migration-backup/$(date +%Y%m%d)/
  cp deployment/docker/requirements*.txt .migration-backup/$(date +%Y%m%d)/
  ```

- [ ] **Git branch created**
  ```bash
  git checkout -b feat/uv-migration
  git push -u origin feat/uv-migration
  ```

- [ ] **Team notified**
  - Slack announcement posted
  - Migration timeline communicated
  - Rollback plan shared

### Dependency Analysis

- [ ] **All requirements files identified**
  ```bash
  find . -name "requirements*.txt" -type f
  # Expected: 13 files
  ```

- [ ] **Version conflicts documented**
  - See UV_MIGRATION_ANALYSIS.md section 2
  - All 12 conflicts have resolution strategy

- [ ] **Deprecated packages identified**
  - python-jwt → PyJWT
  - asyncio → (remove, stdlib)
  - pathlib2 → (remove, stdlib in 3.11+)

- [ ] **Service dependencies mapped**
  - API service dependencies listed
  - WebSocket service dependencies listed
  - Nexus service dependencies listed
  - MCP service dependencies listed
  - Knowledge Graph dependencies listed
  - Intent Classification dependencies listed
  - Translation service dependencies listed
  - Test dependencies listed

### Infrastructure Preparation

- [ ] **Docker Desktop running**
  ```bash
  docker --version
  docker-compose --version
  docker info  # Should show running daemon
  ```

- [ ] **Sufficient disk space**
  ```bash
  df -h  # Should have > 20GB free
  ```

- [ ] **Network connectivity verified**
  ```bash
  curl https://pypi.org/simple/
  # Should return 200 OK
  ```

---

## Phase 1: Foundation (Day 1, Hours 1-4)

### Root Configuration Creation

- [ ] **pyproject.toml created**
  ```bash
  ls -la pyproject.toml
  # Should exist in project root
  ```

- [ ] **Shared dependencies defined**
  - [ ] FastAPI, Uvicorn, Pydantic
  - [ ] Database drivers (asyncpg, psycopg2, SQLAlchemy)
  - [ ] Redis client
  - [ ] HTTP clients (httpx, requests, aiohttp)
  - [ ] WebSocket support
  - [ ] Logging (structlog)
  - [ ] Monitoring (prometheus-client)
  - [ ] Configuration (python-dotenv)

- [ ] **Optional dependencies defined**
  - [ ] `[project.optional-dependencies]` section exists
  - [ ] `api` extra defined
  - [ ] `websocket` extra defined
  - [ ] `nexus` extra defined
  - [ ] `mcp` extra defined
  - [ ] `knowledge-graph` extra defined
  - [ ] `intent-classification` extra defined
  - [ ] `translation` extra defined
  - [ ] `test` extra defined
  - [ ] `dev` extra defined
  - [ ] `all` extra defined (combines all above)

### Lockfile Generation

- [ ] **Lockfile generated successfully**
  ```bash
  uv lock
  # Should complete in < 30 seconds
  ls -la uv.lock
  # Should show ~50-100KB file
  ```

- [ ] **No unresolved conflicts**
  ```bash
  uv tree --conflicts
  # Should return empty or list resolved conflicts
  ```

- [ ] **All platforms supported**
  ```bash
  # Lockfile should include wheels for:
  # - linux_x86_64
  # - win_amd64
  # - macosx_x86_64 / macosx_arm64
  ```

### API Service Testing (Critical Path)

- [ ] **API dependencies install**
  ```bash
  uv sync --extra api
  # Should complete in < 2 minutes
  ```

- [ ] **Virtual environment created**
  ```bash
  ls -la .venv/
  # Should show populated virtual environment
  ```

- [ ] **API imports work**
  ```bash
  uv run python -c "import fastapi; import openai; import sqlalchemy; print('OK')"
  # Should print "OK"
  ```

- [ ] **API unit tests pass**
  ```bash
  uv run pytest tests/unit/api/ -v
  # All tests should pass
  ```

- [ ] **API server starts**
  ```bash
  timeout 10 uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
  sleep 5
  curl http://localhost:8000/health
  # Should return 200 OK
  killall uvicorn
  ```

### Docker Build Testing (API)

- [ ] **Dockerfile.api updated**
  ```dockerfile
  # Should use UV instead of pip
  grep "uv sync" Dockerfile.api
  ```

- [ ] **Docker image builds**
  ```bash
  docker build -f Dockerfile.api -t horme-api:uv-test .
  # Should complete successfully
  ```

- [ ] **Image size acceptable**
  ```bash
  docker images horme-api:uv-test
  # Should be <= baseline or have justification for increase
  ```

- [ ] **Container starts**
  ```bash
  docker run -d --name api-test -p 8000:8000 horme-api:uv-test
  sleep 5
  curl http://localhost:8000/health
  # Should return 200 OK
  docker stop api-test && docker rm api-test
  ```

- [ ] **Container imports work**
  ```bash
  docker run --rm horme-api:uv-test python -c "import fastapi; import openai; print('OK')"
  # Should print "OK"
  ```

### Phase 1 Checkpoint

- [ ] **All Phase 1 tasks completed**
- [ ] **API service fully functional with UV**
- [ ] **Docker build working**
- [ ] **Team lead approval to proceed to Phase 2**
- [ ] **No critical blockers identified**

---

## Phase 2: Service Migration (Day 1-2, Hours 5-12)

### WebSocket Service

- [ ] **Dependencies install**
  ```bash
  uv sync --extra websocket
  ```

- [ ] **Imports work**
  ```bash
  uv run python -c "import websockets; import openai; print('OK')"
  ```

- [ ] **Unit tests pass**
  ```bash
  uv run pytest tests/unit/websocket/ -v
  ```

- [ ] **Dockerfile.websocket updated**
  ```bash
  grep "uv sync" Dockerfile.websocket
  ```

- [ ] **Docker image builds**
  ```bash
  docker build -f Dockerfile.websocket -t horme-websocket:uv-test .
  ```

- [ ] **Container starts and serves**
  ```bash
  docker run -d --name ws-test -p 8001:8001 horme-websocket:uv-test
  sleep 5
  # Test WebSocket connection
  docker stop ws-test && docker rm ws-test
  ```

### Nexus Platform

- [ ] **Dependencies install**
  ```bash
  uv sync --extra nexus
  ```

- [ ] **Imports work**
  ```bash
  uv run python -c "import nexus; import kailash; import dataflow; print('OK')"
  ```

- [ ] **Unit tests pass**
  ```bash
  uv run pytest tests/unit/nexus/ -v
  ```

- [ ] **Dockerfile.nexus updated**
  ```bash
  grep "uv sync" Dockerfile.nexus
  ```

- [ ] **Docker image builds**
  ```bash
  docker build -f Dockerfile.nexus -t horme-nexus:uv-test .
  ```

- [ ] **Container starts**
  ```bash
  docker run -d --name nexus-test -p 8080:8080 horme-nexus:uv-test
  sleep 5
  curl http://localhost:8080/health
  docker stop nexus-test && docker rm nexus-test
  ```

### MCP Server

- [ ] **Dependencies install**
  ```bash
  uv sync --extra mcp
  ```

- [ ] **Imports work**
  ```bash
  uv run python -c "import kailash; import fastmcp; print('OK')"
  ```

- [ ] **Unit tests pass**
  ```bash
  uv run pytest tests/unit/mcp/ -v
  ```

- [ ] **Dockerfile.mcp updated**
  ```bash
  grep "uv sync" deployment/docker/Dockerfile.mcp-production
  ```

- [ ] **Docker image builds**
  ```bash
  docker build -f deployment/docker/Dockerfile.mcp-production -t horme-mcp:uv-test .
  ```

- [ ] **Container starts**
  ```bash
  docker run -d --name mcp-test -p 3002:3002 horme-mcp:uv-test
  sleep 5
  # Test MCP connection
  docker stop mcp-test && docker rm mcp-test
  ```

### ML Services (Knowledge Graph + Intent Classification)

- [ ] **Knowledge Graph dependencies install**
  ```bash
  uv sync --extra knowledge-graph
  ```

- [ ] **Knowledge Graph imports work**
  ```bash
  uv run python -c "import neo4j; import chromadb; import sentence_transformers; print('OK')"
  ```

- [ ] **Knowledge Graph tests pass**
  ```bash
  uv run pytest tests/unit/knowledge_graph/ -v
  ```

- [ ] **Intent Classification dependencies install**
  ```bash
  uv sync --extra intent-classification
  ```

- [ ] **Intent Classification imports work**
  ```bash
  uv run python -c "import torch; import transformers; import spacy; print('OK')"
  ```

- [ ] **Intent Classification tests pass**
  ```bash
  uv run pytest tests/unit/intent_classification/ -v
  ```

### Translation Service

- [ ] **Translation dependencies install**
  ```bash
  uv sync --extra translation
  ```

- [ ] **Translation imports work**
  ```bash
  uv run python -c "import openai; import langdetect; print('OK')"
  ```

- [ ] **Translation tests pass**
  ```bash
  uv run pytest tests/unit/translation/ -v
  ```

### Phase 2 Checkpoint

- [ ] **All services install successfully**
- [ ] **All unit tests pass**
- [ ] **All Docker images build**
- [ ] **No import errors in any service**
- [ ] **Team lead approval to proceed to Phase 3**

---

## Phase 3: Integration Testing (Day 2, Hours 13-18)

### Full Environment Testing

- [ ] **All dependencies install together**
  ```bash
  rm -rf .venv
  uv sync --all-extras
  # Should complete successfully
  ```

- [ ] **Dependency tree clean**
  ```bash
  uv tree --conflicts
  # Should show no unresolved conflicts
  ```

### Integration Tests

- [ ] **Database integration tests pass**
  ```bash
  uv run pytest tests/integration/test_database.py -v
  ```

- [ ] **Redis integration tests pass**
  ```bash
  uv run pytest tests/integration/test_redis.py -v
  ```

- [ ] **API integration tests pass**
  ```bash
  uv run pytest tests/integration/api/ -v
  ```

- [ ] **All integration tests pass**
  ```bash
  uv run pytest tests/integration/ -v
  # All tests should pass
  ```

### Docker Compose Testing

- [ ] **docker-compose.yml updated**
  ```bash
  # All service definitions should reference updated Dockerfiles
  grep -A 5 "build:" docker-compose.test.yml
  ```

- [ ] **All images build**
  ```bash
  docker-compose -f docker-compose.test.yml build
  # Should build all services successfully
  ```

- [ ] **Stack starts successfully**
  ```bash
  docker-compose -f docker-compose.test.yml up -d
  docker-compose -f docker-compose.test.yml ps
  # All services should be "Up"
  ```

- [ ] **Health checks pass**
  ```bash
  curl http://localhost:8000/health  # API
  curl http://localhost:8080/health  # Nexus
  # All should return 200 OK
  ```

- [ ] **E2E tests pass**
  ```bash
  uv run pytest tests/e2e/ -v
  # All E2E tests should pass
  ```

- [ ] **Stack stops cleanly**
  ```bash
  docker-compose -f docker-compose.test.yml down
  # Should stop without errors
  ```

### Performance Benchmarking

- [ ] **Installation time measured**
  ```bash
  # Baseline (pip)
  time pip install -r requirements.txt
  # Baseline result: _____ seconds

  # UV
  rm -rf .venv
  time uv sync --all-extras
  # UV result: _____ seconds

  # Improvement: _____% faster
  # Target: > 50% faster
  ```

- [ ] **Docker build time measured**
  ```bash
  # Baseline (pip)
  docker build -f Dockerfile.api.old -t api:pip .
  # Baseline result: _____ seconds

  # UV
  docker build -f Dockerfile.api -t api:uv .
  # UV result: _____ seconds

  # Improvement: _____% faster
  # Target: > 30% faster
  ```

- [ ] **Image size measured**
  ```bash
  docker images | grep horme-api
  # pip baseline: _____ MB
  # uv result: _____ MB
  # Difference: _____ MB
  # Target: <= baseline or justified
  ```

- [ ] **Lockfile generation time measured**
  ```bash
  rm uv.lock
  time uv lock
  # Result: _____ seconds
  # Target: < 30 seconds
  ```

### Load Testing (Optional)

- [ ] **Locust load test runs**
  ```bash
  uv run locust -f tests/performance/locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
  ```

- [ ] **No performance regression**
  - Response time p50: <= baseline
  - Response time p95: <= baseline
  - Throughput: >= baseline
  - Error rate: <= baseline

### Phase 3 Checkpoint

- [ ] **All integration tests pass**
- [ ] **E2E tests pass**
- [ ] **Performance targets met**
- [ ] **No functionality regression**
- [ ] **Docker Compose stack functional**
- [ ] **Team lead approval to proceed to Phase 4**

---

## Phase 4: Documentation & Rollout (Day 3, Hours 19-24)

### Documentation Updates

- [ ] **CLAUDE.md updated**
  - [ ] UV installation instructions added
  - [ ] UV workflow examples added
  - [ ] Common tasks with UV documented
  - [ ] Troubleshooting section updated
  - [ ] References to requirements.txt replaced

- [ ] **README.md updated**
  - [ ] Quick start uses UV
  - [ ] Installation section updated
  - [ ] Development workflow uses UV

- [ ] **DEPLOYMENT_QUICKSTART_GUIDE.md updated**
  - [ ] Docker build instructions use UV
  - [ ] Deployment commands updated

- [ ] **UV_QUICK_REFERENCE.md created**
  - [ ] Common tasks cheat sheet
  - [ ] UV vs pip command reference
  - [ ] Service-specific commands
  - [ ] Troubleshooting guide

### CI/CD Pipeline Updates

- [ ] **GitHub Actions updated**
  ```yaml
  # .github/workflows/test.yml should use UV
  grep "setup-uv" .github/workflows/test.yml
  ```

- [ ] **GitHub Actions runs successfully**
  - Push to branch and verify CI passes

- [ ] **GitLab CI updated (if applicable)**
  ```yaml
  # .gitlab-ci.yml should use UV
  grep "uv sync" .gitlab-ci.yml
  ```

- [ ] **GitLab CI runs successfully**
  - Push to branch and verify CI passes

### Deployment Scripts

- [ ] **deploy-docker.bat updated (Windows)**
  ```batch
  grep "uv sync" deploy-docker.bat
  ```

- [ ] **deploy-docker.sh updated (Linux/Mac)**
  ```bash
  grep "uv sync" deploy-docker.sh
  ```

- [ ] **Scripts tested**
  ```bash
  ./deploy-docker.sh full
  # Should build and start all services
  ./deploy-docker.sh health
  # Should show all services healthy
  ./deploy-docker.sh stop
  ```

### Team Training

- [ ] **Training session scheduled**
  - Date: _____________
  - Time: _____________
  - Duration: 2 hours
  - Attendees: All developers

- [ ] **Training materials prepared**
  - [ ] Presentation slides
  - [ ] Live demo script
  - [ ] Hands-on exercises
  - [ ] Q&A document

- [ ] **Training session completed**
  - [ ] All developers attended
  - [ ] Hands-on exercises completed
  - [ ] Questions answered
  - [ ] Feedback collected

- [ ] **Post-training survey**
  - [ ] Developers feel confident using UV
  - [ ] Developers know where to get help
  - [ ] No major concerns raised

### Migration Guide

- [ ] **UV_MIGRATION_EXECUTIVE_SUMMARY.md reviewed**
- [ ] **ADR-009 approved**
- [ ] **UV_MIGRATION_ANALYSIS.md published**
- [ ] **Rollback procedures documented**

### Cleanup

- [ ] **Old requirements files removed**
  ```bash
  git rm requirements.txt
  git rm requirements-api.txt
  git rm requirements-websocket.txt
  git rm requirements-translation.txt
  git rm src/new_project/requirements-*.txt
  git rm deployment/docker/requirements-*.txt
  git rm src/knowledge_graph/requirements.txt
  git rm src/intent_classification/requirements.txt
  ```

- [ ] **.gitignore updated**
  ```gitignore
  # UV
  .uv/
  __pypackages__/

  # Keep lockfile
  !uv.lock
  ```

- [ ] **Backup requirements preserved**
  ```bash
  ls -la .migration-backup/$(date +%Y%m%d)/
  # Should show all backed up files
  ```

### Final Validation

- [ ] **Clean checkout test**
  ```bash
  # Simulate new developer
  cd /tmp
  git clone <repo-url> horme-test
  cd horme-test
  uv sync --all-extras
  uv run pytest tests/unit/
  # Should work end-to-end
  ```

- [ ] **Docker production build test**
  ```bash
  docker-compose -f docker-compose.production.yml build
  docker-compose -f docker-compose.production.yml up -d
  # Check health
  docker-compose -f docker-compose.production.yml down
  ```

- [ ] **All services functional**
  - [ ] API service
  - [ ] WebSocket service
  - [ ] Nexus platform
  - [ ] MCP server
  - [ ] Knowledge Graph
  - [ ] Intent Classification
  - [ ] Translation service

### Git Commit

- [ ] **Commit message prepared**
  ```
  feat: Migrate from pip to UV package manager

  - Consolidate 13 requirements files into single pyproject.toml
  - Resolve 12 version conflicts
  - Remove 4 deprecated packages (python-jwt, asyncio, pathlib2)
  - Add workspace structure for monorepo
  - Update all Dockerfiles to use UV multi-stage builds
  - Update CI/CD pipelines (GitHub Actions, GitLab CI)
  - 68% reduction in dependency duplication
  - 3-5x faster installation times
  - Add comprehensive documentation and training materials

  BREAKING CHANGE: Development workflow now uses UV instead of pip.
  See UV_QUICK_REFERENCE.md for migration guide.

  Related:
  - ADR-009: UV Package Manager Migration
  - UV_MIGRATION_ANALYSIS.md: Detailed dependency analysis
  - UV_MIGRATION_EXECUTIVE_SUMMARY.md: Decision rationale
  ```

- [ ] **Changes committed**
  ```bash
  git add .
  git commit -F commit-message.txt
  ```

- [ ] **Changes pushed**
  ```bash
  git push origin feat/uv-migration
  ```

### Pull Request

- [ ] **PR created**
  - Title: "feat: Migrate from pip to UV package manager"
  - Description includes summary and links to ADR
  - All checklists completed
  - Screenshots/benchmarks attached

- [ ] **PR reviewed by stakeholders**
  - [ ] Tech Lead approval
  - [ ] DevOps approval
  - [ ] Backend team approval
  - [ ] QA approval

- [ ] **PR merged to main**

### Phase 4 Checkpoint

- [ ] **All documentation updated**
- [ ] **CI/CD pipelines working**
- [ ] **Team trained**
- [ ] **Old files removed**
- [ ] **Changes merged to main**
- [ ] **Migration complete!**

---

## Post-Migration Monitoring (Week 1)

### Day 1 After Merge

- [ ] **Production deployment successful**
  ```bash
  # Deploy to production
  ./deploy-production.sh
  ```

- [ ] **All services healthy**
  ```bash
  curl https://api.production.example/health
  # All services return 200 OK
  ```

- [ ] **Monitoring dashboards green**
  - Prometheus: No alerts
  - Grafana: Metrics normal
  - Logs: No errors

- [ ] **Team using UV successfully**
  - No major issues reported
  - Questions answered promptly

### Day 3 After Merge

- [ ] **No rollbacks required**
- [ ] **CI/CD pipelines stable**
- [ ] **Docker builds completing faster**
- [ ] **Team velocity unchanged or improved**

### Week 1 After Merge

- [ ] **Performance metrics validated**
  - CI/CD time: _____ % faster
  - Developer install time: _____ % faster
  - Docker build time: _____ % faster

- [ ] **Team satisfaction survey**
  - [ ] >= 80% satisfaction rate
  - [ ] No major usability complaints
  - [ ] Productivity improved or unchanged

- [ ] **Post-migration retrospective**
  - What went well?
  - What could be improved?
  - Lessons learned for future migrations

---

## Rollback Validation (Test Before Migration)

### Rollback Procedure Test

- [ ] **Rollback script tested**
  ```bash
  # Test rollback procedure
  ./scripts/rollback-to-pip.sh
  # Should restore requirements.txt files
  ```

- [ ] **Services work after rollback**
  ```bash
  pip install -r requirements.txt
  python -m src.api.main
  # Should start successfully
  ```

- [ ] **Rollback time measured**
  - Rollback duration: _____ minutes
  - Target: < 60 minutes

### Rollback Triggers

Document when to trigger rollback:
- [ ] Critical service failure (API down > 5 min)
- [ ] Unresolvable dependency conflicts
- [ ] Docker build failures blocking deployment
- [ ] Team consensus to abort (>50% vote)
- [ ] Production incident caused by migration

---

## Success Metrics Dashboard

### Quantitative Metrics

| Metric | Baseline (Pip) | Target (UV) | Actual (UV) | Status |
|--------|---------------|-------------|-------------|--------|
| Installation time | 5-8 min | < 2 min | _____ min | [ ] |
| Docker build time | 10-15 min | < 7 min | _____ min | [ ] |
| Lockfile generation | N/A | < 30 sec | _____ sec | [ ] |
| Image size (API) | _____ MB | <= baseline | _____ MB | [ ] |
| CI/CD pipeline time | _____ min | < 70% baseline | _____ min | [ ] |
| Onboarding time | 30-45 min | < 10 min | _____ min | [ ] |

### Qualitative Metrics

- [ ] **Zero version conflicts** in uv.lock
- [ ] **All deprecated packages removed**
- [ ] **Documentation 100% updated**
- [ ] **Team >80% satisfied** with UV
- [ ] **No production incidents** caused by migration
- [ ] **Rollback plan tested and ready**

---

## Final Sign-Off

### Stakeholder Approval

- [ ] **Tech Lead**: _____________________ Date: _______
- [ ] **DevOps Lead**: ___________________ Date: _______
- [ ] **Backend Team**: __________________ Date: _______
- [ ] **QA Lead**: ______________________ Date: _______

### Migration Status

- [ ] **Pre-migration validation**: Complete
- [ ] **Phase 1 (Foundation)**: Complete
- [ ] **Phase 2 (Services)**: Complete
- [ ] **Phase 3 (Integration)**: Complete
- [ ] **Phase 4 (Rollout)**: Complete
- [ ] **Post-migration monitoring**: Complete

### Final Verdict

- [ ] **Migration successful** - All criteria met
- [ ] **Migration successful with caveats** - Document issues
- [ ] **Migration failed** - Rollback executed

### Lessons Learned

Document key learnings for future reference:
1. What worked well?
2. What challenges were encountered?
3. What would you do differently?
4. Recommendations for similar migrations?

---

**Document Owner**: DevOps Team
**Last Updated**: 2025-10-18
**Next Review**: After migration completion
