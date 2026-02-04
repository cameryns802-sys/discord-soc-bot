"""
Dependency Threat Monitor
Monitors dependencies for CVEs with vendor risk escalation
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class DependencyThreatMonitorCog(commands.Cog):
    """Dependency Threat Monitor - Tracks CVEs and security issues in dependencies"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/dependencies"
        os.makedirs(self.data_dir, exist_ok=True)
        self.deps_file = os.path.join(self.data_dir, "dependencies.json")
        self.cves_file = os.path.join(self.data_dir, "cves.json")
        self.dependencies = self.load_dependencies()
        self.cves = self.load_cves()
        
    def load_dependencies(self):
        if os.path.exists(self.deps_file):
            with open(self.deps_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_dependencies(self):
        with open(self.deps_file, 'w') as f:
            json.dump(self.dependencies, f, indent=4)
    
    def load_cves(self):
        if os.path.exists(self.cves_file):
            with open(self.cves_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_cves(self):
        with open(self.cves_file, 'w') as f:
            json.dump(self.cves, f, indent=4)
    
    @commands.command(name="dep_add")
    @commands.has_permissions(administrator=True)
    async def add_dependency(self, ctx, package_name: str, version: str, *, description: str = ""):
        """Add dependency to monitoring\nUsage: !dep_add <package> <version> [description]"""
        dependency = {
            "id": len(self.dependencies) + 1,
            "package": package_name,
            "version": version,
            "description": description,
            "added_at": get_now_pst().isoformat(),
            "added_by": str(ctx.author.id),
            "cve_count": 0,
            "status": "active"
        }
        
        self.dependencies.append(dependency)
        self.save_dependencies()
        
        embed = discord.Embed(title="✅ Dependency Added", color=discord.Color.green(), timestamp=get_now_pst())
        embed.add_field(name="Dependency ID", value=f"#{dependency['id']}", inline=True)
        embed.add_field(name="Package", value=package_name, inline=True)
        embed.add_field(name="Version", value=version, inline=True)
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="dep_cve")
    @commands.has_permissions(administrator=True)
    async def report_cve(self, ctx, dep_id: int, cve_id: str, severity: str, *, description: str):
        """Report CVE for dependency\nUsage: !dep_cve <dep_id> <CVE-YYYY-XXXXX> <critical|high|medium|low> <description>"""
        dependency = next((d for d in self.dependencies if d["id"] == dep_id), None)
        if not dependency:
            await ctx.send(f"❌ Dependency #{dep_id} not found")
            return
        
        cve = {
            "id": len(self.cves) + 1,
            "cve_id": cve_id,
            "dependency_id": dep_id,
            "package": dependency["package"],
            "version": dependency["version"],
            "severity": severity.lower(),
            "description": description,
            "reported_at": get_now_pst().isoformat(),
            "reported_by": str(ctx.author.id),
            "status": "open",
            "patched": False
        }
        
        self.cves.append(cve)
        dependency["cve_count"] += 1
        self.save_cves()
        self.save_dependencies()
        
        color_map = {"critical": discord.Color.dark_red(), "high": discord.Color.red(), "medium": discord.Color.gold(), "low": discord.Color.green()}
        embed = discord.Embed(title="🚨 CVE Reported", color=color_map.get(severity.lower(), discord.Color.blue()), timestamp=get_now_pst())
        embed.add_field(name="CVE ID", value=cve_id, inline=True)
        embed.add_field(name="Package", value=dependency["package"], inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="⚠️ Status", value="OPEN - Requires Remediation", inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="dep_scan")
    @commands.has_permissions(administrator=True)
    async def scan_dependencies(self, ctx):
        """Scan dependencies for vulnerabilities\nUsage: !dep_scan"""
        if not self.dependencies:
            await ctx.send("📊 No dependencies to scan")
            return
        
        vulnerable_deps = [d for d in self.dependencies if d["cve_count"] > 0]
        critical_cves = [c for c in self.cves if c.get("severity") == "critical" and not c.get("patched", False)]
        high_cves = [c for c in self.cves if c.get("severity") == "high" and not c.get("patched", False)]
        
        embed = discord.Embed(title="🔍 Dependency Vulnerability Scan", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="📦 Total Dependencies", value=len(self.dependencies), inline=True)
        embed.add_field(name="⚠️ Vulnerable", value=len(vulnerable_deps), inline=True)
        embed.add_field(name="🚨 Critical CVEs", value=len(critical_cves), inline=True)
        embed.add_field(name="🔴 High CVEs", value=len(high_cves), inline=True)
        embed.add_field(name="📋 Total CVEs", value=len(self.cves), inline=True)
        
        if vulnerable_deps:
            vuln_text = "\n".join([f"• {d['package']} v{d['version']} - {d['cve_count']} CVEs" for d in vulnerable_deps[:5]])
            embed.add_field(name="Most Vulnerable Dependencies", value=vuln_text, inline=False)
        
        if critical_cves:
            embed.add_field(name="⚠️ Action Required", value=f"{len(critical_cves)} critical CVEs need immediate patching", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="dep_cves")
    @commands.has_permissions(administrator=True)
    async def list_cves(self, ctx, severity: str = None):
        """List CVEs by severity\nUsage: !dep_cves [critical|high|medium|low]"""
        if not self.cves:
            await ctx.send("📋 No CVEs reported")
            return
        
        if severity:
            filtered_cves = [c for c in self.cves if c.get("severity") == severity.lower()]
        else:
            filtered_cves = self.cves
        
        open_cves = [c for c in filtered_cves if c.get("status") == "open"]
        
        embed = discord.Embed(title=f"🚨 CVE List{' - ' + severity.upper() if severity else ''}", color=discord.Color.red(), timestamp=get_now_pst())
        
        for cve in open_cves[:10]:
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            emoji = severity_emoji.get(cve["severity"], "⚪")
            embed.add_field(name=f"{emoji} {cve['cve_id']} - {cve['package']}", value=f"Severity: {cve['severity'].upper()} | Version: {cve['version']}", inline=False)
        
        embed.add_field(name="Total Open CVEs", value=len(open_cves), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="dep_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View dependency monitoring dashboard\nUsage: !dep_dashboard"""
        total_deps = len(self.dependencies)
        total_cves = len(self.cves)
        open_cves = len([c for c in self.cves if c.get("status") == "open"])
        critical_cves = len([c for c in self.cves if c.get("severity") == "critical" and not c.get("patched", False)])
        
        embed = discord.Embed(title="📦 Dependency Threat Monitor Dashboard", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="📊 Tracked Dependencies", value=total_deps, inline=True)
        embed.add_field(name="🚨 Total CVEs", value=total_cves, inline=True)
        embed.add_field(name="⚠️ Open CVEs", value=open_cves, inline=True)
        embed.add_field(name="🔴 Critical Unpatched", value=critical_cves, inline=True)
        
        status = "🟢 SECURE" if critical_cves == 0 else "🟡 MONITOR" if critical_cves < 3 else "🔴 CRITICAL"
        embed.add_field(name="Security Status", value=status, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DependencyThreatMonitorCog(bot))
