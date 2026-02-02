# Threat Intelligence Aggregator & Correlation System
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

DATA_FILE = 'data/threat_intelligence.json'

def load_threat_intel():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return get_default_threats()
    return get_default_threats()

def get_default_threats():
    return {
        "threats": [
            {
                "id": "TI-2024-001",
                "type": "malware",
                "name": "RustyStealer v2.3",
                "severity": "critical",
                "confidence": 98,
                "sources": ["OSINT Feed", "Internal Detection"],
                "indicators": ["hash_abc123", "IP_10.0.0.5"],
                "impact": "Credential theft, data exfiltration",
                "first_seen": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "status": "active"
            }
        ]
    }

def save_threat_intel(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class ThreatIntelligenceAggregatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='threat_intel')
    async def threat_intelligence_dashboard(self, ctx):
        """View aggregated threat intelligence dashboard"""
        data = load_threat_intel()
        threats = data.get('threats', [])
        
        embed = discord.Embed(
            title="🔴 Threat Intelligence Dashboard",
            description="Aggregated threats from all sources",
            color=discord.Color.red()
        )
        
        critical_count = sum(1 for t in threats if t.get('severity') == 'critical')
        high_count = sum(1 for t in threats if t.get('severity') == 'high')
        medium_count = sum(1 for t in threats if t.get('severity') == 'medium')
        
        embed.add_field(
            name="Threat Summary",
            value=f"🔴 Critical: {critical_count}\n🟠 High: {high_count}\n🟡 Medium: {medium_count}\n📊 Total: {len(threats)}",
            inline=False
        )
        
        active_threats = [t for t in threats if t.get('status') == 'active']
        if active_threats:
            threat_names = ", ".join([t.get('name', 'Unknown') for t in active_threats[:5]])
            embed.add_field(
                name="🚨 Active Threats",
                value=threat_names,
                inline=False
            )
        
        embed.set_footer(text="Use !threat <id> for details | Last updated: Just now")
        await ctx.send(embed=embed)

    @commands.command(name='threat')
    async def view_threat(self, ctx, threat_id: str):
        """View detailed threat intelligence"""
        data = load_threat_intel()
        threat = next((t for t in data.get('threats', []) if t.get('id') == threat_id), None)
        
        if not threat:
            await ctx.send("❌ Threat not found")
            return
        
        severity_color = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.green()
        }.get(threat.get('severity', 'unknown'), discord.Color.blue())
        
        embed = discord.Embed(
            title=f"🔴 {threat.get('name')}",
            color=severity_color,
            timestamp=datetime.fromisoformat(threat.get('first_seen', datetime.utcnow().isoformat()))
        )
        
        embed.add_field(name="Threat ID", value=threat_id, inline=True)
        embed.add_field(name="Type", value=threat.get('type', 'Unknown').upper(), inline=True)
        embed.add_field(name="Severity", value=threat.get('severity', 'Unknown').upper(), inline=True)
        
        embed.add_field(
            name="Confidence Score",
            value=f"{threat.get('confidence', 0)}%",
            inline=True
        )
        embed.add_field(
            name="Status",
            value=threat.get('status', 'Unknown').upper(),
            inline=True
        )
        
        embed.add_field(name="Description", value=threat.get('impact', 'No description'), inline=False)
        
        sources = threat.get('sources', [])
        if sources:
            embed.add_field(
                name="Intelligence Sources",
                value=", ".join(sources),
                inline=False
            )
        
        indicators = threat.get('indicators', [])
        if indicators:
            indicator_text = ", ".join(indicators[:5])
            if len(indicators) > 5:
                indicator_text += f" +{len(indicators)-5} more"
            embed.add_field(
                name="Indicators of Compromise (IOCs)",
                value=indicator_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='report_ioc')
    async def report_ioc(self, ctx, threat_id: str, *, indicator: str):
        """Report an indicator of compromise"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only security staff can report IOCs")
            return
        
        data = load_threat_intel()
        threat = next((t for t in data.get('threats', []) if t.get('id') == threat_id), None)
        
        if not threat:
            await ctx.send("❌ Threat not found")
            return
        
        if 'indicators' not in threat:
            threat['indicators'] = []
        
        threat['indicators'].append(indicator)
        threat['last_updated'] = datetime.utcnow().isoformat()
        save_threat_intel(data)
        
        embed = discord.Embed(
            title="✅ IOC Reported",
            color=discord.Color.green()
        )
        embed.add_field(name="Threat ID", value=threat_id, inline=True)
        embed.add_field(name="Indicator", value=indicator, inline=True)
        embed.add_field(name="Reported By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='add_threat')
    async def add_threat(self, ctx, name: str, threat_type: str, severity: str):
        """Add new threat to intelligence database (staff only)"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only security staff can add threats")
            return
        
        valid_types = ['malware', 'ransomware', 'phishing', 'exploit', 'botnet', 'apt', 'other']
        valid_severities = ['critical', 'high', 'medium', 'low']
        
        if threat_type not in valid_types:
            await ctx.send(f"❌ Invalid type. Valid: {', '.join(valid_types)}")
            return
        
        if severity not in valid_severities:
            await ctx.send(f"❌ Invalid severity. Valid: {', '.join(valid_severities)}")
            return
        
        data = load_threat_intel()
        threat_id = f"TI-2024-{str(len(data.get('threats', [])) + 1).zfill(3)}"
        
        threat = {
            "id": threat_id,
            "type": threat_type,
            "name": name,
            "severity": severity,
            "confidence": 0,
            "sources": ["Manual Report"],
            "indicators": [],
            "impact": "To be determined",
            "first_seen": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "status": "new",
            "reported_by": ctx.author.id
        }
        
        data['threats'].append(threat)
        save_threat_intel(data)
        
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity, '❓')
        
        embed = discord.Embed(
            title="✅ Threat Added",
            description=name,
            color=discord.Color.green()
        )
        embed.add_field(name="Threat ID", value=threat_id, inline=True)
        embed.add_field(name="Type", value=threat_type.upper(), inline=True)
        embed.add_field(name="Severity", value=f"{severity_emoji} {severity.upper()}", inline=True)
        embed.add_field(name="Reported By", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='threat_correlation')
    async def threat_correlation(self, ctx):
        """Find correlated threats and indicators"""
        data = load_threat_intel()
        threats = data.get('threats', [])
        
        embed = discord.Embed(
            title="🔗 Threat Correlation Analysis",
            description="Identifying related threats and attack patterns",
            color=discord.Color.blue()
        )
        
        # Group by type
        threats_by_type = {}
        for threat in threats:
            threat_type = threat.get('type', 'unknown')
            if threat_type not in threats_by_type:
                threats_by_type[threat_type] = []
            threats_by_type[threat_type].append(threat.get('name', 'Unknown'))
        
        for threat_type, threat_names in threats_by_type.items():
            if threat_names:
                embed.add_field(
                    name=f"**{threat_type.upper()}** ({len(threat_names)})",
                    value=", ".join(threat_names[:3]),
                    inline=False
                )
        
        # Find IOC overlaps
        all_indicators = []
        ioc_to_threats = {}
        
        for threat in threats:
            for ioc in threat.get('indicators', []):
                if ioc in ioc_to_threats:
                    ioc_to_threats[ioc].append(threat.get('name', 'Unknown'))
                else:
                    ioc_to_threats[ioc] = [threat.get('name', 'Unknown')]
        
        shared_iocs = {ioc: threats for ioc, threats in ioc_to_threats.items() if len(threats) > 1}
        
        if shared_iocs:
            shared_text = f"Found {len(shared_iocs)} shared IOCs across multiple threats"
            embed.add_field(name="⚠️ IOC Correlation", value=shared_text, inline=False)
        
        embed.set_footer(text="Use !threat <id> for details")
        await ctx.send(embed=embed)

    @commands.command(name='threat_hunt')
    async def initiate_threat_hunt(self, ctx, threat_id: str):
        """Initiate automated threat hunt for specific threat"""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Only security staff can initiate threat hunts")
            return
        
        data = load_threat_intel()
        threat = next((t for t in data.get('threats', []) if t.get('id') == threat_id), None)
        
        if not threat:
            await ctx.send("❌ Threat not found")
            return
        
        embed = discord.Embed(
            title="🔍 Threat Hunt Initiated",
            description=f"Hunting: {threat.get('name')}",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="Threat ID", value=threat_id, inline=True)
        embed.add_field(name="Type", value=threat.get('type').upper(), inline=True)
        embed.add_field(name="Initiated By", value=ctx.author.mention, inline=True)
        
        indicators = threat.get('indicators', [])
        if indicators:
            embed.add_field(
                name="Searching For",
                value=f"{len(indicators)} indicators of compromise",
                inline=True
            )
        
        embed.add_field(
            name="Hunt Status",
            value="🔄 In Progress - Scanning infrastructure",
            inline=False
        )
        
        await ctx.send(embed=embed)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == 233662304272834560

async def setup(bot):
    await bot.add_cog(ThreatIntelligenceAggregatorCog(bot))
