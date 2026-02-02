# moved from cogs/verification.py
from discord.ext import commands
from discord.ui import Button, View

VERIFIED_ROLE = "Member"
VERIFICATION_CHANNEL = "verify"

class VerificationView(View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
