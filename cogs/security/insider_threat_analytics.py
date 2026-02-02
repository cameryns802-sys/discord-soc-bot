import discord
from discord.ext import commands

class InsiderThreatAnalytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if any(role.permissions.administrator for role in after.roles):
            await self.alert_staff(after.guild, f"Admin role change for {after.mention}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if after.permissions.administrator and not before.permissions.administrator:
            await self.alert_staff(after.guild, f"Role {after.name} granted admin permissions")

    async def alert_staff(self, guild, message):
        staff_role = discord.utils.get(guild.roles, name="Staff")
        staff_ping = staff_role.mention if staff_role else "@here"
        if guild.system_channel:
            await guild.system_channel.send(f"🚨 {message}\n{staff_ping}")

async def setup(bot):
    await bot.add_cog(InsiderThreatAnalytics(bot))
