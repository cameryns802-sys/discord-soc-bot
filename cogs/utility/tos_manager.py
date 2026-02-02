import discord
from discord.ext import commands
import random

SAMPLE_TOS = [
    "You must be at least 13 years old to use this server.",
    "Do not share personal information of yourself or others.",
    "Respect all staff and follow their instructions.",
    "No illegal activities or discussions.",
    "No impersonation of other users or staff.",
    "All content must be safe for work.",
    "No excessive tagging or DMing members without consent.",
    "Use channels for their intended purposes only.",
    "Violation of these rules may result in a ban."
]

class ToSManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tos = SAMPLE_TOS.copy()


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def randomtos(self, ctx):
        tos = random.sample(self.tos, len(self.tos))
        embed = discord.Embed(title="Randomized Terms of Service and Rules", color=discord.Color.blue())
        for i, rule in enumerate(tos, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    async def tos(self, ctx):
        embed = discord.Embed(title="Current Terms of Service and Rules", color=discord.Color.green())
        for i, rule in enumerate(self.tos, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def settos(self, ctx, *, rules: str):
        self.tos = [r.strip() for r in rules.split(';') if r.strip()]
        embed = discord.Embed(description="ToS and rules updated.", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    async def tosaccept(self, ctx):
        embed = discord.Embed(description=f"{ctx.author.mention}, by using this server you agree to the Terms of Service and rules. Use !tos to view them.", color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ToSManager(bot))
