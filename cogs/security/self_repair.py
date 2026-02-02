# moved from cogs/self_repair.py
from discord.ext import commands, tasks

class SelfRepair(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(SelfRepair(bot))
