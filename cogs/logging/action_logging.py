"""Action Logging System - comprehensive Discord server audit logging"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os
from typing import Optional, Dict, Any
from cogs.core.pst_timezone import get_now_pst

MODULES = {
    "messages": "Message create/edit/delete",
    "members": "Member join/leave/update",
    "moderation": "Bans, unbans, timeouts",
    "channels": "Channel create/update/delete",
    "roles": "Role create/update/delete",
    "server": "Server/guild updates",
    "voice": "Voice state changes",
    "invites": "Invite create/delete",
    "webhooks": "Webhook changes",
    "audit": "Audit log stream"
}

class ActionLoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/action_logging.json"
        self.data = {"guilds": {}}
        self.audit_cursor: Dict[str, int] = {}
        self._load_data()
        self.audit_stream.start()

    def cog_unload(self):
        self.audit_stream.cancel()

    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def _save_data(self):
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def _get_guild_cfg(self, guild_id: int) -> Dict[str, Any]:
        gkey = str(guild_id)
        if gkey not in self.data["guilds"]:
            self.data["guilds"][gkey] = {
                "enabled": True,
                "channel_id": None,
                "modules": {k: True for k in MODULES.keys()},
                "audit_last_id": None
            }
        return self.data["guilds"][gkey]

    def _is_enabled(self, guild_id: int, module: str) -> bool:
        cfg = self._get_guild_cfg(guild_id)
        return cfg.get("enabled", True) and cfg.get("modules", {}).get(module, True)

    def _get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        cfg = self._get_guild_cfg(guild.id)
        channel_id = cfg.get("channel_id")
        if not channel_id:
            env_channel = os.getenv("AUDIT_CHANNEL_ID", "0")
            try:
                channel_id = int(env_channel)
            except ValueError:
                channel_id = 0
        return guild.get_channel(channel_id) if channel_id else None

    async def _send_log(self, guild: discord.Guild, embed: discord.Embed, module: str):
        if not self._is_enabled(guild.id, module):
            return
        channel = self._get_log_channel(guild)
        if channel and channel.permissions_for(guild.me).send_messages:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    async def _get_audit_entry(self, guild: discord.Guild, action: discord.AuditLogAction, target_id: Optional[int] = None):
        if not guild.me.guild_permissions.view_audit_log:
            return None
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if target_id is None or (entry.target and entry.target.id == target_id):
                    if get_now_pst() - entry.created_at.replace(tzinfo=None) < timedelta(seconds=10):
                        return entry
        except Exception:
            return None
        return None

    @commands.command(name="logset")
    @commands.has_permissions(manage_guild=True)
    async def logset(self, ctx, channel: discord.TextChannel):
        cfg = self._get_guild_cfg(ctx.guild.id)
        cfg["channel_id"] = channel.id
        self._save_data()
        await ctx.send(f"? Action log channel set to {channel.mention}")

    @commands.command(name="logenable")
    @commands.has_permissions(manage_guild=True)
    async def logenable(self, ctx):
        cfg = self._get_guild_cfg(ctx.guild.id)
        cfg["enabled"] = True
        self._save_data()
        await ctx.send("? Action logging enabled")

    @commands.command(name="logdisable")
    @commands.has_permissions(manage_guild=True)
    async def logdisable(self, ctx):
        cfg = self._get_guild_cfg(ctx.guild.id)
        cfg["enabled"] = False
        self._save_data()
        await ctx.send("?? Action logging disabled")

    @commands.command(name="logmodule")
    @commands.has_permissions(manage_guild=True)
    async def logmodule(self, ctx, module: str, state: str):
        module = module.lower()
        state = state.lower()
        if module not in MODULES:
            await ctx.send(f"? Module must be one of: {', '.join(MODULES.keys())}")
            return
        if state not in ["on", "off"]:
            await ctx.send("? State must be on/off")
            return
        cfg = self._get_guild_cfg(ctx.guild.id)
        cfg["modules"][module] = (state == "on")
        self._save_data()
        await ctx.send(f"? Module {module} set to {state}")

    @commands.command(name="logstatus")
    @commands.has_permissions(manage_guild=True)
    async def logstatus(self, ctx):
        cfg = self._get_guild_cfg(ctx.guild.id)
        embed = discord.Embed(title="?? Action Logging Status", color=discord.Color.blue())
        embed.add_field(name="Enabled", value=str(cfg.get("enabled", True)), inline=True)
        channel = ctx.guild.get_channel(cfg.get("channel_id")) if cfg.get("channel_id") else None
        embed.add_field(name="Channel", value=channel.mention if channel else "Not set", inline=True)
        modules = cfg.get("modules", {})
        enabled = [m for m, v in modules.items() if v]
        disabled = [m for m, v in modules.items() if not v]
        embed.add_field(name="Enabled Modules", value="\n".join(enabled) if enabled else "None", inline=False)
        if disabled:
            embed.add_field(name="Disabled Modules", value="\n".join(disabled), inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return
        embed = discord.Embed(title="??? Message Deleted", color=discord.Color.orange(), timestamp=get_now_pst())
        embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        content = message.content or "<no text>"
        embed.add_field(name="Content", value=content[:1000], inline=False)
        if message.attachments:
            embed.add_field(name="Attachments", value="\n".join(a.filename for a in message.attachments), inline=False)
        await self._send_log(message.guild, embed, "messages")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or before.content == after.content:
            return
        embed = discord.Embed(title="?? Message Edited", color=discord.Color.gold(), timestamp=get_now_pst())
        embed.add_field(name="Author", value=f"{after.author} ({after.author.id})", inline=True)
        embed.add_field(name="Channel", value=after.channel.mention, inline=True)
        embed.add_field(name="Before", value=(before.content or "<no text>")[:700], inline=False)
        embed.add_field(name="After", value=(after.content or "<no text>")[:700], inline=False)
        await self._send_log(after.guild, embed, "messages")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title="? Member Joined", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        await self._send_log(member.guild, embed, "members")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(title="?? Member Left", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        await self._send_log(member.guild, embed, "members")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            embed = discord.Embed(title="?? Nickname Updated", color=discord.Color.blurple(), timestamp=get_now_pst())
            embed.add_field(name="User", value=f"{after} ({after.id})", inline=True)
            embed.add_field(name="Before", value=before.nick or "None", inline=True)
            embed.add_field(name="After", value=after.nick or "None", inline=True)
            await self._send_log(after.guild, embed, "members")

        before_roles = set(r.id for r in before.roles)
        after_roles = set(r.id for r in after.roles)
        if before_roles != after_roles:
            added = [after.guild.get_role(rid) for rid in after_roles - before_roles]
            removed = [after.guild.get_role(rid) for rid in before_roles - after_roles]
            embed = discord.Embed(title="?? Roles Updated", color=discord.Color.blue(), timestamp=get_now_pst())
            embed.add_field(name="User", value=f"{after} ({after.id})", inline=True)
            if added:
                embed.add_field(name="Added", value="\n".join(r.name for r in added if r), inline=False)
            if removed:
                embed.add_field(name="Removed", value="\n".join(r.name for r in removed if r), inline=False)
            await self._send_log(after.guild, embed, "roles")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        entry = await self._get_audit_entry(guild, discord.AuditLogAction.ban, user.id)
        embed = discord.Embed(title="? Member Banned", color=discord.Color.dark_red(), timestamp=get_now_pst())
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        if entry:
            embed.add_field(name="Moderator", value=f"{entry.user}", inline=True)
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason[:500], inline=False)
        await self._send_log(guild, embed, "moderation")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        entry = await self._get_audit_entry(guild, discord.AuditLogAction.unban, user.id)
        embed = discord.Embed(title="?? Member Unbanned", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        if entry:
            embed.add_field(name="Moderator", value=f"{entry.user}", inline=True)
        await self._send_log(guild, embed, "moderation")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        entry = await self._get_audit_entry(channel.guild, discord.AuditLogAction.channel_create)
        embed = discord.Embed(title="?? Channel Created", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="Channel", value=channel.name, inline=True)
        if entry:
            embed.add_field(name="By", value=f"{entry.user}", inline=True)
        await self._send_log(channel.guild, embed, "channels")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        entry = await self._get_audit_entry(channel.guild, discord.AuditLogAction.channel_delete)
        embed = discord.Embed(title="??? Channel Deleted", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="Channel", value=channel.name, inline=True)
        if entry:
            embed.add_field(name="By", value=f"{entry.user}", inline=True)
        await self._send_log(channel.guild, embed, "channels")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if before.name != after.name:
            entry = await self._get_audit_entry(after.guild, discord.AuditLogAction.channel_update)
            embed = discord.Embed(title="?? Channel Updated", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            if entry:
                embed.add_field(name="By", value=f"{entry.user}", inline=True)
            await self._send_log(after.guild, embed, "channels")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        entry = await self._get_audit_entry(role.guild, discord.AuditLogAction.role_create)
        embed = discord.Embed(title="? Role Created", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="Role", value=role.name, inline=True)
        if entry:
            embed.add_field(name="By", value=f"{entry.user}", inline=True)
        await self._send_log(role.guild, embed, "roles")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        entry = await self._get_audit_entry(role.guild, discord.AuditLogAction.role_delete)
        embed = discord.Embed(title="? Role Deleted", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="Role", value=role.name, inline=True)
        if entry:
            embed.add_field(name="By", value=f"{entry.user}", inline=True)
        await self._send_log(role.guild, embed, "roles")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if before.name != after.name:
            entry = await self._get_audit_entry(after.guild, discord.AuditLogAction.role_update)
            embed = discord.Embed(title="?? Role Updated", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            if entry:
                embed.add_field(name="By", value=f"{entry.user}", inline=True)
            await self._send_log(after.guild, embed, "roles")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name != after.name:
            embed = discord.Embed(title="??? Server Updated", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            await self._send_log(after, embed, "server")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return
        embed = discord.Embed(title="?? Voice State Updated", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="From", value=before.channel.mention if before.channel else "None", inline=True)
        embed.add_field(name="To", value=after.channel.mention if after.channel else "None", inline=True)
        await self._send_log(member.guild, embed, "voice")

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        embed = discord.Embed(title="?? Invite Created", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Channel", value=invite.channel.mention if invite.channel else "N/A", inline=True)
        await self._send_log(invite.guild, embed, "invites")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        embed = discord.Embed(title="??? Invite Deleted", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Channel", value=invite.channel.mention if invite.channel else "N/A", inline=True)
        await self._send_log(invite.guild, embed, "invites")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        entry = await self._get_audit_entry(channel.guild, discord.AuditLogAction.webhook_create)
        action = "created"
        if not entry:
            entry = await self._get_audit_entry(channel.guild, discord.AuditLogAction.webhook_update)
            action = "updated"
        if not entry:
            entry = await self._get_audit_entry(channel.guild, discord.AuditLogAction.webhook_delete)
            action = "deleted"
        if not entry:
            return
        embed = discord.Embed(title="?? Webhook Updated", color=discord.Color.purple(), timestamp=get_now_pst())
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="By", value=f"{entry.user}", inline=True)
        await self._send_log(channel.guild, embed, "webhooks")

    @tasks.loop(seconds=60.0)
    async def audit_stream(self):
        for guild in self.bot.guilds:
            cfg = self._get_guild_cfg(guild.id)
            if not self._is_enabled(guild.id, "audit"):
                continue
            if not guild.me.guild_permissions.view_audit_log:
                continue

            last_id = cfg.get("audit_last_id")
            try:
                async for entry in guild.audit_logs(limit=20):
                    if last_id and entry.id <= last_id:
                        break

                    embed = discord.Embed(
                        title="Audit Log Entry",
                        color=discord.Color.blue(),
                        timestamp=get_now_pst()
                    )
                    embed.add_field(name="Action", value=str(entry.action).replace("AuditLogAction.", ""), inline=True)
                    embed.add_field(name="User", value=f"{entry.user} ({entry.user.id})", inline=True)
                    if entry.target:
                        embed.add_field(name="Target", value=str(entry.target), inline=False)
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason[:500], inline=False)
                    await self._send_log(guild, embed, "audit")

                if guild.audit_logs is not None:
                    latest = [e async for e in guild.audit_logs(limit=1)]
                    if latest:
                        cfg["audit_last_id"] = latest[0].id
                        self._save_data()
            except Exception:
                continue

    @audit_stream.before_loop
    async def before_audit_stream(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ActionLoggingCog(bot))

