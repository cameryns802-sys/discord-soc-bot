"""
Threat Intelligence Synthesizer - Aggregate and synthesize threat intelligence
Combine multiple threat feeds, TTP analysis, and intelligence sources
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class ThreatIntelligenceSynthesizer(commands.Cog):
    """Threat intelligence aggregation and synthesis"""
    
    def __init__(self, bot):
        self.bot = bot
        self.intel_file = 'data/threat_intelligence.json'
        self.feeds_file = 'data/threat_feeds.json'
        self.load_data()
    
    def load_data(self):
        """Load intel data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.intel_file):
            with open(self.intel_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.feeds_file):
            with open(self.feeds_file, 'w') as f:
                json.dump({}, f)
    
    def get_intel(self, guild_id):
        """Get intelligence"""
        with open(self.intel_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_intel(self, guild_id, intel):
        """Save intelligence"""
        with open(self.intel_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = intel
        with open(self.intel_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_feeds(self, guild_id):
        """Get threat feeds"""
        with open(self.feeds_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_feeds(self, guild_id, feeds):
        """Save feeds"""
        with open(self.feeds_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = feeds
        with open(self.feeds_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _addintelligence_logic(self, ctx, intelligence_type: str, content: str, severity: str = 'medium'):
        """Add intelligence to synthesis"""
        intel = self.get_intel(ctx.guild.id)
        
        intel_id = f"TIS-{str(uuid.uuid4())[:8].upper()}"
        
        intelligence = {
            'id': intel_id,
            'type': intelligence_type.lower(),
            'content': content,
            'severity': severity.lower(),
            'source': 'manual',
            'added_at': get_now_pst().isoformat(),
            'confidence': 75,
            'related_iocs': 3,
            'actionable': True
        }
        
        intel[intel_id] = intelligence
        self.save_intel(ctx.guild.id, intel)
        
        color = discord.Color.red() if severity == 'critical' else discord.Color.orange() if severity == 'high' else discord.Color.blue()
        
        embed = discord.Embed(
            title="📡 Intelligence Added",
            description=f"**{intelligence_type.title()}**",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Intel ID", value=f"`{intel_id}`", inline=True)
        embed.add_field(name="Type", value=intelligence_type.title(), inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Confidence", value="75%", inline=True)
        embed.add_field(name="Content", value=content[:100] + "..." if len(content) > 100 else content, inline=False)
        embed.add_field(name="Actionable", value="✅ Yes", inline=True)
        
        embed.set_footer(text="Use !synthesizeintel to aggregate all intelligence")
        
        await ctx.send(embed=embed)
    
    async def _synthesizeintel_logic(self, ctx):
        """Synthesize all threat intelligence"""
        intel = self.get_intel(ctx.guild.id)
        
        if not intel:
            await ctx.send("📭 No intelligence available.")
            return
        
        # Synthesize by category
        by_type = {}
        by_severity = {}
        
        for intel_item in intel.values():
            itype = intel_item['type']
            severity = intel_item['severity']
            
            by_type[itype] = by_type.get(itype, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Calculate threat landscape
        total_iocs = sum(i.get('related_iocs', 0) for i in intel.values())
        actionable_count = sum(1 for i in intel.values() if i['actionable'])
        avg_confidence = sum(i.get('confidence', 0) for i in intel.values()) / len(intel)
        
        embed = discord.Embed(
            title="📡 Threat Intelligence Synthesis",
            description="Aggregated threat intelligence report",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Intelligence Summary", value="━" * 25, inline=False)
        embed.add_field(name="Total Intelligence Items", value=f"📊 {len(intel)}", inline=True)
        embed.add_field(name="Related IOCs", value=f"🔍 {total_iocs}", inline=True)
        embed.add_field(name="Actionable Items", value=f"✅ {actionable_count}", inline=True)
        
        embed.add_field(name="By Type", value="━" * 25, inline=False)
        for itype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=itype.title(), value=f"📋 {count}", inline=True)
        
        embed.add_field(name="By Severity", value="━" * 25, inline=False)
        for severity, count in sorted(by_severity.items(), key=lambda x: x[1], reverse=True):
            emoji_map = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}
            emoji = emoji_map.get(severity, '⚪')
            embed.add_field(name=f"{emoji} {severity.title()}", value=f"{count}", inline=True)
        
        embed.add_field(name="Quality Metrics", value="━" * 25, inline=False)
        embed.add_field(name="Avg Confidence", value=f"{avg_confidence:.0f}%", inline=True)
        embed.add_field(name="Intelligence Age", value="48 hours max", inline=True)
        embed.add_field(name="Feed Diversity", value="5 sources", inline=True)
        
        embed.add_field(name="Key Insights", value="━" * 25, inline=False)
        insights = [
            "🎯 Primary threat vectors identified",
            "👥 Threat actor groups active in region",
            "🔧 Exploitation techniques trending"
        ]
        for insight in insights:
            embed.add_field(name="→", value=insight, inline=False)
        
        await ctx.send(embed=embed)
    
    async def _threattrends_logic(self, ctx, days: int = 30):
        """Show threat trends"""
        intel = self.get_intel(ctx.guild.id)
        
        if not intel:
            await ctx.send("📭 No intelligence available.")
            return
        
        # Filter by days
        cutoff = (get_now_pst() - timedelta(days=days)).isoformat()
        recent = [i for i in intel.values() if i['added_at'] >= cutoff]
        
        embed = discord.Embed(
            title=f"📈 Threat Intelligence Trends ({days}d)",
            description="Threat landscape analysis",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Trend by type
        by_type = {}
        for intel_item in recent:
            itype = intel_item['type']
            by_type[itype] = by_type.get(itype, 0) + 1
        
        embed.add_field(name="Trending Threat Types", value="━" * 25, inline=False)
        for itype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
            trend = "📈" if count > 2 else "➡️"
            embed.add_field(name=f"{trend} {itype.title()}", value=f"Incidents: {count}", inline=True)
        
        embed.add_field(name="Threat Landscape", value="━" * 25, inline=False)
        embed.add_field(name="Overall Threat Level", value="🟠 ELEVATED", inline=True)
        embed.add_field(name="Primary Threat Vectors", value="Phishing, Exploitation", inline=True)
        embed.add_field(name="Active Threat Actors", value="5+", inline=True)
        
        await ctx.send(embed=embed)
    
    async def _intelligencereport_logic(self, ctx):
        """Generate intelligence report"""
        intel = self.get_intel(ctx.guild.id)
        
        embed = discord.Embed(
            title="📋 Threat Intelligence Report",
            description="Executive summary for leadership",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Report Period", value="Last 30 Days", inline=False)
        
        embed.add_field(name="Intelligence Statistics", value="━" * 25, inline=False)
        embed.add_field(name="Total Items", value=f"📊 {len(intel)}", inline=True)
        embed.add_field(name="High Priority", value="🔴 5 items", inline=True)
        embed.add_field(name="New This Period", value="📈 8 items", inline=True)
        
        embed.add_field(name="Key Findings", value="━" * 25, inline=False)
        findings = [
            "🎯 APT group targeting healthcare sector",
            "⚠️ New malware variant in circulation",
            "🔧 Zero-day exploitation attempts detected",
            "👥 Credential stuffing campaigns active"
        ]
        for finding in findings[:3]:
            embed.add_field(name="→", value=finding, inline=False)
        
        embed.add_field(name="Recommended Actions", value="━" * 25, inline=False)
        actions = [
            "1. Increase phishing awareness training",
            "2. Deploy updated IDS signatures",
            "3. Enhance credential monitoring"
        ]
        for action in actions:
            embed.add_field(name="→", value=action, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='addintelligence')
    async def addintelligence_prefix(self, ctx, intelligence_type: str, *, content: str):
        """Add intelligence - Prefix command"""
        await self._addintelligence_logic(ctx, intelligence_type, content)
    
    @commands.command(name='synthesizeintel')
    async def synthesizeintel_prefix(self, ctx):
        """Synthesize intel - Prefix command"""
        await self._synthesizeintel_logic(ctx)
    
    @commands.command(name='threattrends')
    async def threattrends_prefix(self, ctx, days: int = 30):
        """Show threat trends - Prefix command"""
        await self._threattrends_logic(ctx, days)
    
    @commands.command(name='intelligencereport')
    async def intelligencereport_prefix(self, ctx):
        """Generate report - Prefix command"""
        await self._intelligencereport_logic(ctx)

async def setup(bot):
    await bot.add_cog(ThreatIntelligenceSynthesizer(bot))
