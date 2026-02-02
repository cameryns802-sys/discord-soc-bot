import discord
from discord.ext import commands

class DataLeakPrevention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sensitive_keywords = [
            'ssn', 'credit card', 'password', 'secret', 'api_key', 'token', 'private key', 'confidential'
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        content = message.content.lower()
        if any(keyword in content for keyword in self.sensitive_keywords):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            await message.channel.send(f"{message.author.mention}, sharing sensitive information is not allowed.", delete_after=10)

async def setup(bot):
    await bot.add_cog(DataLeakPrevention(bot))
