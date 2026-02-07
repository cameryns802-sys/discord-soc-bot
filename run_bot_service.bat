@echo off
REM This batch file runs the bot as a service (minimized, no window)
REM Used by Windows Task Scheduler for 24/7 operation

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run bot with restart on crash
:restart
echo [%date% %time%] Starting Discord SOC Bot...
python bot.py

REM If bot crashes, wait 5 seconds and restart
echo [%date% %time%] Bot stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak
goto restart
