import discord
from discord.ext import commands, tasks
import datetime

class ComplianceReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remind_compliance.start()

    @tasks.loop(hours=168)  # Once a week
    async def remind_compliance(self):
        # Disabled automatic reminders to prevent DM spam
        return

async def setup(bot):
    await bot.add_cog(ComplianceReminder(bot))
