# 🏗️ THREAT SYSTEMS ARCHITECTURE

## System Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      DISCORD EVENTS                             │
│  (Messages, Member Join, Commands, Audit Log Changes)           │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├─────────────────────────────────────┐
               │                                     │
               ▼                                     ▼
        ┌──────────────┐            ┌──────────────────────┐
        │   Message    │            │  Member Join Event   │
        │  Processing  │            │                      │
        └──────┬───────┘            └──────────┬───────────┘
               │                               │
        ┌──────┴──────┐              ┌────────┴─────────┐
        │             │              │                  │
        ▼             ▼              ▼                  ▼
   ┌─────────┐ ┌──────────────┐ ┌────────┐  ┌─────────────┐
   │  Anti-  │ │    Anti-     │ │Blackl- │  │Auto-        │
   │Phishing │ │Cryptocurrency│ │ist     │  │Quarantine   │
   │System   │ │System        │ │System  │  │(Check only) │
   └────┬────┘ └──────┬───────┘ └───┬────┘  └─────────────┘
        │             │             │
        │  Detects:   │ Detects:    │ Detects:
        │  - URLs     │ - Wallets   │ - Blacklisted
        │  - Domains  │ - Mining    │   users
        │  - Patterns │ - Scams     │ - Kick if found
        │             │             │
        └─────────┬───┴──────┬──────┘
                  │          │
                  └────┬─────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   SIGNAL BUS (Central Hub)   │  ◄─── All events flow here
        │                              │
        │ Deduplication + Correlation  │
        │ Message enrichment           │
        │ Pattern matching             │
        └──────┬───────────────────────┘
               │
        ┌──────┴──────────┬──────────────────┐
        │                 │                  │
        ▼                 ▼                  ▼
   ┌────────────┐  ┌──────────────┐  ┌──────────────┐
   │Auto-       │  │Intelligent   │  │Auto-         │
   │Escalation  │  │Threat        │  │Quarantine    │
   │System      │  │Response      │  │System        │
   │            │  │              │  │              │
   │- Evaluates │  │- Playbooks   │  │- Isolate     │
   │  severity  │  │- Auto-ban    │  │- Preserve    │
   │- Routes to │  │- Auto-kick   │  │  evidence    │
   │  responders│  │- Alerts      │  │- Pending     │
   │- Notifies  │  │              │  │  review      │
   │  on-call   │  │              │  │              │
   └────┬───────┘  └──────┬───────┘  └──────┬───────┘
        │                 │                 │
        │  Actions:       │ Actions:        │ Actions:
        │  1. Log         │ 1. Delete       │ 1. Remove roles
        │  2. Alert       │ 2. Warn user    │ 2. Add Quarantine
        │  3. Timeout     │ 3. Ban          │ 3. Move to #quar
        │  4. Ban         │ 4. Alert mods   │ 4. Preserve data
        │  5. Lockdown    │ 5. Lockdown     │ 5. Email user
        │                 │                 │
        └────────┬────────┴────────┬────────┘
                 │                 │
                 └────────┬────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │   PERSISTENT DATA STORAGE     │
          │                               │
          │  data/                        │
          │  ├─ auto_escalation.json      │
          │  ├─ auto_quarantine.json      │
          │  ├─ crypto_detection.json     │
          │  └─ blacklist.json            │
          └───────────────────────────────┘
```

---

## Threat Response Timeline

```
T+0ms:  Threat Detected
        └─ Signal emitted to signal_bus

T+10ms: Signal Bus receives
        ├─ Deduplicates
        ├─ Correlates with recent threats
        └─ Routes to subscribers

T+20ms: Auto-Escalation evaluates
        ├─ Analyzes severity: 🔴 HIGH
        ├─ Analyzes confidence: 90%
        ├─ Determines level: 4 (Timeout)
        └─ Emits ESCALATION_REQUIRED signal

T+50ms: Auto-Quarantine receives signal
        ├─ Checks confidence > 85%?
        ├─ YES → Initiates quarantine
        ├─ Removes all roles
        ├─ Adds "Quarantine" role
        └─ Preserves evidence

T+80ms: Intelligent Threat Response
        ├─ Checks playbooks
        ├─ Executes automated actions
        ├─ Alerts moderators
        └─ Creates audit entry

T+100ms: On-Call Responder notified
         ├─ DM sent to responder
         ├─ Contains:
         │  ├─ Threat type
         │  ├─ Severity & confidence
         │  ├─ User involved
         │  └─ Recommended action
         └─ Responder can review evidence

