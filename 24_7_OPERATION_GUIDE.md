# Discord SOC Bot - 24/7 Operation Guide

## Overview
Your Discord bot will continue running 24/7 even when your computer screen turns off, as long as the computer itself stays powered on.

---

## **OPTION 1: Python Manager (Easiest & Recommended)**

### Setup
```powershell
# Run this once to set the PowerShell execution policy (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then use this batch file to start the bot
.\start_bot_managed.bat
```

### What it does:
- ✅ Starts your bot
- ✅ Auto-restarts if it crashes
- ✅ Shows real-time logs
- ✅ Handles Ctrl+C gracefully
- ✅ Exponential backoff for restarts

### How to stop:
Press `Ctrl+C` in the terminal

---

## **OPTION 2: Windows Task Scheduler (Best for Hands-Off)**

### Setup (requires Administrator)
```batch
# 1. Open Command Prompt as Administrator
# 2. Navigate to bot directory
cd "C:\Users\camer\OneDrive\Documents\Discord bot"

# 3. Run the setup script
setup_task_scheduler.bat
```

### What it does:
- ✅ Auto-starts bot when computer boots
- ✅ Runs even when you're not logged in
- ✅ Auto-restarts on crash
- ✅ Truly 24/7 (even if you restart PC)

### How to stop:
```batch
# Open Command Prompt as Administrator and run:
schtasks /delete /tn "Discord SOC Bot" /f
```

### How to verify it's running:
```batch
schtasks /query /tn "Discord SOC Bot"
```

---

## **OPTION 3: PowerShell Manager (Advanced)**

### Setup
```powershell
# Run directly with PowerShell
cd "C:\Users\camer\OneDrive\Documents\Discord bot"
powershell -ExecutionPolicy Bypass -File start_bot_managed.ps1
```

### Parameters:
```powershell
# Custom restart delay (in seconds)
.\start_bot_managed.ps1 -RestartDelaySeconds 10

# Limit restarts to 5 attempts
.\start_bot_managed.ps1 -MaxRestarts 5
```

---

## **OPTION 4: Prevent Sleep Mode (Simple)**

If you want to keep your computer awake while the bot runs:

```batch
.\start_bot_no_sleep.bat
```

This will:
- Keep your screen from turning off
- Keep Windows from sleeping
- Run the bot in the foreground

---

## **Recommended Setup for 24/7 Operation**

1. **Use Task Scheduler** for maximum uptime
2. **Configure Windows Sleep Settings**:
   - Settings → System → Power & sleep
   - Set "Sleep" to "Never"
   - Set "Screen timeout" to desired duration

3. **Or use PowerShell Manager** if you prefer to see logs

---

## **Monitoring Your Bot**

### Check if bot is running:
```batch
tasklist | findstr python
```

### Kill bot process if needed:
```batch
taskkill /F /IM python.exe
```

### View Task Scheduler task:
```batch
schtasks /query /tn "Discord SOC Bot" /v
```

---

## **Logging & Debugging**

### Check recent crashes:
The bot logs all events to `logs/bot.log`

```powershell
# View last 50 lines of log
Get-Content "logs\bot.log" -Tail 50
```

### Enable detailed logging:
Edit `.env`:
```
LOG_LEVEL=DEBUG
ENABLE_DETAILED_LOGGING=true
```

---

## **Cloud Deployment (Best Long-term Solution)**

For true 24/7 reliability, consider deploying to:

- **Replit.com** (free tier available)
- **Railway.app** (cheap monthly costs)
- **Heroku** (traditional option)
- **AWS EC2** (if you need more power)
- **DigitalOcean** (affordable VPS)

This ensures the bot runs even if your home computer is down.

---

## **Troubleshooting**

### Bot keeps crashing?
1. Check logs: `type logs\bot.log | tail -100`
2. Check .env file for missing variables
3. Run with DEBUG: `LOG_LEVEL=DEBUG python bot.py`

### Task Scheduler not starting bot?
1. Run Task Scheduler as Administrator
2. Check "Run with highest privileges" in task settings
3. Verify the path to run_bot_service.bat is correct

### Bot won't auto-restart?
1. Use Python Manager instead: `start_bot_managed.bat`
2. Check Windows Task Scheduler logs:
   - Event Viewer → Windows Logs → System

### Memory leak / slow over time?
1. Set automatic restart schedule: Update `.env`:
   ```
   RESTART_INTERVAL_HOURS=6  # Restart every 6 hours
   ```
2. Monitor memory: `tasklist /v | findstr python`

---

## **Quick Start Checklist**

- [ ] Copy one of the batch/PowerShell files to your bot directory
- [ ] Test manually: Run `python bot.py` once to verify it works
- [ ] Choose your 24/7 method (recommended: Task Scheduler)
- [ ] Set up automatic startup
- [ ] Disable Windows sleep mode
- [ ] Verify bot is running after system reboot

---

**Need help?** Check the logs in `logs/bot.log` for details.
