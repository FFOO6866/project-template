@echo off
REM Quick Start - Run services directly without complex Docker builds
echo ================================================================================
echo HORME POV - Quick Start (Direct Mode)
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/4] Starting PostgreSQL...
start "PostgreSQL" docker run --rm --name horme-postgres -e POSTGRES_DB=horme_db -e POSTGRES_USER=horme_user -e POSTGRES_PASSWORD=96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42 -p 5434:5432 postgres:15-alpine
timeout /t 5 >nul
echo ✓ PostgreSQL starting on port 5434
echo.

echo [2/4] Starting Redis...
start "Redis" docker run --rm --name horme-redis -p 6381:6379 redis:7-alpine redis-server --requirepass d0b6c3e5f14c813879c0cc08bfb5f81bea3d1f4aa584e7b3
timeout /t 3 >nul
echo ✓ Redis starting on port 6381
echo.

echo [3/4] Waiting for databases to initialize (10 seconds)...
timeout /t 10 >nul
echo ✓ Databases should be ready
echo.

echo [4/4] Starting Backend API...
echo.
echo ================================================================================
echo Backend API will start in this window
echo Keep this window open to see API logs
echo.
echo Press Ctrl+C to stop the API server
echo ================================================================================
echo.

set DATABASE_URL=postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db
set REDIS_URL=redis://:d0b6c3e5f14c813879c0cc08bfb5f81bea3d1f4aa584e7b3@localhost:6381/0
set JWT_SECRET=24d17531e3bab10fd01b58c7894438642b06ddf2cb942dc773cde369735cdf88
set NEXUS_JWT_SECRET=24d17531e3bab10fd01b58c7894438642b06ddf2cb942dc773cde369735cdf88
set SECRET_KEY=3ef4de347f3aafe9bef36b4359135ef3f005ba61ffda96ae111fc072f776979c
set CORS_ORIGINS=http://localhost:3000,http://localhost:3010,http://localhost:8002
set ENVIRONMENT=development
set ADMIN_EMAIL=admin@yourdomain.com
set ADMIN_PASSWORD_HASH=$2b$12$MEFztYPalfwuGYTH9yBmvOvYSHdyUPwxMCqWSfCnuYi3Wu0.Gw1Zi

python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload
