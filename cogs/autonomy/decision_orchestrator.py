"""
DECISION ORCHESTRATOR - Central AI Decision Engine

Routes security events to appropriate autonomous response systems.

This is the "brain" that decides:
- What to do about each threat
- How confident are we
- What risk is acceptable
- Human escalation
"""

import discord
from discord.ext import commands
from typing import Dict, Optional
from enum import Enum

from cogs.architecture.unified_event_schema import UnifiedSecurityEvent, EventSeverity
from cogs.core.pst_timezone import get_now_pst


class DecisionOutcome(Enum):
    AUTOMATIC_REMEDIATION = "automatic_remediation"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    MONITOR_ONLY = "monitor_only"
    FALSE_POSITIVE = "false_positive"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"


class DecisionOrchestrator(commands.Cog):
    """Central autonomous decision making engine"""
    
    def __init__(self, bot):
        self.bot = bot
        # Decision rules
        self.confidence_threshold = 0.75  # Min confidence for auto-remediation
        self.critical_always_escalate = True
        self.human_override_enabled = True
    
    async def make_decision(self, event: UnifiedSecurityEvent) -> Dict:
        """
        Make autonomous security decision
        
        Returns decision object with outcome and actions
        """
        
        decision = {
            'event_id': event.event_id,
            'timestamp': get_now_pst().isoformat(),
            'outcome': DecisionOutcome.MONITOR_ONLY,
            'confidence': event.confidence,
            'reasoning': [],
            'recommended_actions': [],
            'requires_human_approval': False
        }
        
        # CRITICAL SEVERITY LOGIC
        if event.severity == EventSeverity.CRITICAL:
            decision['outcome'] = DecisionOutcome.ESCALATE_TO_HUMAN
            decision['requires_human_approval'] = True
            decision['reasoning'].append("Critical severity always requires human review")
            return decision
        
        # CONFIDENCE-BASED LOGIC
        if event.confidence < self.confidence_threshold:
            decision['outcome'] = DecisionOutcome.INSUFFICIENT_CONFIDENCE
            decision['reasoning'].append(f"Confidence {event.confidence:.2f} below threshold {self.confidence_threshold}")
            return decision
        
        # FALSE POSITIVE CHECK
        if event.false_positive_score > 0.8:
            decision['outcome'] = DecisionOutcome.FALSE_POSITIVE
            decision['reasoning'].append(f"High false positive likelihood: {event.false_positive_score:.2f}")
            return decision
        
        # HIGH SEVERITY -> ESCALATE
        if event.severity == EventSeverity.HIGH:
            decision['outcome'] = DecisionOutcome.ESCALATE_TO_HUMAN
            decision['requires_human_approval'] = True
            decision['reasoning'].append("High severity threat requires human verification")
            return decision
        
        # MEDIUM+ -> AUTO-REMEDIATE
        if event.severity in [EventSeverity.MEDIUM]:
            if event.confidence > 0.85:
                decision['outcome'] = DecisionOutcome.AUTOMATIC_REMEDIATION
                decision['reasoning'].append(f"High confidence ({event.confidence:.2f}) - auto-remediate")
                decision['recommended_actions'] = self._get_remediation_actions(event)
            else:
                decision['outcome'] = DecisionOutcome.ESCALATE_TO_HUMAN
                decision['reasoning'].append("Medium severity with moderate confidence - escalate")
                decision['requires_human_approval'] = True
            return decision
        
        # LOW/INFO -> MONITOR
        decision['outcome'] = DecisionOutcome.MONITOR_ONLY
        decision['reasoning'].append(f"Low severity ({event.severity.value}) - monitoring only")
        return decision
    
    def _get_remediation_actions(self, event: UnifiedSecurityEvent) -> List[str]:
        """Generate remediation actions"""
        actions = []
        
        # Based on threat type, suggest actions
        if 'phishing' in event.description.lower():
            actions.append("Delete message")
            actions.append("Warn user")
            actions.append("Log for training")
        
        elif 'spam' in event.description.lower():
            actions.append("Timeout user (1 hour)")
            actions.append("Delete messages")
            actions.append("Alert moderators")
        
        elif 'exploit' in event.description.lower():
            actions.append("Isolate user")
            actions.append("Revoke permissions")
            actions.append("Create incident")
        
        return actions
    
    @commands.command(name='decisionstats')
    @commands.is_owner()
    async def decision_stats(self, ctx):
        """View decision engine statistics"""
        embed = discord.Embed(
            title="🤖 Decision Engine Status",
            color=discord.Color.purple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Confidence Threshold", value=f"{self.confidence_threshold:.2f}", inline=True)
        embed.add_field(name="Critical Auto-Escalate", value="✅ Enabled", inline=True)
        embed.add_field(name="Human Override", value="✅ Enabled", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DecisionOrchestrator(bot))
