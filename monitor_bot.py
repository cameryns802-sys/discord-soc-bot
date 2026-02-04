import os
import json
import asyncio
import discord
from datetime import datetime, timedelta
import subprocess

MONITOR_TOKEN = os.getenv("MONITOR_BOT_TOKEN")
ALERT_CHANNEL_ID = int(os.getenv("MONITOR_ALERT_CHANNEL_ID", "0"))
HEARTBEAT_FILE = os.getenv("HEARTBEAT_FILE", "data/heartbeat.json")
MAINTENANCE_FILE = os.getenv("MAINTENANCE_FILE", "data/maintenance_mode.json")
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", "120"))
RESTART_COMMAND = os.getenv("RESTART_COMMAND", "")

if not MONITOR_TOKEN:
    raise SystemExit("MONITOR_BOT_TOKEN is not set")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
last_alert = None
last_restart = None

async def send_alert(text: str):
    global last_alert
    if not ALERT_CHANNEL_ID:
        return
    channel = client.get_channel(ALERT_CHANNEL_ID)
    if channel and channel.permissions_for(channel.guild.me).send_messages:
        await channel.send(text)
        last_alert = datetime.utcnow()

async def set_maintenance(reason: str):
    try:
        data = {"active": True, "reason": reason, "timestamp": datetime.utcnow().isoformat()}
        with open(MAINTENANCE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

async def attempt_restart():
    global last_restart
    if not RESTART_COMMAND:
        return
    if last_restart and datetime.utcnow() - last_restart < timedelta(minutes=15):
        return
    try:
        subprocess.Popen(RESTART_COMMAND, shell=True)
        last_restart = datetime.utcnow()
    except Exception:
        pass

async def monitor_loop():
    while True:
        await asyncio.sleep(30)
        try:
            if not os.path.exists(HEARTBEAT_FILE):
                await send_alert("?? Heartbeat file missing - main bot likely down")
                await set_maintenance("Heartbeat missing")
                await attempt_restart()
                continue

            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            ts = datetime.fromisoformat(hb.get("timestamp"))
            age = (datetime.utcnow() - ts).total_seconds()
            if age > HEARTBEAT_TIMEOUT:
                await send_alert(f"?? Heartbeat stale ({int(age)}s) - main bot likely down")
                await set_maintenance("Heartbeat stale")
                await attempt_restart()
            if not hb.get("signal_bus_ok", True):
                await send_alert("?? Signal bus reported unhealthy")
        except Exception:
            await send_alert("?? Monitor encountered an error reading heartbeat")

@client.event
async def on_ready():
    await send_alert("? Monitor bot online")
    client.loop.create_task(monitor_loop())

client.run(MONITOR_TOKEN)
