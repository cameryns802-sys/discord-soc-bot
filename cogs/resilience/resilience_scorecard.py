"""
Resilience Scorecard - Rate and track system resilience over time
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class ResilienceScorecard(commands.Cog):
    """Track system resilience metrics and trends"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scorecard_file = 'data/resilience_scorecard.json'
        self.load_scorecard()
    
    def load_scorecard(self):
        """Load resilience scorecard"""
        if os.path.exists(self.scorecard_file):
            try:
                with open(self.scorecard_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.init_scorecard()
        else:
            self.init_scorecard()
    
    def init_scorecard(self):
        """Initialize default scorecard"""
        self.data = {
            'mttr': 2.5,        # Mean Time To Recovery (hours)
            'mttf': 720,        # Mean Time To Failure (hours)
            'availability': 0.999,  # 99.9%
            'chaos_tests_passed': 15,
            'vulnerability_patches_delayed': 0
        }
    
    def save_scorecard(self):
        """Save scorecard"""
        os.makedirs(os.path.dirname(self.scorecard_file), exist_ok=True)
        with open(self.scorecard_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def calculate_resilience_score(self) -> float:
        """Calculate overall resilience score (0.0-100.0)"""
        score = 100.0
        
        # Penalize for MTTR
        if self.data['mttr'] > 4:
            score -= 10
        
        # Penalize for low availability
        if self.data['availability'] < 0.99:
            score -= 20
        
        # Reward for MTTF
        if self.data['mttf'] > 1000:
            score += 10
        
        return max(0, min(100, score))
    
    @commands.command(name='resilience')
    async def show_scorecard(self, ctx):
        """View resilience scorecard (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        score = self.calculate_resilience_score()
        
        embed = discord.Embed(
            title="📊 Resilience Scorecard",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Overall Score", value=f"{score:.1f}/100", inline=True)
        embed.add_field(name="Availability", value=f"{self.data['availability']:.2%}", inline=True)
        embed.add_field(name="MTTR", value=f"{self.data['mttr']:.1f}h", inline=True)
        embed.add_field(name="MTTF", value=f"{self.data['mttf']:.1f}h", inline=True)
        embed.add_field(name="Chaos Tests Passed", value=str(self.data['chaos_tests_passed']), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ResilienceScorecard(bot))
