import discord
from discord.ext import commands

class ClosedLoopFeedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.false_positives = 0
        self.false_negatives = 0

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reportfp(self, ctx):
        self.false_positives += 1
        await ctx.send(f"False positive reported. Total: {self.false_positives}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reportfn(self, ctx):
        self.false_negatives += 1
        await ctx.send(f"False negative reported. Total: {self.false_negatives}")

async def setup(bot):
    await bot.add_cog(ClosedLoopFeedback(bot))
