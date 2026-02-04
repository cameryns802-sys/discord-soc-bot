# 🔐 ADVANCED THREAT SYSTEMS - NEW ADDITIONS

**Date**: February 2, 2025  
**Scope**: 4 New Enterprise-Grade Security Systems  
**Status**: ✅ COMPLETE & WIRED TO SIGNAL BUS

---

## 📋 SUMMARY

Added 4 sophisticated threat detection and response systems to strengthen the SOC's defensive posture:

| System | File | Function | Status |
|--------|------|----------|--------|
| **Auto-Escalation** | `auto_escalation_system.py` | Intelligent threat escalation to on-call responders | ✅ ACTIVE |
| **Anti-Cryptocurrency** | `anti_cryptocurrency_system.py` | Block crypto wallets, mining malware, scams | ✅ ACTIVE |
| **Auto-Quarantine** | `auto_quarantine_system.py` | Isolation of high-confidence threats | ✅ ACTIVE |
| **Blacklist System** | `blacklist_system.py` | User/guild/IP/domain blacklisting with appeals | ✅ ACTIVE |

All systems are **automatically loaded** in `bot.py` essential_cogs and **wired to the signal bus** for real-time coordination.

---

## 🚀 SYSTEM 1: AUTO-ESCALATION SYSTEM

**File**: `cogs/security/auto_escalation_system.py`

### Purpose
Automatically routes security threats to appropriate responders based on severity, confidence, and threat type. Implements intelligent escalation rules with on-call responder notification.

### Key Features
- **Threat Evaluation**: Analyzes severity + confidence to determine escalation level (1-5)
- **Automated Actions**:
  - Level 1: Log only (no action)
  - Level 2: Log and watch
  - Level 3: Alert moderators
  - Level 4: Timeout users (1 hour)
  - Level 5: Ban + server lockdown
  
- **On-Call Routing**: Routes critical threats (>80% confidence) to designated responders
- **Configurable Rules**: Customize escalation behavior per threat type
- **History Tracking**: Full audit trail of all escalations

### Commands
```
!setescalationrule <threat_type> <confidence_level> <action>
!escalationhistory [limit]
!setonc <member>
!escalationstats
```

### Example Flow
```
1. THREAT_DETECTED signal (phishing, 90% confidence)
   ↓
2. Auto-Escalation evaluates: high severity + high confidence = Level 4
   ↓
3. Executes: timeout_user (1 hour)
   ↓
4. Notifies on-call responder
   ↓
5. Records escalation in history
```

### Integration Points
- **Signal Bus**: Subscribes to `SignalType.THREAT_DETECTED`
- **On-Call Manager**: Routes to designated responders
- **Audit Trail**: All actions logged for forensics

---

## 🛡️ SYSTEM 2: ANTI-CRYPTOCURRENCY SYSTEM

**File**: `cogs/security/anti_cryptocurrency_system.py`

### Purpose
Detects and blocks cryptocurrency wallet addresses, mining malware, and crypto scams. Protects against financial fraud, ransomware wallets, and hidden mining.

### Detection Methods

#### 1. **Wallet Address Detection** (95% confidence)
```
Ethereum: 0x[40 hex chars]
Bitcoin: bc1/1/3 + 25-39 alphanumeric
Monero: 4[0-9AB] + 94 chars
Dogecoin: D[5-9A-HJ-NP-U] + 32 chars
```

#### 2. **Mining Malware Detection** (85-90% confidence)
- Domain patterns: `coinhive.com`, `cryptoloot.io`, `deepminer.io`
- Script tags: `<script src="...miner...">`
- Script names: CoinHive, Cryptoloot, WebMiner

#### 3. **Crypto Scam Language** (50-99% confidence)
- **Keywords**: "pump and dump", "moon shot", "guaranteed returns", "blockchain opportunity"
- **Confidence boost**: Multiple keywords = higher confidence
- **Urgency tactics**: "now", "urgent", "limited time" + scam keywords = escalation

### Detection Workflow
```
MESSAGE RECEIVED
  ├─ Wallet Check: Ethereum/Bitcoin/Monero addresses?
  ├─ Mining Check: Coinhive/cryptoloot patterns?
  └─ Scam Check: Urgency + crypto keywords?
     ↓ If detected:
     ├─ Delete message
     ├─ Log detection
     ├─ Emit signal (severity = critical/high)
     ├─ Warn user
     └─ Record in detection history
```

### Commands
```
!cryptodetections [days]  # View detections in last N days
!cryptostats              # Overall crypto activity statistics
!checkcrypto <text>      # Scan text for crypto activity (owner only)
```

### Example Detections
```
Message: "Buy this coin and MOON SHOT with 0x1234567890abcdef..."
         ↓
Detections:
  1. Ethereum wallet (confidence: 95%)
  2. Scam language: "moon shot" (confidence: 78%)
  ↓ Action: DELETE + WARN
```

### Integration Points
- **Signal Bus**: Emits `THREAT_DETECTED` with crypto patterns
- **Message Listener**: Real-time content monitoring
- **Evidence**: Records all detections for forensics

---

## 🔒 SYSTEM 3: AUTO-QUARANTINE SYSTEM

**File**: `cogs/security/auto_quarantine_system.py`

### Purpose
Automatically isolates users showing high-confidence threat indicators into a quarantine role/channel with forensic evidence preservation.

### Quarantine Process

#### Step 1: Threat Detection
```
High-confidence threat detected (>85%)
├─ Malware indicators
├─ Phishing attempts
├─ Harassment patterns
├─ Raid activity
└─ Exploit code
```

#### Step 2: Isolation
```
User quarantined:
├─ Remove all roles
├─ Add "Quarantine" role
├─ Move to quarantine channel (read-only)
├─ Send isolation notice
└─ Preserve evidence
```

#### Step 3: Evidence Preservation
```
Evidence vault:
├─ Signal data snapshot
├─ Chain of custody
├─ Threat source & severity
├─ Confidence score
└─ Timestamp
```

#### Step 4: Review & Release
```
Manual review:
├─ Analyze evidence
├─ Approve appeal OR
├─ Maintain quarantine
└─ Release if cleared
```

### Quarantine Reasons
- `malware` - Malware indicators
- `phishing` - Phishing attempts
- `harassment` - Harassment/toxicity
- `spam` - Spam activity
- `raid` - Raid participation
- `exploit` - Exploit code
- `manual_quarantine` - Manual admin decision

### Commands
```
!quarantineuser <member> [reason]     # Manually quarantine
!unquarantineuser <member> [reason]   # Release from quarantine
!quarantinestatus [member]             # View quarantine details
!quarantineevidence <member>           # View threat evidence
!quarantinestats                       # Overall stats
```

### Quarantine Channel
Automatically creates `#quarantine-isolation` with:
- Read-only access for quarantine role
- Full access for admins
- Evidence logging
- Isolation notices

### Integration Points
- **Signal Bus**: Subscribes to high-confidence threats
- **Role Management**: Creates/manages Quarantine role
- **Evidence Vault**: Forensic preservation
- **Notifications**: User alerts & admin logs

---

## 🚫 SYSTEM 4: BLACKLIST SYSTEM

**File**: `cogs/security/blacklist_system.py`

### Purpose
Comprehensive user/guild/IP/domain blacklisting with tiered severity, appeals process, and automatic enforcement.

### Blacklist Types
- `user` - Discord user ID
- `guild` - Discord guild/server ID
- `ip` - IP address
- `domain` - Domain name
- `email` - Email address

### Blacklist Tiers

| Tier | Duration | Appeals | Lift |
|------|----------|---------|------|
| **TEMPORARY** | Auto-expires | ❌ No | Automatic |
| **APPEAL_ELIGIBLE** | Permanent | ✅ Yes | Appeal approved |
| **PERMANENT** | Forever | ❌ No | Manual only |

### Blacklist Enforcement

