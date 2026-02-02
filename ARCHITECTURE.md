# SOC Bot Architecture - Trust, Safety, Security & Governance Platform

## Mental Model

This is **NOT** a feature bot. It is a:

- **Trust & Safety Platform** - Foundation for all other work
- **Security Operations Platform** - Threat detection, incident response
- **Governance Platform** - Policies, compliance, audit trails
- **Human-in-the-Loop System** - AI makes recommendations, humans decide

Think in terms of:

1. **Signals** - Canonical event pipeline
2. **Policies** - Rules that govern behavior
3. **Confidence** - Measure of certainty
4. **Human Oversight** - Decisions tracked, disagreements logged
5. **Resilience** - Graceful degradation, kill switches, safe mode

---

## Cog Loading Strategy

### ✅ Whitelisted (Auto-Loaded by Default)

**Core Infrastructure (CRITICAL)**
- `core/signal_bus.py` - Central signal pipeline for all events
- `core/feature_flags.py` - Runtime feature flag & kill switch system
- `governance/human_override_tracker.py` - Track AI decisions vs human actions
- `ai/abstention_policy.py` - AI can say "I don't know" instead of always acting
- `ai_security/prompt_injection_detector.py` - Protect AI from adversarial input
- `data_manager.py` - Data persistence layer

**Security Baseline (ALWAYS ACTIVE)**
- `security.py`, `antinuke.py`, `anti_phishing.py`
- `permission_audit.py`, `role_change_monitor.py`, `webhook_abuse_prevention.py`

**Moderation Baseline (ALWAYS ACTIVE)**
- `automod.py`, `channel_moderation.py`, `toxicity_detection.py`, `verification.py`

**Compliance Baseline (ALWAYS ACTIVE)**
- `guardrails.py`, `compliance_tools.py`, `data_retention_enforcer.py`, `consent_audit_trail.py`

**Operational Security Systems**
- `alert_management_simple.py` - Alert lifecycle (create, acknowledge, resolve, escalate)
- `anomaly_detection_simple.py` - Behavioral anomaly scoring
- `incident_management_simple.py` - Incident tracking & response
- `threat_hunting_simple.py` - Proactive threat campaigns
- `ioc_management_simple.py` - Indicator of Compromise management
- `pii_detection_simple.py` - Automatic PII exposure detection
- `disaster_recovery_simple.py` - Failover, panic button, bot recovery
- `knowledge_graph_simple.py` - Incident/actor/technique networks
- `wellness_analytics.py` - Staff burnout detection

**Utility & Integration**
- `advanced_welcome.py`, `role_assignment.py`, `server_health_check.py`
- `redteam_simple.py` - Attack simulation for defensive readiness
- `slack_integration_system.py` - Slack integration

### 🚫 NOT Auto-Loaded (On-Demand Features)

These have `feature_flags.is_enabled()` checks in their implementations:

- `predictive_*` - ML-heavy, experimental
- `reinforcement_learning_*` - Requires training, high computational cost
- `generative_*` - LLM-based, resource intensive
- Any cog with `feature_flags.is_enabled('feature_name')` guard

### 📦 Not Cogs (Internal Services)

These should be imported as modules, NOT registered as Discord cogs:

- `risk_scoring_engine.py` - Stateless risk calculation
- `severity_priority_calculator.py` - Score prioritization logic
- `false_positive_manager.py` - FP detection and feedback

Why? They don't need Discord events and shouldn't register commands.

---

## Signal Bus Architecture

### How It Works

1. **Any cog emits a signal** → `signal_bus.emit(Signal(...))`
2. **Signal is deduplicated** → Prevents spam
3. **Signal is logged** → Stored in memory + disk
4. **Subscribers are notified** → Async handlers called
5. **Human review if needed** → High-severity signals require approval

### Signal Types

```python
SignalType.THREAT_DETECTED         # Security threat identified
SignalType.ANOMALY_DETECTED        # Behavioral anomaly detected
SignalType.POLICY_VIOLATION        # Rule violation
SignalType.COMPLIANCE_ISSUE        # Compliance gap
SignalType.PII_EXPOSURE            # Personal data at risk
SignalType.UNAUTHORIZED_ACCESS     # Access control violation
SignalType.USER_ESCALATION         # User escalated to human
SignalType.HUMAN_OVERRIDE          # Human overrode AI decision
```

### Signal Structure

```python
signal = Signal(
    signal_type=SignalType.ANOMALY_DETECTED,
    severity='high',
    source='anomaly_detection_simple',
    data={
        'user_id': 12345,
        'confidence': 0.92,
        'anomaly_reason': 'Login from new location',
        'dedup_key': 'anomaly_user_12345_login'  # For deduplication
    }
)

await signal_bus.emit(signal)
```

---

## Feature Flags & Kill Switch

### Default Flags (All Changeable at Runtime)

```json
{
  "experimental_features": {
    "predictive_moderation": false,
    "ml_anomaly_detection": false,
    "generative_responses": false
  },
  "operational_features": {
    "threat_hunting": true,
    "incident_auto_response": true,
    "pii_auto_detection": true
  },
  "core_features": {
    "automod": true,
    "compliance_monitoring": true,
    "security_baseline": true
  }
}
```

### Usage

```python
from cogs.core.feature_flags import flags

# In any cog:
if flags.is_enabled('predictive_moderation'):
    result = await predict_user_risk()
else:
    await ctx.send("❌ Predictive moderation is disabled")

# Kill a feature in emergency:
if threat_level_critical:
    flags.kill_feature('incident_auto_response')
    await ctx.send("🚨 Auto-response disabled for manual review")

# Safe mode:
if resource_usage_critical:
    flags.enable_safe_mode()  # Only core features active
```

