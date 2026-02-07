"""
EVENT NORMALIZER - Unified Data Format Across All Modules

Converts diverse log formats into standard schema.
"""

import discord
from discord.ext import commands
from typing import Dict, Any

from cogs.architecture.unified_event_schema import UnifiedSecurityEvent, EventType, EventSeverity, EventContext, EventPayload
from cogs.core.pst_timezone import get_now_pst


class EventNormalizer(commands.Cog):
    """Normalize diverse event formats into unified schema"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def normalize_raw_event(self, raw_event: Dict[str, Any], source: str) -> UnifiedSecurityEvent:
        """Convert raw event from any source to unified format"""
        
        # Map source-specific fields to standard format
        if source == "discord":
            return self._normalize_discord_event(raw_event)
        elif source == "siem":
            return self._normalize_siem_event(raw_event)
        elif source == "api":
            return self._normalize_api_event(raw_event)
        else:
            return self._normalize_generic_event(raw_event, source)
    
    def _normalize_discord_event(self, event: Dict) -> UnifiedSecurityEvent:
        """Normalize Discord audit log event"""
        return UnifiedSecurityEvent(
            event_type=EventType.DETECTION,
            severity=EventSeverity.MEDIUM,
            title=event.get('action', 'Unknown Discord Event'),
            description=event.get('reason', ''),
            context=EventContext(
                source_module='discord_audit',
                source_system='discord',
                correlation_id=event.get('id', ''),
                user_id=event.get('user_id'),
                resource_id=event.get('target_id')
            ),
            payload=EventPayload(
                raw_data=event,
                normalized_data={
                    'action': event.get('action'),
                    'user': event.get('user_id'),
                    'target': event.get('target_id'),
                    'reason': event.get('reason')
                }
            )
        )
    
    def _normalize_siem_event(self, event: Dict) -> UnifiedSecurityEvent:
        """Normalize SIEM/external event"""
        return UnifiedSecurityEvent(
            event_type=EventType.THREAT_DETECTED,
            severity=EventSeverity(event.get('severity', 3)),
            title=event.get('name', 'SIEM Alert'),
            description=event.get('description', ''),
            context=EventContext(
                source_module='siem_integration',
                source_system='external_siem',
                correlation_id=event.get('alert_id', '')
            ),
            payload=EventPayload(
                raw_data=event,
                normalized_data={k: v for k, v in event.items() if isinstance(v, (str, int, float))}
            )
        )
    
    def _normalize_api_event(self, event: Dict) -> UnifiedSecurityEvent:
        """Normalize API event"""
        return UnifiedSecurityEvent(
            event_type=EventType.DETECTION,
            severity=EventSeverity.LOW,
            title=event.get('event_type', 'API Event'),
            context=EventContext(
                source_module='api_integration',
                source_system='external_api',
                correlation_id=event.get('event_id', '')
            ),
            payload=EventPayload(
                raw_data=event,
                normalized_data=event
            )
        )
    
    def _normalize_generic_event(self, event: Dict, source: str) -> UnifiedSecurityEvent:
        """Normalize generic event from unknown source"""
        return UnifiedSecurityEvent(
            event_type=EventType.DETECTION,
            severity=EventSeverity.LOW,
            title=f"Event from {source}",
            context=EventContext(
                source_module=source,
                source_system=source,
                correlation_id=event.get('id', '')
            ),
            payload=EventPayload(
                raw_data=event,
                normalized_data=event
            )
        )

async def setup(bot):
    await bot.add_cog(EventNormalizer(bot))
