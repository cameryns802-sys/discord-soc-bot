import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class EvidenceCollector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.incident_log = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logincident(self, ctx, user: discord.Member, *, reason):
        entry = {
            "user": user.id,
            "reason": reason,
            "timestamp": datetime.get_now_pst().isoformat()
        }
        self.incident_log.append(entry)
        await ctx.send(f"Incident logged for {user.mention}: {reason}")

async def setup(bot):
    await bot.add_cog(EvidenceCollector(bot))
