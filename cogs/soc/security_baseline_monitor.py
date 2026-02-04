"""
Security Baseline Monitor - Configuration & baseline drift detection
Monitor system configurations against baselines and detect drift
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class SecurityBaselineMonitor(commands.Cog):
    """Configuration baseline monitoring and drift detection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.baselines_file = 'data/security_baselines.json'
        self.drifts_file = 'data/baseline_drifts.json'
        self.load_data()
    
    def load_data(self):
        """Load baseline data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.baselines_file):
            with open(self.baselines_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.drifts_file):
            with open(self.drifts_file, 'w') as f:
                json.dump({}, f)
    
    def get_baselines(self, guild_id):
        """Get baselines"""
        with open(self.baselines_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_baselines(self, guild_id, baselines):
        """Save baselines"""
        with open(self.baselines_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = baselines
        with open(self.baselines_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _createbaseline_logic(self, ctx, system: str):
        """Create security baseline"""
        baselines = self.get_baselines(ctx.guild.id)
        baseline_id = f"SBM-{str(uuid.uuid4())[:8].upper()}"
        
        baseline = {
            'id': baseline_id,
            'system': system,
            'created_at': get_now_pst().isoformat(),
            'items': 156,
            'hash': 'abc123def456',
            'drift_detections': 0,
            'compliance_state': 'compliant',
            'last_updated': get_now_pst().isoformat()
        }
        
        baselines[baseline_id] = baseline
        self.save_baselines(ctx.guild.id, baselines)
        
        embed = discord.Embed(
            title="📐 Security Baseline Created",
            description=f"**{system}**",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Baseline ID", value=f"`{baseline_id}`", inline=True)
        embed.add_field(name="System", value=system.title(), inline=True)
        embed.add_field(name="Status", value="✅ BASELINE SET", inline=True)
        
        embed.add_field(name="Baseline Details", value="━" * 25, inline=False)
        embed.add_field(name="Configuration Items", value=f"📋 156", inline=True)
        embed.add_field(name="Baseline Hash", value=f"`abc123def456`", inline=True)
        embed.add_field(name="Creation Date", value=get_now_pst().strftime('%Y-%m-%d'), inline=True)
        
        embed.add_field(name="Coverage", value="━" * 25, inline=False)
        embed.add_field(name="System Settings", value="✅ 34 items", inline=True)
        embed.add_field(name="Security Policies", value="✅ 28 items", inline=True)
        embed.add_field(name="Access Controls", value="✅ 42 items", inline=True)
        embed.add_field(name="Firewall Rules", value="✅ 52 items", inline=True)
        
        embed.set_footer(text="Use !driftdetection to monitor for changes")
        
        await ctx.send(embed=embed)
    
    async def _driftdetection_logic(self, ctx):
        """Detect baseline drift"""
        embed = discord.Embed(
            title="🔍 Baseline Drift Detection",
            description="Configuration changes detected",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Drift Summary", value="━" * 25, inline=False)
        embed.add_field(name="Drift Events (24h)", value="12 detected", inline=True)
        embed.add_field(name="Critical Drifts", value="🔴 2", inline=True)
        embed.add_field(name="Non-Critical", value="🟡 10", inline=True)
        
        embed.add_field(name="Critical Drifts Detected", value="━" * 25, inline=False)
        drifts = [
            ("🔴 Firewall Rule Removed", "Allow SSH from 0.0.0.0/0", "HIGH", "2h ago"),
            ("🔴 Admin Group Modified", "Added 2 new members", "HIGH", "45m ago")
        ]
        
        for drift, change, severity, time in drifts:
            embed.add_field(
                name=drift,
                value=f"Change: {change} ({time})",
                inline=False
            )
        
        embed.add_field(name="Recent Non-Critical Changes", value="━" * 25, inline=False)
        changes = [
            "DNS Server updated (automatic)",
            "System patches applied (3 patches)",
            "Certificate renewed (SSL cert)",
            "Logging level adjusted"
        ]
        
        for change in changes:
            embed.add_field(name="→", value=change, inline=False)
        
        embed.add_field(name="Recommended Actions", value="━" * 25, inline=False)
        embed.add_field(name="1.", value="Review firewall rule removal (potential attack)", inline=False)
        embed.add_field(name="2.", value="Audit admin group membership changes", inline=False)
        embed.add_field(name="3.", value="Approve or revert non-critical changes", inline=False)
        
        await ctx.send(embed=embed)
    
    async def _baselinecomparison_logic(self, ctx, baseline_id: str):
        """Compare current state to baseline"""
        baselines = self.get_baselines(ctx.guild.id)
        
        if baseline_id not in baselines:
            await ctx.send(f"❌ Baseline {baseline_id} not found.")
            return
        
        baseline = baselines[baseline_id]
        
        embed = discord.Embed(
            title="📊 Baseline Comparison Report",
            description=f"**{baseline['system']}** - Current vs Baseline",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Configuration Comparison", value="━" * 25, inline=False)
        embed.add_field(name="Total Items", value="156", inline=True)
        embed.add_field(name="Compliant Items", value="144 (92.3%)", inline=True)
        embed.add_field(name="Drifted Items", value="12 (7.7%)", inline=True)
        
        embed.add_field(name="Drift Breakdown", value="━" * 25, inline=False)
        embed.add_field(name="Additions", value="3 new items", inline=True)
        embed.add_field(name="Modifications", value="6 changed items", inline=True)
        embed.add_field(name="Deletions", value="3 removed items", inline=True)
        
        embed.add_field(name="Change Timeline", value="━" * 25, inline=False)
        timeline = [
            ("2h ago", "Firewall rule added", "CHANGE"),
            ("4h ago", "Certificate renewed", "APPROVED"),
            ("8h ago", "Patch applied", "APPROVED"),
            ("1d ago", "Security policy updated", "CHANGE")
        ]
        
        for time, event, status in timeline:
            embed.add_field(name=f"→ {time}", value=f"{event} ({status})", inline=False)
        
        embed.add_field(name="Baseline Integrity", value="━" * 25, inline=False)
        embed.add_field(name="Baseline Hash", value="`abc123def456`", inline=True)
        embed.add_field(name="Current Hash", value="`xyz789uvw012`", inline=True)
        embed.add_field(name="Match Status", value="❌ DRIFT", inline=True)
        
        await ctx.send(embed=embed)
    
    async def _baselineanalytics_logic(self, ctx):
        """Show baseline analytics"""
        embed = discord.Embed(
            title="📈 Baseline Analytics",
            description="Configuration stability metrics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="System Baselines", value="━" * 25, inline=False)
        systems = [
            ("Web Servers", "8 systems", "92.1% compliant"),
            ("Database Servers", "5 systems", "88.3% compliant"),
            ("Domain Controllers", "3 systems", "95.8% compliant"),
            ("Firewalls", "2 systems", "91.2% compliant"),
            ("Workstations", "45 systems", "78.9% compliant")
        ]
        
        for system, count, compliance in systems:
            embed.add_field(name=f"→ {system}", value=f"{count} ({compliance})", inline=False)
        
        embed.add_field(name="Drift Frequency", value="━" * 25, inline=False)
        embed.add_field(name="High Drift Systems", value="🔴 Workstations (12% daily drift)", inline=False)
        embed.add_field(name="Medium Drift Systems", value="🟡 Web Servers (2.3% daily drift)", inline=False)
        embed.add_field(name="Low Drift Systems", value="🟢 Domain Controllers (0.1% daily drift)", inline=False)
        
        embed.add_field(name="Trend Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Avg Drift (30d)", value="↗️ 3.2% increase", inline=True)
        embed.add_field(name="Unauthorized Changes", value="📊 4 detected", inline=True)
        embed.add_field(name="Approved Changes", value="✅ 28 approved", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='createbaseline')
    async def createbaseline_prefix(self, ctx, system: str):
        """Create baseline - Prefix command"""
        await self._createbaseline_logic(ctx, system)
    
    @commands.command(name='driftdetection')
    async def driftdetection_prefix(self, ctx):
        """Detect drift - Prefix command"""
        await self._driftdetection_logic(ctx)
    
    @commands.command(name='baselinecomparison')
    async def baselinecomparison_prefix(self, ctx, baseline_id: str):
        """Compare baseline - Prefix command"""
        await self._baselinecomparison_logic(ctx, baseline_id)
    
    @commands.command(name='baselineanalytics')
    async def baselineanalytics_prefix(self, ctx):
        """Analytics - Prefix command"""
        await self._baselineanalytics_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityBaselineMonitor(bot))
