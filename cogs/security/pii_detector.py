import discord
from discord.ext import commands
import re

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
ADDRESS_REGEX = re.compile(r"\d+\s+([A-Za-z0-9]+\s?)+,?\s*[A-Za-z]+,?\s*[A-Za-z]{2,}")  # Simple heuristic

class PIIDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        found = []
        if EMAIL_REGEX.search(message.content):
            found.append("email address")
        if PHONE_REGEX.search(message.content):
            found.append("phone number")
        if ADDRESS_REGEX.search(message.content):
            found.append("address")
        if found:
            try:
                await message.delete()
            except Exception:
                pass
            staff_role = discord.utils.get(message.guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            await message.channel.send(f"⚠️ {message.author.mention}, your message was removed for containing: {', '.join(found)}. {staff_ping}")

async def setup(bot):
    await bot.add_cog(PIIDetector(bot))
