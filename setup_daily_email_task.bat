@echo off
REM Setup Windows Task Scheduler for Daily Lottery Email
REM This will run daily at 8:00 AM CT regardless of user login

echo Creating Windows Scheduled Task for Daily Lottery Email...

REM Delete existing task if it exists
schtasks /delete /tn "DailyLotteryEmail" /f 2>nul

REM Create new task that runs daily at 8:00 AM
REM /ru SYSTEM makes it run even when no user is logged in
schtasks /create /tn "DailyLotteryEmail" /tr "python \"%~dp0daily_email_report.py\"" /sc daily /st 08:00 /ru "%USERNAME%" /rl HIGHEST

echo.
echo Task created! The daily email will be sent at 8:00 AM every day.
echo.
echo To verify: schtasks /query /tn "DailyLotteryEmail"
echo To delete: schtasks /delete /tn "DailyLotteryEmail" /f
echo.
pause
