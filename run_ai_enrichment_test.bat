@echo off
REM Run ScraperAPI + AI Enrichment Test

set SCRAPERAPI_KEY=your-scraperapi-key-here
set OPENAI_API_KEY=sk-proj-your-openai-api-key-here
set DB_PORT=5434
set DB_PASSWORD=your-database-password-here
set BATCH_SIZE=10
set CONFIDENCE_THRESHOLD=0.7

echo.
echo ================================================================================
echo SCRAPERAPI + AI ENRICHMENT TEST
echo ================================================================================
echo Testing 10 products to validate approach
echo ================================================================================
echo.

python scripts\scraperapi_ai_enrichment.py

echo.
echo Test complete! Check results above.
pause
