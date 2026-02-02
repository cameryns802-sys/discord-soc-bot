import discord
from discord.ext import commands
import random

WELCOME_CONFIG = {
    "channel_name": "welcome",
    "messages": [
        "Welcome to the server, {user}! Please read the rules and verify yourself.",
        "Hey {user}, glad to have you here! Check out #rules and #verify.",
        "Hi {user}! Make sure to review our ToS and privacy policy. Have fun!",
        "{user}, welcome aboard! If you have questions, ask a staff member."
    ]
}

class AdvancedWelcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = WELCOME_CONFIG.copy()


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwelcomechannel(self, ctx, channel: discord.TextChannel):
        self.config["channel_name"] = channel.name
        embed = discord.Embed(description=f"Welcome channel set to {channel.mention}", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addwelcomemsg(self, ctx, *, message: str):
        self.config["messages"].append(message)
        embed = discord.Embed(description="Welcome message added.", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removewelcomemsg(self, ctx, *, message: str):
        if message in self.config["messages"]:
            self.config["messages"].remove(message)
            embed = discord.Embed(description="Welcome message removed.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="Message not found in welcome messages.", color=discord.Color.red())
            await ctx.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name=self.config["channel_name"])
        if channel:
            msg = random.choice(self.config["messages"]).format(user=member.mention)
            embed = discord.Embed(description=msg, color=discord.Color.blue())
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedWelcome(bot))
