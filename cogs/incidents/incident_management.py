"""Incident Management System - Unified with Feature Flags

Consolidates incident_management_simple.py with feature flags for advanced functionality.
- Simple mode: Create, track, assign incidents (always available)
- Advanced mode: Auto-escalation, workflow integration (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags

class IncidentManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.incidents = {}
        self.incident_counter = 0
        self.statuses = ["open", "acknowledged", "investigating", "mitigating", "resolved", "closed"]
        self.data_file = "data/incidents.json"
        self.mode = "simple"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.incidents = data.get('incidents', {})
                self.incident_counter = data.get('counter', 0)
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'incidents': self.incidents, 'counter': self.incident_counter}, f, indent=2)

    async def cog_load(self):
        """Check if advanced features are enabled"""
        if flags.is_enabled('incident_management_advanced'):
            self.mode = "advanced"

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="incidentcreate", description="Create new incident")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def incidentcreate(self, interaction: discord.Interaction, severity: str, title: str, description: str = "No description"):
        """Create incident - Simple mode"""
        if severity.lower() not in ["critical", "high", "medium", "low"]:
            await interaction.response.send_message("❌ Severity must be: critical, high, medium, low", ephemeral=True)
            return
        
        self.incident_counter += 1
        inc_id = str(self.incident_counter)
        color_map = {"critical": 0xFF0000, "high": 0xFF6600, "medium": 0xFFCC00, "low": 0x00CCFF}
        
        self.incidents[inc_id] = {
            "id": inc_id, "title": title, "description": description, "severity": severity.lower(),
            "status": "open", "assigned_to": None, "created_by": interaction.user.id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "timeline": [{"action": "created", "user_id": interaction.user.id, "timestamp": datetime.datetime.utcnow().isoformat()}]
        }
        self.save_data()
        
        # Emit signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.USER_ESCALATION,
            severity=severity.lower(),
            source='incident_management',
            data={
                'incident_id': inc_id,
                'title': title,
                'severity': severity.lower(),
                'created_by': interaction.user.id,
                'confidence': 0.95,
                'dedup_key': f'incident_{inc_id}'
            }
        ))
        
        embed = discord.Embed(title=f"🚨 Incident #{inc_id} Created", description=title, color=color_map[severity.lower()])
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Status", value="OPEN", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="incidentdetail", description="View incident details")
    async def incidentdetail(self, interaction: discord.Interaction, incident_id: str):
        """View incident - Simple mode"""
        if incident_id not in self.incidents:
            await interaction.response.send_message("❌ Incident not found", ephemeral=True)
            return
        
        inc = self.incidents[incident_id]
        embed = discord.Embed(title=f"Incident #{incident_id}: {inc['title']}", color=discord.Color.red())
        embed.add_field(name="Severity", value=inc['severity'].upper(), inline=True)
        embed.add_field(name="Status", value=inc['status'].upper(), inline=True)
        embed.add_field(name="Description", value=inc['description'], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="incidentlist", description="List incidents")
    async def incidentlist(self, interaction: discord.Interaction):
        """List incidents - Simple mode"""
        embed = discord.Embed(title=f"📋 Incidents ({len(self.incidents)})", color=discord.Color.blue())
        for inc_id, inc in list(self.incidents.items())[-10:]:
            embed.add_field(
                name=f"#{inc_id}: {inc['title'][:40]}",
                value=f"Severity: {inc['severity'].upper()} | Status: {inc['status'].upper()}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="incidentnote", description="Add note to incident")
    async def incidentnote(self, interaction: discord.Interaction, incident_id: str, note: str):
        """Add note to incident - Simple mode"""
        if incident_id not in self.incidents:
            await interaction.response.send_message("❌ Incident not found", ephemeral=True)
            return
        
        if "notes" not in self.incidents[incident_id]:
            self.incidents[incident_id]["notes"] = []
        
        self.incidents[incident_id]["notes"].append({
            "user_id": interaction.user.id,
            "text": note,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        self.save_data()
        await interaction.response.send_message(f"📝 Note added to incident #{incident_id}")

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="incidentassign")
    @commands.has_permissions(moderate_members=True)
    async def incidentassign(self, ctx, incident_id: str, member: discord.Member):
        """Assign incident"""
        if incident_id not in self.incidents:
            await ctx.send("❌ Incident not found")
            return
        self.incidents[incident_id]["assigned_to"] = member.id
        self.save_data()
        await ctx.send(f"📌 Incident #{incident_id} assigned to {member.mention}")

    @commands.command(name="incidentstatus")
    @commands.has_permissions(moderate_members=True)
    async def incidentstatus(self, ctx, incident_id: str, new_status: str):
        """Update incident status"""
        if incident_id not in self.incidents:
            await ctx.send("❌ Incident not found")
            return
        if new_status not in self.statuses:
            await ctx.send(f"❌ Status must be one of: {', '.join(self.statuses)}")
            return
        self.incidents[incident_id]["status"] = new_status
        self.save_data()
        await ctx.send(f"🔄 Incident #{incident_id} status updated to {new_status}")

    @commands.command(name="incidenttimeline")
    async def incidenttimeline(self, ctx, incident_id: str):
        """View incident timeline"""
        if incident_id not in self.incidents:
            await ctx.send("❌ Incident not found")
            return
        
        inc = self.incidents[incident_id]
        embed = discord.Embed(title=f"📅 Incident #{incident_id} Timeline", color=discord.Color.blue())
        for entry in inc.get("timeline", []):
            embed.add_field(name=entry["action"], value=entry["timestamp"][:16], inline=False)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="incidentauto", description="[Advanced] Auto-escalation settings")
    async def incidentauto(self, interaction: discord.Interaction):
        """Auto-escalation - Advanced mode only"""
        if not flags.is_enabled('incident_management_advanced'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        await interaction.response.send_message("⚙️ Auto-escalation enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(IncidentManagementCog(bot))
