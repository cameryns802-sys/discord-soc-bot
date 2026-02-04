"""TIER-2 DECISION: Decision Explainability Engine"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class DecisionExplainabilityEngine(commands.Cog):
    """Explain decisions to humans in clear terms"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/decision_explanations.json'
        self.explanations = {}
        self.load_explanations()
    
    def load_explanations(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.explanations = json.load(f)
                print(f"[Explainability] ✅ Loaded {len(self.explanations)} explanations")
            except:
                self.explanations = {}
    
    def explain_decision(self, decision_id: str, decision: str, reasoning: Dict) -> str:
        """Generate human-readable explanation"""
        explanation = f"Decision: {decision}\n\n"
        explanation += "Reasoning:\n"
        
        for key, value in reasoning.items():
            if isinstance(value, (int, float)):
                explanation += f"• {key}: {value:.2f}\n"
            else:
                explanation += f"• {key}: {value}\n"
        
        self.explanations[decision_id] = {
            'decision': decision,
            'reasoning': reasoning,
            'explanation': explanation,
            'generated_at': get_now_pst().isoformat()
        }
        
        self._save()
        return explanation
    
    def get_confidence_level(self, reasoning: Dict) -> str:
        """Estimate confidence from reasoning"""
        confidence = 0
        factors = len(reasoning)
        
        for key, value in reasoning.items():
            if isinstance(value, (int, float)) and value > 0.7:
                confidence += value
        
        avg_confidence = confidence / factors if factors > 0 else 0
        
        if avg_confidence > 0.8:
            return "High"
        elif avg_confidence > 0.5:
            return "Medium"
        else:
            return "Low"
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.explanations, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(DecisionExplainabilityEngine(bot))
