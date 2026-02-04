"""Post-Mortem Workflow - Auto-create and collect incident post-mortems"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class PostMortemWorkflow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/post_mortems.json"
        self.incident_file = "data/incidents.json"
        self.kb_file = "data/incident_knowledge_base.json"
        self.data = {"postmortems": {}, "counter": 0, "config": {}}
        self._load_data()
        self.monitor_incidents.start()

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

    def _load_incidents(self):
        if os.path.exists(self.incident_file):
            try:
                with open(self.incident_file, "r") as f:
                    return json.load(f).get("incidents", {})
            except Exception:
                return {}
        return {}

    def _append_kb(self, entry: dict):
        data = {"entries": []}
        if os.path.exists(self.kb_file):
            try:
                with open(self.kb_file, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {"entries": []}
        data["entries"].append(entry)
        os.makedirs("data", exist_ok=True)
        with open(self.kb_file, "w") as f:
            json.dump(data, f, indent=2)

    def _get_config(self, guild_id: int) -> dict:
        gkey = str(guild_id)
        if gkey not in self.data["config"]:
            self.data["config"][gkey] = {"alert_channel_id": None}
        return self.data["config"][gkey]

    @tasks.loop(minutes=5)
    async def monitor_incidents(self):
        incidents = self._load_incidents()
        for inc_id, inc in incidents.items():
            if inc.get("status") != "closed":
                continue
            if inc_id in self.data["postmortems"]:
                continue
            self.data["counter"] += 1
            pm_id = str(self.data["counter"])
            self.data["postmortems"][inc_id] = {
                "id": pm_id,
                "incident_id": inc_id,
                "status": "pending",
                "created_at": get_now_pst().isoformat(),
                "created_by": inc.get("assigned_to") or inc.get("created_by"),
                "responders": [inc.get("assigned_to")] if inc.get("assigned_to") else [],
                "report": {}
            }
            self._save_data()
            await self._notify_guild(inc.get("created_by"), f"?? Post-mortem required for incident #{inc_id}")

    async def _notify_guild(self, user_id: int, message: str):
        for guild in self.bot.guilds:
            config = self._get_config(guild.id)
            channel = guild.get_channel(config.get("alert_channel_id")) if config.get("alert_channel_id") else guild.system_channel
            if channel and channel.permissions_for(guild.me).send_messages:
                await channel.send(message)
                return
        if user_id:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(message)
            except Exception:
                pass

    @app_commands.command(name="postmortem_submit", description="Submit post-mortem report")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def postmortem_submit(self, interaction: discord.Interaction, incident_id: str, summary: str, root_cause: str, impact: str, lessons: str, action_items: str):
        pm = self.data["postmortems"].get(incident_id)
        if not pm:
            await interaction.response.send_message("? Post-mortem not found for this incident", ephemeral=True)
            return
        pm["report"] = {
            "summary": summary,
            "root_cause": root_cause,
            "impact": impact,
            "lessons": lessons,
            "action_items": action_items
        }
        pm["status"] = "submitted"
        pm["submitted_at"] = get_now_pst().isoformat()
        pm["submitted_by"] = interaction.user.id
        self._save_data()

        self._append_kb({
            "incident_id": incident_id,
            "summary": summary,
            "root_cause": root_cause,
            "impact": impact,
            "lessons": lessons,
            "action_items": action_items,
            "submitted_at": pm["submitted_at"],
            "submitted_by": interaction.user.id
        })

        await interaction.response.send_message(f"? Post-mortem submitted for incident #{incident_id}")

    @app_commands.command(name="postmortem_view", description="View post-mortem report")
    async def postmortem_view(self, interaction: discord.Interaction, incident_id: str):
        pm = self.data["postmortems"].get(incident_id)
        if not pm:
            await interaction.response.send_message("? Post-mortem not found", ephemeral=True)
            return
        report = pm.get("report", {})
        embed = discord.Embed(title=f"Post-Mortem #{incident_id}", color=discord.Color.blue())
        embed.add_field(name="Status", value=pm.get("status"), inline=True)
        embed.add_field(name="Summary", value=report.get("summary", "N/A"), inline=False)
        embed.add_field(name="Root Cause", value=report.get("root_cause", "N/A"), inline=False)
        embed.add_field(name="Impact", value=report.get("impact", "N/A"), inline=False)
        embed.add_field(name="Lessons", value=report.get("lessons", "N/A"), inline=False)
        embed.add_field(name="Action Items", value=report.get("action_items", "N/A"), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="postmortem_list", description="List pending post-mortems")
    async def postmortem_list(self, interaction: discord.Interaction):
        pending = [pm for pm in self.data["postmortems"].values() if pm.get("status") != "submitted"]
        if not pending:
            await interaction.response.send_message("?? No pending post-mortems", ephemeral=True)
            return
        embed = discord.Embed(title="?? Pending Post-Mortems", color=discord.Color.orange())
        for pm in pending[-10:]:
            embed.add_field(name=f"Incident {pm['incident_id']}", value=f"Status: {pm['status']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="postmortem_config", description="Configure post-mortem alerts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def postmortem_config(self, interaction: discord.Interaction, alert_channel: discord.TextChannel):
        config = self._get_config(interaction.guild.id)
        config["alert_channel_id"] = alert_channel.id
        self._save_data()
        await interaction.response.send_message(f"? Post-mortem alerts set to {alert_channel.mention}")

async def setup(bot):
    await bot.add_cog(PostMortemWorkflow(bot))
