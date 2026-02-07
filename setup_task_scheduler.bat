@echo off
REM Create scheduled task to run bot at startup
REM Run this script as Administrator

echo Creating Windows Task Scheduler entry for Discord SOC Bot...
echo.

REM Get current directory
for /f "tokens=*" %%A in ('cd') do set BOTDIR=%%A

REM Create task (remove old one first if exists)
taskkill /F /FI "WINDOWTITLE eq Discord SOC Bot*" 2>nul
schtasks /delete /tn "Discord SOC Bot" /f 2>nul

REM Create new task that runs at startup
schtasks /create /tn "Discord SOC Bot" /tr "cmd /c \"%BOTDIR%\run_bot_service.bat\"" /sc onstart /ru SYSTEM /f

echo Task created! The bot will now auto-start when your computer starts.
echo.
pause
