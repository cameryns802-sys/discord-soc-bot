import discord
from discord.ext import commands
import random

SAMPLE_PRIVACY = [
    "We do not collect or store your personal data beyond what Discord provides.",
    "Your messages are not shared with third parties.",
    "You may request deletion of your data at any time.",
    "We use automated moderation to keep the community safe.",
    "All actions are logged for security and compliance purposes.",
    "By using this server, you consent to these privacy practices."
]

class UtilityPrivacyPolicyManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.privacy = SAMPLE_PRIVACY.copy()


    @commands.command()
    async def privacy(self, ctx):
        embed = discord.Embed(title="Server Privacy Policy", color=discord.Color.purple())
        for i, line in enumerate(self.privacy, 1):
            embed.add_field(name=f"Policy {i}", value=line, inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setprivacy(self, ctx, *, policy: str):
        self.privacy = [p.strip() for p in policy.split(';') if p.strip()]
        embed = discord.Embed(description="Privacy policy updated.", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    async def privacyaccept(self, ctx):
        embed = discord.Embed(description=f"{ctx.author.mention}, by using this server you agree to the privacy policy. Use !privacy to view it.", color=discord.Color.purple())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityPrivacyPolicyManager(bot))
