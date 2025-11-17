# UV Setup Guide - Dynamic Job Pricing Engine

## What is UV?

UV is a extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip and provides:
- ⚡ Lightning-fast dependency installation
- 🔒 Reliable dependency resolution
- 📦 Better caching mechanism
- 🎯 Drop-in replacement for pip

## Installation

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/Mac
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Verify Installation
```bash
uv --version
```

## Local Development Setup

### 1. Create Virtual Environment
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
uv venv
```

This creates a `.venv` directory with a Python virtual environment.

### 2. Activate Virtual Environment

**Windows:**
```powershell
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

**Production dependencies only:**
```bash
uv sync
```

**With development dependencies:**
```bash
uv sync --extra dev
```

### 4. Verify Installation
```bash
python -c "import fastapi; import sqlalchemy; import openai; print('✓ All dependencies installed')"
```

## Docker Deployment

The Dockerfile has been updated to use UV for dependency installation:

### Build Docker Image
```bash
docker-compose build
```

### Run Services
```bash
docker-compose up -d
```

## Common Commands

### Add New Dependency
```bash
# Add to production dependencies
uv add <package-name>

# Add to dev dependencies
uv add --dev <package-name>
```

### Remove Dependency
```bash
uv remove <package-name>
```

### Update All Dependencies
```bash
uv sync --upgrade
```

### Run Scripts
```bash
# UV can run scripts directly
uv run pytest
uv run black src/
uv run mypy src/
```

## Benefits Over pip

1. **Speed**: 10-100x faster installation
2. **Reliability**: Better dependency resolution algorithm
3. **Caching**: Smarter caching reduces redundant downloads
4. **Modern**: Uses pyproject.toml (Python standard)
5. **Docker**: Smaller images, faster builds

## Migration from pip

The project has been migrated from `requirements.txt` to `pyproject.toml`:
- ✅ All dependencies preserved
- ✅ Version constraints maintained
- ✅ Development dependencies separated
- ✅ Tool configurations included (black, mypy, pytest)

## Troubleshooting

### UV not found after installation
Restart your terminal or add UV to PATH:
```bash
export PATH="$HOME/.cargo/bin:$PATH"  # Linux/Mac
```

### Virtual environment not activating
Make sure you're in the correct directory:
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
```

### Dependencies not installing
Try with verbose output:
```bash
uv sync -v
```

## Resources

- UV Documentation: https://github.com/astral-sh/uv
- pyproject.toml Specification: https://packaging.python.org/en/latest/specifications/pyproject-toml/
