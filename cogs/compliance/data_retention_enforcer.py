import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class DataRetentionEnforcer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.retention_days = 30
        self.deletion_requests = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def retention(self, ctx, days: int = None):
        if days:
            self.retention_days = days
            await ctx.send(f"Data retention policy set to {days} days.")
        else:
            await ctx.send(f"Current data retention policy: {self.retention_days} days.")

    @commands.command()
    async def requestdeletion(self, ctx):
        self.deletion_requests.append({"user": ctx.author.id, "timestamp": datetime.get_now_pst().isoformat()})
        await ctx.send("Your data deletion request has been recorded.")

async def setup(bot):
    await bot.add_cog(DataRetentionEnforcer(bot))
