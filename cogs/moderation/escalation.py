# moved from cogs/escalation.py
from discord.ext import commands
from collections import defaultdict

ESCALATION_THRESHOLD = 3  # Offenses before escalation

class EscalationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.offense_counts = defaultdict(int)

    async def escalate(self, member, reason):
        pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        pass

async def setup(bot):
    await bot.add_cog(EscalationCog(bot))
