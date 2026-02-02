import discord
from discord.ext import commands

LEGAL_DISCLAIMER = "This server is provided as-is. By participating, you agree to abide by all posted rules, Discord's Terms of Service, and applicable laws. The server staff is not responsible for user-generated content."

class LegalDisclaimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def disclaimer(self, ctx):
        await ctx.send(LEGAL_DISCLAIMER)

async def setup(bot):
    await bot.add_cog(LegalDisclaimer(bot))
