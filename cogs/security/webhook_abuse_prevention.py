import discord
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class WebhookAbusePrevention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def emit_threat_signal(self, webhook_name: str, channel: str):
        """Emit threat detected signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='critical',
            source='webhook_abuse_prevention',
            data={'webhook': webhook_name, 'channel': channel},
            confidence=0.99,
            dedup_key=f'webhook_abuse:{webhook_name}'
        ))

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.user and not webhook.user.bot:
                await self.emit_threat_signal(webhook.name, str(channel))
                try:
                    await webhook.delete()
                except Exception:
                    pass
                await channel.send(f"🚨 Unauthorized webhook deleted: {webhook.name}")

async def setup(bot):
    await bot.add_cog(WebhookAbusePrevention(bot))
