@echo off
REM Production Backend Restart Script
REM This script properly stops the old backend and starts a new one

echo ======================================
echo Restarting Backend API Server
echo ======================================
echo.

REM Step 1: Find and stop existing backend processes
echo [1/4] Stopping existing backend processes...
for /f "tokens=2" %%i in ('netstat -ano ^| findstr ":8002" ^| findstr "LISTENING"') do (
    echo Found process on port 8002: %%i
    taskkill /PID %%i /F >nul 2>&1
)

REM Step 2: Wait for clean shutdown
echo [2/4] Waiting for clean shutdown...
timeout /t 3 /nobreak >nul

REM Step 3: Verify port is free
echo [3/4] Verifying port 8002 is available...
netstat -ano | findstr ":8002" | findstr "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    echo ERROR: Port 8002 is still in use!
    echo Please manually close the process and try again.
    pause
    exit /b 1
)

echo Port 8002 is now available.

REM Step 4: Load environment variables from .env file
echo [4/4] Loading environment variables and starting backend...
for /f "tokens=1,* delims==" %%a in ('type .env ^| findstr /v "^#"') do (
    set "%%a=%%b"
)

REM Set additional required variables
set DB_HOST=localhost
set DB_PORT=5434
set DB_NAME=horme_db
set DB_USER=horme_user

REM Start the backend API server
echo.
echo Starting backend on http://0.0.0.0:8002
echo Environment: Development
echo Press Ctrl+C to stop
echo.

python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload
