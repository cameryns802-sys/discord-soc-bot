# System Architecture Diagram

## Overall System Flow

```
                        ┌─────────────────────────┐
                        │    DISCORD BOT MAIN      │
                        │    (bot.py)             │
                        └────────────┬────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
    ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
    │   COMMANDS   │        │    EVENTS    │        │   SIGNALS    │
    │   & COGS     │        │              │        │              │
    └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
           │                       │                       │
           │                       ▼                       │
           │            ┌─────────────────┐                │
           │            │   ON_MESSAGE    │                │
           │            │   ON_MEMBER_*   │                │
           │            │   ON_REACTION   │                │
           │            └────────┬────────┘                │
           │                     │                         │
           ├─────────────────────┼─────────────────────────┘
           │                     │
           ▼                     ▼
    ┌──────────────────────────────────────────┐
    │        SECURITY & COMPLIANCE COGS        │
    │                                          │
    │  • anomaly_detection_simple              │
    │  • automod                               │
    │  • anti_phishing                         │
    │  • threat_hunting_simple                 │
    │  • pii_detection_simple                  │
    │  • incident_management_simple            │
    │  • [etc.]                                │
    └─────────────┬──────────────┬─────────────┘
                  │              │
         ANALYZE/ │              │ DECIDE/
         DETECT   │              │ ACT
                  │              │
                  ▼              ▼
    ┌─────────────────────────────────────────┐
    │        CORE INFRASTRUCTURE LAYER        │
    │                                         │
    │  ┌──────────────────────────────────┐   │
    │  │ 1. SIGNAL BUS                    │   │
    │  │    (Central Event Pipeline)      │   │
    │  │    - Deduplication              │   │
    │  │    - History Tracking            │   │
    │  │    - Subscriber Pattern          │   │
    │  └──────────────────────────────────┘   │
    │                  │                       │
    │  ┌──────────────┼──────────────────┐    │
    │  │              │                  │    │
    │  ▼              ▼                  ▼    │
    │┌───────────────────────────────────────┐│
    ││ 2. FEATURE FLAGS      3. POLICIES    ││
    ││    • Enable/Disable       • Confidence  ││
    ││    • Kill Switch           • Thresholds ││
    ││    • Safe Mode             • Overrides  ││
    │└───────────────────────────────────────┘│
    │  │              │                  │    │
    │  │              ▼                  ▼    │
    │  │  ┌──────────────┐  ┌────────────────┐│
    │  │  │4. ABSTENTION │  │5. PROMPT INJ   ││
    │  │  │  POLICY      │  │   DETECTOR     ││
    │  │  │              │  │                ││
    │  │  │ "I don't     │  │ Protect against││
    │  │  │  know"       │  │ adversarial AI ││
    │  │  │              │  │ attacks        ││
    │  │  └──────────────┘  └────────────────┘│
    │  │         │                    │        │
    │  └─────────┼────────────────────┘        │
    │            │                             │
    └────────────┼─────────────────────────────┘
                 │
    ┌────────────▼──────────────────┐
    │ DECISION LOGIC EVALUATOR      │
    │                               │
    │  Is Feature Enabled?          │
    │  -> YES                        │
    │  ├─ Is Input Safe?            │
    │  │  -> YES                    │
    │  │  ├─ Is Confidence >= 0.65? │
    │  │  │  -> YES                 │
    │  │  │  ├─ EXECUTE DECISION    │
    │  │  │  │                      │
    │  │  │  └─ NO                  │
    │  │  │     ABSTAIN & ESCALATE  │
    │  │  │                         │
    │  │  └─ NO                     │
    │  │     BLOCK INPUT            │
    │  │                            │
    │  └─ NO                        │
    │     FEATURE DISABLED          │
    └────────────┬───────────────────┘
                 │
    ┌────────────▼──────────────────────────┐
    │     EXECUTION & TRACKING              │
    │                                       │
    │  1. Execute Action                   │
    │  2. Emit Signal (to signal_bus)      │
    │  3. Store in signal history          │
    │  4. Track in human_override_tracker  │
    │  5. Log decision confidence          │
    └─────────────────────────────────────-┘
                 │
    ┌────────────▼─────────────────────────┐
    │ HUMAN REVIEW (If Needed)             │
    │                                      │
    │ Human Reviews Decision?              │
    │ ├─ AGREES: No action needed          │
    │ └─ DISAGREES:                        │
    │    ├─ Log override                   │
    │    ├─ Record feedback reason         │
    │    └─ Update confidence data         │
    └──────────────────────────────────────┘
```

---

## Signal Types & Flow

```
        SECURITY EVENTS
             │
    ┌────────┼────────────┐
    │        │            │
    ▼        ▼            ▼
BEHAVIOR  POLICY        COMPLIANCE
ANOMALY   VIOLATION     ISSUE
    │        │            │
    │        │            ▼
    │        │      COMPLIANCE_ISSUE
    │        │      (severity: high)
    │        │
    │        ▼
    │    POLICY_VIOLATION
    │    (severity: high)
    │
    ▼
ANOMALY_DETECTED
(severity: variable)
    │
    ├─────────────┬──────────────┐
    │             │              │
    ▼             ▼              ▼
LOGIN      MESSAGE      MEMBER
ANOMALY    ANOMALY      BEHAVIOR
    │             │          │
    └─────────────┼──────────┘
                  │
                  ▼
    ┌─────────────────────────┐
    │   SIGNAL BUS EMITS      │
    │   DEDUPLICATES          │
    │   STORES HISTORY        │
    │   NOTIFIES SUBSCRIBERS  │
    └────────────┬────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
 HANDLER_1   HANDLER_2   HANDLER_3
(Automod)   (Escalate) (Logging)
    │            │            │
    └────────────┼────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │ ACTION QUEUE / RESPONSE  │
    │ (All tracked)            │
    └──────────────────────────┘
```

---

## Feature Flag Decision Tree

```
                    START
                     │
                     ▼
        ┌─────────────────────────┐
        │ Is feature whitelisted? │
        └────────┬────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       NO                YES
        │                 │
        ▼                 ▼
    RETURN          ┌────────────────┐
    (Feature        │ Is flag enabled?│
    Disabled)       └────┬───────────┘
                        │
                    ┌───┴───┐
                   NO      YES
                    │       │
                    ▼       ▼
                 RETURN   PROCEED
               (Disabled)(Feature
                         Active)
```

---

## Abstention Flow

```
            AI MAKES DECISION
                   │
                   ▼
        ┌──────────────────────────┐
        │ Calculate Confidence     │
        │ (based on data/evidence) │
        └────────┬─────────────────┘
                 │
        ┌────────▼─────────┐
        │ Check Thresholds │
        └────────┬─────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
    MIN      UNCERT      DISAGREE
  CONF       AINT        MENT
     │           │           │
     ▼           ▼           ▼
  >= 0.65    <= 0.35    <= 0.20
     │           │           │
    YES/NO      YES/NO      YES/NO
     │           │           │
     └─────┬─────┴─────┬─────┘
           │           │
        PASS       FAIL (any)
           │           │
       ┌───┴───┐       │
       │       │       ▼
      YES     NO   ┌──────────────┐
       │       │   │ ABSTAIN      │
       │       │   │ ESCALATE TO  │
       │       │   │ HUMAN        │
       │       │   └──────┬───────┘
       │       │          │
       │       │   Log in abstention
       │       │   policy tracker
       │       │          │
       │       │   human_override
       │       │   _tracker.log()
       │       │          │
       │       │          ▼
       │       │   Return to User:
       │       │   "Uncertain - review needed"
       │       │
       │       └─ Continue with DECIDE
       │
       ▼
   ┌──────────┐
   │ PROCEED  │
   │ DECIDE   │
   └──────────┘
```

---

## Human Override Feedback Loop

```
    AI DECISION MADE
    (logged in signal_bus)
           │
           ▼
    ┌─────────────────┐
    │ Signal Emitted  │
    │ Stored in       │
    │ History         │
    └────────┬────────┘
             │
             ▼
    ┌──────────────────────┐
    │ Owner Reviews        │
    │ /overridelog         │
    └────────┬─────────────┘
             │
        ┌────┴────┐
        │          │
      AGREES   DISAGREES
        │          │
        │          ▼
        │    ┌────────────────────┐
        │    │ Human Logs Override│
        │    │ • AI decision      │
        │    │ • Human decision   │
        │    │ • Reason why       │
        │    └────────┬───────────┘
        │             │
        │             ▼
        │    ┌──────────────────────┐
        │    │ Log in Tracker       │
        │    │ (human_override      │
        │    │  _tracker.py)        │
        │    └────────┬─────────────┘
        │             │
        │             ▼
        │    ┌──────────────────────┐
        │    │ Analytics:           │
        │    │ • Override rate      │
        │    │ • By system          │
        │    │ • Patterns           │
        │    │ • Bias detection     │
        │    └────────┬─────────────┘
        │             │
        │             ▼
        │    ┌──────────────────────┐
        │    │ Model Improvement:   │
        │    │ • Adjust thresholds  │
        │    │ • Add training data  │
        │    │ • Tune confidence    │
        │    └──────────────────────┘
        │
        └─ Do Nothing (agreement)
```

---

## Bot Startup Sequence

```
    python bot.py
         │
         ▼
    ┌──────────────────────┐
    │ Load .env            │
    │ (TOKEN, OWNER_ID)    │
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Initialize Intents   │
    │ Discord.Intents.all()│
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Create Bot Instance  │
    │ (CustomBot)          │
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Define Slash Commands│
    │ (/ping, /userinfo)   │
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ load_cogs()          │
    │                      │
    │ For each cog in      │
    │ whitelisted:         │
    │  └─ bot.load_ext()   │
    │     │                │
    │     ├─ core/*        │
    │     ├─ security/*    │
    │     ├─ moderation/*  │
    │     ├─ compliance/*  │
    │     └─ other/*       │
    └─────────┬────────────┘
              │
              ├─ Each cog
              │ imports
              │ core systems
              │
              ▼
    ┌──────────────────────┐
    │ Bot.start(TOKEN)     │
    │ Connect to Discord   │
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Bot Ready ✓          │
    │ (on_ready event)     │
    │ (sync slash commands)│
    └─────────┬────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Listening for:       │
    │ • Messages           │
    │ • Member joins       │
    │ • Member leaves      │
    │ • Slash commands     │
    │ • Reactions          │
    └──────────────────────┘
```

---

## Data Persistence

```
    ┌─────────────────────────────────────┐
    │        SIGNAL BUS                   │
    │                                     │
    │  Memory: signal_history (deque)     │
    │  Disk: n/a (live tracking)          │
    │  Max: 10,000 signals in memory      │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │        FEATURE FLAGS                │
    │                                     │
    │  Memory: flags dict                 │
    │  Disk: data/feature_flags.json      │
    │  Updated: When flag changes         │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │        HUMAN OVERRIDES              │
    │                                     │
    │  Memory: overrides list             │
    │  Disk: data/human_overrides.json    │
    │  Updated: When override logged      │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │        ABSTENTION POLICY            │
    │                                     │
    │  Memory: thresholds dict            │
    │  Disk: data/abstention_policy.json  │
    │  Updated: When threshold changes    │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │        PROMPT INJECTION             │
    │                                     │
    │  Memory: patterns & sequences       │
    │  Disk: n/a (static)                 │
    │  Updated: Never (hardcoded)         │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │        OTHER COGS                   │
    │                                     │
    │  Memory: varies                     │
    │  Disk: data/*.json                  │
    │  Updated: Per cog implementation    │
    └─────────────────────────────────────┘
```

---

## Command Groups & Hierarchy

```
SLASH COMMANDS (Global)
│
├─ /flags
│  ├─ View all feature statuses
│  └─ Owner-only
│
├─ /killfeature <name>
│  ├─ Emergency stop a feature
│  └─ Owner-only
│
├─ /safemode on|off|status
│  ├─ Enable/disable safe mode
│  └─ Owner-only
│
├─ /signalstats
│  ├─ View signal pipeline statistics
│  └─ Owner-only
│
├─ /abstentionstats
│  ├─ View AI abstention frequency
│  └─ Owner-only
│
├─ /setabstentionthreshold <name> <value>
│  ├─ Tune confidence thresholds
│  └─ Owner-only
│
├─ /overridestats
│  ├─ View human override statistics
│  └─ Owner-only
│
├─ /overridelog <limit>
│  ├─ View recent human overrides
│  └─ Owner-only
│
├─ /testprompt <text>
│  ├─ Test for prompt injection
│  └─ Owner-only
│
└─ [9 security system commands]
   ├─ /alertcreate, /alertresolve, etc.
   ├─ /anomalyscan, /anomalyreport, etc.
   ├─ [etc.]
   └─ Mixed slash/prefix

PREFIX COMMANDS (Owner-only, ! prefix)
│
├─ !flags
├─ !signalstats
├─ !abstentionstats
├─ !overridestats
│
└─ [9 security system commands - prefix versions]
   ├─ !alertack, !alertassign, etc.
   ├─ !anomalybaseline, !anomalytrain, etc.
   ├─ [etc.]
```

---

## This diagram shows:**

1. **How events flow** from Discord through cogs to core infrastructure
2. **Signal deduplication & distribution** in the signal bus
3. **Decision making** with confidence thresholds
4. **Human feedback** loops and override tracking
5. **Feature control** through flags
6. **AI safety** via prompt injection detection
7. **Data persistence** across all systems
8. **Complete startup sequence**

**Key insight:** Everything feeds into the core infrastructure layer, which applies consistent policies and tracking across all systems.
