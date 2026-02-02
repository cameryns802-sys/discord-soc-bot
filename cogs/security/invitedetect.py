# moved from cogs/invitedetect.py
from discord.ext import commands

class InviteDetectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(InviteDetectionCog(bot))
