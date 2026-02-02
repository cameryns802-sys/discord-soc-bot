"""
Real-time SOC Dashboard - Master security operations center overview for Sentinel
Unified view of all security metrics, threats, incidents, and status
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import Counter

class RealTimeSocDashboard(commands.Cog):
    """Master SOC dashboard with real-time metrics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.threat_file = 'data/threat_responses.json'
        self.incident_file = 'data/incidents.json'
        self.alert_file = 'data/alerts.json'
        self.checklist_file = 'data/security_checklist.json'
    
    def get_threat_data(self, guild_id):
        """Load threat data"""
        if not os.path.exists(self.threat_file):
            return []
        
        with open(self.threat_file, 'r') as f:
            all_threats = json.load(f)
        
        return all_threats.get(str(guild_id), [])
    
    def get_incident_data(self, guild_id):
        """Load incident data"""
        if not os.path.exists(self.incident_file):
            return {}
        
        with open(self.incident_file, 'r') as f:
            all_incidents = json.load(f)
        
        return all_incidents.get(str(guild_id), {})
    
    def get_alert_data(self, guild_id):
        """Load alert data"""
        if not os.path.exists(self.alert_file):
            return {}
        
        with open(self.alert_file, 'r') as f:
            all_alerts = json.load(f)
        
        return all_alerts.get(str(guild_id), {})
    
    def calculate_security_health(self, guild_id):
        """Calculate overall security health score (0-100)"""
        score = 100
        
        threats = self.get_threat_data(guild_id)
        incidents = self.get_incident_data(guild_id)
        alerts = self.get_alert_data(guild_id)
        
        # Threat impact
        recent_threats = [t for t in threats if datetime.fromisoformat(t.get('timestamp', datetime.utcnow().isoformat())) > (datetime.utcnow() - timedelta(hours=24))]
        critical_count = sum(1 for t in recent_threats if t.get('severity') == 'critical')
        high_count = sum(1 for t in recent_threats if t.get('severity') == 'high')
        
        score -= (critical_count * 10)
        score -= (high_count * 5)
        
        # Unresolved incidents
        open_incidents = sum(1 for i in incidents.values() if i.get('status') == 'open')
        score -= (open_incidents * 3)
        
        # Unacknowledged alerts
        unack_alerts = sum(1 for a in alerts.values() if not a.get('acknowledged'))
        score -= (unack_alerts * 2)
        
        return max(0, min(100, score))
    
    async def _socdashboard_logic(self, ctx):
        """Show master SOC dashboard"""
        threats = self.get_threat_data(ctx.guild.id)
        incidents = self.get_incident_data(ctx.guild.id)
        alerts = self.get_alert_data(ctx.guild.id)
        
        now = datetime.utcnow()
        recent_threats = [t for t in threats if datetime.fromisoformat(t.get('timestamp', now.isoformat())) > (now - timedelta(hours=24))]
        recent_incidents = [i for i in incidents.values() if datetime.fromisoformat(i.get('created_at', now.isoformat())) > (now - timedelta(hours=24))]
        
        # Calculate metrics
        critical = sum(1 for t in recent_threats if t.get('severity') == 'critical')
        high = sum(1 for t in recent_threats if t.get('severity') == 'high')
        open_incidents = sum(1 for i in incidents.values() if i.get('status') == 'open')
        unack_alerts = sum(1 for a in alerts.values() if not a.get('acknowledged'))
        total_events = len(threats) + len(incidents) + len(alerts)
        
        health_score = self.calculate_security_health(ctx.guild.id)
        
        # Determine health color
        if health_score >= 80:
            health_color = discord.Color.green()
            health_status = "🟢 EXCELLENT"
        elif health_score >= 60:
            health_color = discord.Color.yellow()
            health_status = "🟡 GOOD"
        elif health_score >= 40:
            health_color = discord.Color.orange()
            health_status = "🟠 WARNING"
        else:
            health_color = discord.Color.red()
            health_status = "🔴 CRITICAL"
        
        embed = discord.Embed(
            title="🎯 SENTINEL SOC Dashboard",
            description="Real-time security operations overview",
            color=health_color,
            timestamp=datetime.utcnow()
        )
        
        # Top metrics
        embed.add_field(name="🏥 Security Health", value=f"{health_score}/100 - {health_status}", inline=True)
        embed.add_field(name="📊 Total Events (All-time)", value=f"`{total_events}`", inline=True)
        embed.add_field(name="⏱️ Last 24 Hours", value=f"`{len(recent_threats)} threats`", inline=True)
        
        # Threat metrics
        embed.add_field(name="🎯 Active Threats (24h)", value=f"`{len(recent_threats)}`", inline=True)
        embed.add_field(name="🔴 Critical", value=f"`{critical}`", inline=True)
        embed.add_field(name="🟠 High", value=f"`{high}`", inline=True)
        
        # Incident metrics
        embed.add_field(name="📋 Total Incidents", value=f"`{len(incidents)}`", inline=True)
        embed.add_field(name="🟢 Open", value=f"`{open_incidents}`", inline=True)
        embed.add_field(name="✅ Closed", value=f"`{len(incidents) - open_incidents}`", inline=True)
        
        # Alert metrics
        embed.add_field(name="🚨 Total Alerts", value=f"`{len(alerts)}`", inline=True)
        embed.add_field(name="📌 Unacknowledged", value=f"`{unack_alerts}`", inline=True)
        embed.add_field(name="✔️ Acknowledged", value=f"`{len(alerts) - unack_alerts}`", inline=True)
        
        # Threat type breakdown
        if recent_threats:
            threat_types = Counter([t.get('threat_type', 'unknown') for t in recent_threats])
            top_threats = "\n".join([f"• {k}: {v}x" for k, v in threat_types.most_common(3)])
            embed.add_field(name="🎯 Top Threats (24h)", value=top_threats, inline=False)
        
        # Status indicators
        status_indicators = []
        if critical > 0:
            status_indicators.append(f"🔴 **CRITICAL THREATS**: {critical} active")
        if open_incidents > 5:
            status_indicators.append(f"📋 **HIGH CASE LOAD**: {open_incidents} open incidents")
        if unack_alerts > 10:
            status_indicators.append(f"🚨 **ALERT BACKLOG**: {unack_alerts} unacknowledged")
        if health_score < 40:
            status_indicators.append(f"⚠️ **SECURITY POSTURE**: Below acceptable threshold")
        
        if status_indicators:
            status_str = "\n".join(status_indicators)
            embed.add_field(name="⚡ Status Alerts", value=status_str, inline=False)
        else:
            embed.add_field(name="✅ Status", value="All systems normal", inline=False)
        
        # Quick actions
        embed.add_field(
            name="⚙️ Quick Actions",
            value="```\n/dashboard - Security metrics\n/threatstatus - Threat level\n/incidentlist - Open cases\n/alertlist - Alert queue\n/threatintel - Intel summary\n```",
            inline=False
        )
        
        embed.set_footer(text=f"Sentinel SOC | Updated {datetime.utcnow().strftime('%H:%M:%S UTC')} | Type: /help for commands")
        
        await ctx.send(embed=embed)
    
    async def _healthcheck_logic(self, ctx):
        """Run security health check"""
        health_score = self.calculate_security_health(ctx.guild.id)
        threats = self.get_threat_data(ctx.guild.id)
        incidents = self.get_incident_data(ctx.guild.id)
        alerts = self.get_alert_data(ctx.guild.id)
        
        now = datetime.utcnow()
        recent_threats = [t for t in threats if datetime.fromisoformat(t.get('timestamp', now.isoformat())) > (now - timedelta(hours=24))]
        
        issues = []
        
        # Check for critical threats
        if any(t.get('severity') == 'critical' for t in recent_threats):
            issues.append("🔴 **CRITICAL**: Active critical-level threats detected")
        
        # Check for too many high threats
        if sum(1 for t in recent_threats if t.get('severity') == 'high') > 2:
            issues.append("🟠 **HIGH**: Multiple high-severity threats present")
        
        # Check for open incidents
        open_incidents = sum(1 for i in incidents.values() if i.get('status') == 'open')
        if open_incidents > 5:
            issues.append(f"📋 **INCIDENT LOAD**: {open_incidents} unresolved incidents")
        
        # Check for unacknowledged alerts
        unack = sum(1 for a in alerts.values() if not a.get('acknowledged'))
        if unack > 10:
            issues.append(f"🚨 **ALERT BACKLOG**: {unack} unacknowledged alerts")
        
        if health_score < 40:
            issues.append("⚠️ **POSTURE**: Security posture below acceptable threshold")
        
        embed = discord.Embed(
            title="🏥 Security Health Check",
            description=f"Health Score: {health_score}/100",
            color=discord.Color.red() if health_score < 40 else discord.Color.orange() if health_score < 60 else discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if issues:
            issues_str = "\n".join(issues)
            embed.add_field(name="⚠️ Issues Found", value=issues_str, inline=False)
        else:
            embed.add_field(name="✅ Status", value="All security checks passed", inline=False)
        
        # Recommendations
        if health_score < 60:
            embed.add_field(
                name="💡 Recommendations",
                value="• Review active threats\n• Prioritize incident resolution\n• Clear alert backlog\n• Run threat intelligence analysis",
                inline=False
            )
        
        embed.set_footer(text="Sentinel Health Check System")
        
        await ctx.send(embed=embed)
    
    async def _metrics_logic(self, ctx, period: str = '24h'):
        """Show detailed metrics for period"""
        multiplier = {
            '24h': 1,
            '7d': 7,
            '30d': 30
        }.get(period.lower(), 1)
        
        cutoff = datetime.utcnow() - timedelta(days=multiplier)
        
        threats = self.get_threat_data(ctx.guild.id)
        incidents = self.get_incident_data(ctx.guild.id)
        alerts = self.get_alert_data(ctx.guild.id)
        
        period_threats = [t for t in threats if datetime.fromisoformat(t.get('timestamp', datetime.utcnow().isoformat())) > cutoff]
        period_incidents = [i for i in incidents.values() if datetime.fromisoformat(i.get('created_at', datetime.utcnow().isoformat())) > cutoff]
        period_alerts = [a for a in alerts.values() if datetime.fromisoformat(a.get('created_at', datetime.utcnow().isoformat())) > cutoff]
        
        embed = discord.Embed(
            title=f"📊 Security Metrics ({period})",
            description=f"Period: {period}",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        # Volume metrics
        embed.add_field(name="📈 Event Volume", value=f"Threats: {len(period_threats)}\nIncidents: {len(period_incidents)}\nAlerts: {len(period_alerts)}\nTotal: {len(period_threats) + len(period_incidents) + len(period_alerts)}", inline=True)
        
        # Severity breakdown
        threat_severity = Counter([t.get('severity', 'low') for t in period_threats])
        severity_str = f"Critical: {threat_severity.get('critical', 0)}\nHigh: {threat_severity.get('high', 0)}\nMedium: {threat_severity.get('medium', 0)}\nLow: {threat_severity.get('low', 0)}"
        embed.add_field(name="🎯 Threat Severity", value=severity_str, inline=True)
        
        # Incident status
        incident_status = Counter([i.get('status', 'unknown') for i in period_incidents])
        status_str = f"Open: {incident_status.get('open', 0)}\nClosed: {incident_status.get('closed', 0)}"
        embed.add_field(name="📋 Incident Status", value=status_str, inline=True)
        
        # Top threats
        if period_threats:
            threat_types = Counter([t.get('threat_type', 'unknown') for t in period_threats])
            top_threats = "\n".join([f"• {k}: {v}" for k, v in threat_types.most_common(5)])
            embed.add_field(name="🎯 Top Threat Types", value=top_threats, inline=False)
        
        embed.set_footer(text="Sentinel Metrics | Period-based analysis")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='socdashboard')
    async def socdashboard_prefix(self, ctx):
        """Show master SOC dashboard - Prefix command"""
        await self._socdashboard_logic(ctx)
    
    @commands.command(name='healthcheck')
    async def healthcheck_prefix(self, ctx):
        """Run security health check - Prefix command"""
        await self._healthcheck_logic(ctx)
    
    @commands.command(name='metrics')
    async def metrics_prefix(self, ctx, period: str = '24h'):
        """Show detailed metrics - Prefix command"""
        if period.lower() not in ['24h', '7d', '30d']:
            await ctx.send("❌ Invalid period. Use: 24h, 7d, or 30d")
            return
        
        await self._metrics_logic(ctx, period)

async def setup(bot):
    await bot.add_cog(RealTimeSocDashboard(bot))
