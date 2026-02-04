"""TIER-2 ADVERSARY: Learning System - Learn from incidents and adapt defenses"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class AdversaryLearningSystem(commands.Cog):
    """Learn from incidents and improve detection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/learned_patterns.json'
        self.patterns = {}
        self.effectiveness = {}
        self.load_patterns()
    
    def load_patterns(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.patterns = data.get('patterns', {})
                    self.effectiveness = data.get('effectiveness', {})
                print(f"[Learning] ✅ Loaded {len(self.patterns)} patterns")
            except:
                self.patterns = {}
                self.effectiveness = {}
    
    def record_incident(self, incident_id: str, pattern: str, detected: bool, response: str = None):
        """Record incident for learning"""
        if pattern not in self.patterns:
            self.patterns[pattern] = {'count': 0, 'detections': 0, 'incidents': []}
        
        self.patterns[pattern]['count'] += 1
        if detected:
            self.patterns[pattern]['detections'] += 1
        
        self.patterns[pattern]['incidents'].append({
            'id': incident_id,
            'detected': detected,
            'response': response,
            'timestamp': get_now_pst().isoformat()
        })
        
        self._save()
    
    def get_pattern_effectiveness(self, pattern: str) -> float:
        """Calculate detection effectiveness for pattern"""
        if pattern not in self.patterns:
            return 0.0
        
        data = self.patterns[pattern]
        return (data['detections'] / data['count'] * 100) if data['count'] > 0 else 0.0
    
    def get_improvement_suggestions(self) -> List[str]:
        """Get suggestions for defense improvement"""
        suggestions = []
        
        for pattern, data in self.patterns.items():
            effectiveness = (data['detections'] / data['count'] * 100) if data['count'] > 0 else 0.0
            
            if effectiveness < 50:
                suggestions.append(f"Low detection rate for {pattern} ({effectiveness:.1f}%)")
        
        return suggestions[:10]
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'patterns': self.patterns, 'effectiveness': self.effectiveness}, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(AdversaryLearningSystem(bot))
