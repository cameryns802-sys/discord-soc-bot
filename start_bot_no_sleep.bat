@echo off
REM Start bot and prevent Windows from sleeping
REM This script runs the bot and keeps the system awake

echo Starting Discord SOC Bot (Sleep Prevention Enabled)...
echo.

REM Prevent system sleep while script runs
powershell -Command "Get-Process | Where-Object { $_.ProcessName -eq 'python' } | Stop-Process -Force -ErrorAction SilentlyContinue" 2>nul

REM Keep system awake by simulating activity
start "" powershell -WindowStyle Hidden -Command "while($true) { [System.Windows.Forms.SendKeys]::SendWait('{NUMLOCK}{NUMLOCK}'); Start-Sleep -Seconds 60 }"

REM Start the bot
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python bot.py

REM Cleanup on exit
taskkill /F /FI "WINDOWTITLE eq Windows PowerShell" >nul 2>&1
echo Bot stopped.
pause
