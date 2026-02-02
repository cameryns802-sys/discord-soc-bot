import discord
from discord.ext import commands
import re
from cogs.core.signal_bus import signal_bus, Signal, SignalType

# Example list of known phishing domains (expand with real data or use a threat feed)
PHISHING_DOMAINS = [
    "discord-giveaway.com",
    "free-nitro.com",
    "nitro-discord.com",
    "discord-airdrop.com",
    "gift-discord.com"
]

PHISHING_REGEX = re.compile(r"https?://([\w.-]+)")

class AntiPhishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def emit_threat_signal(self, url: str):
        """Emit threat detected signal for phishing"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='critical',
            source='anti_phishing',
            data={'phishing_url': url},
            confidence=0.98,
            dedup_key=f'phishing:{url}'
        ))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        urls = PHISHING_REGEX.findall(message.content)
        for url in urls:
            for domain in PHISHING_DOMAINS:
                if domain in url:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.emit_threat_signal(url)
                    await message.channel.send(f"⚠️ {message.author.mention}, phishing link detected and removed.")
                    return

async def setup(bot):
    await bot.add_cog(AntiPhishing(bot))
