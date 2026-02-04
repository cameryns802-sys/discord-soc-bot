import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class StaffAssignment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assignments = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def assignstaff(self, ctx, user: discord.Member):
        self.assignments.append({"user": user.id, "timestamp": datetime.get_now_pst().isoformat()})
        await ctx.send(f"{user.mention} assigned to incident.")

    @commands.command()
    async def myassignments(self, ctx):
        user_assignments = [a for a in self.assignments if a["user"] == ctx.author.id]
        if not user_assignments:
            await ctx.send("You have no assignments.")
            return
        msg = "Your assignments:\n"
        for a in user_assignments[-5:]:
            msg += f"- Assigned at {a['timestamp']}\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(StaffAssignment(bot))
