import discord
from discord.ext import commands
import random

DEFAULT_RULES = [
    "Be respectful to all members.",
    "No spamming or flooding the chat.",
    "No hate speech, harassment, or discrimination.",
    "No NSFW or inappropriate content.",
    "No advertising or self-promotion without permission.",
    "Follow Discord's Terms of Service.",
    "Protect your personal information and privacy.",
    "Report suspicious or harmful behavior to staff."
]

class ToSGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules = DEFAULT_RULES.copy()
        self.tos = self.generate_tos()

    def generate_tos(self):
        tos = "Server Terms of Service and Rules:\n\n"
        for i, rule in enumerate(self.rules, 1):
            tos += f"{i}. {rule}\n"
        tos += "\nBy using this server, you agree to follow these rules and Discord's Terms of Service."
        return tos


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def generaterules(self, ctx):
        """Generate and display the server rules."""
        self.rules = random.sample(DEFAULT_RULES, len(DEFAULT_RULES))
        self.tos = self.generate_tos()
        embed = discord.Embed(title="Generated Server Rules", color=discord.Color.blue())
        for i, rule in enumerate(self.rules, 1):
            embed.add_field(name=f"Rule {i}", value=rule, inline=False)
        await ctx.send(embed=embed)




    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removerule(self, ctx, *, rule: str):
        if rule in self.rules:
            self.rules.remove(rule)
            self.tos = self.generate_tos()
            embed = discord.Embed(description=f"Rule removed: {rule}", color=discord.Color.orange())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="Rule not found.", color=discord.Color.red())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ToSGenerator(bot))
