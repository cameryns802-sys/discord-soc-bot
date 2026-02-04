"""TIER-2 ADVERSARY: Attacker Intent Classifier - Classify adversary intent and motivation"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict
from cogs.core.pst_timezone import get_now_pst

class AttackerIntentClassifier(commands.Cog):
    """Classify and predict attacker intent"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/intent_classifications.json'
        self.classifications = {}
        self.intents = ['financial', 'espionage', 'sabotage', 'hacktivism', 'research', 'unknown']
        self.load_classifications()
    
    def load_classifications(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.classifications = json.load(f)
                print(f"[IntentClassifier] ✅ Loaded {len(self.classifications)} classifications")
            except:
                self.classifications = {}
    
    def classify_intent(self, incident_id: str, indicators: Dict, confidence: float = 0.5) -> str:
        """Classify attacker intent based on indicators"""
        # Simplified classification logic
        if indicators.get('data_exfiltration'):
            intent = 'espionage' if confidence > 0.7 else 'financial'
        elif indicators.get('system_destruction'):
            intent = 'sabotage'
        elif indicators.get('public_posting'):
            intent = 'hacktivism'
        else:
            intent = 'unknown'
        
        self.classifications[incident_id] = {
            'intent': intent,
            'confidence': confidence,
            'classified_at': get_now_pst().isoformat(),
            'indicators': indicators
        }
        
        self._save()
        return intent
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.classifications, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(AttackerIntentClassifier(bot))
