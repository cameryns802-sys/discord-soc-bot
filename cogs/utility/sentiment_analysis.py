import discord
from discord.ext import commands, tasks
import random

class UtilitySentimentAnalysis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sentiment_score = 0
        self.message_count = 0
        self.check_sentiment.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # Placeholder: In production, use NLP sentiment analysis
        # Here, randomly assign positive/negative for demo
        score = random.choice([-1, 1])
        self.sentiment_score += score
        self.message_count += 1

    @tasks.loop(hours=1)
    async def check_sentiment(self):
        if self.message_count == 0:
            return
        avg = self.sentiment_score / self.message_count
        for guild in self.bot.guilds:
            staff_role = discord.utils.get(guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            if guild.system_channel:
                embed = discord.Embed(title="Sentiment Report", color=discord.Color.purple())
                embed.add_field(name="Average Sentiment", value=f"{avg:.2f}", inline=True)
                embed.add_field(name="Messages Analyzed", value=str(self.message_count), inline=True)
                await guild.system_channel.send(f"{staff_ping}", embed=embed)
        self.sentiment_score = 0
        self.message_count = 0

async def setup(bot):
    await bot.add_cog(UtilitySentimentAnalysis(bot))
