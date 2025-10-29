@echo off
REM Network Deployment Verification Script for Horme POV
REM Tests the new isolated network configuration

echo ==========================================
echo Horme POV Network Deployment Verification
echo ==========================================
echo.

set FAILURE_COUNT=0

echo [1/8] Checking Docker daemon status...
docker info >nul 2>&1
if errorlevel 1 (
    echo     ❌ Docker daemon is not running
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ Docker daemon is running
)

echo.
echo [2/8] Verifying isolated networks exist...
docker network inspect horme-isolated-network >nul 2>&1
if errorlevel 1 (
    echo     ❌ horme-isolated-network not found
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ horme-isolated-network exists
)

docker network inspect legalcopilot-isolated-network >nul 2>&1
if errorlevel 1 (
    echo     ❌ legalcopilot-isolated-network not found
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ legalcopilot-isolated-network exists
)

docker network inspect pickleball-isolated-network >nul 2>&1
if errorlevel 1 (
    echo     ❌ pickleball-isolated-network not found
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ pickleball-isolated-network exists
)

echo.
echo [3/8] Checking for port conflicts...
netstat -an | findstr ":5434.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo     ✅ Port 5434 (Horme PostgreSQL) is available
) else (
    echo     ❌ Port 5434 is already in use
    set /a FAILURE_COUNT+=1
)

netstat -an | findstr ":8002.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo     ✅ Port 8002 (Horme API) is available
) else (
    echo     ❌ Port 8002 is already in use
    set /a FAILURE_COUNT+=1
)

netstat -an | findstr ":3010.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo     ✅ Port 3010 (Horme Frontend) is available
) else (
    echo     ❌ Port 3010 is already in use
    set /a FAILURE_COUNT+=1
)

echo.
echo [4/8] Checking network IP ranges...
docker network inspect horme-isolated-network --format "{{range .IPAM.Config}}{{.Subnet}}{{end}}" | findstr "172.30.0.0/16" >nul 2>&1
if errorlevel 1 (
    echo     ❌ horme-isolated-network has incorrect subnet
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ horme-isolated-network subnet is correct (172.30.0.0/16)
)

echo.
echo [5/8] Verifying environment configuration...
if exist ".env.production" (
    findstr /C:"API_PORT=8002" .env.production >nul 2>&1
    if errorlevel 1 (
        echo     ❌ .env.production missing API_PORT=8002
        set /a FAILURE_COUNT+=1
    ) else (
        echo     ✅ .env.production has correct port configuration
    )
) else (
    echo     ⚠️  .env.production not found (copy from .env.production.network-isolated)
)

echo.
echo [6/8] Testing Horme service connectivity...
docker ps --format "{{.Names}}" | findstr "horme-postgres" >nul 2>&1
if not errorlevel 1 (
    echo     ✅ Horme PostgreSQL container is running
    
    REM Test database connectivity
    docker exec horme-postgres pg_isready -U horme_user >nul 2>&1
    if errorlevel 1 (
        echo     ❌ PostgreSQL is not ready
        set /a FAILURE_COUNT+=1
    ) else (
        echo     ✅ PostgreSQL is ready and accepting connections
    )
) else (
    echo     ⚠️  Horme PostgreSQL container not running (start with deploy-docker.bat)
)

docker ps --format "{{.Names}}" | findstr "horme-redis" >nul 2>&1
if not errorlevel 1 (
    echo     ✅ Horme Redis container is running
    
    REM Test Redis connectivity
    docker exec horme-redis redis-cli ping >nul 2>&1
    if errorlevel 1 (
        echo     ❌ Redis is not responding
        set /a FAILURE_COUNT+=1
    ) else (
        echo     ✅ Redis is responding to ping
    )
) else (
    echo     ⚠️  Horme Redis container not running (start with deploy-docker.bat)
)

echo.
echo [7/8] Testing external connectivity...
timeout /t 2 >nul 2>&1

REM Test if services are accessible from host
curl -s -o nul -w "%%{http_code}" http://localhost:3010 2>nul | findstr "200" >nul 2>&1
if not errorlevel 1 (
    echo     ✅ Horme Frontend accessible on http://localhost:3010
) else (
    curl -s -f http://localhost:3010 >nul 2>&1
    if errorlevel 1 (
        echo     ⚠️  Horme Frontend not accessible (may not be running)
    ) else (
        echo     ✅ Horme Frontend responding
    )
)

curl -s -o nul -w "%%{http_code}" http://localhost:8002/health 2>nul | findstr "200" >nul 2>&1
if not errorlevel 1 (
    echo     ✅ Horme API accessible on http://localhost:8002/health
) else (
    echo     ⚠️  Horme API not accessible (may not be running)
)

echo.
echo [8/8] Checking for project isolation...
docker network inspect horme-isolated-network --format "{{range .Containers}}{{.Name}} {{end}}" | findstr "legalcopilot\|pickleball" >nul 2>&1
if not errorlevel 1 (
    echo     ❌ Non-Horme containers found in Horme network
    set /a FAILURE_COUNT+=1
) else (
    echo     ✅ Horme network properly isolated
)

echo.
echo ==========================================
echo Verification Summary
echo ==========================================

if %FAILURE_COUNT% EQU 0 (
    echo ✅ All checks passed! Network deployment is successful.
    echo.
    echo Access your services at:
    echo   Frontend:     http://localhost:3010
    echo   API:          http://localhost:8002
    echo   MCP Server:   ws://localhost:3004
    echo   Nexus:        http://localhost:8090
    echo   Database:     localhost:5434
    echo   Cache:        localhost:6381
) else (
    echo ❌ %FAILURE_COUNT% check(s) failed. Review the issues above.
    echo.
    echo Common fixes:
    echo   1. Run: .\scripts\cleanup-docker-conflicts.bat
    echo   2. Copy: .env.production.network-isolated to .env.production
    echo   3. Start: .\deploy-docker.bat start
)

echo.
echo Detailed network information:
docker network ls | findstr "horme\|legal\|pickleball"
echo.
echo Running containers:
docker ps --format "table {{.Names}}\t{{.Ports}}" | findstr "horme\|legal\|pickleball"

echo.
pause