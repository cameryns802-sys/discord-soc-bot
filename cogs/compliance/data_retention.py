import discord
from discord.ext import commands
import datetime

RETENTION_DAYS = 30

class DataRetention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # This is a placeholder. Actual retention enforcement should be scheduled and use message timestamps.
        pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pruneold(self, ctx):
        now = datetime.datetime.utcnow()
        deleted = 0
        async for msg in ctx.channel.history(limit=1000):
            if (now - msg.created_at).days > RETENTION_DAYS:
                try:
                    await msg.delete()
                    deleted += 1
                except Exception:
                    pass
        await ctx.send(f"Pruned {deleted} messages older than {RETENTION_DAYS} days.")

async def setup(bot):
    await bot.add_cog(DataRetention(bot))
