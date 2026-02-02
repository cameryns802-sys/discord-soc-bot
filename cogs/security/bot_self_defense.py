import discord
from discord.ext import commands

class BotSelfDefense(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id == self.bot.user.id:
            # Bot was kicked or banned
            # In production, notify owner via external means if possible
            print("[ALERT] Bot was removed from a server!")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"[ALERT] Bot was removed from guild: {guild.name}")

async def setup(bot):
    await bot.add_cog(BotSelfDefense(bot))
