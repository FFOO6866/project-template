@echo off
REM Start Backend API Server with environment variables from .env

echo ======================================
echo Starting Horme Backend API Server
echo ======================================
echo.

REM Load environment variables from .env file
for /f "tokens=1,* delims==" %%a in ('type .env ^| findstr /v "^#"') do (
    set "%%a=%%b"
)

REM Additional required environment variables
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=horme_db
set DB_USER=horme_user

echo Environment variables loaded from .env
echo.
echo Starting server on http://0.0.0.0:8002
echo Press Ctrl+C to stop
echo.

REM Start the backend API server
python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload
