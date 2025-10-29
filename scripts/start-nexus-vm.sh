#!/bin/bash
# VM-Optimized Nexus Platform Startup Script
# Includes multi-channel coordination and database connectivity fixes

set -e

echo "🔀 Starting Horme Nexus Platform (VM-Optimized)"
echo "==============================================="

# Environment validation
echo "📋 Validating environment..."
if [[ -z "$DATABASE_URL" ]]; then
    echo "❌ DATABASE_URL is not set"
    exit 1
fi

if [[ -z "$REDIS_URL" ]]; then
    echo "❌ REDIS_URL is not set"
    exit 1
fi

# Database connection test with retry logic
echo "🔍 Testing database connectivity..."
max_attempts=30
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if python -c "
import psycopg2
import os
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
try:
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        connect_timeout=10
    )
    conn.close()
    print('✅ Database connection successful')
    exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"; then
        echo "✅ Database connectivity confirmed"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - Waiting for database..."
        sleep 5
        ((attempt++))
    fi
done

if [[ $attempt -gt $max_attempts ]]; then
    echo "❌ Database connection failed after $max_attempts attempts"
    exit 1
fi

# Redis connection test
echo "🔍 Testing Redis connectivity..."
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if python -c "
import redis
import os
from urllib.parse import urlparse

url = urlparse(os.environ['REDIS_URL'])
try:
    r = redis.Redis(
        host=url.hostname,
        port=url.port or 6379,
        password=url.password,
        socket_timeout=10,
        socket_connect_timeout=10
    )
    r.ping()
    print('✅ Redis connection successful')
    exit(0)
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"; then
        echo "✅ Redis connectivity confirmed"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - Waiting for Redis..."
        sleep 3
        ((attempt++))
    fi
done

if [[ $attempt -gt $max_attempts ]]; then
    echo "❌ Redis connection failed after $max_attempts attempts"
    exit 1
fi

# Wait for dependent services
echo "🔗 Waiting for dependent services..."
echo "   - Checking API service..."
max_service_attempts=20
attempt=1

while [[ $attempt -le $max_service_attempts ]]; do
    if curl -f -s -S --max-time 5 http://api:8000/health >/dev/null 2>&1; then
        echo "   ✅ API service is ready"
        break
    else
        echo "   ⏳ Attempt $attempt/$max_service_attempts - Waiting for API service..."
        sleep 10
        ((attempt++))
    fi
done

echo "   - Checking MCP service..."
attempt=1
while [[ $attempt -le $max_service_attempts ]]; do
    if curl -f -s -S --max-time 5 http://mcp:3002/health >/dev/null 2>&1; then
        echo "   ✅ MCP service is ready"
        break
    else
        echo "   ⏳ Attempt $attempt/$max_service_attempts - Waiting for MCP service..."
        sleep 10
        ((attempt++))
    fi
done

# Pre-flight system checks
echo "🔧 Running pre-flight checks..."
echo "   - Python version: $(python --version)"
echo "   - Working directory: $(pwd)"
echo "   - Available memory: $(free -h | grep '^Mem' | awk '{print $7}' 2>/dev/null || echo 'Unknown')"

# Set VM-optimized runtime parameters
export NEXUS_PORT=${NEXUS_PORT:-8080}
export NEXUS_WORKERS=${NEXUS_WORKERS:-2}
export NEXUS_SESSION_TIMEOUT=${NEXUS_SESSION_TIMEOUT:-3600}

echo "⚙️  Runtime Configuration (VM-Optimized):"
echo "   - Port: $NEXUS_PORT"
echo "   - Workers: $NEXUS_WORKERS"
echo "   - Session Timeout: ${NEXUS_SESSION_TIMEOUT}s"
echo "   - Channels: ${NEXUS_CHANNELS:-api,cli,mcp}"

# Start the Nexus platform
echo "🌟 Starting Horme Nexus platform..."
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers $NEXUS_WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --keep-alive 5 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile /app/logs/nexus-access.log \
    --error-logfile /app/logs/nexus-error.log \
    --log-level info \
    src.nexus_production_api:app