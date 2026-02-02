import discord
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class RoleChangeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_roles = {}
    
    async def emit_unauthorized_access_signal(self, user: str, changes: str, severity: str = "high"):
        """Emit unauthorized access signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.UNAUTHORIZED_ACCESS,
            severity=severity,
            source='role_change_monitor',
            data={'user': user, 'changes': changes},
            confidence=0.95,
            dedup_key=f'role_change:{user}'
        ))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            removed = set(before.roles) - set(after.roles)
            added = set(after.roles) - set(before.roles)
            change_str = f"removed:{[r.name for r in removed]}, added:{[r.name for r in added]}"
            
            if len(removed) > 3 or len(added) > 3:
                await self.emit_unauthorized_access_signal(str(after), change_str, "high")
                await self.alert_staff(after.guild, f"Mass role change for {after.mention}")
            elif len(removed) > 0 or len(added) > 0:
                await self.emit_unauthorized_access_signal(str(after), change_str, "medium")

    async def alert_staff(self, guild, message):
        staff_role = discord.utils.get(guild.roles, name="Staff")
        staff_ping = staff_role.mention if staff_role else "@here"
        if guild.system_channel:
            await guild.system_channel.send(f"🚨 {message}\n{staff_ping}")

async def setup(bot):
    await bot.add_cog(RoleChangeMonitor(bot))