All within 100ms! ⚡
```

---

## Data Flow: Crypto Scam Example

```
INCOMING MESSAGE: "Send to 0x1234... moon shot! Limited time!"
                          │
                          ▼
              ┌────────────────────────┐
              │ Anti-Crypto System     │
              └────────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
         Wallet Found  Mining    Scam Language
         Confidence:   Malware   Keywords:
         95%           Detected  "moon shot"
                       (0%)      "limited time"
                                 Score: 80%
              │           │           │
              └───────────┴───────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  SIGNAL BUS                   │
          │  ┌─────────────────────────┐  │
          │  │ SignalType:             │  │
          │  │   THREAT_DETECTED       │  │
          │  │ Severity: HIGH          │  │
          │  │ Confidence: 87.5%       │  │
          │  │ Source: anti_crypto     │  │
          │  │ Data:                   │  │
          │  │  - wallets: [0x1234]    │  │
          │  │  - keywords: 2          │  │
          │  │  - confidence: 0.875    │  │
          │  └─────────────────────────┘  │
          └───────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   Auto-  │ │Intelligent│ │   Auto-  │
        │Escalation│ │  Threat   │ │Quarantine│
        │ System   │ │Response   │ │ System   │
        └──────────┘ └──────────┘ └──────────┘
              │           │           │
         Level: 3    Playbook:   >85%?
        (Alert)     Delete +    YES:
                    Timeout     Isolate
                               
              │           │           │
              └───────────┴───────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  ACTIONS EXECUTED                │
        ├─────────────────────────────────┤
        │ ✅ Message deleted               │
        │ ✅ User warned                   │
        │ ✅ Moderators alerted            │
        │ ✅ User timed out (1 hour)       │
        │ ✅ User quarantined              │
        │ ✅ Evidence preserved            │
        │ ✅ On-call notified              │
        │ ✅ Audit trail created           │
        └─────────────────────────────────┘
```

---

## Escalation Decision Tree

```
THREAT DETECTED
  │
  ├─ Severity? 
  │  ├─ CRITICAL (threat actor, exploit) → Base Level: 5
  │  ├─ HIGH (malware, phishing) → Base Level: 4
  │  ├─ MEDIUM (harassment, raid) → Base Level: 3
  │  └─ LOW (spam, typos) → Base Level: 2
  │
  ├─ Confidence?
  │  ├─ >95% (95-100%) → Boost: +1 level
  │  ├─ 80-95% → Boost: +0 levels
  │  └─ <80% → Reduce: -1 level
  │
  ├─ Pattern Match?
  │  ├─ Repeat offender → Boost: +1 level
  │  └─ New threat → No change
  │
  └─ FINAL LEVEL (1-5)
     │
     ├─ Level 1: LOG (record only)
     │   └─ Action: Nothing, just log
     │
     ├─ Level 2: LOG & WATCH
     │   └─ Action: Add to watchlist
     │
     ├─ Level 3: ALERT MODERATORS
     │   └─ Action: Post to #mod-logs
     │
     ├─ Level 4: TIMEOUT USER
     │   └─ Action: Timeout 1 hour
     │
     └─ Level 5: BAN & LOCKDOWN
         ├─ Action: Ban user
         ├─ Action: Lock channels
         ├─ Action: Alert owner
         └─ Action: Notify on-call
```

---

## Evidence Preservation in Quarantine

```
USER QUARANTINED
       │
       ▼
