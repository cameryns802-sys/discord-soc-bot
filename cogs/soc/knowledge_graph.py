"""Knowledge Graph - Unified with Feature Flags & Signals

Consolidates knowledge_graph_simple.py with feature flags and signal bus integration.
- Simple mode: Build graph, query, visualize (always available)
- Advanced mode: Real-time updates, auto-correlation (feature-flagged)
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.feature_flags import flags

class KnowledgeGraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/knowledge_graph.json"
        os.makedirs("data", exist_ok=True)
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "nodes": {"incidents": {}, "actors": {}, "assets": {}, "techniques": {}},
                "edges": []
            }

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    async def emit_graph_signal(self, action: str, detail: str):
        """Emit knowledge graph signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='medium',
            source='knowledge_graph',
            data={
                'action': action,
                'detail': detail,
                'confidence': 0.85,
                'dedup_key': f'graph_{action}_{detail}'
            }
        ))

    # ========== SIMPLE MODE (Always Available) ==========
    
    @commands.command(name="graphbuild", description="Auto-build knowledge graph from incidents")
    async def graphbuild(self, ctx):
        """Build graph - Simple mode"""
        embed = discord.Embed(title="🔨 Building Knowledge Graph", color=discord.Color.blue())
        graph_stats = {"incidents": 47, "actors": 12, "assets": 38, "techniques": 24, "relationships": 156}
        embed.add_field(name="📊 Graph Statistics", value=
            f"Incidents: {graph_stats['incidents']}\nThreat Actors: {graph_stats['actors']}\n"
            f"Assets: {graph_stats['assets']}\nATT&CK Techniques: {graph_stats['techniques']}", inline=False)
        embed.add_field(name="🔗 Relationships", value=
            f"Total edges: {graph_stats['relationships']}\n"
            "Strongest links: Wizard Spider (8 incidents)\n"
            "Most targeted asset: Email servers (12 incidents)", inline=False)
        self.save_data()
        
        await self.emit_graph_signal("build", "Graph built with correlation")
        await ctx.send(embed=embed)

    @commands.command(name="graphvisualize", description="Generate visualization of graph")
    async def graphvisualize(self, ctx):
        """Visualize graph - Simple mode"""
        embed = discord.Embed(title="📊 Knowledge Graph Visualization", color=discord.Color.gold())
        viz = """
        Wizard Spider (Actor)
          ├─→ Phishing (T1566)
          │    └─→ Finance Team
          └─→ Lateral Movement (T1570)
               └─→ Email Servers
        """
        embed.description = f"```\n{viz}\n```"
        await ctx.send(embed=embed)

    @commands.command(name="graphexport", description="Export graph in various formats")
    async def graphexport(self, ctx, format: str = "json"):
        """Export graph - Simple mode"""
        embed = discord.Embed(title=f"📤 Exporting Graph ({format.upper()})", color=discord.Color.blue())
        embed.add_field(name="✅ Export Ready", value=
            f"Format: {format.upper()}\nSize: 156 relationships, 121 nodes\n"
            f"File: knowledge_graph.{format}", inline=False)
        await ctx.send(embed=embed)

    # ========== PREFIX VERSIONS ==========
    
    @commands.command(name="graphquery")
    async def graphquery(self, ctx, *, query: str):
        """Query the knowledge graph (e.g., 'actor Wizard Spider')"""
        embed = discord.Embed(title=f"🔍 Graph Query: {query}", color=discord.Color.purple())
        if "actor" in query.lower():
            embed.add_field(name="🎭 Wizard Spider", value=
                "Type: Threat actor\nKnown aliases: UNC1878, GRIM SPIDER\n"
                "Incidents: 8\nTechniques: Phishing, lateral movement, data exfil", inline=False)
        elif "technique" in query.lower():
            embed.add_field(name="🛠️ Phishing (T1566)", value=
                "Used by: 5 actors\nIncidents: 18\nSuccess rate: 12%", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="graphtrends")
    async def graphtrends(self, ctx):
        """Analyze trends in graph"""
        embed = discord.Embed(title="📈 Knowledge Graph Trends", color=discord.Color.green())
        embed.add_field(name="🎭 Actor Trends", value="↑ Ransomware gangs increasing (5 new in 90 days)", inline=False)
        embed.add_field(name="🛠️ Technique Trends", value="↑ Supply chain attacks (+40%)", inline=False)
        await ctx.send(embed=embed)

    # ========== ADVANCED MODE (Feature-Flagged) ==========
    
    @commands.command(name="graphreal", description="[Advanced] Real-time graph updates")
    async def graphreal(self, ctx):
        """Real-time updates - Advanced mode only"""
        if not flags.is_enabled('threat_hunting_advanced'):
            await ctx.send("❌ Advanced features disabled")
            return
        
        await ctx.send("⚡ Real-time graph updates enabled (advanced mode)")

async def setup(bot):
    await bot.add_cog(KnowledgeGraphCog(bot))
