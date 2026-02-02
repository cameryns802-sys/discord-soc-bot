import discord
from discord.ext import commands
from discord import app_commands

class WelcomeOnboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            embed = discord.Embed(title="Welcome!", color=discord.Color.gold())
            embed.add_field(name="Rules", value="Use /rules to view the server rules.", inline=False)
            embed.add_field(name="TOS", value="Use /tos to view the Terms of Service.", inline=False)
            embed.add_field(name="Privacy", value="Use /privacy to view the Privacy Policy.", inline=False)
            embed.add_field(name="Consent", value="Use /accept_rules to accept and gain full access.", inline=False)
            await member.send(embed=embed)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(WelcomeOnboarding(bot))