┌──────────────────────────────────────┐
│  EVIDENCE VAULT ENTRY                │
├──────────────────────────────────────┤
│ ID: EVD-20250202T160234Z234          │
│ Timestamp: 2025-02-02 16:02:34 UTC   │
│                                      │
│ Signal Data:                         │
│  ├─ Type: THREAT_DETECTED            │
│  ├─ Source: anti_phishing            │
│  ├─ Severity: HIGH                   │
│  ├─ Confidence: 0.94                 │
│  └─ Payload:                         │
│      ├─ URLs: [phishing-site.com]    │
│      ├─ Pattern: confirmed phishing  │
│      └─ Message ID: 123456789        │
│                                      │
│ Chain of Custody:                    │
│  ├─ Captured: 2025-02-02 16:02:30    │
│  ├─ By: auto_escalation_system       │
│  ├─ Preserved: 2025-02-02 16:02:33   │
│  └─ Sealed: ✅                       │
│                                      │
│ User Account:                        │
│  ├─ ID: 987654321                    │
│  ├─ Name: SuspiciousUser#1234        │
│  ├─ Account Age: 2 days              │
│  └─ Previous Incidents: 3            │
│                                      │
│ Quarantine Status:                   │
│  ├─ Status: ACTIVE                   │
│  ├─ Started: 2025-02-02 16:02:34     │
│  ├─ Reason: Phishing attempt         │
│  └─ Appeals: 0/3 used                │
└──────────────────────────────────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
   REVIEW                FORENSIC
   ┌──────┐              ┌───────────┐
   │Admin │              │Forensics  │
   │review│              │analysis   │
   │panel │              │team       │
   └──────┘              └───────────┘
       │                     │
       ├─────────────────────┤
       │                     │
    APPROVE              INVESTIGATE
       │                     │
       ├─────────────────────┤
       │                     │
       ▼                     ▼
   RELEASE         ELEVATED ACTION
   • Restore      • Involve law
     roles          enforcement
   • Notify       • Create case
     user         • Archive
   • Clear           evidence
     record
```

---

## Performance & Scalability

```
MESSAGE PROCESSING
  │
  ├─ Anti-Phishing: ~5ms
  │  └─ Regex + pattern matching
  │
  ├─ Anti-Crypto: ~8ms
  │  ├─ Wallet detection (5ms)
  │  ├─ Mining patterns (2ms)
  │  └─ Scam language (1ms)
  │
  ├─ Blacklist Check: ~2ms
  │  └─ Hash lookup
  │
  └─ Signal Emission: ~15ms
     ├─ Deduplication (3ms)
     ├─ Correlation (8ms)
     └─ Subscriber notify (4ms)
     
TOTAL: ~30ms per message
(Discord processes ~1000s msg/sec, we handle <1% impact)
```

---

## System Interdependencies

```
AUTO-ESCALATION
  │
  ├─ Reads: Signal Bus
  ├─ Reads: Threat patterns
  ├─ Writes: Escalation history
  ├─ Calls: On-call manager
  └─ Emits: ESCALATION_REQUIRED signal
      │
      └─→ Triggers: Auto-Quarantine
              └─→ Isolation begins

ANTI-CRYPTOCURRENCY
  │
  ├─ Reads: Message content
  ├─ Reads: Detection patterns
  ├─ Writes: Detection history
  └─ Emits: THREAT_DETECTED signal
      │
      ├─→ Triggers: Auto-Escalation
      │   ├─→ Routes: On-call responder
      │   └─→ Executes: Appropriate action
      │
      └─→ Triggers: Auto-Quarantine
          ├─→ Isolates: User
          └─→ Preserves: Evidence

AUTO-QUARANTINE
  │
  ├─ Reads: Signal Bus (high confidence threats)
  ├─ Reads: Member join events
  ├─ Writes: Quarantine entries
  ├─ Writes: Evidence vault
  ├─ Manages: Quarantine role
  ├─ Creates: Isolation channel
  └─ Emits: POLICY_VIOLATION signal

BLACKLIST SYSTEM
  │
  ├─ Reads: Member join events
  ├─ Reads: Blacklist entries
  ├─ Writes: Blacklist entries
  ├─ Writes: Appeal queue
  ├─ Emits: POLICY_VIOLATION signal
  └─ Auto-enforces: On join
```

---

## Configuration & Management

```
CONFIGURATION HIERARCHY

┌─ Signal Bus (config.json)
│  ├─ Dedup window: 300s
│  ├─ Max history: 10,000
│  └─ Subscriber limit: 100
│
├─ Auto-Escalation
│  ├─ Escalation rules (per threat type)
│  ├─ On-call assignment
│  └─ Response levels (1-5)
│
├─ Anti-Crypto
│  ├─ Wallet patterns (regex)
│  ├─ Mining domains (list)
│  └─ Scam keywords (list)
│
├─ Auto-Quarantine
│  ├─ Confidence threshold: 85%
│  ├─ Quarantine role name: "Quarantine"
│  ├─ Channel name: "quarantine-isolation"
│  └─ Evidence vault size: 10,000
│
└─ Blacklist
   ├─ Tier definitions (temp/permanent/appeal)
   ├─ Appeal rules (max 3/month)
   ├─ TTL for temporary entries
   └─ Type categories (user/guild/ip/domain/email)
```

---

**Updated**: February 2, 2025 | **Version**: 1.0
