"""
EVENT ROUTER - Central event distribution hub

Routes unified events to:
1. Decision engine (for immediate response)
2. Data lake (for storage)
3. Correlation engine (for pattern matching)
4. Graph engine (for relationship tracking)
5. Relevant security modules
"""

import asyncio
from typing import Callable, List, Dict, Any
from enum import Enum

from cogs.architecture.unified_event_schema import UnifiedSecurityEvent


class EventRoute(Enum):
    DECISION_ENGINE = "decision_engine"
    DATA_LAKE = "data_lake"
    GRAPH_ENGINE = "graph_engine"
    CORRELATION = "correlation"
    ANALYST = "analyst"
    RESPONSE = "response"


class EventRouter:
    """
    Central event routing and distribution.
    
    Single source of truth for event flow through the system.
    """
    
    def __init__(self):
        self.subscribers: Dict[EventRoute, List[Callable]] = {
            route: [] for route in EventRoute
        }
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processed_count = 0
        self.dropped_count = 0
    
    def subscribe(self, route: EventRoute, callback: Callable):
        """Subscribe to event route"""
        self.subscribers[route].append(callback)
    
    async def route_event(self, event: UnifiedSecurityEvent):
        """Route event to subscribers"""
        
        # Always send to data lake (for immutable audit trail)
        await self._dispatch_to_route(EventRoute.DATA_LAKE, event)
        
        # Always send to decision engine (for autonomous response)
        await self._dispatch_to_route(EventRoute.DECISION_ENGINE, event)
        
        # Critical/High -> Escalate to analyst
        if event.severity.value >= 3:  # HIGH or CRITICAL
            await self._dispatch_to_route(EventRoute.ANALYST, event)
        
        # Send to graph engine (for relationship tracking)
        await self._dispatch_to_route(EventRoute.GRAPH_ENGINE, event)
        
        # Send to correlation engine
        await self._dispatch_to_route(EventRoute.CORRELATION, event)
        
        self.processed_count += 1
    
    async def _dispatch_to_route(self, route: EventRoute, event: UnifiedSecurityEvent):
        """Dispatch event to specific route subscribers"""
        subscribers = self.subscribers.get(route, [])
        
        tasks = [sub(event) for sub in subscribers]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for result in results:
            if isinstance(result, Exception):
                print(f"[EventRouter] Error in {route.value}: {result}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            'processed_events': self.processed_count,
            'dropped_events': self.dropped_count,
            'queue_size': self.event_queue.qsize(),
            'subscribers': {
                route.value: len(subs)
                for route, subs in self.subscribers.items()
            }
        }


# Global event router instance
event_router = EventRouter()
