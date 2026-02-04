"""
Blast Radius Analyzer - Analyze what breaks if X fails
Dependency impact analysis and failure cascade mapping
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Set
from cogs.core.pst_timezone import get_now_pst

class BlastRadiusAnalyzer(commands.Cog):
    """Analyze cascade failures and system dependencies"""
    
    def __init__(self, bot):
        self.bot = bot
        # Define dependency graph: component -> [dependent components]
        self.dependency_graph = {
            'signal_bus': ['threat_detector', 'incident_manager', 'compliance_monitor'],
            'data_manager': ['security_dashboard', 'audit_log_analyzer'],
            'threat_intel_hub': ['phishing_detector', 'ioc_analyzer'],
            'signal_bus': ['all_security_systems'],
            'discord_api': ['all_cogs']
        }
    
    def analyze_blast_radius(self, failed_component: str) -> Dict:
        """Analyze what would break if a component fails"""
        affected = set()
        to_process = [failed_component]
        processed = set()
        
        while to_process:
            current = to_process.pop(0)
            if current in processed:
                continue
            
            processed.add(current)
            
            # Find all dependents
            for dependency, dependents in self.dependency_graph.items():
                if current in dependents or dependency == current:
                    affected.update(dependents)
                    to_process.extend(dependents)
        
        return {
            'failed_component': failed_component,
            'direct_dependents': self.dependency_graph.get(failed_component, []),
            'cascade_affected': list(affected),
            'total_affected': len(affected),
            'blast_radius_percentage': len(affected) / len(self.dependency_graph) * 100
        }
    
    def find_critical_nodes(self) -> List[str]:
        """Find components whose failure would affect most systems"""
        impact_scores = {}
        
        for component in self.dependency_graph.keys():
            analysis = self.analyze_blast_radius(component)
            impact_scores[component] = analysis['total_affected']
        
        # Sort by impact
        return sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
    
    def get_dependency_chain(self, component: str) -> List[str]:
        """Get full dependency chain for a component"""
        chain = [component]
        current = component
        
        # Traverse up the dependency tree
        for _ in range(10):  # Max depth
            for dependency, dependents in self.dependency_graph.items():
                if current in dependents:
                    chain.append(dependency)
                    current = dependency
                    break
            else:
                break
        
        return chain
    
    @commands.command(name='blastradius')
    async def analyze_blast(self, ctx, component: str):
        """Analyze blast radius of component failure (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        analysis = self.analyze_blast_radius(component)
        
        embed = discord.Embed(
            title=f"💥 Blast Radius Analysis - {component}",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Direct Dependents", 
                       value=str(len(analysis['direct_dependents'])), inline=True)
        embed.add_field(name="Total Cascade Affected", 
                       value=str(analysis['total_affected']), inline=True)
        embed.add_field(name="Blast Radius", 
                       value=f"{analysis['blast_radius_percentage']:.1f}%", inline=True)
        
        if analysis['cascade_affected']:
            affected_str = ", ".join(analysis['cascade_affected'][:5])
            if len(analysis['cascade_affected']) > 5:
                affected_str += f" +{len(analysis['cascade_affected']) - 5} more"
            embed.add_field(name="Affected Components", value=affected_str, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BlastRadiusAnalyzer(bot))
