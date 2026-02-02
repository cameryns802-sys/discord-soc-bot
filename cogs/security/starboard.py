# moved from cogs/starboard.py
from discord.ext import commands

class StarboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starred = set()

async def setup(bot):
    await bot.add_cog(StarboardCog(bot))
