"""Central Signal Bus - Canonical Signal Pipeline for all security events"""
import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Callable, Any
import asyncio
from enum import Enum
import json

class SignalType(Enum):
    """All possible signal types in the system"""
    # Security signals
    THREAT_DETECTED = "threat_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    POLICY_VIOLATION = "policy_violation"
    COMPLIANCE_ISSUE = "compliance_issue"
    PII_EXPOSURE = "pii_exposure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ESCALATION_REQUIRED = "escalation_required"
    
    # System signals
    RESOURCE_WARNING = "resource_warning"
    PERFORMANCE_ISSUE = "performance_issue"
    INTEGRATION_FAILURE = "integration_failure"
    
    # User signals
    USER_ESCALATION = "user_escalation"
    USER_FEEDBACK = "user_feedback"
    HUMAN_OVERRIDE = "human_override"

class Signal:
    """Standard signal format across entire system"""
    def __init__(self, signal_type: SignalType, severity: str, source: str, data: Dict):
        self.id = f"{signal_type.value}_{int(datetime.utcnow().timestamp()*1000)}"
        self.type = signal_type
        self.severity = severity  # critical, high, medium, low, info
        self.source = source  # which cog/service emitted
        self.data = data
        self.timestamp = datetime.utcnow()
        self.confidence = data.get('confidence', 0.5)  # 0.0-1.0
        self.requires_human_review = severity in ['critical', 'high']
        self.deduplication_key = data.get('dedup_key', None)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity,
            'source': self.source,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

class SignalBus:
    """Central event bus for all signals"""
    def __init__(self):
        self.subscribers: Dict[SignalType, List[Callable]] = {}
        self.wildcard_subscribers: List[Callable] = []  # Subscribe to all signals
        self.signal_history: List[Signal] = []
        self.deduplication_window = 300  # 5 minutes
        self.max_history = 10000
    
    async def emit(self, signal: Signal) -> None:
        """Emit a signal to all subscribers"""
        # Deduplication
        if signal.deduplication_key:
            recent = [s for s in self.signal_history[-100:] 
                     if s.deduplication_key == signal.deduplication_key 
                     and (datetime.utcnow() - s.timestamp).seconds < self.deduplication_window]
            if recent:
                return  # Duplicate, suppress
        
        # Store in history
        self.signal_history.append(signal)
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
        
        # Notify wildcard subscribers first
        if self.wildcard_subscribers:
            await asyncio.gather(*[sub(signal) for sub in self.wildcard_subscribers], return_exceptions=True)
        
        # Notify type-specific subscribers
        subscribers = self.subscribers.get(signal.type, [])
        if subscribers:
            await asyncio.gather(*[sub(signal) for sub in subscribers], return_exceptions=True)
    
    def subscribe(self, signal_type, callback: Callable) -> None:
        """Subscribe to signals - accepts string name for wildcard or SignalType enum"""
        # Wildcard subscription (all signals)
        if isinstance(signal_type, str):
            self.wildcard_subscribers.append(callback)
        # Type-specific subscription
        elif isinstance(signal_type, SignalType):
            if signal_type not in self.subscribers:
                self.subscribers[signal_type] = []
            self.subscribers[signal_type].append(callback)
    
    def get_recent_signals(self, signal_type: SignalType = None, limit: int = 100) -> List[Signal]:
        """Get recent signals, optionally filtered by type"""
        if signal_type:
            return [s for s in self.signal_history[-limit:] if s.type == signal_type]
        return self.signal_history[-limit:]
    
    def get_stats(self) -> Dict:
        """Get signal statistics"""
        return {
            'total_signals': len(self.signal_history),
            'by_type': {t.value: len([s for s in self.signal_history if s.type == t]) 
                       for t in SignalType},
            'by_severity': {
                'critical': len([s for s in self.signal_history if s.severity == 'critical']),
                'high': len([s for s in self.signal_history if s.severity == 'high']),
                'medium': len([s for s in self.signal_history if s.severity == 'medium']),
                'low': len([s for s in self.signal_history if s.severity == 'low']),
            }
        }

# Global signal bus instance
signal_bus = SignalBus()

class SignalBusCog(commands.Cog):
    """Signal bus infrastructure"""
    def __init__(self, bot):
        self.bot = bot
        self.signal_bus = signal_bus
    
    @commands.command(name="signalstats")
    @commands.is_owner()
    async def signal_stats(self, ctx):
        """View signal bus statistics"""
        stats = self.signal_bus.get_stats()
        embed = discord.Embed(title="📊 Signal Bus Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Signals", value=stats['total_signals'], inline=False)
        embed.add_field(name="By Type", value="\n".join([
            f"{t}: {c}" for t, c in stats['by_type'].items() if c > 0
        ]), inline=False)
        embed.add_field(name="By Severity", value="\n".join([
            f"{sev}: {c}" for sev, c in stats['by_severity'].items() if c > 0
        ]), inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SignalBusCog(bot))
    print(f"[SignalBus] ✅ Central signal bus initialized")
