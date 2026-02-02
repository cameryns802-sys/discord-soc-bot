# moved from cogs/alerts.py
from discord.ext import commands

class AlertCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(AlertCog(bot))
