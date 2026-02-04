"""AI Abstention Policy - Confidence thresholds and automatic human escalation"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, Optional
from enum import Enum
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class AbstentionReason(Enum):
    """Reasons why an AI system might abstain"""
    LOW_CONFIDENCE = "low_confidence"
    HIGH_UNCERTAINTY = "high_uncertainty"
    INSUFFICIENT_DATA = "insufficient_data"
    PATTERN_MISMATCH = "pattern_mismatch"
    MANUAL_ESCALATION = "manual_escalation"

class AbstentionPolicy:
    """Configure when AI systems should escalate to humans"""
    
    def __init__(self):
        self.data_file = "data/abstention_policy.json"
        self.config = {
            'min_confidence': 0.65,           # Min confidence to act
            'max_uncertainty': 0.35,          # Max uncertainty acceptable
            'min_samples': 5,                 # Min data points needed
            'max_disagreement': 0.20,         # Max disagreement with other systems
            'escalation_enabled': True,
            'auto_escalate': True
        }
        self.abstentions: Dict[str, int] = {}  # Track abstention counts by system
        self.load_data()
    
    def load_data(self):
        """Load policy from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.config.update(data.get('config', {}))
                    self.abstentions = data.get('abstentions', {})
            except:
                pass
    
    def save_data(self):
        """Save policy to disk"""
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'config': self.config,
                'abstentions': self.abstentions
            }, f, indent=2)
    
    def should_abstain(self, system_name: str, confidence: float, uncertainty: float, 
                      sample_count: int, disagreement_level: float = 0.0) -> Optional[AbstentionReason]:
        """Determine if system should abstain from making a decision"""
        
        if confidence < self.config['min_confidence']:
            return AbstentionReason.LOW_CONFIDENCE
        
        if uncertainty > self.config['max_uncertainty']:
            return AbstentionReason.HIGH_UNCERTAINTY
        
        if sample_count < self.config['min_samples']:
            return AbstentionReason.INSUFFICIENT_DATA
        
        if disagreement_level > self.config['max_disagreement']:
            return AbstentionReason.PATTERN_MISMATCH
        
        return None  # OK to proceed
    
    def record_abstention(self, system_name: str, reason: AbstentionReason):
        """Log an abstention event"""
        if system_name not in self.abstentions:
            self.abstentions[system_name] = 0
        self.abstentions[system_name] += 1
        self.save_data()
    
    async def emit_escalation_signal(self, system: str, confidence: float, reason: str):
        """Emit ESCALATION_REQUIRED signal when abstention needed"""
        signal = Signal(
            signal_type=SignalType.ESCALATION_REQUIRED,
            source='abstention_policy',
            severity='HIGH',
            confidence=0.98,
            details={
                'system': system,
                'confidence': confidence,
                'reason': reason,
                'escalation_type': 'ABSTENTION_REQUIRED'
            },
            timestamp=get_now_pst().isoformat()
        )
        await signal_bus.emit(signal)
    
    def should_escalate(self, confidence: float, uncertainty: float, system: str) -> tuple[bool, str]:
        """Determine if a decision should be escalated to humans"""
        
        # Check confidence threshold
        if confidence < self.config['min_confidence']:
            return True, f"Confidence {confidence:.2%} below threshold {self.config['min_confidence']:.2%}"
        
        # Check uncertainty
        if uncertainty > self.config['max_uncertainty']:
            return True, f"Uncertainty {uncertainty:.2%} exceeds maximum {self.config['max_uncertainty']:.2%}"
        
        return False, ""
    
    def get_abstention_rate(self, system: str) -> float:
        """Get abstention rate for a system (0-1.0)"""
        return min(self.abstentions.get(system, 0) / 100, 1.0)
    
    def get_abstention_rate(self, system_name: str) -> float:
        """Get abstention rate for a system (0.0-1.0)"""
        return self.abstentions.get(system_name, 0) / 100.0  # Simple metric

class AbstentionCog(commands.Cog):
    """Commands for managing abstention policy"""
    
    def __init__(self, bot):
        self.bot = bot
        self.policy = AbstentionPolicy()
    
    @commands.command(name='abstentionpolicy')
    async def abstention_policy_cmd(self, ctx):
        """View current abstention policy (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        config = self.policy.config
        embed = discord.Embed(title="🤔 AI Abstention Policy", color=discord.Color.gold())
        embed.add_field(name="Min Confidence", value=f"{config['min_confidence']:.2f}", inline=True)
        embed.add_field(name="Max Uncertainty", value=f"{config['max_uncertainty']:.2f}", inline=True)
        embed.add_field(name="Min Samples", value=config['min_samples'], inline=True)
        embed.add_field(name="Max Disagreement", value=f"{config['max_disagreement']:.2f}", inline=True)
        embed.add_field(name="Escalation Enabled", value="✅" if config['escalation_enabled'] else "❌", inline=True)
        embed.add_field(name="Auto-Escalate", value="✅" if config['auto_escalate'] else "❌", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='setabstention')
    async def set_abstention(self, ctx, threshold: str, value: float):
        """Update abstention threshold (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        if threshold in self.policy.config:
            self.policy.config[threshold] = value
            self.policy.save_data()
            await ctx.send(f"✅ Updated {threshold} to {value}")
        else:
            await ctx.send(f"❌ Unknown threshold: {threshold}")
    
    @commands.command(name='abstentionrate')
    async def abstention_rate_cmd(self, ctx, system: Optional[str] = None):
        """View abstention rates (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            return
        
        embed = discord.Embed(title="📊 Abstention Rates", color=discord.Color.blue())
        
        if system:
            rate = self.policy.get_abstention_rate(system)
            embed.add_field(name=system, value=f"{rate:.2%}", inline=False)
        else:
            for system, count in self.policy.abstentions.items():
                embed.add_field(name=system, value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AbstentionCog(bot))

# Global singleton for cross-cog access
policy = AbstentionPolicy()
