@echo off
echo ========================================
echo IMAP Password Test
echo ========================================
echo.
echo This will test IMAP connection with your password
echo.
set /p password="Enter password for integrum@horme.com.sg: "
echo.
echo Testing with mail.horme.com.sg...
echo.
python tests/utils/quick_imap_test.py integrum@horme.com.sg %password%
echo.
pause
