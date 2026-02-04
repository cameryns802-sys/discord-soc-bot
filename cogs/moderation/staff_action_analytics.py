import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class StaffActionAnalytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_log = []

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.action_log.append({"action": "ban", "user": user.id, "guild": guild.id, "timestamp": datetime.get_now_pst().isoformat()})

    @commands.Cog.listener()
    async def on_member_kick(self, member):
        self.action_log.append({"action": "kick", "user": member.id, "guild": member.guild.id, "timestamp": datetime.get_now_pst().isoformat()})

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def staffstats(self, ctx):
        bans = sum(1 for a in self.action_log if a["action"] == "ban")
        kicks = sum(1 for a in self.action_log if a["action"] == "kick")
        await ctx.send(f"Staff actions: {bans} bans, {kicks} kicks.")

async def setup(bot):
    await bot.add_cog(StaffActionAnalytics(bot))