#### On User Join
```
Member joins
  ↓
Check blacklist (user ID)
  ├─ Found → DM + Kick
  └─ Not found → Allow join
```

#### Automatic Actions
- Prevent blacklisted users from joining
- Block blacklisted domains in messages
- Quarantine blacklisted IP activity

### Appeals Process

#### Step 1: Submit Appeal
```
User submits: /appeal user <id> <reason>
  ├─ Check if eligible
  ├─ Check recent appeals (max 3/month)
  └─ Submit for review
```

#### Step 2: Review
```
Owner reviews appeal:
  ├─ View evidence
  ├─ Approve → Remove from blacklist
  └─ Deny → User notified
```

### Commands
```
!blacklist <type> <value> [duration] <reason>  # Add to blacklist
!unblacklist <type> <value>                    # Remove from blacklist
!checkblacklist <type> <value>                 # Check if blacklisted
!appeal <type> <value> <reason>                # Submit appeal
!blacklistreviews [limit]                      # Review pending appeals
!reviewappeal <entry_id> <approve|deny>        # Decide on appeal
!blackliststats                                # Statistics
```

### Example Usage
```
# Add user to blacklist (temp, 30 days)
!blacklist user 123456789 30 Harassing members

# Add domain to blacklist (permanent)
!blacklist domain phishing-site.com 0 Confirmed phishing

# User appeals
!appeal user 123456789 I'm sorry, won't happen again

# Owner reviews
!reviewappeal user:123456789 approve Behavior improved

# User is unbanned
```

### Integration Points
- **Signal Bus**: Emits policy violation signals
- **Member Join Event**: Automatic enforcement
- **Message Content**: Domain/email detection
- **Appeal System**: Full workflow management

---

## 🔗 SIGNAL BUS INTEGRATION

All 4 systems are wired to the **central signal bus**:

### Auto-Escalation
```
Input Signals: 
  - THREAT_DETECTED (all sources)
  
Output Signals:
  - ESCALATION_REQUIRED (critical threats)
  - Policy violations logged
```

### Anti-Cryptocurrency
```
Input Signals:
  - On-message events (real-time scanning)
  
Output Signals:
  - THREAT_DETECTED (high confidence)
  - Crypto activity recorded
```

### Auto-Quarantine
```
Input Signals:
  - THREAT_DETECTED (>85% confidence)
  
Output Signals:
  - POLICY_VIOLATION (user quarantined)
  - Evidence preserved
  
On Member Join:
  - Auto-enforcement of active quarantines
```

### Blacklist System
```
Input Signals:
  - Manual blacklist additions
  - Message scanning for patterns
  
Output Signals:
  - POLICY_VIOLATION (entry added)
  - Audit trail created
  
On Member Join:
  - Auto-kick if blacklisted
```

---

## ⚙️ CONFIGURATION

### Essential Systems in bot.py
```python
'auto_escalation_system',     # Auto-escalate threats
'auto_quarantine_system',     # Isolate high-confidence threats
'anti_cryptocurrency_system', # Block crypto scams/wallets
# 'blacklist_system' already existed
```

### Escalation Rules (Customizable)
```python
escalation_rules = {
    'threat_detected': {
        'low_confidence': {'threshold': 0.4, 'action': 'log'},
        'medium_confidence': {'threshold': 0.6, 'action': 'alert_mods'},
        'high_confidence': {'threshold': 0.8, 'action': 'timeout'},
        'critical_confidence': {'threshold': 0.95, 'action': 'ban'},
    }
}
```

### Crypto Detection Patterns
```python
ethereum = r'0x[a-fA-F0-9]{40}'       # 40 hex chars
bitcoin = r'(bc1|[13])[...]{25,39}'   # BTC formats
monero = r'4[0-9AB][...]{93}'         # XMR format
```

### Quarantine Configuration
```python
# Auto-created resources:
- "Quarantine" role (red, read-only)
- "#quarantine-isolation" channel (private)
- Evidence vault (JSON)
```

---

## 📊 MONITORING & ANALYTICS

