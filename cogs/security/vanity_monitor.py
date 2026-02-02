# moved from cogs/vanity_monitor.py
from discord.ext import commands

class VanityMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vanity_cache = {}

async def setup(bot):
    await bot.add_cog(VanityMonitor(bot))
