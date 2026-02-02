import discord
from discord.ext import commands, tasks
import datetime

class ComplianceReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remind_compliance.start()

    @tasks.loop(hours=168)  # Once a week
    async def remind_compliance(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue
                try:
                    await member.send("Reminder: Please review the server rules, TOS, and privacy policy to stay compliant.")
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(ComplianceReminder(bot))
