import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class ConsentAuditTrail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audit_trail = []

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending and not after.pending:
            self.audit_trail.append({
                "user": after.id,
                "timestamp": datetime.get_now_pst().isoformat(),
                "event": "Accepted server rules"
            })

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def consentaudit(self, ctx):
        """Show the consent audit trail."""
        if not self.audit_trail:
            await ctx.send("No consent events recorded yet.")
            return
        msg = "Consent Audit Trail:\n"
        for entry in self.audit_trail[-10:]:
            user = self.bot.get_user(entry["user"]) or entry["user"]
            msg += f"User: {user}, Event: {entry['event']}, Time: {entry['timestamp']}\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(ConsentAuditTrail(bot))
