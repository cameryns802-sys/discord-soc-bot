import discord
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType

DANGEROUS_PERMS = [
    "administrator",
    "manage_guild",
    "ban_members",
    "kick_members",
    "manage_roles",
    "manage_channels"
]

class PermissionAudit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def emit_unauthorized_access_signal(self, role_name: str, perms: list):
        """Emit unauthorized access signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.UNAUTHORIZED_ACCESS,
            severity='high',
            source='permission_audit',
            data={'role': role_name, 'dangerous_perms': perms},
            confidence=0.99,
            dedup_key=f'permission:{role_name}'
        ))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def perm_audit(self, ctx):
        risky_roles = []
        for role in ctx.guild.roles:
            dangerous = []
            for perm in DANGEROUS_PERMS:
                if getattr(role.permissions, perm, False):
                    dangerous.append(perm)
            if dangerous:
                risky_roles.append(role.name)
                await self.emit_unauthorized_access_signal(role.name, dangerous)
        if risky_roles:
            await ctx.send(f"⚠️ Risky roles: {', '.join(risky_roles)}")
        else:
            await ctx.send("No risky roles found.")

async def setup(bot):
    await bot.add_cog(PermissionAudit(bot))
