"""
Threat Intelligence Synthesizer - Auto-generates actionable threat summaries for Sentinel
Synthesizes raw threat data into executive briefings, trend analysis, and recommendations
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import Counter

class ThreatIntelligenceSynthesizer(commands.Cog):
    """Synthesize threat data into actionable intelligence"""
    
    def __init__(self, bot):
        self.bot = bot
        self.threat_file = 'data/threat_responses.json'
    
    def load_threat_data(self):
        """Load threat data from file"""
        if not os.path.exists(self.threat_file):
            return {}
        
        with open(self.threat_file, 'r') as f:
            return json.load(f)
    
    def get_threat_synthesis(self, guild_id):
        """Synthesize threats for intel generation"""
        all_threats = self.load_threat_data()
        guild_threats = all_threats.get(str(guild_id), [])
        
        if not guild_threats:
            return None
        
        now = datetime.utcnow()
        recent = [t for t in guild_threats if datetime.fromisoformat(t.get('timestamp', now.isoformat())) > (now - timedelta(hours=24))]
        
        return {
            'total': len(guild_threats),
            'recent_24h': len(recent),
            'threats': recent,
            'all_threats': guild_threats
        }
    
    def get_threat_type_distribution(self, threats):
        """Analyze threat type distribution"""
        types = [t.get('threat_type', 'unknown') for t in threats]
        return Counter(types)
    
    def get_threat_severity_distribution(self, threats):
        """Analyze threat severity distribution"""
        severities = [t.get('severity', 'low') for t in threats]
        return Counter(severities)
    
    def generate_trend_analysis(self, threats):
        """Generate trend analysis from threats"""
        if not threats:
            return "No threats detected. All clear."
        
        severity_dist = self.get_threat_severity_distribution(threats)
        type_dist = self.get_threat_type_distribution(threats)
        
        trends = []
        
        # Severity trends
        if severity_dist.get('critical', 0) > 2:
            trends.append("⚠️ **ESCALATING**: Multiple critical threats detected")
        elif severity_dist.get('critical', 0) > 0:
            trends.append("🔴 **CRITICAL PRESENT**: At least one critical threat active")
        elif severity_dist.get('high', 0) > 3:
            trends.append("🟠 **ELEVATED**: Multiple high-severity threats")
        
        # Type trends
        most_common = type_dist.most_common(1)
        if most_common:
            threat_type, count = most_common[0]
            if count > 2:
                trends.append(f"🎯 **PATTERN**: {threat_type} threats appearing {count}x (repeat activity)")
        
        # Timeline trends
        if len(threats) > 0:
            time_diffs = []
            sorted_threats = sorted(threats, key=lambda x: x.get('timestamp', ''))
            for i in range(1, len(sorted_threats)):
                t1 = datetime.fromisoformat(sorted_threats[i-1].get('timestamp', datetime.utcnow().isoformat()))
                t2 = datetime.fromisoformat(sorted_threats[i].get('timestamp', datetime.utcnow().isoformat()))
                diff = (t2 - t1).total_seconds() / 60
                if diff < 30 and diff > 0:
                    time_diffs.append(diff)
            
            if time_diffs:
                avg_spacing = sum(time_diffs) / len(time_diffs)
                if avg_spacing < 15:
                    trends.append("⚡ **COORDINATED**: Threats appearing in rapid succession")
        
        return trends or ["📊 No significant trends detected"]
    
    def generate_recommendations(self, threats, guild):
        """Generate actionable recommendations"""
        if not threats:
            return ["✅ Continue monitoring", "🔐 Maintain security posture"]
        
        recs = []
        severity_dist = self.get_threat_severity_distribution(threats)
        type_dist = self.get_threat_type_distribution(threats)
        
        # Severity-based
        if severity_dist.get('critical', 0) > 0:
            recs.append("🚨 **URGENT**: Escalate critical threats immediately")
            recs.append("👥 Notify guild admins and security team")
        elif severity_dist.get('high', 0) > 0:
            recs.append("⚠️ Review and respond to high-severity threats")
            recs.append("📋 Document threat details for incident record")
        
        # Type-based
        if 'Suspicious User Activity' in type_dist:
            recs.append("🔍 Review recent user actions and audit logs")
        
        if 'Phishing Attempt' in type_dist:
            recs.append("🚫 Warn members about phishing links")
            recs.append("📢 Share phishing indicators in #announcements")
        
        if 'Unauthorized Access' in type_dist:
            recs.append("🔐 Reset potentially compromised credentials")
            recs.append("🛡️ Verify role permissions and 2FA status")
        
        if 'Mass Action' in type_dist:
            recs.append("⛔ Consider temporary lockdown on moderation actions")
            recs.append("👁️ Enable audit log monitoring")
        
        # General
        if len(threats) > 5:
            recs.append("📊 Begin incident investigation")
            recs.append("📝 Create incident case for tracking")
        
        return recs or ["✅ Continue routine monitoring"]
    
    async def _threatintel_logic(self, ctx):
        """Generate threat intelligence summary"""
        synthesis = self.get_threat_synthesis(ctx.guild.id)
        
        if not synthesis or synthesis['total'] == 0:
            embed = discord.Embed(
                title="🟢 Threat Intelligence Summary",
                description="**Status: ALL CLEAR**",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Detected Threats", value="0", inline=True)
            embed.add_field(name="Last 24 Hours", value="0", inline=True)
            embed.add_field(name="Assessment", value="✅ No active threats detected", inline=False)
            embed.set_footer(text="Sentinel Threat Intelligence System")
            await ctx.send(embed=embed)
            return
        
        # Generate analysis
        recent = synthesis['recent_24h']
        all_threats = synthesis['all_threats']
        recent_threat_objs = [t for t in all_threats if datetime.fromisoformat(t.get('timestamp', datetime.utcnow().isoformat())) > (datetime.utcnow() - timedelta(hours=24))]
        
        trends = self.generate_trend_analysis(recent_threat_objs)
        recs = self.generate_recommendations(recent_threat_objs, ctx.guild)
        
        # Determine severity color
        severity_dist = self.get_threat_severity_distribution(recent_threat_objs)
        if severity_dist.get('critical', 0) > 0:
            color = discord.Color.red()
            status = "🔴 CRITICAL"
        elif severity_dist.get('high', 0) > 0:
            color = discord.Color.orange()
            status = "🟠 HIGH"
        elif recent > 0:
            color = discord.Color.gold()
            status = "🟡 ELEVATED"
        else:
            color = discord.Color.green()
            status = "🟢 NORMAL"
        
        embed = discord.Embed(
            title=f"{status} Threat Intelligence Summary",
            description="Synthesized threat analysis and recommendations",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Total Threats (All Time)", value=f"`{synthesis['total']}`", inline=True)
        embed.add_field(name="Recent (24h)", value=f"`{recent}`", inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        
        # Type breakdown
        type_dist = self.get_threat_type_distribution(recent_threat_objs)
        if type_dist:
            type_str = "\n".join([f"• {k}: {v}x" for k, v in type_dist.most_common(3)])
            embed.add_field(name="🎯 Top Threat Types", value=type_str, inline=False)
        
        # Severity breakdown
        severity_str = f"🔴 Critical: {severity_dist.get('critical', 0)}\n🟠 High: {severity_dist.get('high', 0)}\n🟡 Medium: {severity_dist.get('medium', 0)}\n🟢 Low: {severity_dist.get('low', 0)}"
        embed.add_field(name="📊 Severity Distribution", value=severity_str, inline=False)
        
        # Trends
        trends_str = "\n".join([f"• {t}" for t in trends[:3]])
        embed.add_field(name="📈 Threat Trends", value=trends_str, inline=False)
        
        # Recommendations
        recs_str = "\n".join([f"• {r}" for r in recs[:3]])
        embed.add_field(name="💡 Recommendations", value=recs_str, inline=False)
        
        embed.set_footer(text="Sentinel Threat Intelligence | ML-powered synthesis")
        
        await ctx.send(embed=embed)
    
    async def _threatbrief_logic(self, ctx):
        """Generate executive threat briefing"""
        synthesis = self.get_threat_synthesis(ctx.guild.id)
        
        if not synthesis or synthesis['total'] == 0:
            await ctx.send("✅ **Executive Briefing**: No threats to report. Security posture is normal.")
            return
        
        recent = synthesis['recent_24h']
        all_threats = synthesis['all_threats']
        recent_threat_objs = [t for t in all_threats if datetime.fromisoformat(t.get('timestamp', datetime.utcnow().isoformat())) > (datetime.utcnow() - timedelta(hours=24))]
        
        severity_dist = self.get_threat_severity_distribution(recent_threat_objs)
        recs = self.generate_recommendations(recent_threat_objs, ctx.guild)
        
        # Executive briefing format
        brief = f"""
