# moved from cogs/antialt.py
import discord
from discord.ext import commands
from datetime import datetime, timezone

MIN_ACCOUNT_AGE_DAYS = 7  # Minimum days old to join

class AntiAltCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        now = datetime.now(timezone.utc)
        account_age = (now - member.created_at).days
        if account_age < MIN_ACCOUNT_AGE_DAYS:
            try:
                await member.send(f"Your account is too new to join this server. Minimum age: {MIN_ACCOUNT_AGE_DAYS} days.")
            except Exception:
                pass
            await member.kick(reason=f"Account too new: {account_age} days old.")

async def setup(bot):
    await bot.add_cog(AntiAltCog(bot))
