"""Case Peer Review System - Second-approver workflow for high-impact actions"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from cogs.core.pst_timezone import get_now_pst

class CasePeerReview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/peer_review_cases.json"
        self.data = {"requests": {}, "counter": 0}
        self._load_data()

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

    def _create_request(self, guild_id: int, user_id: int, action: str, target_id: int, reason: str, extra: dict):
        self.data["counter"] += 1
        rid = str(self.data["counter"])
        self.data["requests"][rid] = {
            "id": rid,
            "guild_id": guild_id,
            "requested_by": user_id,
            "action": action,
            "target_id": target_id,
            "reason": reason,
            "extra": extra,
            "status": "pending",
            "created_at": get_now_pst().isoformat()
        }
        self._save_data()
        return rid

    async def _execute_action(self, guild: discord.Guild, request: dict):
        action = request["action"]
        target_id = request["target_id"]
        reason = request.get("reason")
        member = guild.get_member(target_id)

        if action == "ban":
            await guild.ban(discord.Object(id=target_id), reason=reason, delete_message_days=request["extra"].get("delete_days", 0))
        elif action == "kick" and member:
            await member.kick(reason=reason)
        elif action == "timeout" and member:
            minutes = int(request["extra"].get("minutes", 10))
            await member.timeout(timedelta(minutes=minutes), reason=reason)
        elif action == "role_remove" and member:
            role_id = request["extra"].get("role_id")
            role = guild.get_role(role_id) if role_id else None
            if role:
                await member.remove_roles(role, reason=reason)

    @app_commands.command(name="peerreview_request", description="Request peer review for high-impact action")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def peerreview_request(self, interaction: discord.Interaction, action: str, target: discord.Member, reason: str, timeout_minutes: int = 10, role: discord.Role = None, delete_message_days: int = 0):
        action = action.lower()
        if action not in ["ban", "kick", "timeout", "role_remove"]:
            await interaction.response.send_message("? Action must be ban, kick, timeout, role_remove", ephemeral=True)
            return
        extra = {"minutes": timeout_minutes, "role_id": role.id if role else None, "delete_days": delete_message_days}
        rid = self._create_request(interaction.guild.id, interaction.user.id, action, target.id, reason, extra)
        await interaction.response.send_message(f"?? Peer review request #{rid} created for {target.mention}")

    @app_commands.command(name="peerreview_approve", description="Approve peer review request")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def peerreview_approve(self, interaction: discord.Interaction, request_id: str):
        request = self.data["requests"].get(request_id)
        if not request:
            await interaction.response.send_message("? Request not found", ephemeral=True)
            return
        if request["requested_by"] == interaction.user.id:
            await interaction.response.send_message("? A different moderator must approve", ephemeral=True)
            return
        if request["status"] != "pending":
            await interaction.response.send_message("? Request is not pending", ephemeral=True)
            return

        request["status"] = "approved"
        request["approved_by"] = interaction.user.id
        request["approved_at"] = get_now_pst().isoformat()
        self._save_data()

        try:
            await self._execute_action(interaction.guild, request)
            request["status"] = "executed"
            request["executed_at"] = get_now_pst().isoformat()
            self._save_data()
            await interaction.response.send_message(f"? Request {request_id} approved and executed")
        except Exception as e:
            request["status"] = "execution_failed"
            request["error"] = str(e)
            self._save_data()
            await interaction.response.send_message(f"?? Approved but execution failed: {e}")

    @app_commands.command(name="peerreview_deny", description="Deny peer review request")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def peerreview_deny(self, interaction: discord.Interaction, request_id: str, reason: str = "Denied"):
        request = self.data["requests"].get(request_id)
        if not request:
            await interaction.response.send_message("? Request not found", ephemeral=True)
            return
        request["status"] = "denied"
        request["denied_by"] = interaction.user.id
        request["denied_at"] = get_now_pst().isoformat()
        request["deny_reason"] = reason
        self._save_data()
        await interaction.response.send_message(f"?? Request {request_id} denied: {reason}")

    @app_commands.command(name="peerreview_list", description="List peer review requests")
    async def peerreview_list(self, interaction: discord.Interaction, status: str = "pending"):
        items = [r for r in self.data["requests"].values() if r.get("status") == status]
        if not items:
            await interaction.response.send_message("?? No requests found", ephemeral=True)
            return
        embed = discord.Embed(title="?? Peer Review Requests", color=discord.Color.orange())
        for req in items[-10:]:
            embed.add_field(
                name=f"#{req['id']} - {req['action']}",
                value=f"Target: <@{req['target_id']}> | Status: {req['status']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="peerreview_view", description="View peer review request")
    async def peerreview_view(self, interaction: discord.Interaction, request_id: str):
        req = self.data["requests"].get(request_id)
        if not req:
            await interaction.response.send_message("? Request not found", ephemeral=True)
            return
        embed = discord.Embed(title=f"Peer Review #{request_id}", color=discord.Color.blue())
        embed.add_field(name="Action", value=req["action"], inline=True)
        embed.add_field(name="Target", value=f"<@{req['target_id']}>", inline=True)
        embed.add_field(name="Status", value=req["status"], inline=True)
        embed.add_field(name="Reason", value=req.get("reason"), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CasePeerReview(bot))
