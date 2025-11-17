# ==============================================================================
# Dockerfile - Dynamic Job Pricing Engine (UV-based)
# ==============================================================================
# Multi-stage build using UV for fast, reliable dependency management
# UV is 10-100x faster than pip for dependency installation
# ==============================================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app/src

# Set working directory
WORKDIR /app

# Install system dependencies (required for psycopg2, selenium, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    curl \
    wget \
    # Chromium for Selenium (lighter than full Chrome)
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Builder Stage - Install Python dependencies with UV
# ==============================================================================
FROM base as builder

# Install UV (fast Python package installer) using the official installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies using UV
# UV is much faster than pip (10-100x faster)
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
    fastapi>=0.104.1 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-multipart>=0.0.6 \
    sqlalchemy>=2.0.23 \
    psycopg2-binary>=2.9.9 \
    alembic>=1.12.1 \
    asyncpg>=0.29.0 \
    pgvector>=0.2.3 \
    redis>=5.0.1 \
    hiredis>=2.2.3 \
    openai>=1.3.0 \
    tiktoken>=0.5.1 \
    celery>=5.3.4 \
    kombu>=5.3.4 \
    selenium>=4.15.0 \
    beautifulsoup4>=4.12.2 \
    lxml>=4.9.3 \
    webdriver-manager>=4.0.1 \
    pandas>=2.1.3 \
    openpyxl>=3.1.2 \
    numpy>=1.26.2 \
    xlrd>=2.0.1 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    bcrypt==4.0.1 \
    httpx>=0.25.1 \
    requests>=2.31.0 \
    python-dotenv>=1.0.0 \
    python-dateutil>=2.8.2 \
    pytz>=2023.3 \
    email-validator>=2.1.0 \
    structlog>=23.2.0 \
    sentry-sdk>=1.38.0 \
    slowapi>=0.1.9 \
    prometheus-client>=0.19.0 \
    PyPDF2>=3.0.0 \
    python-docx>=1.1.0

# ==============================================================================
# Production Stage
# ==============================================================================
FROM base as production

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv

# Add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Create app user (don't run as root for security)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/logs /app/src && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser alembic/ /app/alembic/
COPY --chown=appuser:appuser alembic.ini /app/

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.job_pricing.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================================================
# Build Instructions:
#
# Build:
#   docker build -t job-pricing-api:latest .
#
# Run (with .env file):
#   docker run --env-file .env -p 8000:8000 job-pricing-api:latest
#
# Run (with docker-compose):
#   docker-compose up -d
#
# Benefits of UV:
# - 10-100x faster than pip
# - Reliable dependency resolution
# - Better caching
# - Smaller final image size
#
# ==============================================================================
