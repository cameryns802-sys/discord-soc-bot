# 🔐 THREAT SYSTEMS QUICK REFERENCE

**4 New Enterprise-Grade Security Systems** | Feb 2, 2025

---

## 🚀 SYSTEMS AT A GLANCE

### 1️⃣ AUTO-ESCALATION SYSTEM
**What**: Smart threat routing to responders  
**Triggers**: High-confidence threats  
**Actions**: Log → Alert → Timeout → Ban → Lockdown  

```bash
!setescalationrule <threat_type> <confidence> <action>
!escalationstats
!setonc <member>           # Set on-call responder
```

---

### 2️⃣ ANTI-CRYPTOCURRENCY SYSTEM
**What**: Detect wallets, mining malware, crypto scams  
**Detects**:
- 🪙 Wallet addresses (Ethereum, Bitcoin, Monero, Dogecoin)
- ⛏️ Mining malware (Coinhive, Cryptoloot, WebMiner)
- 🚨 Crypto scams ("moon shot", "guaranteed returns", etc.)

```bash
!cryptodetections [days]   # View detections
!cryptostats               # Statistics
!checkcrypto <text>        # Scan text
```

---

### 3️⃣ AUTO-QUARANTINE SYSTEM
**What**: Auto-isolate high-confidence threats  
**Does**:
- 🚫 Removes all roles → adds "Quarantine" role
- 📝 Preserves evidence for forensics
- ⏳ Pending manual review/appeal
- ✅ Can be released on appeal approval

```bash
!quarantineuser <member> <reason>       # Manual
!quarantinestatus [member]              # View
!quarantineevidence <member>            # Evidence
!unquarantineuser <member> <reason>     # Release
```

---

### 4️⃣ BLACKLIST SYSTEM
**What**: Permanent/temporary blacklisting with appeals  
**Types**: User ID, Guild ID, IP, Domain, Email  
**Tiers**:
- 🔴 TEMPORARY (30 days) → auto-expires
- 🟠 APPEAL_ELIGIBLE → can appeal  
- ⚫ PERMANENT → manual lift only

```bash
!blacklist <type> <value> [days] <reason>
!unblacklist <type> <value>
!appeal <type> <value> <reason>         # User appeal
!blacklistreviews                       # View pending
!reviewappeal <entry_id> approve|deny   # Owner decision
!checkblacklist <type> <value>
```

---

## 🔗 HOW THEY WORK TOGETHER

```
MESSAGE/ACTION
  │
  ├─ Anti-Crypto detects pattern
  │   └─ THREAT_DETECTED signal (95% confidence)
  │
  ├─ Auto-Escalation evaluates
  │   └─ Routes to appropriate response level
  │
  ├─ Auto-Quarantine (if >85% confidence)
  │   ├─ Isolates user
  │   └─ Preserves evidence
  │
  └─ Blacklist (if repeated violations)
      └─ Adds to blacklist with appeals option
```

---

## ⚡ QUICK COMMANDS

| System | Command | Purpose |
|--------|---------|---------|
| **Escalation** | `!escalationstats` | View stats |
| **Escalation** | `!setonc @user` | Set responder |
| **Crypto** | `!cryptodetections 7` | Last 7 days |
| **Crypto** | `!checkcrypto <text>` | Scan text |
| **Quarantine** | `!quarantineuser @user` | Manual quarantine |
| **Quarantine** | `!quarantinestats` | View stats |
| **Blacklist** | `!blacklist user 123 30 Spam` | Add (30 days) |
| **Blacklist** | `!appeal user 123 I'm sorry` | User appeal |
| **Blacklist** | `!reviewappeal user:123 approve` | Owner decision |

---

## 🎯 THREAT RESPONSE FLOW

```
Severity:  LOW → MEDIUM → HIGH → CRITICAL
Confidence: 40% → 60% → 80% → 95%
Action:    LOG → ALERT → TIMEOUT → BAN+LOCKDOWN
```

### Example Crypto Detection
```
Message: "BUY NOW! 0x123... moon shot guaranteed!"

Detection:
├─ Wallet address (95% confidence)
└─ Scam language (80% confidence)

Response:
├─ ✅ Delete message
├─ ⚠️ Warn user
├─ 🚨 Alert moderators
└─ On 2nd violation → Timeout
```

---

## 📊 DATA STORAGE

All systems save to `data/` folder:
- `auto_escalation.json` - Rules & history
- `auto_quarantine.json` - Quarantine entries & evidence
- `crypto_detection.json` - Crypto detections
- `blacklist.json` - Blacklist & appeals

---

## 🔧 CUSTOMIZATION

### Add Escalation Rule
```python
!setescalationrule raid users_per_minute lockdown
```

### Set On-Call Responder
```python
!setonc @SecurityLead
```

### Check Crypto Patterns
```python
!checkcrypto "Send to 0x1234567890abcdef for airdrop"
# Detects Ethereum wallet + scam language
```

---

## ✅ VERIFICATION

After startup, check for:
```
[Loader] ✅ auto_escalation_system
[Loader] ✅ anti_cryptocurrency_system
[Loader] ✅ auto_quarantine_system
[Loader] ✅ blacklist_system
```

All systems are **always active** and **automatically enforced** on threats.

---

## 💡 KEY FEATURES

✨ **Auto-Escalation**
- Confidence-based routing
- On-call responder notifications
- Configurable rules per threat type
- Full audit trail

✨ **Anti-Crypto**
- 4 wallet types detected
- Mining malware patterns
- Scam language detection
- Real-time message scanning

✨ **Auto-Quarantine**
- Automatic isolation (>85% confidence)
- Evidence preservation
- Forensic analysis ready
- Appeal process available

✨ **Blacklist**
- Multi-type support (user/guild/IP/domain/email)
- Tiered enforcement (temp/appeal/permanent)
- Appeals with review process
- Auto-expiration for temporary bans

---

**Status**: ✅ ALL SYSTEMS ACTIVE | **Last Updated**: Feb 2, 2025
