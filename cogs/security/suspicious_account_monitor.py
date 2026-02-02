import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

SUSPICIOUS_ACCOUNT_AGE_DAYS = 3  # Flag accounts newer than this

class SuspiciousAccountMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        now = datetime.now(timezone.utc)
        account_age = (now - member.created_at).days
        suspicious = False
        reasons = []
        if account_age < SUSPICIOUS_ACCOUNT_AGE_DAYS:
            suspicious = True
            reasons.append(f"Account age: {account_age} days")
        if member.avatar is None or member.default_avatar == member.avatar:
            suspicious = True
            reasons.append("Default avatar")
        # Add more heuristics as needed
        if suspicious:
            staff_role = discord.utils.get(member.guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            reason_str = ", ".join(reasons)
            await member.guild.system_channel.send(
                f"🚨 Suspicious account joined: {member.mention} ({member})\nReason: {reason_str}\n{staff_ping}"
            )

async def setup(bot):
    await bot.add_cog(SuspiciousAccountMonitor(bot))
