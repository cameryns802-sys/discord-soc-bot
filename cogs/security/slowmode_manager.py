# moved from cogs/slowmode_manager.py
from discord.ext import commands, tasks
from collections import deque

class SlowmodeManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_times = {}
        self.dynamic_slowmode.start()

    @tasks.loop(seconds=10)
    async def dynamic_slowmode(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

async def setup(bot):
    await bot.add_cog(SlowmodeManager(bot))
