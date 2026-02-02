import discord
from discord.ext import commands
import time

# Simple heuristic/ML placeholder for spam/raid detection
class SpamRaidDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {}
        self.spam_threshold = 5  # messages
        self.time_window = 10    # seconds

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        now = time.time()
        user_id = message.author.id
        times = self.user_message_times.get(user_id, [])
        times = [t for t in times if now - t < self.time_window]
        times.append(now)
        self.user_message_times[user_id] = times
        if len(times) > self.spam_threshold:
            try:
                await message.delete()
            except Exception:
                pass
            staff_role = discord.utils.get(message.guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            await message.channel.send(f"🚨 {message.author.mention} flagged for spam/raid. {staff_ping}")
            self.user_message_times[user_id] = []

async def setup(bot):
    await bot.add_cog(SpamRaidDetector(bot))
