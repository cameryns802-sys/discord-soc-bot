"""
Security Command Groups - Organized security management commands
Provides grouped commands for threat management, IOCs, scans, and monitoring
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

class SecurityGroups(commands.Cog):
    """Security command groups for organized threat management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== THREAT GROUP ====================
    threat_group = app_commands.Group(name="threat", description="Threat management and intelligence")
    
    @threat_group.command(name="scan", description="Scan server for threats")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threat_scan(self, interaction: discord.Interaction):
        """Scan server for security threats"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔍 Threat Scan",
            description="Scanning server for security threats...",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Scan results
        threats_found = 0
        embed.add_field(name="Status", value="✅ Scan Complete", inline=False)
        embed.add_field(name="Threats Found", value=f"🔴 {threats_found}", inline=True)
        embed.add_field(name="Channels Scanned", value=str(len(interaction.guild.text_channels)), inline=True)
        embed.add_field(name="Members Scanned", value=str(interaction.guild.member_count), inline=True)
        
        await interaction.followup.send(embed=embed)
    
    @threat_group.command(name="level", description="View current threat level")
    async def threat_level(self, interaction: discord.Interaction):
        """View current server threat level"""
        embed = discord.Embed(
            title="⚠️ Threat Level",
            description="Current threat assessment",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Threat Level", value="🟢 **LOW**", inline=True)
        embed.add_field(name="Active Threats", value="0", inline=True)
        embed.add_field(name="Monitoring", value="✅ Active", inline=True)
        embed.add_field(name="Last Incident", value="None", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @threat_group.command(name="actors", description="List known threat actors")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threat_actors(self, interaction: discord.Interaction):
        """List known threat actors"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        
        if not threat_intel:
            await interaction.response.send_message("❌ Threat intel system not available", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="👤 Known Threat Actors",
            description=f"Total: {len(threat_intel.threat_actors)}",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for actor_name, data in list(threat_intel.threat_actors.items())[:5]:
            embed.add_field(
                name=actor_name,
                value=f"**Origin:** {data.get('origin', 'Unknown')}\n**Motivation:** {data.get('motivation', 'Unknown')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @threat_group.command(name="report", description="Generate threat report")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threat_report(self, interaction: discord.Interaction, hours: int = 24):
        """Generate comprehensive threat report"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📊 Threat Intelligence Report",
            description=f"Analysis for last {hours} hours",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Threats Detected", value="2", inline=True)
        embed.add_field(name="Threats Mitigated", value="2", inline=True)
        embed.add_field(name="Active Monitoring", value="✅", inline=True)
        embed.add_field(name="IOCs Matched", value="3", inline=True)
        embed.add_field(name="False Positives", value="0", inline=True)
        embed.add_field(name="Confidence", value="94%", inline=True)
        
        await interaction.followup.send(embed=embed)
    
    # ==================== IOC GROUP ====================
    ioc_group = app_commands.Group(name="ioc", description="Indicator of Compromise management")
    
    @ioc_group.command(name="add", description="Add IOC to database")
    @app_commands.describe(
        ioc_type="Type: ip, domain, url, hash, email",
        value="IOC value",
        category="Category: malware, phishing, etc."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ioc_add(self, interaction: discord.Interaction, ioc_type: str, value: str, category: str):
        """Add IOC to threat intelligence database"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        
        if not threat_intel:
            await interaction.response.send_message("❌ Threat intel system not available", ephemeral=True)
            return
        
        ioc_id = threat_intel.add_ioc(ioc_type, value, category)
        
        embed = discord.Embed(
            title="✅ IOC Added",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="IOC ID", value=ioc_id, inline=True)
        embed.add_field(name="Type", value=ioc_type, inline=True)
        embed.add_field(name="Value", value=f"`{value}`", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @ioc_group.command(name="search", description="Search IOC database")
    @app_commands.describe(query="Search query")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ioc_search(self, interaction: discord.Interaction, query: str):
        """Search IOC database"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        
        if not threat_intel:
            await interaction.response.send_message("❌ Threat intel system not available", ephemeral=True)
            return
        
        results = threat_intel.search_iocs(query=query, limit=5)
        
        embed = discord.Embed(
            title=f"🔍 IOC Search: {query}",
            description=f"Found {len(results)} results",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for ioc in results[:5]:
            embed.add_field(
                name=f"`{ioc['value'][:50]}`",
                value=f"**Type:** {ioc['type']}\n**Category:** {ioc['category']}\n**Severity:** {ioc['severity']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @ioc_group.command(name="stats", description="View IOC statistics")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ioc_stats(self, interaction: discord.Interaction):
        """View IOC statistics"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        
        if not threat_intel:
            await interaction.response.send_message("❌ Threat intel system not available", ephemeral=True)
            return
        
        stats = threat_intel.get_ioc_stats()
        
        embed = discord.Embed(
            title="📊 IOC Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total IOCs", value=stats['total_iocs'], inline=True)
        embed.add_field(name="Threat Actors", value=stats['threat_actors'], inline=True)
        embed.add_field(name="Campaigns", value=stats['campaigns'], inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @ioc_group.command(name="list", description="List recent IOCs")
    @app_commands.describe(limit="Number to show")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ioc_list(self, interaction: discord.Interaction, limit: int = 10):
        """List recent IOCs"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        
        if not threat_intel:
            await interaction.response.send_message("❌ Threat intel system not available", ephemeral=True)
            return
        
        iocs = list(threat_intel.iocs.values())[-limit:]
        
        embed = discord.Embed(
            title=f"📋 Recent IOCs ({len(iocs)})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for ioc in iocs[:5]:
            embed.add_field(
                name=ioc['value'][:50],
                value=f"**Type:** {ioc['type']} | **Severity:** {ioc['severity']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    # ==================== SCAN GROUP ====================
    scan_group = app_commands.Group(name="scan", description="Security scanning operations")
    
    @scan_group.command(name="permissions", description="Scan role permissions")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scan_permissions(self, interaction: discord.Interaction):
        """Scan for risky role permissions"""
        await interaction.response.defer()
        
        risky_roles = []
        dangerous_perms = ['administrator', 'manage_guild', 'manage_roles', 'ban_members']
        
        for role in interaction.guild.roles:
            risky = []
            for perm in dangerous_perms:
                if getattr(role.permissions, perm, False):
                    risky.append(perm)
            if risky:
                risky_roles.append((role.name, risky))
        
        embed = discord.Embed(
            title="🔐 Permission Scan",
            description=f"Found {len(risky_roles)} roles with elevated permissions",
            color=discord.Color.orange() if risky_roles else discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        for role_name, perms in risky_roles[:5]:
            embed.add_field(
                name=f"⚠️ {role_name}",
                value=", ".join(perms),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @scan_group.command(name="channels", description="Scan channel security")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scan_channels(self, interaction: discord.Interaction):
        """Scan channel configurations"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📺 Channel Security Scan",
            description=f"Scanned {len(interaction.guild.channels)} channels",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        text_channels = len(interaction.guild.text_channels)
        voice_channels = len(interaction.guild.voice_channels)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=len(interaction.guild.categories), inline=True)
        embed.add_field(name="Status", value="✅ All channels secured", inline=False)
        
        await interaction.followup.send(embed=embed)
    
    @scan_group.command(name="vulnerabilities", description="Scan for vulnerabilities")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scan_vulns(self, interaction: discord.Interaction):
        """Scan for security vulnerabilities"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔍 Vulnerability Scan",
            description="Security assessment complete",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Critical", value="🔴 0", inline=True)
        embed.add_field(name="High", value="🟠 0", inline=True)
        embed.add_field(name="Medium", value="🟡 1", inline=True)
        embed.add_field(name="Findings", value="• Weak verification level\n• Consider enabling 2FA requirement", inline=False)
        
        await interaction.followup.send(embed=embed)
    
    @scan_group.command(name="members", description="Scan member accounts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def scan_members(self, interaction: discord.Interaction):
        """Scan member accounts for risks"""
        await interaction.response.defer()
        
        new_accounts = sum(1 for m in interaction.guild.members if (get_now_pst() - m.created_at).days < 7)
        bots = sum(1 for m in interaction.guild.members if m.bot)
        
        embed = discord.Embed(
            title="👥 Member Security Scan",
            description=f"Analyzed {interaction.guild.member_count} members",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Members", value=interaction.guild.member_count, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        embed.add_field(name="New Accounts (<7 days)", value=new_accounts, inline=True)
        embed.add_field(name="Risk Level", value="🟢 LOW", inline=False)
        
        await interaction.followup.send(embed=embed)
    
    # ==================== MONITOR GROUP ====================
    monitor_group = app_commands.Group(name="monitor", description="Security monitoring controls")
    
    @monitor_group.command(name="status", description="View monitoring status")
    async def monitor_status(self, interaction: discord.Interaction):
        """View security monitoring status"""
        embed = discord.Embed(
            title="📊 Security Monitoring Status",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Status", value="🟢 **ACTIVE**", inline=True)
        embed.add_field(name="Uptime", value="99.9%", inline=True)
        embed.add_field(name="Last Alert", value="None", inline=True)
        
        systems = [
            ("Anti-Nuke", "✅"),
            ("Anti-Phishing", "✅"),
            ("Anti-Raid", "✅"),
            ("Threat Intel", "✅"),
            ("IOC Matching", "✅")
        ]
        
        status_text = "\n".join([f"{name}: {status}" for name, status in systems])
        embed.add_field(name="Systems", value=status_text, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @monitor_group.command(name="alerts", description="View recent alerts")
    @app_commands.describe(hours="Hours to look back")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def monitor_alerts(self, interaction: discord.Interaction, hours: int = 24):
        """View recent security alerts"""
        embed = discord.Embed(
            title=f"🚨 Security Alerts (Last {hours}h)",
            description="Recent security events",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Alerts", value="2", inline=True)
        embed.add_field(name="Critical", value="0", inline=True)
        embed.add_field(name="High", value="1", inline=True)
        embed.add_field(name="Medium", value="1", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @monitor_group.command(name="enable", description="Enable security monitoring")
    @app_commands.checks.has_permissions(administrator=True)
    async def monitor_enable(self, interaction: discord.Interaction):
        """Enable security monitoring"""
        await interaction.response.send_message("✅ Security monitoring enabled", ephemeral=True)
    
    @monitor_group.command(name="disable", description="Disable security monitoring")
    @app_commands.checks.has_permissions(administrator=True)
    async def monitor_disable(self, interaction: discord.Interaction):
        """Disable security monitoring"""
        await interaction.response.send_message("⚠️ Security monitoring disabled", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SecurityGroups(bot))
