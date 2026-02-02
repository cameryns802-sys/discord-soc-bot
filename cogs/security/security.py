# moved from cogs/security.py
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class SecurityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(SecurityCog(bot))
