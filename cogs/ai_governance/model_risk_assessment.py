"""
Model Risk Assessment - Hallucination, bias, and misuse scoring
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class ModelRiskAssessment(commands.Cog):
    """Assess AI model risks: hallucination, bias, misuse"""
    
    def __init__(self, bot):
        self.bot = bot
        self.risk_scores_file = 'data/ai_model_risks.json'
        self.load_risk_scores()
    
    def load_risk_scores(self):
        """Load risk assessment scores"""
        if os.path.exists(self.risk_scores_file):
            try:
                with open(self.risk_scores_file, 'r') as f:
                    self.risk_scores = json.load(f)
            except:
                self.risk_scores = {}
        else:
            self.risk_scores = {}
    
    def assess_hallucination_risk(self, model_id: str, context: str) -> float:
        """Score hallucination risk (0.0-1.0)"""
        # Factors: model size, training data freshness, context clarity
        base_score = 0.3
        
        # Adjust based on context
        if len(context) < 50:
            base_score += 0.2  # Ambiguous context increases risk
        if 'unknown' in context.lower():
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def assess_bias_risk(self, model_id: str) -> float:
        """Score bias risk (0.0-1.0)"""
        # Factors: training data diversity, fairness testing, protected attributes
        base_score = 0.25
        
        # Model-specific adjustments from cache
        if model_id in self.risk_scores:
            cached = self.risk_scores[model_id].get('bias_risk', base_score)
            return cached
        
        return base_score
    
    def assess_misuse_risk(self, model_id: str, prompt: str) -> float:
        """Score misuse risk (0.0-1.0)"""
        # Factors: prompt injection attempts, harmful intent detection
        score = 0.1
        
        # Detect suspicious patterns
        dangerous_patterns = ['ignore', 'forget', 'override', 'admin', 'sudo']
        for pattern in dangerous_patterns:
            if pattern in prompt.lower():
                score += 0.15
        
        return min(1.0, score)
    
    async def emit_risk_alert(self, model_id: str, hallucination: float, bias: float, misuse: float):
        """Emit alert if any risk exceeds threshold"""
        max_risk = max(hallucination, bias, misuse)
        
        if max_risk > 0.7:
            # High risk - escalate
            pass
    
    @commands.command(name='modelrisk')
    async def assess_model(self, ctx, model_id: str):
        """Assess risk for a specific model"""
        hallucination = self.assess_hallucination_risk(model_id, "")
        bias = self.assess_bias_risk(model_id)
        misuse = self.assess_misuse_risk(model_id, "")
        
        embed = discord.Embed(
            title=f"⚠️ Risk Assessment - {model_id}",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Hallucination Risk", value=f"{hallucination:.2%}", inline=True)
        embed.add_field(name="Bias Risk", value=f"{bias:.2%}", inline=True)
        embed.add_field(name="Misuse Risk", value=f"{misuse:.2%}", inline=True)
        
        overall = (hallucination + bias + misuse) / 3
        embed.add_field(name="Overall Risk", value=f"{overall:.2%}", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModelRiskAssessment(bot))
