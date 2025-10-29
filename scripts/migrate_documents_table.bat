@echo off
REM Database Migration Script for Documents Table (Windows)
REM Safely creates documents table if it doesn't exist

echo =========================================
echo Horme POV - Documents Table Migration
echo =========================================
echo.

REM Configuration from environment or defaults
if not defined DB_HOST set DB_HOST=localhost
if not defined DB_PORT set DB_PORT=5433
if not defined DB_NAME set DB_NAME=horme_db
if not defined DB_USER set DB_USER=horme_user
if not defined DB_PASSWORD set DB_PASSWORD=horme_pass

echo Database Configuration:
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_USER%
echo.

REM Check if docker is available (for Docker Desktop users)
docker --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Using Docker PostgreSQL...
    echo.
    echo Creating documents table...

    docker exec -i horme-postgres psql -U %DB_USER% -d %DB_NAME% < migrations\create_documents_table.sql

    if %ERRORLEVEL% EQU 0 (
        echo.
        echo =========================================
        echo Migration completed successfully!
        echo =========================================
        echo.
        echo Next steps:
        echo 1. Restart your API server: docker-compose restart horme-api
        echo 2. Test document upload: POST /api/v1/documents/upload
        echo 3. Monitor processing: GET /api/v1/documents/status/{id}
        echo.
    ) else (
        echo.
        echo =========================================
        echo Migration failed!
        echo =========================================
        echo.
        echo Please check if the horme-postgres container is running:
        echo   docker ps ^| findstr postgres
        echo.
        exit /b 1
    )
) else (
    echo ERROR: Docker not found
    echo.
    echo This script requires Docker for Windows.
    echo Please ensure Docker Desktop is installed and running.
    echo.
    echo Alternatively, use psql directly:
    echo   psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f migrations\create_documents_table.sql
    echo.
    exit /b 1
)
