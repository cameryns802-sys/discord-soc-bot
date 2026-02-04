"""
Confidence Threshold Enforcer - Auto-escalate low-confidence AI decisions
"""

import discord
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ConfidenceThresholdEnforcer(commands.Cog):
    """Enforce confidence thresholds and auto-escalate uncertain decisions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.thresholds = {
            'critical_decision': 0.95,      # 95% confidence required
            'security_action': 0.85,        # 85% for security actions
            'moderation': 0.75,             # 75% for mod actions
            'low_risk': 0.60                # 60% for low-risk actions
        }
        self.escalations = []
    
    async def check_confidence(self, decision_type: str, confidence: float, 
                              decision_id: str, context: str) -> bool:
        """
        Check if confidence meets threshold
        Returns True if decision can proceed, False if needs escalation
        """
        threshold = self.thresholds.get(decision_type, 0.75)
        
        if confidence < threshold:
            # Escalate
            await self.escalate_decision(decision_type, confidence, threshold, 
                                         decision_id, context)
            return False
        
        return True
    
    async def escalate_decision(self, decision_type: str, confidence: float, 
                               threshold: float, decision_id: str, context: str):
        """Escalate low-confidence decision to human review"""
        escalation = {
            'timestamp': get_now_pst().isoformat(),
            'decision_type': decision_type,
            'confidence': confidence,
            'threshold': threshold,
            'gap': threshold - confidence,
            'decision_id': decision_id,
            'context': context,
            'status': 'pending_review'
        }
        
        self.escalations.append(escalation)
        
        # Emit escalation signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.ESCALATION_REQUIRED,
            severity='HIGH',
            source='confidence_threshold_enforcer',
            data={
                'reason': f'Low confidence: {confidence:.2%} below threshold {threshold:.2%}',
                'decision_type': decision_type,
                'decision_id': decision_id
            }
        ))
    
    def set_threshold(self, decision_type: str, confidence_level: float):
        """Adjust confidence threshold for decision type"""
        self.thresholds[decision_type] = min(1.0, max(0.0, confidence_level))
    
    def get_escalation_rate(self) -> float:
        """Get percentage of decisions escalated"""
        pending = [e for e in self.escalations if e['status'] == 'pending_review']
        return len(pending) / len(self.escalations) if self.escalations else 0.0
    
    @commands.command(name='setthreshold')
    async def set_threshold_cmd(self, ctx, decision_type: str, confidence: float):
        """Set confidence threshold for a decision type (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        self.set_threshold(decision_type, confidence)
        await ctx.send(f"✅ Threshold for {decision_type} set to {confidence:.0%}")

async def setup(bot):
    await bot.add_cog(ConfidenceThresholdEnforcer(bot))
