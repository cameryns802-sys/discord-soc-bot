"""TIER-2 ADVERSARY: Deception System - Deploy honeypots and decoys"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class DeceptionSystem(commands.Cog):
    """Honeypot and deception management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/deceptions.json'
        self.honeypots = {}
        self.load_deceptions()
    
    def load_deceptions(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.honeypots = json.load(f)
                print(f"[Deception] ✅ Loaded {len(self.honeypots)} honeypots")
            except:
                self.honeypots = {}
    
    def create_honeypot(self, honeypot_id: str, decoy_type: str, config: Dict = None) -> str:
        self.honeypots[honeypot_id] = {
            'id': honeypot_id,
            'type': decoy_type,
            'created_at': get_now_pst().isoformat(),
            'alerts': 0,
            'last_triggered': None,
            'config': config or {}
        }
        self._save()
        return honeypot_id
    
    def trigger_alert(self, honeypot_id: str) -> bool:
        if honeypot_id not in self.honeypots:
            return False
        self.honeypots[honeypot_id]['alerts'] += 1
        self.honeypots[honeypot_id]['last_triggered'] = get_now_pst().isoformat()
        self._save()
        return True
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.honeypots, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(DeceptionSystem(bot))
