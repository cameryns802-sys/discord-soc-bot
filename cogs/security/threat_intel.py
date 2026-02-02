# moved from cogs/threat_intel.py
from discord.ext import commands

class ThreatIntel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(ThreatIntel(bot))
