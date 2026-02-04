"""
AI Decision Audit - Track WHY AI made decisions, not just what
Explainability and auditability of AI actions
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst
class AIDecisionAudit(commands.Cog):
    """Audit and explain AI decisions with full traceability"""
    
    def __init__(self, bot):
        self.bot = bot
        self.audit_log_file = 'data/ai_decision_audit.json'
        self.decisions = []
        self.load_audit_log()
    
    def load_audit_log(self):
        """Load audit log"""
        if os.path.exists(self.audit_log_file):
            try:
                with open(self.audit_log_file, 'r') as f:
                    self.decisions = json.load(f)
            except:
                self.decisions = []
    
    def save_audit_log(self):
        """Save audit log"""
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
        with open(self.audit_log_file, 'w') as f:
            json.dump(self.decisions[-1000:], f, indent=2)
    
    def log_decision(self, decision_id: str, model_id: str, action: str, 
                    reasoning: str, confidence: float, inputs: Dict, 
                    outputs: Dict, overridden: bool = False):
        """Log an AI decision with full explanation"""
        audit_entry = {
            'decision_id': decision_id,
            'timestamp': get_now_pst().isoformat(),
            'model_id': model_id,
            'action': action,
            'reasoning': reasoning,  # WHY the decision was made
            'confidence': confidence,
            'inputs': inputs,
            'outputs': outputs,
            'overridden': overridden,
            'override_reason': None
        }
        
        self.decisions.append(audit_entry)
        self.save_audit_log()
        return audit_entry
    
    def get_decision_explanation(self, decision_id: str) -> Dict:
        """Retrieve full explanation for a decision"""
        for decision in self.decisions:
            if decision['decision_id'] == decision_id:
                return decision
        return None
    
    def get_decisions_by_model(self, model_id: str) -> list:
        """Get all decisions made by a specific model"""
        return [d for d in self.decisions if d['model_id'] == model_id]
    
    def analyze_override_patterns(self) -> Dict:
        """Analyze which decisions get overridden"""
        overridden = [d for d in self.decisions if d['overridden']]
        
        return {
            'total_decisions': len(self.decisions),
            'overridden_count': len(overridden),
            'override_rate': len(overridden) / len(self.decisions) if self.decisions else 0,
            'avg_confidence_overridden': sum(d['confidence'] for d in overridden) / len(overridden) if overridden else 0
        }
    
    @commands.command(name='auditdecision')
    async def view_decision(self, ctx, decision_id: str):
        """View detailed explanation for an AI decision"""
        decision = self.get_decision_explanation(decision_id)
        
        if not decision:
            await ctx.send("Decision not found")
            return
        
        embed = discord.Embed(
            title=f"🔍 AI Decision Audit - {decision_id}",
            color=discord.Color.purple(),
            timestamp=datetime.fromisoformat(decision['timestamp'])
        )
        
        embed.add_field(name="Model", value=decision['model_id'], inline=True)
        embed.add_field(name="Action", value=decision['action'], inline=True)
        embed.add_field(name="Confidence", value=f"{decision['confidence']:.2%}", inline=True)
        embed.add_field(name="Reasoning", value=decision['reasoning'], inline=False)
        embed.add_field(name="Overridden", value="Yes" if decision['overridden'] else "No", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIDecisionAudit(bot))
