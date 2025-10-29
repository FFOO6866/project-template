@echo off
REM Keyword Mapping Migration Verification Script (Windows)
REM
REM This script verifies that the database keyword mapping migration is complete
REM and ready for production deployment.
REM
REM Usage:
REM   .\scripts\verify_keyword_migration.bat

echo ================================================================================
echo Database Keyword Mapping Migration Verification
echo ================================================================================
echo.

set PASSED=0
set FAILED=0
set WARNINGS=0

echo Step 1: Verifying Docker Environment
echo --------------------------------------------------------------------------------

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [31mX Docker is not running[0m
    echo Start Docker Desktop and try again
    exit /b 1
) else (
    echo [32m✓ Docker is running[0m
    set /a PASSED+=1
)

REM Check if containers are running
docker ps | findstr horme-api >nul
if %errorlevel% neq 0 (
    echo [31mX horme-api container is not running[0m
    echo Run: docker-compose up -d
    exit /b 1
) else (
    echo [32m✓ horme-api container is running[0m
    set /a PASSED+=1
)

docker ps | findstr horme-postgres >nul
if %errorlevel% neq 0 (
    echo [31mX horme-postgres container is not running[0m
    echo Run: docker-compose up -d
    exit /b 1
) else (
    echo [32m✓ horme-postgres container is running[0m
    set /a PASSED+=1
)

echo.
echo Step 2: Verifying Database Schema
echo --------------------------------------------------------------------------------

REM Check if category_keyword_mappings table exists
docker exec horme-postgres psql -U horme_user -d horme_db -c "\dt category_keyword_mappings" | findstr "category_keyword_mappings" >nul
if %errorlevel% neq 0 (
    echo [31mX Table 'category_keyword_mappings' not found[0m
    echo Run schema migration first
    set /a FAILED+=1
    exit /b 1
) else (
    echo [32m✓ Table 'category_keyword_mappings' exists[0m
    set /a PASSED+=1
)

REM Check if task_keyword_mappings table exists
docker exec horme-postgres psql -U horme_user -d horme_db -c "\dt task_keyword_mappings" | findstr "task_keyword_mappings" >nul
if %errorlevel% neq 0 (
    echo [31mX Table 'task_keyword_mappings' not found[0m
    echo Run schema migration first
    set /a FAILED+=1
    exit /b 1
) else (
    echo [32m✓ Table 'task_keyword_mappings' exists[0m
    set /a PASSED+=1
)

echo.
echo Step 3: Verifying Data Population
echo --------------------------------------------------------------------------------

REM Check category keyword count
for /f %%i in ('docker exec horme-postgres psql -U horme_user -d horme_db -t -c "SELECT COUNT(*) FROM category_keyword_mappings"') do set CATEGORY_COUNT=%%i
if %CATEGORY_COUNT% gtr 0 (
    echo [32m✓ Category keyword mappings loaded: %CATEGORY_COUNT% records[0m
    set /a PASSED+=1
) else (
    echo [31mX No category keyword mappings found[0m
    echo Run: docker exec horme-api python scripts/load_category_task_mappings.py
    set /a FAILED+=1
    exit /b 1
)

REM Check task keyword count
for /f %%i in ('docker exec horme-postgres psql -U horme_user -d horme_db -t -c "SELECT COUNT(*) FROM task_keyword_mappings"') do set TASK_COUNT=%%i
if %TASK_COUNT% gtr 0 (
    echo [32m✓ Task keyword mappings loaded: %TASK_COUNT% records[0m
    set /a PASSED+=1
) else (
    echo [31mX No task keyword mappings found[0m
    echo Run: docker exec horme-api python scripts/load_category_task_mappings.py
    set /a FAILED+=1
    exit /b 1
)

echo.
echo Step 4: Verifying Code Changes
echo --------------------------------------------------------------------------------

REM Check if hardcoded dictionaries are removed
findstr /C:"category_keywords = {" src\ai\hybrid_recommendation_engine.py >nul
if %errorlevel% equ 0 (
    echo [31mX Hardcoded category_keywords dictionary still exists[0m
    set /a FAILED+=1
) else (
    echo [32m✓ Hardcoded category_keywords dictionary removed[0m
    set /a PASSED+=1
)

findstr /C:"'drill': 'task_drill_hole'" src\ai\hybrid_recommendation_engine.py >nul
if %errorlevel% equ 0 (
    echo [31mX Hardcoded task_keywords dictionary still exists[0m
    set /a FAILED+=1
) else (
    echo [32m✓ Hardcoded task_keywords dictionary removed[0m
    set /a PASSED+=1
)

REM Check if database loading methods exist
findstr /C:"_load_category_keywords_from_db" src\ai\hybrid_recommendation_engine.py >nul
if %errorlevel% equ 0 (
    echo [32m✓ Database loading method '_load_category_keywords_from_db' exists[0m
    set /a PASSED+=1
) else (
    echo [31mX Database loading method '_load_category_keywords_from_db' not found[0m
    set /a FAILED+=1
)

findstr /C:"_load_task_keywords_from_db" src\ai\hybrid_recommendation_engine.py >nul
if %errorlevel% equ 0 (
    echo [32m✓ Database loading method '_load_task_keywords_from_db' exists[0m
    set /a PASSED+=1
) else (
    echo [31mX Database loading method '_load_task_keywords_from_db' not found[0m
    set /a FAILED+=1
)

echo.
echo Step 5: Verifying Test Suite
echo --------------------------------------------------------------------------------

if exist "scripts\test_database_keyword_loading.py" (
    echo [32m✓ Test script exists: test_database_keyword_loading.py[0m
    set /a PASSED+=1

    REM Run tests in Docker container
    docker exec horme-api python scripts/test_database_keyword_loading.py
    if %errorlevel% equ 0 (
        echo [32m✓ Test suite passed[0m
        set /a PASSED+=1
    ) else (
        echo [31mX Test suite failed[0m
        set /a FAILED+=1
    )
) else (
    echo [31mX Test script not found: scripts\test_database_keyword_loading.py[0m
    set /a FAILED+=1
)

echo.
echo Step 6: Sample Data Verification
echo --------------------------------------------------------------------------------

echo Category keyword mappings (sample):
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT category, ARRAY_AGG(keyword ORDER BY keyword) as keywords FROM category_keyword_mappings GROUP BY category ORDER BY category LIMIT 5"

echo.
echo Task keyword mappings (sample):
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT keyword, task_id FROM task_keyword_mappings ORDER BY keyword LIMIT 5"

echo.
echo ================================================================================
echo Verification Summary
echo ================================================================================
echo [32mPassed: %PASSED%[0m
echo [31mFailed: %FAILED%[0m
echo [33mWarnings: %WARNINGS%[0m
echo.

if %FAILED% gtr 0 (
    echo [31mX VERIFICATION FAILED[0m
    echo Please fix the issues above before deploying to production
    exit /b 1
) else if %WARNINGS% gtr 0 (
    echo [33m! VERIFICATION PASSED WITH WARNINGS[0m
    echo Review warnings above, but migration is complete
    exit /b 0
) else (
    echo [32m✓ VERIFICATION PASSED[0m
    echo Migration is complete and ready for production deployment
    exit /b 0
)
