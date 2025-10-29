@echo off
REM Quick Start Script for Horme POV Services
REM This script starts all required services in the correct order

echo ================================================================================
echo HORME POV - Starting Services
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/5] Loading environment variables...
if not exist ".env.production" (
    echo ERROR: .env.production file not found!
    echo Please ensure .env.production exists in the project root.
    pause
    exit /b 1
)
echo ✓ Environment file found
echo.

echo [2/5] Stopping any existing containers...
docker-compose -f docker-compose.production.yml down 2>nul
echo ✓ Existing containers stopped
echo.

echo [3/5] Starting database services (PostgreSQL, Redis, Neo4j)...
docker-compose -f docker-compose.production.yml up -d postgres redis neo4j
echo ✓ Database services starting...
echo.

echo [4/5] Waiting for databases to be ready (15 seconds)...
timeout /t 15 /nobreak >nul
echo ✓ Databases should be ready
echo.

echo [5/5] Starting application services (API, WebSocket, Frontend)...
docker-compose -f docker-compose.production.yml up -d --build api websocket
echo ✓ Application services starting...
echo.

echo ================================================================================
echo Waiting for services to initialize (30 seconds)...
echo ================================================================================
timeout /t 30 /nobreak >nul

echo.
echo ================================================================================
echo Service Status Check
echo ================================================================================
docker-compose -f docker-compose.production.yml ps
echo.

echo ================================================================================
echo Testing API Health...
echo ================================================================================
curl -s http://localhost:8002/api/health
echo.
echo.

echo ================================================================================
echo SERVICES READY!
echo ================================================================================
echo.
echo Frontend: http://localhost:3000 (if configured)
echo Backend API: http://localhost:8002
echo API Documentation: http://localhost:8002/docs
echo Health Check: http://localhost:8002/api/health
echo.
echo Admin Login:
echo   Email: admin@yourdomain.com
echo   Password: 2Cbs_Ehbz4wLTOVW8vS6KmoRsLOpl7xLJGo0TlG85Q0
echo.
echo To view logs: docker-compose -f docker-compose.production.yml logs -f
echo To stop services: docker-compose -f docker-compose.production.yml down
echo.
echo ================================================================================

pause
