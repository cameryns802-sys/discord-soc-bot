"""TIER-2 DECISION: Multi-Criteria Decision Making (MCDA)"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class MultiCriteriaDecisionMaking(commands.Cog):
    """MCDA scoring and decision support"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/mcda_decisions.json'
        self.decisions = {}
        self.load_decisions()
    
    def load_decisions(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.decisions = json.load(f)
                print(f"[MCDA] ✅ Loaded {len(self.decisions)} decisions")
            except:
                self.decisions = {}
    
    def score_alternatives(self, decision_id: str, criteria: Dict, alternatives: Dict) -> Dict:
        """Score decision alternatives using MCDA"""
        scores = {}
        
        for alt_name, alt_data in alternatives.items():
            score = 0
            for criterion, weight in criteria.items():
                if criterion in alt_data:
                    score += alt_data[criterion] * weight
            
            scores[alt_name] = score
        
        self.decisions[decision_id] = {
            'criteria': criteria,
            'alternatives': alternatives,
            'scores': scores,
            'best': max(scores, key=scores.get) if scores else None,
            'decided_at': get_now_pst().isoformat()
        }
        
        self._save()
        return scores
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.decisions, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(MultiCriteriaDecisionMaking(bot))
