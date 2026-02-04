"""Bot-of-Bots Health Monitor - Heartbeat for external monitor bot"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.signal_bus import signal_bus
from cogs.core.pst_timezone import get_now_pst

class BotOfBotsHealthMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.heartbeat_file = "data/heartbeat.json"
        self.heartbeat_task.start()

    @tasks.loop(seconds=30)
    async def heartbeat_task(self):
        data = {
            "timestamp": get_now_pst().isoformat(),
            "guilds": len(self.bot.guilds),
            "uptime_seconds": int((get_now_pst() - getattr(self.bot, "uptime", get_now_pst())).total_seconds()),
            "signal_bus_ok": True,
            "signal_stats": signal_bus.get_stats()
        }
        os.makedirs("data", exist_ok=True)
        with open(self.heartbeat_file, "w") as f:
            json.dump(data, f, indent=2)

    @app_commands.command(name="heartbeat_status", description="View heartbeat status")
    async def heartbeat_status(self, interaction: discord.Interaction):
        if not os.path.exists(self.heartbeat_file):
            await interaction.response.send_message("? Heartbeat not initialized", ephemeral=True)
            return
        with open(self.heartbeat_file, "r") as f:
            data = json.load(f)
        embed = discord.Embed(title="?? Heartbeat Status", color=discord.Color.green())
        embed.add_field(name="Last Beat", value=data.get("timestamp"), inline=False)
        embed.add_field(name="Guilds", value=str(data.get("guilds")), inline=True)
        embed.add_field(name="Uptime (s)", value=str(data.get("uptime_seconds")), inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BotOfBotsHealthMonitor(bot))
