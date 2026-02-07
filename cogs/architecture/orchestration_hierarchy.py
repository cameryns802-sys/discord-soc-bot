"""
ORCHESTRATION HIERARCHY - Layered decision architecture

Layers:
1. TIER-1: Critical human decisions (board-level)
2. TIER-2: High-risk autonomous (confidence-gated)
3. TIER-3: Medium-risk autonomous (policy-based)
4. TIER-4: Low-risk autonomous (fully automated)

Each layer gates the next.
"""

from enum import Enum
from typing import Dict, Optional

from cogs.architecture.unified_event_schema import UnifiedSecurityEvent, EventSeverity


class DecisionTier(Enum):
    TIER1_CRITICAL = 1  # Executive review
    TIER2_HIGH = 2      # Confidence-gated autonomous
    TIER3_MEDIUM = 3    # Policy-driven autonomous
    TIER4_LOW = 4       # Fully automated


class OrchestrationHierarchy:
    """
    Layered decision-making architecture.
    
    Routes events to appropriate decision tier based on:
    - Severity
    - Confidence
    - Risk tolerance
    - Business context
    """
    
    def __init__(self):
        self.tier_configs = {
            DecisionTier.TIER1_CRITICAL: {
                'min_severity': EventSeverity.CRITICAL,
                'requires_human': True,
                'auto_action': False,
                'escalation_time_sla': 15  # minutes
            },
            DecisionTier.TIER2_HIGH: {
                'min_severity': EventSeverity.HIGH,
                'requires_human': True,
                'auto_action': False,
                'confidence_threshold': 0.9,
                'escalation_time_sla': 60
            },
            DecisionTier.TIER3_MEDIUM: {
                'min_severity': EventSeverity.MEDIUM,
                'requires_human': False,
                'auto_action': True,
                'confidence_threshold': 0.8,
                'policy_based': True,
                'escalation_time_sla': 300
            },
            DecisionTier.TIER4_LOW: {
                'min_severity': EventSeverity.LOW,
                'requires_human': False,
                'auto_action': True,
                'confidence_threshold': 0.7,
                'escalation_time_sla': None
            }
        }
    
    def determine_tier(self, event: UnifiedSecurityEvent) -> DecisionTier:
        """Determine which decision tier event belongs to"""
        
        # TIER-1: Critical severity always
        if event.severity == EventSeverity.CRITICAL:
            return DecisionTier.TIER1_CRITICAL
        
        # TIER-2: High severity
        if event.severity == EventSeverity.HIGH:
            return DecisionTier.TIER2_HIGH
        
        # TIER-3: Medium severity
        if event.severity == EventSeverity.MEDIUM:
            return DecisionTier.TIER3_MEDIUM
        
        # TIER-4: Low/Info
        return DecisionTier.TIER4_LOW
    
    def can_auto_remediate(self, event: UnifiedSecurityEvent) -> bool:
        """Check if event can be auto-remediated"""
        tier = self.determine_tier(event)
        config = self.tier_configs[tier]
        
        # Must not require human review
        if config.get('requires_human', False):
            return False
        
        # Must meet confidence threshold
        threshold = config.get('confidence_threshold', 1.0)
        if event.confidence < threshold:
            return False
        
        return config.get('auto_action', False)
    
    def get_escalation_sla(self, event: UnifiedSecurityEvent) -> Optional[int]:
        """Get SLA for escalation in minutes"""
        tier = self.determine_tier(event)
        config = self.tier_configs[tier]
        return config.get('escalation_time_sla')
    
    def get_tier_handlers(self) -> Dict[DecisionTier, str]:
        """Get handler for each tier"""
        return {
            DecisionTier.TIER1_CRITICAL: 'HumanReviewHandler',
            DecisionTier.TIER2_HIGH: 'SeniorAnalystHandler',
            DecisionTier.TIER3_MEDIUM: 'PolicyEnforcementEngine',
            DecisionTier.TIER4_LOW: 'AutonomousResponseEngine'
        }


# Global orchestration hierarchy
orchestration = OrchestrationHierarchy()