### Auto-Escalation Dashboard
```
!escalationstats
├─ Total escalations
├─ Actions taken breakdown
├─ Severity distribution
└─ On-call responder assignments
```

### Anti-Crypto Dashboard
```
!cryptodetections [days]
├─ Detection types
├─ Top violators
├─ Confidence scores
└─ Detection timeline
```

### Quarantine Dashboard
```
!quarantinestats
├─ Active quarantines
├─ Released users
├─ Evidence count
└─ Reasons breakdown
```

### Blacklist Dashboard
```
!blackliststats
├─ Total entries
├─ By type (user/guild/ip/domain/email)
├─ By tier (temporary/permanent/appealable)
└─ Pending appeals count
```

---

## 🔄 WORKFLOW EXAMPLES

### Example 1: Phishing Attack Response
```
1. USER sends phishing link
   ├─ anti_phishing detects → emits THREAT_DETECTED (90% confidence)
   │
2. auto_escalation_system receives signal
   ├─ Evaluates: high severity + high confidence = Level 4 (timeout)
   ├─ Executes: timeout user 1 hour
   ├─ Notifies: on-call responder
   │
3. auto_quarantine_system receives signal (if enabled)
   ├─ Checks: confidence > 85%? → YES
   ├─ Quarantines: user in isolation role
   ├─ Preserves: evidence (link, confidence, timestamp)
   │
4. intelligent_threat_response receives escalation
   ├─ Emits: alert to #mod-logs
   ├─ Notifies: moderators
   ├─ Responds: bans repeaters after 2+ violations
```

### Example 2: Crypto Wallet Post Detection
```
1. USER posts "Earn crypto! Send to 0x1234567890abcdef!"
   ├─ anti_cryptocurrency detects:
   │  ├─ Ethereum wallet address (95% confidence)
   │  └─ Scam language "Earn crypto" + urgency (80% confidence)
   │
2. System response:
   ├─ Deletes message
   ├─ Logs detection
   ├─ Emits THREAT_DETECTED (high severity)
   ├─ Warns user: "Crypto activity prohibited"
   │
3. auto_escalation_system:
   ├─ Confidence: 87.5% average
   ├─ Action: Alert moderators (Level 3)
   ├─ Notifies: #mod-logs channel
   │
4. On 2nd violation → Auto timeout
```

### Example 3: Quarantine & Appeal
```
1. User caught with malware attachment (98% confidence)
   ├─ auto_quarantine isolates immediately
   ├─ Moves to #quarantine-isolation (read-only)
   ├─ Evidence preserved
   ├─ User notified
   │
2. User submits appeal:
   ├─ /appeal user <id> "My account was hacked"
   ├─ Added to pending review queue
   ├─ Owner notified
   │
3. Owner reviews:
   ├─ Views evidence vault
   ├─ Makes decision: approve/deny
   ├─ If approved:
   │  ├─ Removes from blacklist
   │  ├─ Restores roles
   │  ├─ Notifies user
   └─ Full audit trail maintained
```

---

## 🎯 NEXT STEPS

These systems work independently AND together via the signal bus:

1. **Real-world testing** in production
2. **Tune escalation rules** based on patterns
3. **Add more crypto patterns** as new scams emerge
4. **Integrate with on-call manager** for responder assignment
5. **Archive quarantined evidence** for compliance audits

---

## 📝 DATA STORAGE

All systems use JSON-based persistent storage:

```
data/
├── auto_escalation.json         # Escalation rules & history
├── auto_quarantine.json          # Quarantine entries & evidence
├── crypto_detection.json         # Crypto detections log
└── blacklist.json               # Blacklist entries & appeals
```

---

## ✅ VERIFICATION

To verify all systems are loaded:

```
python bot.py

Expected output:
[Loader] ✅ auto_escalation_system
[Loader] ✅ anti_cryptocurrency_system
[Loader] ✅ auto_quarantine_system
[Loader] ✅ blacklist_system
```

---

**Status**: ✅ COMPLETE | **Date**: February 2, 2025
