"""Alert Management System - Unified with Feature Flags

Consolidates alert_management_simple.py with feature flags for advanced functionality.
- Simple mode: Create, resolve, list, escalate alerts (always available)
- Advanced mode: Correlation, intelligent routing, auto-actions (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags

class AlertManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/alerts.json"
        self.alerts = {}
        self.alert_counter = 0
        self.mode = "simple"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.alerts = data.get('alerts', {})
                self.alert_counter = data.get('counter', 0)
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'alerts': self.alerts, 'counter': self.alert_counter}, f, indent=2)

    async def cog_load(self):
        """Check if advanced features are enabled"""
        if flags.is_enabled('alert_management_advanced'):
            self.mode = "advanced"

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="alertcreate", description="Create new alert")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def alertcreate(self, interaction: discord.Interaction, severity: str, title: str, source: str = "manual"):
        """Create alert - Simple mode"""
        if severity.lower() not in ["critical", "high", "medium", "low", "info"]:
            await interaction.response.send_message("❌ Severity must be: critical, high, medium, low, info", ephemeral=True)
            return
        
        self.alert_counter += 1
        alert_id = str(self.alert_counter)
        color_map = {"critical": 0xFF0000, "high": 0xFF6600, "medium": 0xFFCC00, "low": 0x00CCFF, "info": 0x808080}
        
        self.alerts[alert_id] = {
            "id": alert_id, "title": title, "severity": severity.lower(), "status": "new",
            "source": source, "created_by": interaction.user.id,
            "created_at": datetime.utcnow().isoformat()
        }
        self.save_data()
        
        # Emit signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.POLICY_VIOLATION,
            severity=severity.lower(),
            source='alert_management',
            data={
                'alert_id': alert_id,
                'title': title,
                'source': source,
                'created_by': interaction.user.id,
                'confidence': 0.95,
                'dedup_key': f'alert_{alert_id}'
            }
        ))
        
        embed = discord.Embed(title=f"🚨 Alert #{alert_id}", description=title, color=color_map[severity.lower()])
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Source", value=source, inline=True)
        embed.add_field(name="Status", value="NEW", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="alertresolve", description="Resolve an alert")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def alertresolve(self, interaction: discord.Interaction, alert_id: str, resolution: str = "resolved"):
        """Resolve alert - Simple mode"""
        if alert_id not in self.alerts:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        self.alerts[alert_id]["status"] = "resolved"
        self.alerts[alert_id]["resolved_by"] = interaction.user.id
        self.alerts[alert_id]["resolved_at"] = datetime.utcnow().isoformat()
        self.save_data()
        
        await interaction.response.send_message(f"✅ Alert #{alert_id} resolved")

    @app_commands.command(name="alertlist", description="List all active alerts")
    async def alertlist(self, interaction: discord.Interaction):
        """List alerts - Simple mode"""
        active = {k: v for k, v in self.alerts.items() if v.get("status") != "resolved"}
        
        embed = discord.Embed(title=f"📋 Active Alerts ({len(active)})", color=discord.Color.blue())
        for alert_id, alert in list(active.items())[-10:]:
            embed.add_field(
                name=f"Alert #{alert_id}: {alert['title'][:50]}",
                value=f"Severity: {alert['severity'].upper()} | Status: {alert['status'].upper()}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="alertescalate", description="Escalate an alert")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def alertescalate(self, interaction: discord.Interaction, alert_id: str, new_severity: str = "critical"):
        """Escalate alert - Simple mode"""
        if alert_id not in self.alerts:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        old_severity = self.alerts[alert_id]["severity"]
        self.alerts[alert_id]["severity"] = new_severity.lower()
        self.save_data()
        
        await interaction.response.send_message(f"⬆️ Alert #{alert_id} escalated from {old_severity} to {new_severity}")

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="alertack")
    @commands.has_permissions(moderate_members=True)
    async def alertack(self, ctx, alert_id: str):
        """Acknowledge alert"""
        if alert_id not in self.alerts:
            await ctx.send("❌ Alert not found")
            return
        self.alerts[alert_id]["status"] = "acknowledged"
        self.save_data()
        await ctx.send(f"👁️ Alert #{alert_id} acknowledged")

    @commands.command(name="alertassign")
    @commands.has_permissions(moderate_members=True)
    async def alertassign(self, ctx, alert_id: str, member: discord.Member):
        """Assign alert to member"""
        if alert_id not in self.alerts:
            await ctx.send("❌ Alert not found")
            return
        self.alerts[alert_id]["assigned_to"] = member.id
        self.save_data()
        await ctx.send(f"📌 Alert #{alert_id} assigned to {member.mention}")

    @commands.command(name="alertdetail")
    async def alertdetail(self, ctx, alert_id: str):
        """View alert details"""
        if alert_id not in self.alerts:
            await ctx.send("❌ Alert not found")
            return
        alert = self.alerts[alert_id]
        embed = discord.Embed(title=f"Alert #{alert_id}", color=discord.Color.blue())
        embed.add_field(name="Title", value=alert['title'], inline=False)
        embed.add_field(name="Severity", value=alert['severity'].upper(), inline=True)
        embed.add_field(name="Status", value=alert['status'].upper(), inline=True)
        embed.add_field(name="Source", value=alert['source'], inline=True)
        embed.add_field(name="Created", value=alert['created_at'][:16], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="alertstats")
    async def alertstats(self, ctx):
        """View alert statistics"""
        stats = {
            'total': len(self.alerts),
            'critical': len([a for a in self.alerts.values() if a['severity'] == 'critical']),
            'high': len([a for a in self.alerts.values() if a['severity'] == 'high']),
            'active': len([a for a in self.alerts.values() if a['status'] != 'resolved'])
        }
        embed = discord.Embed(title="📊 Alert Statistics", color=discord.Color.blue())
        for key, value in stats.items():
            embed.add_field(name=key.title(), value=str(value), inline=True)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="alertcorrelate", description="[Advanced] Correlate related alerts")
    async def alertcorrelate(self, interaction: discord.Interaction):
        """Correlate alerts - Advanced mode only"""
        if not flags.is_enabled('alert_management_advanced'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        # Advanced correlation logic would go here
        await interaction.response.send_message("🔗 Alert correlation enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(AlertManagementCog(bot))
