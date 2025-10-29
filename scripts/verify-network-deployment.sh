#!/bin/bash
# Network Deployment Verification Script for Horme POV  
# Tests the new isolated network configuration

set -e

echo "=========================================="
echo "Horme POV Network Deployment Verification"
echo "=========================================="
echo

FAILURE_COUNT=0

echo "[1/8] Checking Docker daemon status..."
if docker info &>/dev/null; then
    echo "    ✅ Docker daemon is running"
else
    echo "    ❌ Docker daemon is not running"
    ((FAILURE_COUNT++))
fi

echo
echo "[2/8] Verifying isolated networks exist..."
if docker network inspect horme-isolated-network &>/dev/null; then
    echo "    ✅ horme-isolated-network exists"
else
    echo "    ❌ horme-isolated-network not found"
    ((FAILURE_COUNT++))
fi

if docker network inspect legalcopilot-isolated-network &>/dev/null; then
    echo "    ✅ legalcopilot-isolated-network exists"
else
    echo "    ❌ legalcopilot-isolated-network not found"
    ((FAILURE_COUNT++))
fi

if docker network inspect pickleball-isolated-network &>/dev/null; then
    echo "    ✅ pickleball-isolated-network exists"
else
    echo "    ❌ pickleball-isolated-network not found"
    ((FAILURE_COUNT++))
fi

echo
echo "[3/8] Checking for port conflicts..."
if ! netstat -ln | grep -q ":5434.*LISTEN"; then
    echo "    ✅ Port 5434 (Horme PostgreSQL) is available"
else
    echo "    ❌ Port 5434 is already in use"
    ((FAILURE_COUNT++))
fi

if ! netstat -ln | grep -q ":8002.*LISTEN"; then
    echo "    ✅ Port 8002 (Horme API) is available"
else
    echo "    ❌ Port 8002 is already in use"  
    ((FAILURE_COUNT++))
fi

if ! netstat -ln | grep -q ":3010.*LISTEN"; then
    echo "    ✅ Port 3010 (Horme Frontend) is available"
else
    echo "    ❌ Port 3010 is already in use"
    ((FAILURE_COUNT++))
fi

echo
echo "[4/8] Checking network IP ranges..."
HORME_SUBNET=$(docker network inspect horme-isolated-network --format "{{range .IPAM.Config}}{{.Subnet}}{{end}}" 2>/dev/null || echo "")
if [[ "$HORME_SUBNET" == "172.30.0.0/16" ]]; then
    echo "    ✅ horme-isolated-network subnet is correct (172.30.0.0/16)"
else
    echo "    ❌ horme-isolated-network has incorrect subnet: $HORME_SUBNET"
    ((FAILURE_COUNT++))
fi

echo
echo "[5/8] Verifying environment configuration..."
if [[ -f ".env.production" ]]; then
    if grep -q "API_PORT=8002" .env.production; then
        echo "    ✅ .env.production has correct port configuration"
    else
        echo "    ❌ .env.production missing API_PORT=8002"
        ((FAILURE_COUNT++))
    fi
else
    echo "    ⚠️  .env.production not found (copy from .env.production.network-isolated)"
fi

echo
echo "[6/8] Testing Horme service connectivity..."
if docker ps --format "{{.Names}}" | grep -q "horme-postgres"; then
    echo "    ✅ Horme PostgreSQL container is running"
    
    # Test database connectivity
    if docker exec horme-postgres pg_isready -U horme_user &>/dev/null; then
        echo "    ✅ PostgreSQL is ready and accepting connections"
    else
        echo "    ❌ PostgreSQL is not ready"
        ((FAILURE_COUNT++))
    fi
else
    echo "    ⚠️  Horme PostgreSQL container not running (start with ./deploy-docker.sh)"
fi

if docker ps --format "{{.Names}}" | grep -q "horme-redis"; then
    echo "    ✅ Horme Redis container is running"
    
    # Test Redis connectivity
    if docker exec horme-redis redis-cli ping &>/dev/null; then
        echo "    ✅ Redis is responding to ping"
    else
        echo "    ❌ Redis is not responding"
        ((FAILURE_COUNT++))
    fi
else
    echo "    ⚠️  Horme Redis container not running (start with ./deploy-docker.sh)"
fi

echo
echo "[7/8] Testing external connectivity..."
sleep 2

# Test if services are accessible from host
if curl -s -f http://localhost:3010 &>/dev/null; then
    echo "    ✅ Horme Frontend accessible on http://localhost:3010"
else
    echo "    ⚠️  Horme Frontend not accessible (may not be running)"
fi

if curl -s -f http://localhost:8002/health &>/dev/null; then
    echo "    ✅ Horme API accessible on http://localhost:8002/health"
else
    echo "    ⚠️  Horme API not accessible (may not be running)"
fi

echo
echo "[8/8] Checking for project isolation..."
HORME_CONTAINERS=$(docker network inspect horme-isolated-network --format "{{range .Containers}}{{.Name}} {{end}}" 2>/dev/null || echo "")
if echo "$HORME_CONTAINERS" | grep -q -E "legalcopilot|pickleball"; then
    echo "    ❌ Non-Horme containers found in Horme network"
    ((FAILURE_COUNT++))
else
    echo "    ✅ Horme network properly isolated"
fi

echo
echo "=========================================="
echo "Verification Summary"
echo "=========================================="

if [[ $FAILURE_COUNT -eq 0 ]]; then
    echo "✅ All checks passed! Network deployment is successful."
    echo
    echo "Access your services at:"
    echo "  Frontend:     http://localhost:3010"
    echo "  API:          http://localhost:8002"
    echo "  MCP Server:   ws://localhost:3004"
    echo "  Nexus:        http://localhost:8090"
    echo "  Database:     localhost:5434"
    echo "  Cache:        localhost:6381"
else
    echo "❌ $FAILURE_COUNT check(s) failed. Review the issues above."
    echo
    echo "Common fixes:"
    echo "  1. Run: ./scripts/cleanup-docker-conflicts.sh"
    echo "  2. Copy: .env.production.network-isolated to .env.production"
    echo "  3. Start: ./deploy-docker.sh start"
fi

echo
echo "Detailed network information:"
docker network ls | grep -E "horme|legal|pickleball"
echo
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "horme|legal|pickleball"

echo