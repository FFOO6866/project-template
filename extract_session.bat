@echo off
REM Extract Horme.com.sg Session Cookies
REM Opens browser for manual login, then saves session cookies

echo.
echo ================================================================================
echo HORME.COM.SG SESSION COOKIE EXTRACTOR
echo ================================================================================
echo.
echo This script will:
echo 1. Install Playwright if needed
echo 2. Open a browser window
echo 3. Wait for you to log in to Horme.com.sg
echo 4. Save your session cookies for automated scraping
echo.
echo ================================================================================
echo.

REM Check if Playwright is installed
python -c "import playwright" 2>nul
if errorlevel 1 (
    echo Playwright not found. Installing...
    echo.
    pip install playwright
    echo.
    echo Installing Chromium browser...
    playwright install chromium
    echo.
    echo ================================================================================
    echo Installation complete!
    echo ================================================================================
    echo.
)

echo Starting session extraction...
echo.
python scripts\extract_horme_session.py

echo.
echo ================================================================================
if exist horme_session.json (
    echo SUCCESS! Session saved to: horme_session.json
    echo.
    echo Next step: Run authenticated enrichment
    echo Command: run_authenticated_enrichment.bat
) else (
    echo Session extraction failed or cancelled
    echo Please try again
)
echo ================================================================================
pause
