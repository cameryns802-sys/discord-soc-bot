import discord
from discord.ext import commands
import subprocess

class DependencySecurity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def checkdeps(self, ctx):
        """Check for dependency vulnerabilities."""
        try:
            result = subprocess.run(["pip", "list", "--outdated"], capture_output=True, text=True)
            await ctx.send(f"Outdated dependencies:\n{result.stdout}")
        except Exception as e:
            await ctx.send(f"Error checking dependencies: {e}")

async def setup(bot):
    await bot.add_cog(DependencySecurity(bot))
