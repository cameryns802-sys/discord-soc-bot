import discord
from discord.ext import commands

class AuditLogAnomalyDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        # Alert on mass bans (simple version)
        # In production, track ban frequency and alert if threshold exceeded
        await self.alert_staff(guild, f"Ban issued: {user}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.alert_staff(channel.guild, f"Channel deleted: {channel.name}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        # Alert if dangerous permissions are granted
        dangerous_perms = ["administrator", "manage_guild", "ban_members", "kick_members"]
        for perm in dangerous_perms:
            if getattr(before.permissions, perm) is False and getattr(after.permissions, perm) is True:
                await self.alert_staff(after.guild, f"Role {after.name} granted dangerous permission: {perm}")

    async def alert_staff(self, guild, message):
        staff_role = discord.utils.get(guild.roles, name="Staff")
        staff_ping = staff_role.mention if staff_role else "@here"
        if guild.system_channel:
            await guild.system_channel.send(f"🚨 {message}\n{staff_ping}")

async def setup(bot):
    await bot.add_cog(AuditLogAnomalyDetector(bot))
