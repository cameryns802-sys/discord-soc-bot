# moved from cogs/antinuke.py
from discord.ext import commands
from datetime import datetime, timedelta
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class AntiNukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nuke_attempts = {}
    
    async def emit_threat_signal(self, reason: str, severity: str = "high"):
        """Emit threat detected signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity=severity,
            source='antinuke',
            data={'reason': reason},
            confidence=0.95,
            dedup_key=f'antinuke:{reason}'
        ))
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Detect mass channel deletion"""
        await self.emit_threat_signal(f"channel_deleted: {channel.name}", "high")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Detect mass kicks/bans"""
        await self.emit_threat_signal(f"member_removed: {member.name}", "high")

async def setup(bot):
    await bot.add_cog(AntiNukeCog(bot))
