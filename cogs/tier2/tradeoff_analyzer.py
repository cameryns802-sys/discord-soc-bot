"""TIER-2 DECISION: Tradeoff Analyzer - Cost-benefit analysis"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict
from cogs.core.pst_timezone import get_now_pst

class TradeoffAnalyzer(commands.Cog):
    """Analyze tradeoffs and cost-benefit relationships"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/tradeoff_analyses.json'
        self.analyses = {}
        self.load_analyses()
    
    def load_analyses(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.analyses = json.load(f)
                print(f"[Tradeoff] ✅ Loaded {len(self.analyses)} analyses")
            except:
                self.analyses = {}
    
    def analyze_tradeoff(self, analysis_id: str, options: Dict) -> Dict:
        """Analyze tradeoffs between options"""
        results = {}
        
        for opt_name, opt_data in options.items():
            benefit = opt_data.get('benefit', 0)
            cost = opt_data.get('cost', 0)
            risk = opt_data.get('risk', 0)
            
            # Calculate benefit-cost ratio and risk-adjusted value
            bcr = benefit / cost if cost > 0 else 0
            risk_adj_value = (benefit - risk) / cost if cost > 0 else 0
            
            results[opt_name] = {
                'benefit': benefit,
                'cost': cost,
                'risk': risk,
                'bcr': bcr,
                'risk_adjusted_value': risk_adj_value
            }
        
        self.analyses[analysis_id] = {
            'options': options,
            'analysis': results,
            'analyzed_at': get_now_pst().isoformat()
        }
        
        self._save()
        return results
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.analyses, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(TradeoffAnalyzer(bot))
