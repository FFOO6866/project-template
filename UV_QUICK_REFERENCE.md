# UV Quick Reference Guide
## Team Cheat Sheet for UV Package Manager

**Updated**: 2025-10-18
**Audience**: All Developers

---

## TL;DR - Just Tell Me What Changed

**Old Way (pip)**:
```bash
pip install -r requirements.txt
```

**New Way (UV)**:
```bash
uv sync
```

That's it. Everything else is similar or easier.

---

## Common Tasks

### Initial Setup (First Time)

**Before (pip)**:
```bash
git clone repo
cd repo
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-api.txt
pip install -r requirements-test.txt
# ... 13 files total
```

**After (UV)**:
```bash
git clone repo
cd repo
uv sync --all-extras
# Done! Virtual environment created automatically at .venv
```

**Time savings**: 30-45 min → < 10 min

---

### Daily Development

#### Activate Virtual Environment

**Before**:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**After**:
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or use uv run (no activation needed)
uv run python script.py
uv run pytest tests/
```

#### Install Dependencies

**Before**:
```bash
pip install -r requirements-api.txt
```

**After**:
```bash
uv sync --extra api

# Or install everything
uv sync --all-extras
```

#### Add a New Package

**Before**:
```bash
# Manually edit requirements.txt
echo "requests==2.31.0" >> requirements.txt
pip install -r requirements.txt
```

**After**:
```bash
uv add requests

# Add to specific service
uv add openai --optional api

# Add dev dependency
uv add --dev pytest
```

#### Remove a Package

**Before**:
```bash
# Manually edit requirements.txt
# Remove line
pip install -r requirements.txt
```

**After**:
```bash
uv remove requests
```

#### Update a Package

**Before**:
```bash
pip install --upgrade requests
pip freeze > requirements.txt
```

**After**:
```bash
uv lock --upgrade-package requests

# Or update all packages
uv lock --upgrade
```

#### See What's Installed

**Before**:
```bash
pip list
pip freeze
```

**After**:
```bash
uv pip list
uv pip freeze

# See dependency tree
uv tree
```

---

### Running Code

#### Run Python Scripts

**Before**:
```bash
source venv/bin/activate
python src/main.py
```

**After**:
```bash
# No activation needed
uv run python src/main.py

# Or activate first (same as before)
source .venv/bin/activate
python src/main.py
```

#### Run Tests

**Before**:
```bash
source venv/bin/activate
pytest tests/
```

**After**:
```bash
uv run pytest tests/

# Or with specific extras
uv sync --extra test
uv run pytest tests/
```

#### Run Application

**Before**:
```bash
source venv/bin/activate
uvicorn src.api.main:app --reload
```

**After**:
```bash
uv run uvicorn src.api.main:app --reload
```

---

### Docker Development

#### Build Docker Image

**Before**:
```dockerfile
# Dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
```
```bash
docker build -t myapp .
```

**After**:
```dockerfile
# Dockerfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra api
```
```bash
docker build -t myapp .
```

#### Docker Compose

**Before**:
```bash
docker-compose up
```

**After**:
```bash
# Same command! Dockerfiles updated internally
docker-compose up
```

---

### Troubleshooting

#### "uv: command not found"

**Solution**:
```bash
pip install uv
# Or
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
```

#### Virtual Environment Not Found

**Solution**:
```bash
# UV creates .venv automatically
uv sync

# If you want a different location
UV_VENV_PATH=/path/to/venv uv sync
```

#### Dependency Conflict

**Before (pip)**:
```bash
# Cryptic error, manual resolution required
ERROR: package-a requires package-b<2.0, but you have 2.1
```

**After (UV)**:
```bash
# Clear error message during lock
error: Could not resolve dependencies:
  package-a==1.0.0 requires package-b<2.0
  package-c==2.0.0 requires package-b>=2.1

# UV tells you exactly what's wrong and suggests fixes
```

**Solution**:
```bash
# Update conflicting package
uv add package-a --upgrade

# Or pin specific version
uv add "package-b<2.0"
```

#### "Lockfile is out of date"

**Solution**:
```bash
uv lock
```

#### Import Error at Runtime

**Solution**:
```bash
# Make sure you synced dependencies
uv sync --all-extras

# Check what's installed
uv pip list | grep package-name

