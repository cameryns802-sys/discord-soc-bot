"""
Interactive Buttons for Alert Management
Provides Discord UI components for alert handling
"""

import discord
from discord.ext import commands
from discord import ui
import datetime

class AlertActionButtons(ui.View):
    """Interactive buttons for alert actions"""
    
    def __init__(self, alert_system, alert_id: str, timeout=None):
        super().__init__(timeout=timeout)
        self.alert_system = alert_system
        self.alert_id = alert_id
    
    @ui.button(label="Acknowledge", style=discord.ButtonStyle.success, emoji="✅")
    async def acknowledge_button(self, interaction: discord.Interaction, button: ui.Button):
        """Acknowledge this alert"""
        alert = self.alert_system.alerts.get(self.alert_id)
        if not alert:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        if alert.get('acknowledged'):
            await interaction.response.send_message("ℹ️ Alert already acknowledged", ephemeral=True)
            return
        
        # Acknowledge alert
        alert['acknowledged'] = True
        alert['acknowledged_by'] = interaction.user.id
        alert['acknowledged_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        alert['status'] = 'acknowledged'
        self.alert_system.save_data()
        
        await interaction.response.send_message(
            f"✅ Alert **{self.alert_id}** acknowledged",
            ephemeral=True
        )
        
        # Update the embed
        await self.update_alert_embed(interaction)
    
    @ui.button(label="Escalate", style=discord.ButtonStyle.danger, emoji="🚨")
    async def escalate_button(self, interaction: discord.Interaction, button: ui.Button):
        """Escalate this alert to critical"""
        alert = self.alert_system.alerts.get(self.alert_id)
        if not alert:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        old_severity = alert['severity']
        alert['severity'] = 'critical'
        alert['escalated'] = True
        alert['escalated_by'] = interaction.user.id
        alert['escalated_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        self.alert_system.save_data()
        
        await interaction.response.send_message(
            f"🚨 Alert **{self.alert_id}** escalated from **{old_severity}** to **CRITICAL**",
            ephemeral=True
        )
        
        # Update the embed
        await self.update_alert_embed(interaction)
    
    @ui.button(label="Resolve", style=discord.ButtonStyle.secondary, emoji="🔒")
    async def resolve_button(self, interaction: discord.Interaction, button: ui.Button):
        """Resolve this alert"""
        alert = self.alert_system.alerts.get(self.alert_id)
        if not alert:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        if alert.get('resolved'):
            await interaction.response.send_message("ℹ️ Alert already resolved", ephemeral=True)
            return
        
        # Resolve alert
        alert['resolved'] = True
        alert['resolved_by'] = interaction.user.id
        alert['resolved_at'] = datetime.datetime.now(datetime.UTC).isoformat()
        alert['status'] = 'resolved'
        self.alert_system.save_data()
        
        await interaction.response.send_message(
            f"✅ Alert **{self.alert_id}** resolved",
            ephemeral=True
        )
        
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        
        # Update the embed
        await self.update_alert_embed(interaction)
    
    @ui.button(label="Create Incident", style=discord.ButtonStyle.primary, emoji="📋")
    async def create_incident_button(self, interaction: discord.Interaction, button: ui.Button):
        """Create an incident from this alert"""
        alert = self.alert_system.alerts.get(self.alert_id)
        if not alert:
            await interaction.response.send_message("❌ Alert not found", ephemeral=True)
            return
        
        # Check if incident management is available
        incident_cog = interaction.client.get_cog('IncidentManagement')
        if not incident_cog:
            await interaction.response.send_message("❌ Incident management system not available", ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"📋 To create incident from alert **{self.alert_id}**, use:\n`!createincident {alert['severity']} Alert: {alert.get('title', 'Unknown')[:50]}`",
            ephemeral=True
        )
    
    async def update_alert_embed(self, interaction: discord.Interaction):
        """Update the alert embed with current information"""
        alert = self.alert_system.alerts.get(self.alert_id)
        if not alert or not interaction.message:
            return
        
        # Build updated embed
        severity_colors = {
            'low': discord.Color.blue(),
            'medium': discord.Color.gold(),
            'high': discord.Color.orange(),
            'critical': discord.Color.red()
        }
        
        status_emoji = {
            'active': '🔴',
            'acknowledged': '🟡',
            'resolved': '🟢'
        }
        
        embed = discord.Embed(
            title=f"🚨 Alert {self.alert_id}",
            description=alert.get('description', alert.get('title', 'No description')),
            color=severity_colors.get(alert['severity'], discord.Color.gray()),
            timestamp=datetime.datetime.fromisoformat(alert['created_at'])
        )
        
        embed.add_field(name="Status", value=f"{status_emoji.get(alert.get('status', 'active'), '⚪')} {alert.get('status', 'active').title()}", inline=True)
        embed.add_field(name="Severity", value=alert['severity'].upper(), inline=True)
        
        if alert.get('acknowledged'):
            embed.add_field(name="Acknowledged By", value=f"<@{alert['acknowledged_by']}>", inline=True)
        
        if alert.get('resolved'):
            embed.add_field(name="Resolved By", value=f"<@{alert['resolved_by']}>", inline=True)
        
        embed.add_field(name="Source", value=alert.get('source', 'Unknown'), inline=True)
        
        try:
            await interaction.message.edit(embed=embed, view=self)
        except:
            pass

async def setup(bot):
    """This is a utility module, no cog to register"""
    pass
