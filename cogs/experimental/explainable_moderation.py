"""
Explainable Moderation System: Transparent mod actions with reasoning, audit trails, and policy references.
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import hashlib
from cogs.core.pst_timezone import get_now_pst

class ExplainableModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "./data/moderation"
        self.audit_file = f"{self.data_dir}/audit_trail.json"
        os.makedirs(self.data_dir, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not os.path.exists(self.audit_file):
            with open(self.audit_file, 'w') as f:
                json.dump({"audit_log": [], "action_count": 0}, f, indent=2)

    def _generate_audit_id(self):
        timestamp = get_now_pst().isoformat()
        hash_obj = hashlib.sha256(timestamp.encode())
        return f"AUDIT-{hash_obj.hexdigest()[:12].upper()}"

    def _log_action(self, guild, action_type, target, actor, reason):
        audit_id = self._generate_audit_id()
        log_entry = {
            "audit_id": audit_id,
            "timestamp": get_now_pst().isoformat(),
            "action_type": action_type,
            "actor_id": actor.id,
            "actor_name": str(actor),
            "target_id": target.id,
            "target_name": str(target),
            "reason": reason,
            "guild_id": guild.id,
            "status": "LOGGED"
        }
        
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        data["audit_log"].append(log_entry)
        data["action_count"] += 1
        with open(self.audit_file, 'w') as f:
            json.dump(data, f, indent=2)
        return audit_id

    @app_commands.command(name="warn_with_explanation", description="Issue warning with full explanation")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_with_explanation(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if user == interaction.user:
            await interaction.response.send_message("❌ Cannot warn yourself", ephemeral=True)
            return
        audit_id = self._log_action(interaction.guild, "WARN", user, interaction.user, reason)
        try:
            await user.send(f"⚠️ You received a warning: {reason}")
        except discord.Forbidden:
            pass
        embed = discord.Embed(title=f"⚠️ Warning Issued - {audit_id}", description=f"**User:** {user.mention}\n**Reason:** {reason}", color=discord.Color.orange(), timestamp=get_now_pst())
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"Audit ID: {audit_id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute_with_explanation", description="Mute user with explanation")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute_with_explanation(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        audit_id = self._log_action(interaction.guild, "MUTE", user, interaction.user, reason)
        try:
            await user.send(f"🔇 You have been muted: {reason}")
        except discord.Forbidden:
            pass
        embed = discord.Embed(title=f"🔇 User Muted - {audit_id}", description=f"**User:** {user.mention}\n**Reason:** {reason}", color=discord.Color.yellow(), timestamp=get_now_pst())
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"Audit ID: {audit_id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban_with_explanation", description="Ban user with explanation")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_with_explanation(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        audit_id = self._log_action(interaction.guild, "BAN", user, interaction.user, reason)
        try:
            await user.send(f"🔨 You have been banned: {reason}")
        except discord.Forbidden:
            pass
        await interaction.guild.ban(user, reason=reason)
        embed = discord.Embed(title=f"🔨 User Banned - {audit_id}", description=f"**User:** {user.mention}\n**Reason:** {reason}", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"Audit ID: {audit_id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="view_audit_trail", description="View moderation audit trail")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def view_audit_trail(self, interaction: discord.Interaction):
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        if not data["audit_log"]:
            await interaction.response.send_message("No audit logs found.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Audit Trail", color=discord.Color.blue(), timestamp=get_now_pst())
        recent = data["audit_log"][-10:]
        for log in recent:
            embed.add_field(name=f"{log['action_type']} - {log['audit_id']}", value=f"Target: {log['target_name']}\nReason: {log['reason']}", inline=False)
        embed.add_field(name="Total", value=str(data["action_count"]), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="export_audit_for_appeal", description="Export audit for appeal")
    async def export_audit_for_appeal(self, interaction: discord.Interaction, audit_id: str):
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        entry = next((log for log in data["audit_log"] if log["audit_id"] == audit_id), None)
        if not entry:
            await interaction.response.send_message(f"Audit ID {audit_id} not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"🔍 Audit - {audit_id}", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="Action", value=entry["action_type"], inline=True)
        embed.add_field(name="Target", value=entry["target_name"], inline=True)
        embed.add_field(name="Moderator", value=entry["actor_name"], inline=True)
        embed.add_field(name="Reason", value=entry["reason"], inline=False)
        embed.add_field(name="Timestamp", value=entry["timestamp"], inline=True)
        embed.set_footer(text=f"Audit ID: {audit_id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mod_consistency_report", description="Moderator consistency report")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def mod_consistency_report(self, interaction: discord.Interaction):
        with open(self.audit_file, 'r') as f:
            data = json.load(f)
        mods = {}
        for log in data["audit_log"]:
            actor = log["actor_name"]
            if actor not in mods:
                mods[actor] = {"total": 0, "WARN": 0, "MUTE": 0, "BAN": 0}
            mods[actor]["total"] += 1
            mods[actor][log["action_type"]] = mods[actor].get(log["action_type"], 0) + 1
        embed = discord.Embed(title="📊 Mod Report", color=discord.Color.blue(), timestamp=get_now_pst())
        for mod, stats in mods.items():
            embed.add_field(name=mod, value=f"Total: {stats['total']} | W:{stats['WARN']} M:{stats['MUTE']} B:{stats['BAN']}", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ExplainableModerationCog(bot))
