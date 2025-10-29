@echo off
REM Authenticated Product Enrichment with AI
REM Requires: horme_session.json (run extract_session.bat first)

set OPENAI_API_KEY=sk-proj-your-openai-api-key-here
set BATCH_SIZE=10
set CONFIDENCE_THRESHOLD=0.7

echo.
echo ================================================================================
echo AUTHENTICATED AI PRODUCT ENRICHMENT
echo ================================================================================
echo.

REM Check if session file exists
if not exist horme_session.json (
    echo ERROR: Session file not found!
    echo.
    echo Please run: extract_session.bat
    echo This will open a browser for you to log in to Horme.com.sg
    echo.
    pause
    exit /b 1
)

echo Using saved session: horme_session.json
echo Batch size: %BATCH_SIZE%
echo Confidence threshold: %CONFIDENCE_THRESHOLD%
echo.
echo ================================================================================
echo.

python scripts\scraperapi_ai_enrichment_authenticated.py

echo.
echo ================================================================================
echo Enrichment complete! Check results above.
echo.
echo If session expired, run: extract_session.bat
echo ================================================================================
pause
