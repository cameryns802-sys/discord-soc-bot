import discord
from discord.ext import commands

class Guardrails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules = ["No spam", "No NSFW", "No harassment"]

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_guardrail_rule(self, ctx, *, rule: str):
        self.rules.append(rule)
        await ctx.send(f"Rule added: {rule}")

    @commands.command()
    async def rules(self, ctx):
        msg = "Server Rules:\n" + "\n".join(f"- {r}" for r in self.rules)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Guardrails(bot))
