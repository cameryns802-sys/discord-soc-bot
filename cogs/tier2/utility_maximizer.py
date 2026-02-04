"""TIER-2 DECISION: Utility Maximizer - Calculate optimal decisions"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class UtilityMaximizer(commands.Cog):
    """Calculate optimal decisions to maximize utility"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/utility_calculations.json'
        self.calculations = {}
        self.load_calculations()
    
    def load_calculations(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.calculations = json.load(f)
                print(f"[Utility] ✅ Loaded {len(self.calculations)} calculations")
            except:
                self.calculations = {}
    
    def maximize_utility(self, scenario_id: str, options: Dict, preferences: Dict = None) -> Dict:
        """Calculate option with maximum utility"""
        utilities = {}
        
        for opt_name, opt_value in options.items():
            utility = opt_value.get('benefit', 0) - opt_value.get('cost', 0)
            if preferences:
                for pref, weight in preferences.items():
                    if pref in opt_value:
                        utility += opt_value[pref] * weight
            
            utilities[opt_name] = utility
        
        optimal = max(utilities, key=utilities.get) if utilities else None
        
        self.calculations[scenario_id] = {
            'options': options,
            'utilities': utilities,
            'optimal': optimal,
            'calculated_at': get_now_pst().isoformat()
        }
        
        self._save()
        return {'optimal': optimal, 'utility': utilities.get(optimal, 0)}
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.calculations, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(UtilityMaximizer(bot))
