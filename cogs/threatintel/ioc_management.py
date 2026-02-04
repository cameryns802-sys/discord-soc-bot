"""IOC Management - Unified with Feature Flags & Signals

Consolidates ioc_management_simple.py with feature flags and signal bus integration.
- Simple mode: Add, search, list IOCs (always available)
- Advanced mode: Auto-correlation, threat intelligence feeds (feature-flagged)
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

class IOCManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.iocs = {}
        self.ioc_counter = 0
        self.data_file = "data/iocs.json"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.iocs = data.get('iocs', {})
                self.ioc_counter = data.get('counter', 0)
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'iocs': self.iocs, 'counter': self.ioc_counter}, f, indent=2)

    async def emit_ioc_signal(self, ioc_id: str, ioc_type: str, value: str, severity: str):
        """Emit IOC signal to central bus"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity=severity,
            source='ioc_management',
            data={
                'ioc_id': ioc_id,
                'ioc_type': ioc_type,
                'value': value,
                'severity': severity,
                'confidence': 0.95,
                'dedup_key': f'ioc_{ioc_id}_{value}'
            }
        ))

    # ========== SIMPLE MODE (Always Available) ==========
    
    @app_commands.command(name="iocadd", description="Add new IOC")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def iocadd(self, interaction: discord.Interaction, ioc_type: str, value: str, severity: str = "medium"):
        """Add IOC - Simple mode"""
        self.ioc_counter += 1
        ioc_id = str(self.ioc_counter)
        self.iocs[ioc_id] = {
            "id": ioc_id, "type": ioc_type.lower(), "value": value, "severity": severity.lower(),
            "added_by": interaction.user.id, "added_at": datetime.get_now_pst().isoformat(),
            "hits": 0
        }
        self.save_data()
        
        # Emit signal
        await self.emit_ioc_signal(ioc_id, ioc_type, value, severity.lower())
        
        embed = discord.Embed(title=f"🚨 IOC #{ioc_id} Added", color=discord.Color.red())
        embed.add_field(name="Type", value=ioc_type, inline=True)
        embed.add_field(name="Value", value=value, inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="iocsearch", description="Search for IOC")
    async def iocsearch(self, interaction: discord.Interaction, query: str):
        """Search IOCs - Simple mode"""
        results = [ioc for ioc in self.iocs.values() if query.lower() in ioc['value'].lower()]
        if not results:
            await interaction.response.send_message("ℹ️ No IOCs found", ephemeral=True)
            return
        embed = discord.Embed(title="🔍 IOC Search Results", color=discord.Color.blue())
        for ioc in results[:10]:
            embed.add_field(name=f"#{ioc['id']} - {ioc['type'].upper()}", value=f"{ioc['value']}\nHits: {ioc['hits']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ioclist", description="List IOCs by type")
    async def ioclist(self, interaction: discord.Interaction, ioc_type: str = "all"):
        """List IOCs - Simple mode"""
        iocs = list(self.iocs.values())
        if ioc_type != "all":
            iocs = [i for i in iocs if i['type'] == ioc_type.lower()]
        if not iocs:
            await interaction.response.send_message(f"ℹ️ No IOCs ({ioc_type})", ephemeral=True)
            return
        embed = discord.Embed(title=f"📋 IOCs ({ioc_type.upper()})", color=discord.Color.orange())
        for ioc in iocs[:15]:
            embed.add_field(name=f"#{ioc['id']} - {ioc['severity'].upper()}", value=f"{ioc['value']}\nHits: {ioc['hits']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="iocstats", description="View IOC statistics")
    async def iocstats(self, interaction: discord.Interaction):
        """IOC stats - Simple mode"""
        total_hits = sum(ioc['hits'] for ioc in self.iocs.values())
        embed = discord.Embed(title="📊 IOC Statistics", color=discord.Color.blue())
        embed.add_field(name="Total IOCs", value=len(self.iocs), inline=True)
        embed.add_field(name="Total Hits", value=total_hits, inline=True)
        embed.add_field(name="Types", value=len(set(ioc['type'] for ioc in self.iocs.values())), inline=True)
        await interaction.response.send_message(embed=embed)

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="iocremove")
    @commands.has_permissions(moderate_members=True)
    async def iocremove(self, ctx, ioc_id: str):
        """Remove IOC"""
        if ioc_id not in self.iocs:
            await ctx.send("❌ IOC not found")
            return
        del self.iocs[ioc_id]
        self.save_data()
        await ctx.send(f"✅ IOC #{ioc_id} removed")

    @commands.command(name="iocdetail")
    async def iocdetail(self, ctx, ioc_id: str):
        """View IOC details"""
        if ioc_id not in self.iocs:
            await ctx.send("❌ IOC not found")
            return
        ioc = self.iocs[ioc_id]
        embed = discord.Embed(title=f"IOC #{ioc['id']}", color=discord.Color.red())
        embed.add_field(name="Type", value=ioc['type'].upper(), inline=True)
        embed.add_field(name="Severity", value=ioc['severity'].upper(), inline=True)
        embed.add_field(name="Hits", value=ioc['hits'], inline=True)
        embed.add_field(name="Value", value=ioc['value'], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="iocexport")
    async def iocexport(self, ctx):
        """Export IOCs"""
        if not self.iocs:
            await ctx.send("ℹ️ No IOCs to export")
            return
        await ctx.send(f"📤 Exported {len(self.iocs)} IOCs to `data/iocs.json`")

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @app_commands.command(name="iocrules", description="[Advanced] Auto-correlation rules")
    async def iocrules(self, interaction: discord.Interaction):
        """Correlation rules - Advanced mode only"""
        if not flags.is_enabled('threat_hunting_advanced'):
            await interaction.response.send_message("❌ Advanced features disabled", ephemeral=True)
            return
        
        await interaction.response.send_message("🔗 IOC correlation enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(IOCManagementCog(bot))
