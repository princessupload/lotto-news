@echo off
REM Setup Windows Task Scheduler for Daily Family Lottery Email
REM Runs DAILY at 12:00 PM CT (Noon)

echo ============================================
echo   FAMILY EMAIL SCHEDULER SETUP
echo   Schedule: DAILY at 12:00 PM CT (Noon)
echo ============================================
echo.

REM Delete existing task if it exists
schtasks /delete /tn "DailyFamilyLotteryEmail" /f 2>nul

REM Create new task that runs daily at 12:00 PM (Noon CT)
schtasks /create /tn "DailyFamilyLotteryEmail" /tr "pythonw \"%~dp0daily_email_report.py\"" /sc daily /st 12:00 /ru "%USERNAME%" /rl HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! Family email scheduled for DAILY at 12:00 PM CT
    echo.
    echo Recipients: sarasinead@aol.com, marysineadart@gmail.com,
    echo             princessuploadie@gmail.com, rick@gamingdatasystems.com
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator.
)

echo.
echo ============================================
echo   COMMANDS
echo ============================================
echo To verify:  schtasks /query /tn "DailyFamilyLotteryEmail"
echo To run now: schtasks /run /tn "DailyFamilyLotteryEmail"
echo To delete:  schtasks /delete /tn "DailyFamilyLotteryEmail" /f
echo.
pause
