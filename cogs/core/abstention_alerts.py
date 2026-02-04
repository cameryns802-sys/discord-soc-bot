"""
ABSTENTION ALERTS SYSTEM
Monitors AI system abstentions (low confidence decisions) and escalates alerts to owner.

Architecture:
- Watches abstention_policy for escalation events
- Emits alerts to signal_bus (ESCALATION_REQUIRED signal)
- Sends rich embeds to audit channel
- Provides owner commands for monitoring
- Tracks abstention metrics and patterns
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import core systems
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst
# Lazy imports to avoid circular dependencies
# from cogs.core.abstention_policy import abstention_policy
# from cogs.core.human_override_tracker import human_override_tracker

class AbstentionAlert(commands.Cog):
    """Abstention alert and escalation monitoring system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/abstention_alerts.json'
        self.alerts = []
        self.load_alerts()
    
    def load_alerts(self):
        """Load abstention alerts from persistent storage"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.alerts = json.load(f)
            except:
                self.alerts = []
        else:
            self.alerts = []
    
    def save_alerts(self):
        """Save abstention alerts to persistent storage"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)
    
    def add_alert(self, system: str, confidence: float, reason: str, severity: str = "MEDIUM") -> Dict:
        """Record an abstention alert"""
        alert = {
            'timestamp': get_now_pst().isoformat(),
            'system': system,
            'confidence': confidence,
            'reason': reason,
            'severity': severity,
            'acknowledged': False,
            'reviewed_by': None
        }
        self.alerts.append(alert)
        self.save_alerts()
        return alert
    
    async def emit_escalation_signal(self, system: str, confidence: float, reason: str):
        """Emit ESCALATION_REQUIRED signal to signal bus"""
        signal = Signal(
            signal_type=SignalType.ESCALATION_REQUIRED,
            source='abstention_alerts',
            severity='HIGH',
            confidence=0.95,
            details={
                'system': system,
                'confidence': confidence,
                'reason': reason,
                'escalation_type': 'LOW_CONFIDENCE_ABSTENTION'
            },
            timestamp=get_now_pst().isoformat()
        )
        await signal_bus.emit(signal)
    
    async def send_alert_embed(self, system: str, confidence: float, reason: str, severity: str):
        """Send rich alert embed to audit channel"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        audit_channel_id = int(os.getenv('AUDIT_CHANNEL_ID', '0'))
        
        # Determine color based on severity
        color_map = {
            'CRITICAL': discord.Color.red(),
            'HIGH': discord.Color.orange(),
            'MEDIUM': discord.Color.yellow(),
            'LOW': discord.Color.blue()
        }
        color = color_map.get(severity, discord.Color.blue())
        
        # Create embed
        embed = discord.Embed(
            title=f"🚨 AI System Abstention Alert",
            description=f"System **{system}** abstained due to low confidence",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="System",
            value=f"`{system}`",
            inline=True
        )
        
        embed.add_field(
            name="Confidence",
            value=f"`{confidence:.2%}`",
            inline=True
        )
        
        embed.add_field(
            name="Severity",
            value=f"{severity}",
            inline=True
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="Action Required",
            value="Review system health and consider retraining or threshold adjustment",
            inline=False
        )
        
        # Send to audit channel if configured
        if audit_channel_id:
            try:
                channel = self.bot.get_channel(audit_channel_id)
                if channel:
                    await channel.send(embed=embed)
            except:
                pass
        
        # Send to owner DM
        if owner_id:
            try:
                owner = await self.bot.fetch_user(owner_id)
                if owner:
                    await owner.send(embed=embed)
            except:
                pass
    
    def get_recent_alerts(self, minutes: int = 60, system: str = None) -> List[Dict]:
        """Get recent abstention alerts"""
        cutoff_time = get_now_pst() - timedelta(minutes=minutes)
        recent = [
            a for a in self.alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff_time
        ]
        
        if system:
            recent = [a for a in recent if a['system'] == system]
        
        return sorted(recent, key=lambda x: x['timestamp'], reverse=True)
    
    def get_alert_stats(self) -> Dict:
        """Calculate abstention alert statistics"""
        if not self.alerts:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_system': {},
                'by_hour': {},
                'acknowledged_count': 0,
                'unacknowledged_count': 0
            }
        
        # By severity
        by_severity = {}
        for alert in self.alerts:
            sev = alert['severity']
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        # By system
        by_system = {}
        for alert in self.alerts:
            sys = alert['system']
            by_system[sys] = by_system.get(sys, 0) + 1
        
        # By hour (last 24 hours)
        by_hour = {}
        cutoff = get_now_pst() - timedelta(hours=24)
        for alert in self.alerts:
            ts = datetime.fromisoformat(alert['timestamp'])
            if ts > cutoff:
                hour = ts.strftime('%Y-%m-%d %H:00')
                by_hour[hour] = by_hour.get(hour, 0) + 1
        
        # Acknowledgment
        acknowledged = sum(1 for a in self.alerts if a['acknowledged'])
        unacknowledged = len(self.alerts) - acknowledged
        
        return {
            'total_alerts': len(self.alerts),
            'by_severity': by_severity,
            'by_system': by_system,
            'by_hour': by_hour,
            'acknowledged_count': acknowledged,
            'unacknowledged_count': unacknowledged,
            'critical_count': by_severity.get('CRITICAL', 0),
            'high_count': by_severity.get('HIGH', 0),
            'medium_count': by_severity.get('MEDIUM', 0),
            'low_count': by_severity.get('LOW', 0)
        }
    
    def acknowledge_alert(self, alert_index: int, reviewed_by: str = None) -> bool:
        """Mark an alert as acknowledged"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]['acknowledged'] = True
            self.alerts[alert_index]['reviewed_by'] = reviewed_by
            self.save_alerts()
            return True
        return False
    
    @commands.command(name='abstentionalert')
    async def abstention_alert_cmd(self, ctx, system: str = None, hours: int = 24):
        """View recent abstention alerts (owner only)"""
        
        # Check permission
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        # Get recent alerts
        recent = self.get_recent_alerts(minutes=hours*60, system=system)
        
        if not recent:
            await ctx.send(f"✅ No abstention alerts in the last {hours} hours")
            return
        
        # Build embed
        embed = discord.Embed(
            title="🚨 Recent Abstention Alerts",
            description=f"Showing {len(recent)} alerts from the last {hours} hours",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        # Group by severity for visualization
        for alert in recent[:10]:  # Show last 10
            ts = datetime.fromisoformat(alert['timestamp'])
            time_str = ts.strftime('%Y-%m-%d %H:%M:%S')
            
            # Severity indicator
            severity_indicators = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🔵'
            }
            indicator = severity_indicators.get(alert['severity'], '⚪')
            
            # Acknowledgment indicator
            ack_str = '✅' if alert['acknowledged'] else '⏳'
            
            field_value = f"{indicator} **{alert['severity']}** | {ack_str}\n"
            field_value += f"System: `{alert['system']}`\n"
            field_value += f"Confidence: `{alert['confidence']:.2%}`\n"
            field_value += f"Reason: {alert['reason'][:100]}\n"
            field_value += f"Time: <t:{int(ts.timestamp())}:R>"
            
            embed.add_field(
                name=f"Alert {recent.index(alert)+1}",
                value=field_value,
                inline=False
            )
        
        # Add statistics
        stats = self.get_alert_stats()
        embed.add_field(
            name="📊 Statistics",
            value=f"Total: {stats['total_alerts']}\n"
                  f"🔴 Critical: {stats['critical_count']}\n"
                  f"🟠 High: {stats['high_count']}\n"
                  f"🟡 Medium: {stats['medium_count']}\n"
                  f"🔵 Low: {stats['low_count']}\n"
                  f"⏳ Unacknowledged: {stats['unacknowledged_count']}",
            inline=False
        )
        
        embed.set_footer(text="Use /abstractionalert <system> to filter by system")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='abstentiontrends')
    async def abstention_trends_cmd(self, ctx):
        """View abstention trends by system and severity (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        stats = self.get_alert_stats()
        
        if stats['total_alerts'] == 0:
            await ctx.send("✅ No abstention alerts recorded yet")
            return
        
        # Build trends embed
        embed = discord.Embed(
            title="📈 Abstention Trends",
            description=f"Analysis of {stats['total_alerts']} total abstention events",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        # By severity
        severity_text = "**By Severity:**\n"
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = stats['by_severity'].get(sev, 0)
            percent = (count / stats['total_alerts'] * 100) if stats['total_alerts'] > 0 else 0
            severity_indicators = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🔵'
            }
            indicator = severity_indicators.get(sev, '⚪')
            severity_text += f"{indicator} {sev}: {count} ({percent:.1f}%)\n"
        
        embed.add_field(
            name="Severity Distribution",
            value=severity_text,
            inline=False
        )
        
        # By system (top 5)
        sorted_systems = sorted(stats['by_system'].items(), key=lambda x: x[1], reverse=True)[:5]
        system_text = "**Top Systems by Abstention Count:**\n"
        for system, count in sorted_systems:
            system_text += f"`{system}`: {count} abstentions\n"
        
        embed.add_field(
            name="System Distribution",
            value=system_text,
            inline=False
        )
        
        # Hourly trend (last 24 hours)
        if stats['by_hour']:
            hourly_text = "**Last 24 Hours:**\n"
            for hour in sorted(stats['by_hour'].keys())[-6:]:  # Last 6 hours
                count = stats['by_hour'][hour]
                bar = "█" * min(count, 20)
                hourly_text += f"{hour}: {bar} ({count})\n"
            embed.add_field(
                name="Hourly Trend",
                value=hourly_text,
                inline=False
            )
        
        # Acknowledgment status
        ack_text = f"✅ Acknowledged: {stats['acknowledged_count']}\n"
        ack_text += f"⏳ Pending Review: {stats['unacknowledged_count']}\n"
        ack_text += f"📊 Review Rate: {(stats['acknowledged_count']/stats['total_alerts']*100):.1f}%" if stats['total_alerts'] > 0 else "N/A"
        
        embed.add_field(
            name="Acknowledgment Status",
            value=ack_text,
            inline=False
        )
        
        embed.set_footer(text="Track these trends to identify system patterns and degradation")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='abstentionrecap')
    async def abstention_recap_cmd(self, ctx, hours: int = 24):
        """Daily recap of abstention events (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        recent = self.get_recent_alerts(minutes=hours*60)
        stats = self.get_alert_stats()
        
        # Build recap embed
        embed = discord.Embed(
            title=f"📋 Abstention Recap ({hours}h)",
            description=f"Summary of system abstentions and escalations",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        # Summary
        summary = f"**Events:** {len(recent)}\n"
        summary += f"**Critical:** {sum(1 for a in recent if a['severity'] == 'CRITICAL')}\n"
        summary += f"**High:** {sum(1 for a in recent if a['severity'] == 'HIGH')}\n"
        summary += f"**Pending:** {sum(1 for a in recent if not a['acknowledged'])}\n"
        
        embed.add_field(
            name="📊 Summary",
            value=summary,
            inline=False
        )
        
        # Most problematic systems
        system_counts = {}
        for alert in recent:
            system_counts[alert['system']] = system_counts.get(alert['system'], 0) + 1
        
        if system_counts:
            top_systems = sorted(system_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            systems_text = ""
            for system, count in top_systems:
                systems_text += f"`{system}`: {count} events\n"
            
            embed.add_field(
                name="⚠️ Most Problematic Systems",
                value=systems_text,
                inline=False
            )
        
        # Recommendations
        recommendations = ""
        
        # Critical events recommendation
        critical_count = sum(1 for a in recent if a['severity'] == 'CRITICAL')
        if critical_count > 0:
            recommendations += f"🔴 {critical_count} critical abstentions - immediate review recommended\n"
        
        # Unacknowledged recommendation
        unack = sum(1 for a in recent if not a['acknowledged'])
        if unack > 5:
            recommendations += f"⏳ {unack} alerts pending review - prioritize review workflow\n"
        
        if not recommendations:
            recommendations = "✅ All systems operating within normal parameters"
        
        embed.add_field(
            name="💡 Recommendations",
            value=recommendations,
            inline=False
        )
        
        embed.set_footer(text="Review unacknowledged alerts to ensure system health")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AbstentionAlert(bot))
