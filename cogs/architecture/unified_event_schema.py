"""
UNIFIED EVENT SCHEMA - Enterprise SOC Event Format

Standard event envelope for all system-wide security events.
Enables cross-module communication and correlation.

Architecture:
- All events conform to this schema
- Central routing/deduplication
- Supports enrichment layers
- Enables graph-based correlation
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import hashlib

from cogs.core.pst_timezone import get_now_pst


class EventType(Enum):
    """Standard event types across all modules"""
    # Detection events
    DETECTION = "detection"
    THREAT_DETECTED = "threat_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    
    # Access/Identity events
    LOGIN_ATTEMPT = "login_attempt"
    PRIVILEGE_CHANGE = "privilege_change"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Data events
    DATA_ACCESS = "data_access"
    DATA_EXFILTRATION = "data_exfiltration"
    DATA_MODIFIED = "data_modified"
    
    # Vulnerability events
    VULNERABILITY_DISCOVERED = "vulnerability_discovered"
    VULNERABILITY_EXPLOITED = "vulnerability_exploited"
    
    # Attack surface events
    ASSET_DISCOVERED = "asset_discovered"
    MISCONFIGURATION_DETECTED = "misconfiguration_detected"
    
    # Incident events
    INCIDENT_CREATED = "incident_created"
    INCIDENT_ESCALATED = "incident_escalated"
    INCIDENT_RESOLVED = "incident_resolved"
    
    # Investigation events
    INVESTIGATION_STARTED = "investigation_started"
    EVIDENCE_COLLECTED = "evidence_collected"
    HYPOTHESIS_TESTED = "hypothesis_tested"


class EventSeverity(Enum):
    """Severity levels (1-5 scale)"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class EventStatus(Enum):
    """Event lifecycle status"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class EventContext:
    """Context about the event"""
    source_module: str  # Module that generated event
    source_system: str  # System (e.g., "discord", "external_api")
    correlation_id: str  # For linking related events
    parent_event_id: Optional[str] = None  # For event hierarchies
    
    # Entity references
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    asset_id: Optional[str] = None
    
    # Classifications
    mitre_techniques: List[str] = field(default_factory=list)  # ATT&CK techniques
    tags: List[str] = field(default_factory=list)  # Custom tags


@dataclass
class EventPayload:
    """Event-specific data"""
    raw_data: Dict[str, Any]  # Original event data
    normalized_data: Dict[str, Any]  # Normalized key-value pairs
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventEnrichment:
    """Enrichment metadata"""
    enriched_at: datetime = field(default_factory=get_now_pst)
    enrichment_sources: List[str] = field(default_factory=list)
    threat_intel_matches: List[Dict] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    graph_edges: List[Dict] = field(default_factory=list)  # Graph relationships


@dataclass
class UnifiedSecurityEvent:
    """
    Enterprise Security Event Format
    
    All security events in the system conform to this envelope.
    """
    
    # Identity
    event_id: str  # Unique event ID
    event_type: EventType
    timestamp: datetime = field(default_factory=get_now_pst)
    
    # Core information
    severity: EventSeverity
    status: EventStatus = EventStatus.NEW
    title: str = ""
    description: str = ""
    
    # Context
    context: EventContext = field(default_factory=lambda: EventContext("unknown", "unknown", ""))
    
    # Payload
    payload: EventPayload = field(default_factory=lambda: EventPayload({}, {}))
    
    # Enrichment
    enrichment: EventEnrichment = field(default_factory=EventEnrichment)
    
    # Scoring
    confidence: float = 0.5  # 0.0-1.0
    risk_score: float = 0.5  # 0.0-1.0
    false_positive_score: float = 0.0  # 0.0-1.0 (how likely false positive)
    
    # Handling
    requires_investigation: bool = False
    assigned_to: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate event ID if not provided"""
        if not self.event_id:
            event_hash = hashlib.sha256(
                f"{self.timestamp}{self.context.source_module}{self.payload.raw_data}".encode()
            ).hexdigest()[:12]
            self.event_id = f"EVT-{event_hash}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'status': self.status.value,
            'title': self.title,
            'description': self.description,
            'context': asdict(self.context),
            'payload': asdict(self.payload),
            'enrichment': asdict(self.enrichment),
            'confidence': self.confidence,
            'risk_score': self.risk_score,
            'false_positive_score': self.false_positive_score,
            'requires_investigation': self.requires_investigation,
            'assigned_to': self.assigned_to,
            'sla_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None
        }
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)
    
    @staticmethod
    def from_dict(data: Dict) -> 'UnifiedSecurityEvent':
        """Create event from dictionary"""
        # Parse enums
        event_type = EventType(data.get('event_type', 'detection'))
        severity = EventSeverity(data.get('severity', 3))
        status = EventStatus(data.get('status', 'new'))
        
        # Parse timestamps
        timestamp = datetime.fromisoformat(data.get('timestamp'))
        sla_deadline = None
        if data.get('sla_deadline'):
            sla_deadline = datetime.fromisoformat(data['sla_deadline'])
        
        # Reconstruct objects
        context_data = data.get('context', {})
        context = EventContext(
            source_module=context_data.get('source_module', 'unknown'),
            source_system=context_data.get('source_system', 'unknown'),
            correlation_id=context_data.get('correlation_id', ''),
            parent_event_id=context_data.get('parent_event_id'),
            user_id=context_data.get('user_id'),
            resource_id=context_data.get('resource_id'),
            asset_id=context_data.get('asset_id'),
            mitre_techniques=context_data.get('mitre_techniques', []),
            tags=context_data.get('tags', [])
        )
        
        payload_data = data.get('payload', {})
        payload = EventPayload(
            raw_data=payload_data.get('raw_data', {}),
            normalized_data=payload_data.get('normalized_data', {}),
            metadata=payload_data.get('metadata', {})
        )
        
        return UnifiedSecurityEvent(
            event_id=data.get('event_id', ''),
            event_type=event_type,
            timestamp=timestamp,
            severity=severity,
            status=status,
            title=data.get('title', ''),
            description=data.get('description', ''),
            context=context,
            payload=payload,
            confidence=data.get('confidence', 0.5),
            risk_score=data.get('risk_score', 0.5),
            false_positive_score=data.get('false_positive_score', 0.0),
            requires_investigation=data.get('requires_investigation', False),
            assigned_to=data.get('assigned_to'),
            sla_deadline=sla_deadline
        )
