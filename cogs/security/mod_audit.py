# moved from cogs/mod_audit.py
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class AuditLogMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(AuditLogMonitorCog(bot))
