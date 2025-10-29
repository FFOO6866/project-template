#!/bin/bash
# VM-Optimized API Service Startup Script
# Includes database connectivity fixes and connection pooling

set -e

echo "🚀 Starting Horme API Service (VM-Optimized)"
echo "============================================="

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

# Redis connection test with retry logic
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

# Initialize database schema if needed
echo "🗃️  Initializing database schema..."
python -c "
import os
import sys
sys.path.insert(0, '/app/src')

try:
    # Import your database initialization code here
    from database_setup import initialize_schema
    initialize_schema()
    print('✅ Database schema initialized')
except ImportError:
    print('⚠️  Database initialization module not found, skipping...')
except Exception as e:
    print(f'⚠️  Database initialization error: {e}')
"

# Pre-flight system checks
echo "🔧 Running pre-flight checks..."
echo "   - Python version: $(python --version)"
echo "   - Working directory: $(pwd)"
echo "   - Available memory: $(free -h | grep '^Mem' | awk '{print $7}' 2>/dev/null || echo 'Unknown')"
echo "   - CPU cores: $(nproc 2>/dev/null || echo 'Unknown')"

# Set VM-optimized runtime parameters
export WORKERS=${WORKERS:-2}
export WORKER_CLASS=${WORKER_CLASS:-uvicorn.workers.UvicornWorker}
export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-300}
export GUNICORN_KEEPALIVE=${GUNICORN_KEEPALIVE:-5}
export DB_POOL_SIZE=${DB_POOL_SIZE:-5}
export DB_MAX_OVERFLOW=${DB_MAX_OVERFLOW:-10}

echo "⚙️  Runtime Configuration (VM-Optimized):"
echo "   - Workers: $WORKERS"
echo "   - Worker Class: $WORKER_CLASS"
echo "   - Timeout: ${GUNICORN_TIMEOUT}s"
echo "   - Keep-Alive: ${GUNICORN_KEEPALIVE}s"
echo "   - DB Pool Size: $DB_POOL_SIZE"
echo "   - DB Max Overflow: $DB_MAX_OVERFLOW"

# Start the API server with VM-optimized settings
echo "🌟 Starting Horme API server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --worker-class $WORKER_CLASS \
    --timeout $GUNICORN_TIMEOUT \
    --keep-alive $GUNICORN_KEEPALIVE \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    src.production_api_server:app