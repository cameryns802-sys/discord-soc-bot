import discord
from discord.ext import commands
import random

SUGGESTIONS = []

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def suggest(self, ctx, *, suggestion: str):
        SUGGESTIONS.append({"user": ctx.author.id, "suggestion": suggestion})
        embed = discord.Embed(description="Thank you for your suggestion!", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def viewsuggestions(self, ctx):
        if not SUGGESTIONS:
            embed = discord.Embed(description="No suggestions yet.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Suggestions", color=discord.Color.blue())
        for s in SUGGESTIONS[-10:]:
            user = self.bot.get_user(s["user"]) or s["user"]
            embed.add_field(name=str(user), value=s['suggestion'], inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
