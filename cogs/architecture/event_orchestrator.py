"""
CENTRAL EVENT ORCHESTRATOR

Unified routing, enrichment, and orchestration of all security events.

This is the traffic controller that:
- Routes events to analyzers
- Deduplicates
- Correlates
- Enriches
- Makes decisions
- Executes responses
"""

import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Coroutine
from collections import defaultdict

from cogs.architecture.unified_event_schema import (
    UnifiedSecurityEvent, EventType, EventSeverity, EventStatus, EventContext
)
from cogs.core.pst_timezone import get_now_pst


class EventOrchestrator:
    """Central event routing and orchestration"""
    
    def __init__(self):
        self.events_file = 'data/orchestrated_events.json'
        self.dedup_window = 300  # 5 minutes
        
        # Event storage
        self.events: List[UnifiedSecurityEvent] = []
        self.dedup_cache: Dict[str, datetime] = {}  # For deduplication
        
        # Routing tables
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.universal_handlers: List[Callable] = []  # Run for all events
        
        # Enrichment pipeline
        self.enrichers: List[Callable] = []
        
        # Decision engine callbacks
        self.decision_callbacks: List[Callable] = []
        
        self.load_events()
    
    def load_events(self):
        """Load event history"""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct events
                    self.events = [UnifiedSecurityEvent.from_dict(e) for e in data.get('events', [])]
            except:
                self.events = []
    
    def save_events(self):
        """Save event history"""
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
        with open(self.events_file, 'w') as f:
            json.dump({
                'events': [e.to_dict() for e in self.events[-10000:]]  # Keep last 10k
            }, f, indent=2)
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register handler for specific event type"""
        self.event_handlers[event_type].append(handler)
    
    def register_universal_handler(self, handler: Callable):
        """Register handler for all event types"""
        self.universal_handlers.append(handler)
    
    def register_enricher(self, enricher: Callable):
        """Register enrichment function"""
        self.enrichers.append(enricher)
    
    def register_decision_callback(self, callback: Callable):
        """Register decision callback"""
        self.decision_callbacks.append(callback)
    
    async def process_event(self, event: UnifiedSecurityEvent) -> bool:
        """
        Process event through orchestration pipeline
        
        Returns: True if event was processed, False if deduplicated
        """
        
        # 1. DEDUPLICATION
        if self._is_duplicate(event):
            return False
        
        # 2. STORE
        self.events.append(event)
        if len(self.events) > 100000:
            self.events = self.events[-100000:]
        self.save_events()
        
        # 3. ENRICHMENT PIPELINE
        for enricher in self.enrichers:
            try:
                await enricher(event)
            except Exception as e:
                print(f"[Orchestrator] Enricher error: {e}")
        
        # 4. UNIVERSAL HANDLERS (run for all events)
        for handler in self.universal_handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"[Orchestrator] Universal handler error: {e}")
        
        # 5. EVENT-TYPE SPECIFIC HANDLERS
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"[Orchestrator] Handler error for {event.event_type}: {e}")
        
        # 6. DECISION CALLBACKS (for AI/autonomous systems)
        for callback in self.decision_callbacks:
            try:
                await callback(event)
            except Exception as e:
                print(f"[Orchestrator] Decision callback error: {e}")
        
        return True
    
    def _is_duplicate(self, event: UnifiedSecurityEvent) -> bool:
        """Check if event is duplicate"""
        
        # Create dedup key
        dedup_key = f"{event.context.source_module}:{event.event_type.value}:{event.payload.raw_data}"
        
        # Check cache
        if dedup_key in self.dedup_cache:
            age = (get_now_pst() - self.dedup_cache[dedup_key]).seconds
            if age < self.dedup_window:
                return True  # Duplicate
            else:
                # Expired from cache
                del self.dedup_cache[dedup_key]
        
        # Not duplicate - add to cache
        self.dedup_cache[dedup_key] = get_now_pst()
        return False
    
    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[UnifiedSecurityEvent]:
        """Get recent events by type"""
        return [e for e in self.events[-limit:] if e.event_type == event_type]
    
    def get_events_by_severity(self, severity: EventSeverity, limit: int = 100) -> List[UnifiedSecurityEvent]:
        """Get recent events by severity"""
        return [e for e in self.events[-limit:] if e.severity == severity]
    
    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[UnifiedSecurityEvent]:
        """Get events for specific user"""
        return [e for e in self.events[-limit:] if e.context.user_id == user_id]
    
    def get_events_by_resource(self, resource_id: str, limit: int = 100) -> List[UnifiedSecurityEvent]:
        """Get events for specific resource"""
        return [e for e in self.events[-limit:] if e.context.resource_id == resource_id]
    
    def get_statistics(self) -> Dict:
        """Get event statistics"""
        now = get_now_pst()
        last_hour = now - timedelta(hours=1)
        
        recent_events = [e for e in self.events if e.timestamp > last_hour]
        
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        by_status = defaultdict(int)
        
        for event in recent_events:
            by_type[event.event_type.value] += 1
            by_severity[event.severity.value] += 1
            by_status[event.status.value] += 1
        
        critical_unresolved = len([
            e for e in self.events
            if e.severity == EventSeverity.CRITICAL and e.status != EventStatus.RESOLVED
        ])
        
        return {
            'total_events': len(self.events),
            'last_hour_events': len(recent_events),
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'by_status': dict(by_status),
            'critical_unresolved': critical_unresolved,
            'avg_time_to_investigate': self._calculate_avg_tti()
        }
    
    def _calculate_avg_tti(self) -> float:
        """Calculate average time to investigate"""
        investigating = [
            e for e in self.events
            if e.status == EventStatus.INVESTIGATING
        ]
        
        if not investigating:
            return 0.0
        
        times = []
        for event in investigating:
            delta = (get_now_pst() - event.timestamp).total_seconds()
            times.append(delta / 3600)  # Convert to hours
        
        return sum(times) / len(times)


# Global orchestrator instance
event_orchestrator = EventOrchestrator()


class EventOrchestratorCog(commands.Cog):
    """Commands for event orchestrator management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.orchestrator = event_orchestrator
    
    @commands.command(name='eventstats')
    @commands.is_owner()
    async def event_stats(self, ctx):
        """View event orchestration statistics"""
        stats = self.orchestrator.get_statistics()
        
        embed = discord.Embed(
            title="📊 Event Orchestration Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Events", value=str(stats['total_events']), inline=True)
        embed.add_field(name="Last Hour", value=str(stats['last_hour_events']), inline=True)
        embed.add_field(name="Critical Unresolved", value=str(stats['critical_unresolved']), inline=True)
        
        embed.add_field(name="By Event Type", value="━" * 25, inline=False)
        for etype, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            embed.add_field(name=f"• {etype}", value=str(count), inline=True)
        
        embed.add_field(name="By Severity", value="━" * 25, inline=False)
        for severity, count in sorted(stats['by_severity'].items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=f"• {severity}", value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EventOrchestratorCog(bot))
