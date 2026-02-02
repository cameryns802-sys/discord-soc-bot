"""
Alert Management System - Enterprise alert lifecycle management for Sentinel
Handles alert creation, escalation, acknowledgment, and resolution tracking
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class AlertManagement(commands.Cog):
    """Enterprise alert management and escalation system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.alert_file = 'data/alerts.json'
        self.load_alerts()
    
    def load_alerts(self):
        """Load alerts from storage"""
        if not os.path.exists(self.alert_file):
            os.makedirs(os.path.dirname(self.alert_file), exist_ok=True)
            with open(self.alert_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_alerts(self, guild_id):
        """Get alerts for a specific guild"""
        with open(self.alert_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_alerts(self, guild_id, alerts):
        """Save alerts to storage"""
        with open(self.alert_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = alerts
        with open(self.alert_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_alert(self, guild_id, title, severity, description, source):
        """Create a new alert"""
        alerts = self.get_guild_alerts(guild_id)
        alert_id = str(uuid.uuid4())[:8]
        
        alert = {
            'id': alert_id,
            'title': title,
            'severity': severity.lower(),
            'description': description,
            'source': source,
            'status': 'open',
            'created_at': datetime.utcnow().isoformat(),
            'acknowledged': False,
            'acknowledged_by': None,
            'acknowledged_at': None,
            'resolved': False,
            'resolved_by': None,
            'resolved_at': None,
            'escalation_level': 1,
            'escalated_to': None
        }
        
        alerts[alert_id] = alert
        self.save_alerts(guild_id, alerts)
        return alert
    
    def get_severity_color(self, severity):
        """Get color for severity level"""
        severity_map = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.yellow(),
            'info': discord.Color.blue()
        }
        return severity_map.get(severity.lower(), discord.Color.greyple())
    
    def get_severity_emoji(self, severity):
        """Get emoji for severity level"""
        emoji_map = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️',
            'info': '📋'
        }
        return emoji_map.get(severity.lower(), '❓')
    
    async def _alertcreate_logic(self, ctx, title: str, severity: str, description: str, source: str):
        """Create alert command logic"""
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if severity.lower() not in valid_severities:
            await ctx.send(f"❌ Invalid severity. Use: {', '.join(valid_severities)}")
            return
        
        alert = self.create_alert(ctx.guild.id, title, severity, description, source)
        
        embed = discord.Embed(
            title=f"{self.get_severity_emoji(severity)} Alert Created",
            description=f"**{title}**",
            color=self.get_severity_color(severity),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert ID", value=f"`{alert['id']}`", inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Source", value=source, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Status", value="🟢 Open", inline=True)
        embed.add_field(name="Escalation Level", value="1", inline=True)
        embed.set_footer(text=f"Alert tracking system | ID: {alert['id']}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='alertcreate')
    async def alertcreate_prefix(self, ctx, severity: str, *, args: str):
        """Create a new alert - Prefix command"""
        parts = args.split('|')
        if len(parts) < 3:
            await ctx.send("Usage: `!alertcreate <severity> <title> | <description> | <source>`")
            return
        
        title = parts[0].strip()
        description = parts[1].strip()
        source = parts[2].strip()
        await self._alertcreate_logic(ctx, title, severity, description, source)
    
    @commands.command(name='alertlist')
    async def alertlist_prefix(self, ctx, status: str = 'open'):
        """List alerts by status - Prefix command"""
        await self._alertlist_logic(ctx, status)
    
    @commands.command(name='alertack')
    async def alertack_prefix(self, ctx, alert_id: str):
        """Acknowledge an alert - Prefix command"""
        await self._alertack_logic(ctx, alert_id)
    
    @commands.command(name='alertescalate')
    async def alertescalate_prefix(self, ctx, alert_id: str, level: int = 2):
        """Escalate an alert - Prefix command"""
        await self._alertescalate_logic(ctx, alert_id, level)
    
    @commands.command(name='alertresolve')
    async def alertresolve_prefix(self, ctx, alert_id: str):
        """Resolve an alert - Prefix command"""
        await self._alertresolve_logic(ctx, alert_id)
    
    @commands.command(name='alertdetail')
    async def alertdetail_prefix(self, ctx, alert_id: str):
        """Show alert details - Prefix command"""
        await self._alertdetail_logic(ctx, alert_id)
    
    async def _alertlist_logic(self, ctx, status: str = 'open'):
        """List alerts by status"""
        alerts = self.get_guild_alerts(ctx.guild.id)
        filtered = {k: v for k, v in alerts.items() if v['status'] == status.lower()}
        
        if not filtered:
            await ctx.send(f"📋 No **{status.upper()}** alerts found.")
            return
        
        embed = discord.Embed(
            title=f"🚨 {status.upper()} Alerts",
            description=f"{len(filtered)} alert(s) found",
            color=discord.Color.greyple(),
            timestamp=datetime.utcnow()
        )
        
        for alert in list(filtered.values())[:10]:  # Max 10 per message
            emoji = self.get_severity_emoji(alert['severity'])
            status_indicator = "🟢" if not alert['acknowledged'] else "🟡"
            embed.add_field(
                name=f"{emoji} {alert['title']}",
                value=f"ID: `{alert['id']}` | Level: {alert['escalation_level']} | {status_indicator} {alert['severity'].upper()}",
                inline=False
            )
        
        embed.set_footer(text="Use /alertdetail <id> for full details")
        await ctx.send(embed=embed)
    
    async def _alertack_logic(self, ctx, alert_id: str):
        """Acknowledge an alert"""
        alerts = self.get_guild_alerts(ctx.guild.id)
        if alert_id not in alerts:
            await ctx.send(f"❌ Alert `{alert_id}` not found.")
            return
        
        alert = alerts[alert_id]
        alert['acknowledged'] = True
        alert['acknowledged_by'] = ctx.author.id
        alert['acknowledged_at'] = datetime.utcnow().isoformat()
        self.save_alerts(ctx.guild.id, alerts)
        
        embed = discord.Embed(
            title="✅ Alert Acknowledged",
            description=f"**{alert['title']}**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert ID", value=f"`{alert['id']}`", inline=True)
        embed.add_field(name="Acknowledged By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Severity", value=alert['severity'].upper(), inline=True)
        embed.set_footer(text="Alert acknowledged and being handled")
        
        await ctx.send(embed=embed)
    
    async def _alertescalate_logic(self, ctx, alert_id: str, level: int):
        """Escalate an alert to higher level"""
        alerts = self.get_guild_alerts(ctx.guild.id)
        if alert_id not in alerts:
            await ctx.send(f"❌ Alert `{alert_id}` not found.")
            return
        
        if level < 1 or level > 5:
            await ctx.send("❌ Escalation level must be 1-5.")
            return
        
        alert = alerts[alert_id]
        old_level = alert['escalation_level']
        alert['escalation_level'] = level
        alert['escalated_to'] = ctx.author.id
        self.save_alerts(ctx.guild.id, alerts)
        
        embed = discord.Embed(
            title="⬆️ Alert Escalated",
            description=f"**{alert['title']}**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert ID", value=f"`{alert['id']}`", inline=True)
        embed.add_field(name="Previous Level", value=str(old_level), inline=True)
        embed.add_field(name="New Level", value=str(level), inline=True)
        embed.add_field(name="Escalated By", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"Alert escalation level: {level}/5")
        
        await ctx.send(embed=embed)
    
    async def _alertresolve_logic(self, ctx, alert_id: str):
        """Resolve an alert"""
        alerts = self.get_guild_alerts(ctx.guild.id)
        if alert_id not in alerts:
            await ctx.send(f"❌ Alert `{alert_id}` not found.")
            return
        
        alert = alerts[alert_id]
        alert['status'] = 'resolved'
        alert['resolved'] = True
        alert['resolved_by'] = ctx.author.id
        alert['resolved_at'] = datetime.utcnow().isoformat()
        self.save_alerts(ctx.guild.id, alerts)
        
        embed = discord.Embed(
            title="✔️ Alert Resolved",
            description=f"**{alert['title']}**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert ID", value=f"`{alert['id']}`", inline=True)
        embed.add_field(name="Resolved By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Duration", value=f"~{(datetime.fromisoformat(alert['resolved_at']) - datetime.fromisoformat(alert['created_at'])).seconds // 60} minutes", inline=True)
        embed.set_footer(text="Alert closed and archived")
        
        await ctx.send(embed=embed)
    
    async def _alertdetail_logic(self, ctx, alert_id: str):
        """Show full alert details"""
        alerts = self.get_guild_alerts(ctx.guild.id)
        if alert_id not in alerts:
            await ctx.send(f"❌ Alert `{alert_id}` not found.")
            return
        
        alert = alerts[alert_id]
        
        embed = discord.Embed(
            title=f"{self.get_severity_emoji(alert['severity'])} Alert Details",
            description=f"**{alert['title']}**",
            color=self.get_severity_color(alert['severity']),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert ID", value=f"`{alert['id']}`", inline=True)
        embed.add_field(name="Status", value=alert['status'].upper(), inline=True)
        embed.add_field(name="Severity", value=alert['severity'].upper(), inline=True)
        embed.add_field(name="Source", value=alert['source'], inline=True)
        embed.add_field(name="Escalation Level", value=f"{alert['escalation_level']}/5", inline=True)
        embed.add_field(name="Acknowledged", value="✅ Yes" if alert['acknowledged'] else "❌ No", inline=True)
        embed.add_field(name="Description", value=alert['description'], inline=False)
        embed.add_field(name="Created", value=f"<t:{int(datetime.fromisoformat(alert['created_at']).timestamp())}:R>", inline=True)
        
        if alert['acknowledged']:
            embed.add_field(name="Acknowledged At", value=f"<t:{int(datetime.fromisoformat(alert['acknowledged_at']).timestamp())}:R>", inline=True)
        
        if alert['resolved']:
            embed.add_field(name="Resolved At", value=f"<t:{int(datetime.fromisoformat(alert['resolved_at']).timestamp())}:R>", inline=True)
        
        embed.set_footer(text="Sentinel Alert Management System")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AlertManagement(bot))
