import discord
from discord.ext import commands

class DataExfiltrationDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_counts = {}
        self.threshold = 50  # Example: 50 messages in a short time

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = message.author.id
        self.user_message_counts[user_id] = self.user_message_counts.get(user_id, 0) + 1
        if self.user_message_counts[user_id] > self.threshold:
            await self.alert_staff(message.guild, f"Possible data exfiltration by {message.author.mention}")
            self.user_message_counts[user_id] = 0

    async def alert_staff(self, guild, message):
        staff_role = discord.utils.get(guild.roles, name="Staff")
        staff_ping = staff_role.mention if staff_role else "@here"
        if guild and guild.system_channel:
            await guild.system_channel.send(f"🚨 {message}\n{staff_ping}")

async def setup(bot):
    await bot.add_cog(DataExfiltrationDetector(bot))
