import discord
from discord.ext import commands, tasks
import importlib.metadata

class DependencySecurityCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_dependencies.start()

    @tasks.loop(hours=24)
    async def check_dependencies(self):
        # Disabled to prevent spam in system channels
        return

async def setup(bot):
    await bot.add_cog(DependencySecurityCheck(bot))
