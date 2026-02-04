import discord
from discord.ext import commands, tasks
import datetime

class ServerHealthCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_health.start()

    @tasks.loop(minutes=30)
    async def check_health(self):
        # Disabled automatic health checks to prevent spam
        return

async def setup(bot):
    await bot.add_cog(ServerHealthCheck(bot))
