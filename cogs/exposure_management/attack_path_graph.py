"""
ATTACK PATH ANALYZER - Graph-based Attack Path Analysis

Analyzes how attackers could move through your environment.
"""

import discord
from discord.ext import commands
from typing import List, Dict

from cogs.graph_engine.threat_graph import threat_graph
from cogs.core.pst_timezone import get_now_pst


class AttackPathGraph(commands.Cog):
    """Analyze attack paths in the environment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.threat_graph = threat_graph
    
    def analyze_paths_to_target(self, threat_node_id: str, target_node_id: str) -> Dict:
        """Find all attack paths from threat to target"""
        paths = self.threat_graph.find_paths(threat_node_id, target_node_id)
        
        return {
            'threat': threat_node_id,
            'target': target_node_id,
            'paths_found': len(paths),
            'paths': paths,
            'shortest_path_length': min(len(p) for p in paths) if paths else 0
        }
    
    def calculate_blast_radius(self, compromised_node: str) -> Dict:
        """Calculate impact of node compromise"""
        return self.threat_graph.get_blast_radius(compromised_node)
    
    @commands.command(name='attackpaths')
    @commands.is_owner()
    async def show_attack_paths(self, ctx):
        """Show attack path analysis"""
        stats = self.threat_graph.get_statistics()
        
        embed = discord.Embed(
            title="🔴 Attack Path Analysis",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Graph Nodes", value=str(stats['total_nodes']), inline=True)
        embed.add_field(name="Relationships", value=str(stats['total_edges']), inline=True)
        embed.add_field(name="Crown Jewels", value=str(stats['crown_jewels']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AttackPathGraph(bot))
