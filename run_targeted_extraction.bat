@echo off
REM Targeted ERP Price Extraction
REM Only extracts prices for products already in database

set DB_HOST=localhost
set DB_PORT=5434
set DB_NAME=horme_db
set DB_USER=horme_user
set DB_PASSWORD=96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42

echo.
echo ================================================================================
echo HORME ERP TARGETED PRICE EXTRACTION
echo ================================================================================
echo This will extract prices for ONLY the 19,143 products in your database
echo Much faster than extracting all 69,926 products!
echo Estimated time: 20-30 minutes
echo ================================================================================
echo.

python scripts\extract_targeted_prices.py

echo.
echo Extraction complete!
pause
