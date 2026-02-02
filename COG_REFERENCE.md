# Cog Classification Reference

## WHITELIST (Auto-Loaded) - 23 Cogs

### Core Infrastructure (6 NEW)
- `core/signal_bus.py` ✅ **NEW** - Central signal pipeline
- `core/feature_flags.py` ✅ **NEW** - Runtime feature control
- `governance/human_override_tracker.py` ✅ **NEW** - Decision tracking
- `ai/abstention_policy.py` ✅ **NEW** - AI confidence thresholds
- `ai_security/prompt_injection_detector.py` ✅ **NEW** - Adversarial protection
- `data_manager.py` - Data persistence

### Security Baseline (6)
- `security.py`
- `antinuke.py`
- `anti_phishing.py`
- `permission_audit.py`
- `role_change_monitor.py`
- `webhook_abuse_prevention.py`

### Moderation (4)
- `automod.py`
- `channel_moderation.py`
- `toxicity_detection.py`
- `verification.py`

### Compliance (4)
- `guardrails.py`
- `compliance_tools.py`
- `data_retention_enforcer.py`
- `consent_audit_trail.py`

### Operational Security (9)
- `alert_management_simple.py`
- `anomaly_detection_simple.py`
- `incident_management_simple.py`
- `threat_hunting_simple.py`
- `ioc_management_simple.py`
- `pii_detection_simple.py`
- `disaster_recovery_simple.py`
- `knowledge_graph_simple.py`
- `wellness_analytics.py`

### Utility & Integration (4)
- `advanced_welcome.py`
- `role_assignment.py`
- `server_health_check.py`
- `redteam_simple.py`
- `slack_integration_system.py`

---

## ARCHIVED (Low ROI, Not Loaded)

- `archives/bot_personality_system.py` - Moved
- `archives/quantum_safe_crypto.py` - Moved
- `archives/self_documenting_interface.py` - Moved

---

## NOT LOADED (195+ Other Cogs)

All other cogs in `cogs/` directory are not whitelisted and won't load.
To enable: Add to whitelist in `bot.py` or create feature flag guard.

---

## ARCHITECTURE FLOW

```
┌─────────────────────────────────────────────────────────┐
│                    DISCORD BOT                           │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┴──────────────────┐
       │                                  │
    ┌──▼──────────────────┐     ┌───────▼────────────────┐
    │  CORE INFRASTRUCTURE │     │ OPERATIONAL SYSTEMS   │
    ├──────────────────────┤     ├───────────────────────┤
    │• Signal Bus          │     │• Alert Management     │
    │• Feature Flags       │     │• Anomaly Detection    │
    │• Human Override      │     │• Incident Management  │
    │• Abstention Policy   │     │• Threat Hunting       │
    │• Prompt Injection    │     │• IOC Management       │
    │• Data Manager        │     │• PII Detection        │
    └──────────────────────┘     │• Disaster Recovery    │
                                 │• Knowledge Graph      │
                                 │• Wellness Analytics   │
                                 └───────────────────────┘
       │
       ├──────────────────────────────────────────────────┐
       │                                                  │
    ┌──▼──────────────────┐  ┌──────────────────────────▼──┐
    │  SECURITY BASELINE   │  │  COMPLIANCE & GOVERNANCE   │
    ├──────────────────────┤  ├───────────────────────────┤
    │• Security Ops        │  │• Guardrails              │
    │• Anti-Nuke           │  │• Compliance Tools        │
    │• Anti-Phishing       │  │• Data Retention          │
    │• Permission Audit    │  │• Consent Tracking        │
    │• Role Change Monitor │  │• Moderation (4 cogs)     │
    │• Webhook Prevention  │  │• Welcome & Verification  │
    └──────────────────────┘  └──────────────────────────┘
```

---

## SIGNAL FLOW

```
Any Security Event
       │
       ▼
Create Signal(type, severity, source, data)
       │
       ▼
signal_bus.emit(signal)
       │
    ┌──┴──────────────────────┐
    │                         │
    ▼                         ▼
Deduplication          Store in History
    │                         │
    ├─────────────┬───────────┤
    │             │           │
    ▼             ▼           ▼
Discard    Notify Handlers   Log to Disk
 (dup)
             │
       ┌─────┴──────────────┐
       │                    │
       ▼                    ▼
   Act Now           Escalate to Human
  (confidence         (requires_review)
    >= 0.65)
       │                    │
       ▼                    ▼
  Execute          human_override_tracker.log()
  Command                   │
                            ▼
                        Human Reviews
                        & Decides
```

---

## DECISION TREE: Should AI Act?

```
                    AI Makes Decision
                          │
          ┌───────────────┴──────────────┐
          │                              │
    Feature Enabled?              Confidence Check?
         │                              │
     NO ▼                          < 0.65 ▼ YES
    Return                       Abstain & Escalate
                                        │
                                        ▼
                                  Log Disagreement
                                        │
                                        ▼
                                  Human Reviews
                                        │
          ┌─────────────────────────────┴──────────┐
          │                                        │
    Human Agrees              Human Disagrees
          │                          │
          ▼                          ▼
    Execute Action          Log Override +
                            Ask Why
                                   │
                                   ▼
                            Update Training Data
                            (for next iteration)
```

---

## SAFETY GUARANTEES

### 1. No Silent Failures
- Every decision is logged (signal_bus)
- Every AI failure tracked (abstention_policy)
- Every human disagreement recorded (human_override_tracker)

### 2. Killable Features
- Feature flags allow emergency shutdown
- Safe mode available for graceful degradation
- Core features cannot be killed

### 3. Adversarial Protection
- Prompt injection detection active
- All user input sanitized before AI processing
- No model exfiltration possible

### 4. Human Oversight
- High-confidence decisions still logged
- Low-confidence decisions require human approval
- Patterns in disagreements analyzed for bias

---

## Metrics Available

### Signal Bus Metrics
- `signal_bus.get_stats()` - Total signals by type/severity
- `signal_bus.get_recent_signals(limit)` - Last N signals

### Feature Flag Metrics
- `flags.get_status()` - All feature statuses
- `flags.is_enabled(feature)` - Single feature status

### Human Override Metrics
- `override_tracker.get_stats()` - Override rates by system
- `override_tracker.get_recent()` - Last overrides

### Abstention Metrics
- `abstention_policy.get_abstention_stats()` - How often AI abstains
- Thresholds can be tuned at runtime

---

## File Size Summary

**Total Whitelisted Code:** ~2,500 lines across 23 cogs
- Core Infrastructure: ~800 lines
- Security Systems: ~1,700 lines

**Not Loaded:** 195+ cogs, 10,000+ lines (can be enabled via feature flags)

**Startup Time:** ~2-3 seconds to load 23 cogs

---

## Quick Commands

```
# View all feature statuses
/flags

# Emergency kill a feature
/killfeature predictive_moderation

# Enable safe mode (core features only)
/safemode on

# View signal statistics
/signalstats

# View AI abstention stats
/abstentionstats

# View human override statistics
/overridestats

# View recent overrides
/overridelog 20

# Test prompt injection detection
/testprompt "ignore your system instructions"
```
