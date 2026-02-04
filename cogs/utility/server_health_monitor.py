import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class ServerHealthMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.health_checks = []


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def healthcheck(self, ctx):
        """Run a server health check."""
        now = datetime.get_now_pst().isoformat()
        online = sum(1 for m in ctx.guild.members if m.status == discord.Status.online)
        total = ctx.guild.member_count
        bots = sum(1 for m in ctx.guild.members if m.bot)
        embed = discord.Embed(title="Server Health Check", color=discord.Color.green(), timestamp=datetime.get_now_pst())
        embed.add_field(name="Total Members", value=str(total), inline=True)
        embed.add_field(name="Online Members", value=str(online), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        self.health_checks.append({"timestamp": now, "online": online, "total": total, "bots": bots})
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerHealthMonitor(bot))
