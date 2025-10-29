@echo off
REM Batch script to load products into PostgreSQL
REM Sets environment variables and runs the Python script

SET DATABASE_URL=postgresql://horme_user:2b63586bf11e28434f192c20cebbee4373fc66d82364527a@localhost:5434/horme_db

echo ================================================================================
echo Horme Product Data Loader
echo ================================================================================
echo Database: localhost:5434/horme_db
echo Excel File: docs/reference/ProductData (Top 3 Cats).xlsx
echo ================================================================================
echo.

python scripts\load_horme_products.py

echo.
echo ================================================================================
echo Loading Complete
echo ================================================================================
pause
