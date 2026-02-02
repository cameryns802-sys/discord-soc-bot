"""Human Override Tracker - Comprehensive logging of all human vs AI decisions"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

class HumanOverrideTracker:
    """Track all human overrides of AI decisions for bias detection and explainability"""
    
    def __init__(self):
        self.data_file = "data/human_overrides.json"
        self.overrides: List[Dict] = []
        self.disagreement_matrix: Dict[str, Dict[str, int]] = {}
        self.load_data()
    
    def load_data(self):
        """Load override history from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.overrides = data.get('overrides', [])
                    self.disagreement_matrix = data.get('disagreement_matrix', {})
            except:
                self.overrides = []
                self.disagreement_matrix = {}
    
    def save_data(self):
        """Save override history to disk"""
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'overrides': self.overrides,
                'disagreement_matrix': self.disagreement_matrix
            }, f, indent=2)
    
    async def log_override(self, system_name: str, decision: str, human_decision: str, 
                          user_id: int, reason: str, confidence: float = 0.0):
        """Log a human override of an AI decision"""
        override = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_name,
            'ai_decision': decision,
            'human_decision': human_decision,
            'user_id': user_id,
            'reason': reason,
            'ai_confidence': confidence,
            'disagreement': decision != human_decision
        }
        self.overrides.append(override)
        
        # Update disagreement matrix
        key = f"{system_name}:{decision}→{human_decision}"
        if system_name not in self.disagreement_matrix:
            self.disagreement_matrix[system_name] = {}
        self.disagreement_matrix[system_name][key] = self.disagreement_matrix[system_name].get(key, 0) + 1
        
        self.save_data()
        return override
    
    def get_bias_score(self, system_name: str) -> float:
        """Calculate bias score (0.0-1.0) for a system based on override patterns"""
        if system_name not in self.disagreement_matrix:
            return 0.0
        
        total_disagreements = sum(self.disagreement_matrix[system_name].values())
        if total_disagreements == 0:
            return 0.0
        
        # Find most common disagreement pattern
        pattern_counts = self.disagreement_matrix[system_name]
        max_count = max(pattern_counts.values())
        bias_score = min(1.0, max_count / total_disagreements)
        return bias_score
    
    def get_override_stats(self, system_name: Optional[str] = None) -> Dict:
        """Get statistics on overrides"""
        if system_name:
            system_overrides = [o for o in self.overrides if o['system'] == system_name]
        else:
            system_overrides = self.overrides
        
        total = len(system_overrides)
        disagreements = sum(1 for o in system_overrides if o['disagreement'])
        
        return {
            'total_overrides': total,
            'disagreements': disagreements,
            'agreement_rate': (total - disagreements) / total if total > 0 else 0.0,
            'avg_confidence': sum(o.get('ai_confidence', 0) for o in system_overrides) / total if total > 0 else 0.0
        }

class HumanOverrideCog(commands.Cog):
    """User-facing commands for override tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.tracker = HumanOverrideTracker()
    
    @commands.command(name='overridestats')
    async def override_stats(self, ctx, system: Optional[str] = None):
        """View override statistics for a system (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        stats = self.tracker.get_override_stats(system)
        embed = discord.Embed(title=f"Override Statistics - {system or 'All Systems'}", color=discord.Color.blue())
        embed.add_field(name="Total Overrides", value=stats['total_overrides'], inline=True)
        embed.add_field(name="Disagreements", value=stats['disagreements'], inline=True)
        embed.add_field(name="Agreement Rate", value=f"{stats['agreement_rate']*100:.1f}%", inline=True)
        embed.add_field(name="Avg AI Confidence", value=f"{stats['avg_confidence']:.2f}", inline=True)
        
        if system and stats['total_overrides'] > 0:
            bias_score = self.tracker.get_bias_score(system)
            embed.add_field(name="Bias Score", value=f"{bias_score:.2f}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='biasreport')
    async def bias_report(self, ctx):
        """Generate comprehensive bias analysis report (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(title="🔍 AI Bias Analysis Report", color=discord.Color.red())
        
        if not self.tracker.overrides:
            embed.description = "No override data available yet."
            await ctx.send(embed=embed)
            return
        
        # Analyze all systems
        systems = set(o['system'] for o in self.tracker.overrides)
        for system in systems:
            bias_score = self.tracker.get_bias_score(system)
            stats = self.tracker.get_override_stats(system)
            
            if bias_score > 0.1:  # Highlight systems with potential bias
                embed.add_field(
                    name=f"⚠️ {system}",
                    value=f"Bias: {bias_score:.2%} | Disagreements: {stats['disagreements']}/{stats['total_overrides']}",
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HumanOverrideCog(bot))

# Global singleton for cross-cog access
tracker = HumanOverrideTracker()
