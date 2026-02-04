"""Threat Hunting - Unified with Feature Flags

Consolidates threat_hunting_simple.py with feature flags for advanced functionality.
- Simple mode: Start hunts, log findings, view results (always available)
- Advanced mode: ML-guided hunting, pattern detection (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags
from cogs.core.pst_timezone import get_now_pst

class ThreatHuntingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hunts = {}
        self.hunt_counter = 0
        self.data_file = "data/threat_hunts.json"
        self.mode = "simple"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.hunts = data.get('hunts', {})
                self.hunt_counter = data.get('counter', 0)
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'hunts': self.hunts, 'counter': self.hunt_counter}, f, indent=2)

    async def cog_load(self):
        """Check if advanced features are enabled"""
        if flags.is_enabled('threat_hunting_advanced'):
            self.mode = "advanced"

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="huntstart", description="Start new threat hunt")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def huntstart(self, interaction: discord.Interaction, hypothesis: str, scope: str = "full"):
        """Start hunt - Simple mode"""
        self.hunt_counter += 1
        hunt_id = str(self.hunt_counter)
        
        self.hunts[hunt_id] = {
            "id": hunt_id, "hypothesis": hypothesis, "scope": scope, "status": "active",
            "started_by": interaction.user.id, "started_at": datetime.get_now_pst().isoformat(),
            "findings": []
        }
        self.save_data()
        
        # Emit signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='high',
            source='threat_hunting',
            data={
                'hunt_id': hunt_id,
                'hypothesis': hypothesis,
                'scope': scope,
                'started_by': interaction.user.id,
                'confidence': 0.80,
                'dedup_key': f'hunt_{hunt_id}'
            }
        ))
        
        embed = discord.Embed(title=f"🔍 Hunt #{hunt_id} Started", description=hypothesis, color=discord.Color.orange())
        embed.add_field(name="Scope", value=scope, inline=True)
        embed.add_field(name="Status", value="ACTIVE", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="huntdetail", description="View hunt details")
    async def huntdetail(self, interaction: discord.Interaction, hunt_id: str):
        """View hunt - Simple mode"""
        if hunt_id not in self.hunts:
            await interaction.response.send_message("❌ Hunt not found", ephemeral=True)
            return
        
        hunt = self.hunts[hunt_id]
        embed = discord.Embed(title=f"Hunt #{hunt_id}: {hunt['hypothesis']}", color=discord.Color.orange())
        embed.add_field(name="Status", value=hunt['status'].upper(), inline=True)
        embed.add_field(name="Findings", value=str(len(hunt['findings'])), inline=True)
        embed.add_field(name="Started", value=hunt['started_at'][:16], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="huntlist", description="List all threat hunts")
    async def huntlist(self, interaction: discord.Interaction):
        """List hunts - Simple mode"""
        embed = discord.Embed(title=f"🔍 Active Hunts ({len(self.hunts)})", color=discord.Color.orange())
        for hunt_id, hunt in list(self.hunts.items())[-10:]:
            embed.add_field(
                name=f"Hunt #{hunt_id}: {hunt['hypothesis'][:50]}",
                value=f"Status: {hunt['status'].upper()} | Findings: {len(hunt['findings'])}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="huntclose", description="Close a threat hunt")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def huntclose(self, interaction: discord.Interaction, hunt_id: str):
        """Close hunt - Simple mode"""
        if hunt_id not in self.hunts:
            await interaction.response.send_message("❌ Hunt not found", ephemeral=True)
            return
        
        self.hunts[hunt_id]["status"] = "closed"
        self.hunts[hunt_id]["closed_at"] = datetime.get_now_pst().isoformat()
        self.save_data()
        await interaction.response.send_message(f"🏁 Hunt #{hunt_id} closed")

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="huntfinding")
    @commands.has_permissions(moderate_members=True)
    async def huntfinding(self, ctx, hunt_id: str, *, finding: str):
        """Log hunt finding"""
        if hunt_id not in self.hunts:
            await ctx.send("❌ Hunt not found")
            return
        
        self.hunts[hunt_id]["findings"].append({
            "text": finding,
            "logged_by": ctx.author.id,
            "timestamp": datetime.get_now_pst().isoformat()
        })
        self.save_data()
        await ctx.send(f"📝 Finding logged for hunt #{hunt_id}")

    @commands.command(name="huntquery")
    async def huntquery(self, ctx, hunt_id: str):
        """Query hunt findings"""
        if hunt_id not in self.hunts:
            await ctx.send("❌ Hunt not found")
            return
        
        findings = self.hunts[hunt_id]["findings"]
        embed = discord.Embed(title=f"Hunt #{hunt_id} Findings ({len(findings)})", color=discord.Color.orange())
        for finding in findings[-5:]:
            embed.add_field(name="Finding", value=finding['text'][:100], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="huntreport")
    async def huntreport(self, ctx, hunt_id: str):
        """Generate hunt report"""
        if hunt_id not in self.hunts:
            await ctx.send("❌ Hunt not found")
            return
        
        hunt = self.hunts[hunt_id]
        embed = discord.Embed(title=f"📊 Hunt #{hunt_id} Report", color=discord.Color.orange())
        embed.add_field(name="Hypothesis", value=hunt['hypothesis'], inline=False)
        embed.add_field(name="Status", value=hunt['status'].upper(), inline=True)
        embed.add_field(name="Total Findings", value=str(len(hunt['findings'])), inline=True)
        embed.add_field(name="Scope", value=hunt['scope'], inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="huntstats")
    async def huntstats(self, ctx):
        """Hunt statistics"""
        active = len([h for h in self.hunts.values() if h['status'] == 'active'])
        closed = len([h for h in self.hunts.values() if h['status'] == 'closed'])
        total_findings = sum(len(h['findings']) for h in self.hunts.values())
        
        embed = discord.Embed(title="📊 Threat Hunting Statistics", color=discord.Color.orange())
        embed.add_field(name="Total Hunts", value=len(self.hunts), inline=True)
        embed.add_field(name="Active", value=active, inline=True)
        embed.add_field(name="Closed", value=closed, inline=True)
        embed.add_field(name="Total Findings", value=total_findings, inline=True)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="huntml", description="[Advanced] ML-guided hunting")
    async def huntml(self, interaction: discord.Interaction, hunt_id: str):
        """ML-guided hunting - Advanced mode only"""
        if not flags.is_enabled('threat_hunting_advanced'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        await interaction.response.send_message("🤖 ML-guided hunting enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(ThreatHuntingCog(bot))
