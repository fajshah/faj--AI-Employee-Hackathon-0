@echo off
REM Silver Tier Scheduler Windows Task Setup
REM Run this with admin privileges to schedule the Silver Tier tasks

echo Setting up Silver Tier scheduled tasks...

REM Daily LinkedIn posting at 9 AM
schtasks /create /tn "SilverTier_LinkedIn_Post" /tr "python \"%~dp0\LinkedIn_Poster.py\" " /sc daily /st 09:00 /f

REM System health check every 30 minutes during business hours
schtasks /create /tn "SilverTier_System_Check" /tr "python \"%~dp0\ai_employee_system.py\" " /sc hourly /mo 1 /f

REM Weekly report generation every Monday at 9 AM
schtasks /create /tn "SilverTier_Weekly_Report" /tr "python \"%~dp0\ai_employee_system.py\" " /sc weekly /d MON /st 09:00 /f

echo Scheduled tasks created successfully!
pause
