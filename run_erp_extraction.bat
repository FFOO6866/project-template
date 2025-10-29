@echo off
REM Complete ERP Price Extraction
REM Extracts all 69,926 products with prices from Horme ERP

set DB_HOST=localhost
set DB_PORT=5434
set DB_NAME=horme_db
set DB_USER=horme_user
set DB_PASSWORD=96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42

echo.
echo ================================================================================
echo HORME ERP COMPLETE PRICE EXTRACTION
echo ================================================================================
echo This will extract ALL 69,926 products from the ERP admin panel
echo Estimated time: 30-60 minutes
echo ================================================================================
echo.
echo Features:
echo  - Automatic pagination through ~2,797 pages
echo  - Saves to CSV: erp_product_prices.csv
echo  - Updates PostgreSQL database automatically
echo  - Checkpoint/resume capability every 10 pages
echo  - Progress reports every 50 pages
echo.
echo ================================================================================
echo.

pause

python scripts\extract_all_erp_prices.py

echo.
echo Extraction complete! Check the results above.
pause
