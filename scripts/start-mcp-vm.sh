#!/bin/bash
# VM-Optimized MCP Server Startup Script
# Includes database connectivity fixes and optimized WebSocket handling

set -e

echo "🔗 Starting Horme MCP Server (VM-Optimized)"
echo "============================================"

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

# Pre-flight system checks
echo "🔧 Running pre-flight checks..."
echo "   - Python version: $(python --version)"
echo "   - Working directory: $(pwd)"
echo "   - Available memory: $(free -h | grep '^Mem' | awk '{print $7}' 2>/dev/null || echo 'Unknown')"

# Set VM-optimized runtime parameters
export MCP_PORT=${MCP_PORT:-3002}
export MCP_TIMEOUT=${MCP_TIMEOUT:-300}
export MCP_MAX_CONNECTIONS=${MCP_MAX_CONNECTIONS:-50}

echo "⚙️  Runtime Configuration (VM-Optimized):"
echo "   - Port: $MCP_PORT"
echo "   - Timeout: ${MCP_TIMEOUT}s"
echo "   - Max Connections: $MCP_MAX_CONNECTIONS"

# Start the MCP server
echo "🌟 Starting Horme MCP server..."
exec python -c "
import sys
sys.path.insert(0, '/app/src')

import asyncio
import os
from production_nexus_mcp_server import run_mcp_server

if __name__ == '__main__':
    asyncio.run(run_mcp_server())
"