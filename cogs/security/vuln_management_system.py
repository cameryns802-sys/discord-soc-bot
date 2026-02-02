"""
Vulnerability Management System - Track and manage security vulnerabilities for Sentinel
Vulnerability tracking, risk assessment, patching workflow, and remediation management
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class VulnerabilityManagementSystem(commands.Cog):
    """Vulnerability tracking and remediation management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.vuln_file = 'data/vulnerabilities.json'
        self.load_vulnerabilities()
    
    def load_vulnerabilities(self):
        """Load vulnerabilities"""
        if not os.path.exists(self.vuln_file):
            os.makedirs(os.path.dirname(self.vuln_file), exist_ok=True)
            with open(self.vuln_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_vulns(self, guild_id):
        """Get vulnerabilities for guild"""
        with open(self.vuln_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_vulns(self, guild_id, vulns):
        """Save vulnerabilities"""
        with open(self.vuln_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = vulns
        with open(self.vuln_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_cvss_score(self, severity):
        """Simulate CVSS score based on severity"""
        score_map = {
            'critical': (9.0, 10.0),
            'high': (7.0, 8.9),
            'medium': (4.0, 6.9),
            'low': (0.1, 3.9)
        }
        return score_map.get(severity, (0.0, 0.0))
    
    def create_vulnerability(self, guild_id, title, description, severity, affected_system, reporter):
        """Create new vulnerability"""
        vulns = self.get_guild_vulns(guild_id)
        
        vuln_id = f"VULN-{str(uuid.uuid4())[:8].upper()}"
        cvss_range = self.calculate_cvss_score(severity)
        
        vuln = {
            'id': vuln_id,
            'title': title,
            'description': description,
            'severity': severity.lower(),
            'cvss_score': f"{cvss_range[0]}-{cvss_range[1]}",
            'affected_system': affected_system,
            'status': 'open',
            'reported_at': datetime.utcnow().isoformat(),
            'reported_by': reporter,
            'assigned_to': None,
            'patched': False,
            'patched_at': None,
            'verified': False,
            'notes': [],
            'cve_id': None
        }
        
        vulns[vuln_id] = vuln
        self.save_vulns(guild_id, vulns)
        return vuln
    
    async def _vulncreate_logic(self, ctx, severity: str, affected_system: str, *, description: str):
        """Create vulnerability record"""
        valid_severities = ['critical', 'high', 'medium', 'low']
        
        if severity.lower() not in valid_severities:
            await ctx.send(f"❌ Invalid severity. Use: {', '.join(valid_severities)}")
            return
        
        parts = description.split('|')
        if len(parts) < 2:
            await ctx.send("Usage: `!vulncreate <severity> <system> <title> | <description>`")
            return
        
        title = parts[0].strip()
        desc = parts[1].strip()
        
        vuln = self.create_vulnerability(ctx.guild.id, title, desc, severity, affected_system, ctx.author.id)
        
        severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity.lower(), '❓')
        severity_color = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.yellow()
        }.get(severity.lower(), discord.Color.greyple())
        
        embed = discord.Embed(
            title=f"{severity_emoji} Vulnerability Created",
            description=f"**{title}**",
            color=severity_color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Vulnerability ID", value=f"`{vuln['id']}`", inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="CVSS Score", value=vuln['cvss_score'], inline=True)
        embed.add_field(name="Affected System", value=affected_system, inline=True)
        embed.add_field(name="Status", value="🟢 OPEN", inline=True)
        embed.add_field(name="Reported By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Description", value=desc, inline=False)
        embed.set_footer(text="Sentinel Vulnerability Management")
        
        await ctx.send(embed=embed)
    
    async def _vulnlist_logic(self, ctx, status: str = 'open'):
        """List vulnerabilities"""
        vulns = self.get_guild_vulns(ctx.guild.id)
        
        filtered = {k: v for k, v in vulns.items() if v['status'].lower() == status.lower()}
        
        if not filtered:
            await ctx.send(f"📋 No **{status.upper()}** vulnerabilities found.")
            return
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_vulns = sorted(filtered.values(), key=lambda v: severity_order.get(v['severity'], 4))
        
        embed = discord.Embed(
            title=f"🔒 {status.upper()} Vulnerabilities",
            description=f"{len(sorted_vulns)} vulnerability(ies)",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for vuln in sorted_vulns[:10]:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(vuln['severity'], '❓')
            patch_status = "✅ Patched" if vuln['patched'] else "❌ Unpatched"
            
            embed.add_field(
                name=f"{severity_emoji} {vuln['title']} ({vuln['id']})",
                value=f"System: {vuln['affected_system']}\nCVSS: {vuln['cvss_score']} | {patch_status}",
                inline=False
            )
        
        if len(sorted_vulns) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_vulns) - 10} additional vulnerabilities", inline=False)
        
        embed.set_footer(text="Use !vulndetail <id> for full details")
        
        await ctx.send(embed=embed)
    
    async def _vulnstats_logic(self, ctx):
        """Show vulnerability statistics"""
        vulns = self.get_guild_vulns(ctx.guild.id)
        
        if not vulns:
            await ctx.send("📊 No vulnerabilities tracked yet.")
            return
        
        # Calculate stats
        total = len(vulns)
        by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        by_status = {'open': 0, 'patched': 0, 'closed': 0}
        patched_count = 0
        unpatched_count = 0
        
        for vuln in vulns.values():
            by_severity[vuln['severity']] = by_severity.get(vuln['severity'], 0) + 1
            by_status[vuln['status']] = by_status.get(vuln['status'], 0) + 1
            if vuln['patched']:
                patched_count += 1
            else:
                unpatched_count += 1
        
        # Calculate risk score
        risk_score = (by_severity['critical'] * 10) + (by_severity['high'] * 5) + (by_severity['medium'] * 2) + by_severity['low']
        
        embed = discord.Embed(
            title="📊 Vulnerability Statistics",
            description=f"Total: {total} | Risk Score: {risk_score}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        severity_str = f"🔴 Critical: {by_severity['critical']}\n🟠 High: {by_severity['high']}\n🟡 Medium: {by_severity['medium']}\n🟢 Low: {by_severity['low']}"
        embed.add_field(name="📈 By Severity", value=severity_str, inline=True)
        
        status_str = f"🟢 Open: {by_status.get('open', 0)}\n✅ Patched: {by_status.get('patched', 0)}\n🔒 Closed: {by_status.get('closed', 0)}"
        embed.add_field(name="📊 By Status", value=status_str, inline=True)
        
        patch_str = f"✅ Patched: {patched_count}\n❌ Unpatched: {unpatched_count}\nPatch Rate: {(patched_count/total*100):.0f}%"
        embed.add_field(name="🔧 Patching", value=patch_str, inline=True)
        
        embed.set_footer(text="Sentinel Vulnerability Management | Current snapshot")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='vulncreate')
    async def vulncreate_prefix(self, ctx, severity: str, affected_system: str, *, description: str):
        """Create vulnerability - Prefix command"""
        await self._vulncreate_logic(ctx, severity, affected_system, description=description)
    
    @commands.command(name='vulnlist')
    async def vulnlist_prefix(self, ctx, status: str = 'open'):
        """List vulnerabilities - Prefix command"""
        await self._vulnlist_logic(ctx, status)
    
    @commands.command(name='vulnstats')
    async def vulnstats_prefix(self, ctx):
        """Show vulnerability stats - Prefix command"""
        await self._vulnstats_logic(ctx)

async def setup(bot):
    await bot.add_cog(VulnerabilityManagementSystem(bot))