### Commands

- `/flags` - View all feature statuses
- `/killfeature <name>` - Emergency kill a feature
- `/safemode on|off|status` - Enable/disable safe mode

---

## Human Override Tracking

### Why?

Trust requires **transparency**. You need to know:

- When AI made decisions humans disagreed with
- Patterns in disagreements (bias detection)
- Whether certain systems are reliable
- Legal defensibility of moderation

### What Gets Tracked

```python
override_tracker.log_override(
    ai_decision="Ban user",
    human_decision="Mute instead",
    reason="First offense - too harsh",
    user_id=OWNER_ID,
    system='automod'
)

override_tracker.log_ai_disagreement(
    system='anomaly_detection',
    topic='user_login',
    confidence=0.42,
    disagreement_reason="Multiple signals contradict"
)
```

### Commands

- `/overridestats` - View override statistics
- `/overridelog <limit>` - View recent overrides

---

## AI Abstention Policy

### The Principle

AI should be allowed to say **"I don't know"** instead of always acting.

### When AI Abstains

```python
should_abstain, reason = abstention_policy.should_abstain(
    system='threat_detection',
    confidence=0.55,  # Below 0.65 threshold
    uncertainty=0.40,
    data_points=3  # Below 5 required
)

if should_abstain:
    await escalate_to_human(reason)
else:
    await take_action()
```

### Thresholds

- `min_confidence`: 0.65 (must be >= this)
- `max_uncertainty`: 0.35 (must be <= this)
- `min_samples`: 5 (need at least this many data points)
- `max_disagreement`: 0.20 (internal models must agree)

### Commands

- `/abstentionstats` - View how often AI abstains
- `/setabstentionthreshold <threshold> <value>` - Tune thresholds

---

## Prompt Injection Detection

### Protected Against

- Injection patterns: "ignore system instructions"
- Code execution attempts: "execute SQL"
- Jailbreak attempts: "pretend you're not limited"
- Suspicious sequences: JavaScript, HTML, SQL markers

### Usage

```python
from cogs.ai_security.prompt_injection_detector import detector

is_injection, reason, confidence = detector.detect(user_input)
if is_injection:
    await ctx.send(f"🛡️ Blocked: {reason}")
else:
    await process_normally()
```

---

## Structural Layers

### Layer 1: *_simple.py (Baseline)

Entry point for each domain. Contains:
- Individual slash/prefix commands
- Stateless operations
- Data persistence hooks
- Human-in-the-loop decision points

Examples:
- `alert_management_simple.py`
- `incident_management_simple.py`
- `threat_hunting_simple.py`

### Layer 2: Full Cogs (Advanced)

NOT auto-loaded. These would be for:
- Complex stateful workflows
- ML-heavy features
- Experimental functionality

NOT CURRENTLY USED - use feature flags instead.

### Layer 3: Services (No Discord)

Imported directly, not registered as cogs:
- `risk_scoring_engine.py`
- `severity_priority_calculator.py`
- `false_positive_manager.py`

---

## Archived (Low ROI)

Moved to `cogs/archives/` - good ideas but not operationally critical:

- `bot_personality_system.py` - Cute but adds no security value
- `quantum_safe_crypto.py` - Over-engineered for Discord
- `self_documenting_interface.py` - Maintenance burden > benefit

To restore: Move back from `archives/` to root and add to whitelist.

---

## Complete Cog Checklist

### ✅ Loaded by Default (20 Cogs)

```
Core Infrastructure (6):
  - signal_bus.py
  - feature_flags.py
  - human_override_tracker.py
  - abstention_policy.py
  - prompt_injection_detector.py
  - data_manager.py

Security Baseline (6):
  - security.py
  - antinuke.py
  - anti_phishing.py
  - permission_audit.py
  - role_change_monitor.py
  - webhook_abuse_prevention.py

Moderation (4):
  - automod.py
  - channel_moderation.py
  - toxicity_detection.py
  - verification.py

Compliance (4):
  - guardrails.py
  - compliance_tools.py
  - data_retention_enforcer.py
  - consent_audit_trail.py

Operational Security (9):
  - alert_management_simple.py
  - anomaly_detection_simple.py
  - incident_management_simple.py
  - threat_hunting_simple.py
  - ioc_management_simple.py
  - pii_detection_simple.py
  - disaster_recovery_simple.py
  - knowledge_graph_simple.py
  - wellness_analytics.py

Utility & Integration (4):
  - advanced_welcome.py
  - role_assignment.py
  - server_health_check.py
  - redteam_simple.py
  - slack_integration_system.py
```

### 🚫 Not Loaded (195+ Cogs)

All others in `cogs/` directory - can be enabled via feature flags.

---

## Next Steps

1. **Test signal bus** - Emit test signals, verify deduplication
2. **Wire signal bus into cogs** - Make all cogs emit signals
3. **Set up monitoring** - Dashboard for signals/alerts
4. **Deploy feature flags** - Make all experimental features flag-guarded
5. **Document disagreement patterns** - Use override tracker for bias detection

---

## Commands Quick Reference

### Signal Bus
- `/signalstats` - View signal statistics

### Feature Flags
- `/flags` - View all feature statuses
- `/killfeature <name>` - Emergency kill a feature
- `/safemode on|off` - Enable/disable safe mode

### Human Override Tracking
- `/overridestats` - View override statistics
- `/overridelog <limit>` - View recent overrides

### AI Abstention
- `/abstentionstats` - View how often AI abstains
- `/setabstentionthreshold <threshold> <value>` - Tune thresholds

### Prompt Injection (Owner-only)
- `/testprompt <text>` - Test if text contains injection attempts
