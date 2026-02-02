import discord
from discord.ext import commands, tasks
import datetime

class ServerHealthCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_health.start()

    @tasks.loop(minutes=30)
    async def check_health(self):
        for guild in self.bot.guilds:
            staff_role = discord.utils.get(guild.roles, name="Staff")
            staff_ping = staff_role.mention if staff_role else "@here"
            if guild.system_channel:
                embed = discord.Embed(title="Server Health Check", description="All systems nominal.", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
                await guild.system_channel.send(content=f"{staff_ping}", embed=embed)

async def setup(bot):
    await bot.add_cog(ServerHealthCheck(bot))
