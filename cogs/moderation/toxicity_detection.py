import discord
from discord.ext import commands

class ToxicityDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Placeholder: In production, integrate with a real ML API or model
        self.toxic_words = ["hate", "idiot", "stupid", "kill", "racist"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        content = message.content.lower()
        if any(word in content for word in self.toxic_words):
            try:
                await message.delete()
            except Exception:
                pass
            staff_role = discord.utils.get(message.guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            await message.channel.send(f"⚠️ {message.author.mention}, your message was removed for toxic language. {staff_ping}")

async def setup(bot):
    await bot.add_cog(ToxicityDetection(bot))