**📋 EXECUTIVE THREAT BRIEFING**
*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*

**Overview**
Total Threats: `{synthesis['total']}`
Last 24 Hours: `{recent}`
Critical: `{severity_dist.get('critical', 0)}` | High: `{severity_dist.get('high', 0)}`

**Key Findings**
"""
        
        if severity_dist.get('critical', 0) > 0:
            brief += "\n🔴 **CRITICAL ALERT**: Active critical-level threats require immediate attention"
        elif severity_dist.get('high', 0) > 0:
            brief += f"\n🟠 **ALERT**: {severity_dist.get('high', 0)} high-severity threat(s) detected"
        else:
            brief += "\n🟡 Security events detected; monitoring continues"
        
        brief += "\n\n**Recommended Actions**\n"
        for rec in recs[:3]:
            brief += f"\n• {rec}"
        
        brief += "\n\n📊 Use `/threatintel` for full analysis details"
        
        await ctx.send(brief)
    
    @commands.command(name='threatintel')
    async def threatintel_prefix(self, ctx):
        """Generate threat intelligence summary - Prefix command"""
        await self._threatintel_logic(ctx)
    
    @commands.command(name='threatbrief')
    async def threatbrief_prefix(self, ctx):
        """Generate executive threat briefing - Prefix command"""
        await self._threatbrief_logic(ctx)

async def setup(bot):
    await bot.add_cog(ThreatIntelligenceSynthesizer(bot))
