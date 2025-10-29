@echo off
REM Quick test runner for ScraperAPI
REM Sets API key and runs test

set SCRAPERAPI_KEY=3c29b7d4798bd49564aacf76ba828d8a

echo.
echo ================================================================================
echo Running ScraperAPI Test
echo ================================================================================
echo API Key: %SCRAPERAPI_KEY:~0,10%...%SCRAPERAPI_KEY:~-5%
echo.

python scripts\test_scraperapi.py

pause
