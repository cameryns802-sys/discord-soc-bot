import discord
from discord.ext import commands
import random

CANARY_TOKENS = [
    "canary-secret-12345",
    "canary-password-abcde"
]

class CanaryTokenMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for token in CANARY_TOKENS:
            if token in message.content:
                await self.alert_staff(message.guild, f"Canary token accessed by {message.author.mention}")
                break

    async def alert_staff(self, guild, message):
        staff_role = discord.utils.get(guild.roles, name="Staff")
        staff_ping = staff_role.mention if staff_role else "@here"
        if guild and guild.system_channel:
            await guild.system_channel.send(f"🚨 {message}\n{staff_ping}")

async def setup(bot):
    await bot.add_cog(CanaryTokenMonitor(bot))
