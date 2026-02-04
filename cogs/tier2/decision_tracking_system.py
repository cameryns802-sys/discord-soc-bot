"""TIER-2 DECISION: Decision Tracking System - Audit all decisions"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class DecisionTrackingSystem(commands.Cog):
    """Track and audit all decisions for accountability"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/decision_audit_log.json'
        self.audit_log = []
        self.load_audit_log()
    
    def load_audit_log(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.audit_log = data.get('decisions', [])
                print(f"[DecisionTracking] ✅ Loaded {len(self.audit_log)} decisions")
            except:
                self.audit_log = []
    
    def log_decision(self, decision_id: str, system: str, decision: str, 
                     confidence: float, outcome: str = None, overridden: bool = False) -> str:
        """Log a decision for audit purposes"""
        entry = {
            'id': decision_id,
            'system': system,
            'decision': decision,
            'confidence': confidence,
            'outcome': outcome,
            'overridden': overridden,
            'timestamp': get_now_pst().isoformat(),
            'audit_status': 'logged'
        }
        
        self.audit_log.append(entry)
        
        # Keep last 100000 entries
        if len(self.audit_log) > 100000:
            self.audit_log = self.audit_log[-100000:]
        
        self._save()
        return decision_id
    
    def mark_override(self, decision_id: str, reason: str = None):
        """Mark decision as overridden by human"""
        for entry in reversed(self.audit_log):
            if entry['id'] == decision_id:
                entry['overridden'] = True
                entry['override_reason'] = reason
                entry['overridden_at'] = get_now_pst().isoformat()
                self._save()
                return True
        
        return False
    
    def get_audit_report(self, system: str = None, limit: int = 100) -> List[Dict]:
        """Get audit report"""
        if system:
            return [e for e in self.audit_log if e['system'] == system][-limit:]
        
        return self.audit_log[-limit:]
    
    def get_override_rate(self, system: str = None) -> float:
        """Calculate override rate"""
        if system:
            decisions = [e for e in self.audit_log if e['system'] == system]
        else:
            decisions = self.audit_log
        
        if not decisions:
            return 0.0
        
        overridden = sum(1 for e in decisions if e['overridden'])
        return (overridden / len(decisions) * 100) if decisions else 0.0
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'decisions': self.audit_log}, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(DecisionTrackingSystem(bot))
