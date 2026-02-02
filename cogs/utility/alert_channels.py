import discord
from discord.ext import commands

class AlertChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alert_channels = []


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addalertchannel(self, ctx, channel: discord.TextChannel):
        if channel.id not in self.alert_channels:
            self.alert_channels.append(channel.id)
            embed = discord.Embed(description=f"Alert channel {channel.mention} added.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="Channel already in alert list.", color=discord.Color.orange())
            await ctx.send(embed=embed)


    async def send_alert(self, message):
        for cid in self.alert_channels:
            channel = self.bot.get_channel(cid)
            if channel:
                embed = discord.Embed(description=message, color=discord.Color.red())
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AlertChannels(bot))
