import discord
from discord.ext import commands
import aiohttp

THREAT_FEED_URL = "https://example.com/threat-feed.txt"  # Replace with real feed

class ThreatIntelFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blocked_domains = set()

    async def cog_load(self):
        await self.update_feed()

    async def update_feed(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(THREAT_FEED_URL) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    self.blocked_domains = set(text.splitlines())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for domain in self.blocked_domains:
            if domain in message.content:
                await message.delete()
                await message.channel.send(f"⚠️ Blocked threat domain detected: {domain}")
                break

async def setup(bot):
    await bot.add_cog(ThreatIntelFeed(bot))
