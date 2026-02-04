import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class IncidentTicketing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = []


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def openticket(self, ctx, user: discord.Member, *, issue):
        ticket = {
            "user": user.id,
            "issue": issue,
            "opened": datetime.get_now_pst().isoformat(),
            "status": "open"
        }
        self.tickets.append(ticket)
        embed = discord.Embed(title="Incident Ticket Opened", color=discord.Color.orange())
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Issue", value=issue, inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def closeticket(self, ctx, user: discord.Member):
        for ticket in self.tickets:
            if ticket["user"] == user.id and ticket["status"] == "open":
                ticket["status"] = "closed"
                ticket["closed"] = datetime.get_now_pst().isoformat()
                embed = discord.Embed(title="Ticket Closed", description=f"Ticket for {user.mention} closed.", color=discord.Color.green())
                await ctx.send(embed=embed)
                return
        embed = discord.Embed(description="No open ticket found for that user.", color=discord.Color.red())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IncidentTicketing(bot))