# Verify in correct environment
which python  # Should point to .venv/bin/python
```

---

### Git Workflow

#### Pull Changes with New Dependencies

**Before**:
```bash
git pull
pip install -r requirements.txt
```

**After**:
```bash
git pull
uv sync  # Reads uv.lock and installs exact versions
```

#### Merge Conflict in Lockfile

**Solution**:
```bash
# Accept both changes, then regenerate lockfile
git checkout --theirs uv.lock  # Or --ours
uv lock  # Regenerate from pyproject.toml
```

#### Commit New Dependency

**Before**:
```bash
# Edit requirements.txt
pip install package
git add requirements.txt
git commit -m "Add package"
```

**After**:
```bash
uv add package
# Automatically updates pyproject.toml and uv.lock
git add pyproject.toml uv.lock
git commit -m "Add package"
```

---

## UV vs Pip Command Reference

| Task | Pip | UV |
|------|-----|-----|
| Install from lockfile | `pip install -r requirements.txt` | `uv sync` |
| Add package | Edit file + `pip install` | `uv add package` |
| Remove package | Edit file + `pip uninstall` | `uv remove package` |
| Update package | `pip install --upgrade package` | `uv lock --upgrade-package package` |
| List packages | `pip list` | `uv pip list` |
| Show package info | `pip show package` | `uv pip show package` |
| Create venv | `python -m venv venv` | Automatic with `uv sync` |
| Activate venv | `source venv/bin/activate` | `source .venv/bin/activate` |
| Run without activation | Not possible | `uv run python script.py` |
| Freeze dependencies | `pip freeze > requirements.txt` | `uv lock` |

---

## Service-Specific Commands

### API Service

```bash
# Install API dependencies
uv sync --extra api

# Run API server
uv run uvicorn src.api.main:app --reload

# Run API tests
uv run pytest tests/unit/api/
```

### WebSocket Service

```bash
# Install WebSocket dependencies
uv sync --extra websocket

# Run WebSocket server
uv run python src/websocket/server.py

# Run WebSocket tests
uv run pytest tests/unit/websocket/
```

### Nexus Platform

```bash
# Install Nexus dependencies
uv sync --extra nexus

# Run Nexus server
uv run python src/nexus/main.py

# Run Nexus tests
uv run pytest tests/unit/nexus/
```

### MCP Server

```bash
# Install MCP dependencies
uv sync --extra mcp

# Run MCP server
uv run python src/mcp/server.py

# Run MCP tests
uv run pytest tests/unit/mcp/
```

### All Services

```bash
# Install everything
uv sync --all-extras

# Run all tests
uv run pytest tests/
```

---

## Environment Variables

### UV Configuration

```bash
# Custom virtual environment location
export UV_VENV_PATH=/path/to/venv

# Use system Python instead of managed Python
export UV_PYTHON_PREFERENCE=system

# Cache directory
export UV_CACHE_DIR=/path/to/cache

# Verbose output
export UV_VERBOSE=1
```

### Project Configuration (pyproject.toml)

```toml
[tool.uv]
# Development dependencies
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=24.0.0",
]

# Package index (if using private registry)
index-url = "https://pypi.org/simple"

# Extra index URLs
extra-index-url = [
    "https://private-repo.example/simple",
]
```

---

## Performance Tips

### Faster Installs

```bash
# Use frozen lockfile (faster, no resolution)
uv sync --frozen

# Skip dev dependencies in production
uv sync --no-dev

# Install only specific extras
uv sync --extra api  # Don't install test, nexus, etc.
```

### Better Caching

```bash
# Pre-populate cache (good for CI)
uv cache prewarm

# Clear cache if corrupted
uv cache clean

# Show cache info
uv cache dir
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup UV
        uses: astral-sh/setup-uv@v1
        with:
          version: "0.1.0"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest tests/
```

### GitLab CI

```yaml
test:
  image: python:3.11
  before_script:
    - pip install uv
    - uv sync --all-extras
  script:
    - uv run pytest tests/
```

---

## Migration Checklist (For Reference)

When migrating a service from pip to UV:

- [ ] Install UV: `pip install uv`
- [ ] Create pyproject.toml (or use existing)
- [ ] Generate lockfile: `uv lock`
- [ ] Test installation: `uv sync --all-extras`
- [ ] Run tests: `uv run pytest tests/`
- [ ] Update Dockerfile
- [ ] Update CI/CD pipeline
- [ ] Update documentation
- [ ] Remove old requirements.txt files

---

## Emergency Rollback

If UV is completely broken and you need to revert immediately:

```bash
# 1. Restore old requirements files (if still in git history)
git checkout HEAD~1 -- requirements*.txt

# 2. Use pip as before
pip install -r requirements.txt

