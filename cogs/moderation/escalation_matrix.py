import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class EscalationMatrix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.incidents = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def escalate(self, ctx, user: discord.Member, severity: int):
        if severity >= 3:
            # Escalate to admins
            role = discord.utils.get(ctx.guild.roles, name="Admin")
        elif severity == 2:
            role = discord.utils.get(ctx.guild.roles, name="Moderator")
        else:
            role = discord.utils.get(ctx.guild.roles, name="Staff")
        if role:
            await ctx.send(f"Incident for {user.mention} escalated to {role.mention} (severity {severity})")
        else:
            await ctx.send("No appropriate role found for escalation.")
        self.incidents.append({"user": user.id, "severity": severity, "timestamp": datetime.get_now_pst().isoformat()})

async def setup(bot):
    await bot.add_cog(EscalationMatrix(bot))
