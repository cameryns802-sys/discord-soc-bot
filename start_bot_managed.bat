@echo off
REM Run the bot with automatic restart on crashes
REM This is the recommended way to run 24/7

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Starting Discord SOC Bot Manager...
echo Bot will auto-restart if it crashes.
echo Press Ctrl+C to stop.
echo.

python bot_manager.py
