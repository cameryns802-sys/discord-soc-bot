import discord
from discord.ext import commands
from discord import app_commands

class WelcomeBanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        banner_url = "https://example.com/welcome.png"  # Replace with your image URL
        embed = discord.Embed(title="Welcome to the server!", color=discord.Color.gold())
        embed.set_image(url=banner_url)
        await member.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeBanner(bot))