# 3. Report issue to team lead
```

---

## Getting Help

1. **UV Documentation**: https://github.com/astral-sh/uv
2. **Team Training Session**: Every Friday 2-4pm (first month)
3. **Slack Channel**: #uv-migration
4. **Internal Docs**: `docs/adr/ADR-009-uv-package-manager-migration.md`
5. **Ask in Standup**: Any UV-related questions

---

## Common Mistakes (And How to Avoid Them)

### Mistake 1: Forgetting to sync after git pull

**Problem**:
```bash
git pull
python script.py  # Error: ModuleNotFoundError
```

**Solution**:
```bash
git pull
uv sync  # Always sync after pulling
python script.py
```

### Mistake 2: Modifying uv.lock manually

**Problem**: Hand-editing uv.lock
**Solution**: Never edit uv.lock. Modify pyproject.toml and run `uv lock`

### Mistake 3: Not committing uv.lock

**Problem**: Adding uv.lock to .gitignore
**Solution**: Always commit uv.lock (unlike requirements.txt, it's meant to be committed)

### Mistake 4: Using wrong Python version

**Problem**:
```bash
uv run python script.py  # Uses wrong Python
```

**Solution**:
```bash
# Specify Python version in pyproject.toml
[project]
requires-python = ">=3.11"

# UV will enforce this
```

### Mistake 5: Installing globally instead of in project

**Problem**:
```bash
uv pip install package  # Installs in global scope
```

**Solution**:
```bash
uv add package  # Adds to project pyproject.toml
```

---

## Advanced Usage

### View Dependency Tree

```bash
# See all dependencies and their dependencies
uv tree

# See what depends on a specific package
uv tree --package requests

# Show only conflicts
uv tree --conflicts
```

### Export to requirements.txt (for compatibility)

```bash
# Export for tools that need requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Export specific extras
uv pip compile pyproject.toml --extra api -o requirements-api.txt
```

### Use UV with existing pip requirements.txt

```bash
# UV can read requirements.txt files
uv pip install -r requirements.txt

# Or convert to pyproject.toml
# (manual process, but UV can help validate)
```

### Pin specific package versions

```bash
# Add with specific version
uv add "requests==2.31.0"

# Add with version constraint
uv add "requests>=2.30,<3.0"

# Pin current version
uv add requests --pin
```

---

## Quick Comparison Chart

| Feature | Pip | UV | Better? |
|---------|-----|-----|---------|
| **Install speed** | 5-8 min | 1-2 min | UV ✓ |
| **Reproducibility** | No lockfile | uv.lock | UV ✓ |
| **Dependency resolution** | Slow | 10-100x faster | UV ✓ |
| **Conflict detection** | Runtime errors | Lock-time errors | UV ✓ |
| **Virtual env management** | Manual | Automatic | UV ✓ |
| **Learning curve** | Easy | Easy (pip-compatible) | Tie |
| **Maturity** | Very mature | New (v0.1.x) | Pip ✓ |
| **Docker support** | Good | Excellent | UV ✓ |
| **IDE integration** | Excellent | Good (improving) | Pip ✓ |

**Overall**: UV wins on performance and developer experience, pip wins on maturity

---

## Real Examples from Our Codebase

### Before: Installing for API development

```bash
# Old way (8 steps)
cd horme-pov
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-api.txt
pip install -r tests/requirements-test.txt
# Wait 6 minutes...
python src/api/main.py
```

### After: Installing for API development

```bash
# New way (3 steps)
cd horme-pov
uv sync --extra api --extra test
# Wait 90 seconds...
uv run python src/api/main.py
```

### Before: Adding OpenAI dependency

```bash
# Which file? requirements.txt? requirements-api.txt?
# Check what's already there...
grep openai requirements*.txt
# Found in 3 different files with 3 different versions!
# Edit requirements-api.txt
echo "openai==1.51.2" >> requirements-api.txt
pip install -r requirements-api.txt
# Conflict with requirements.txt version! Manual resolution...
```

### After: Adding OpenAI dependency

```bash
uv add openai --optional api
# UV automatically resolves version conflicts
# Updates pyproject.toml and uv.lock
# Done!
```

---

## Summary for the Impatient

**Three things to remember**:

1. **Install dependencies**: `uv sync`
2. **Add new package**: `uv add package-name`
3. **Run commands**: `uv run python script.py`

Everything else is similar to pip or easier. When in doubt, UV has great error messages that tell you exactly what to do.

---

**Last Updated**: 2025-10-18
**Maintained By**: DevOps Team
**Questions?**: Ask in #uv-migration Slack channel
