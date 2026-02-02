# 🚨 Drill & Threat Status Integration

## Overview
The bot's dynamic status now automatically changes based on active security drills and threats, providing real-time visual feedback across Discord.

---

## 📊 Status Levels

### **🟢 Normal (Green - Online)**
- Default state when no drills or threats active
- Rotating messages: "All systems nominal", "Security operations running", etc.
- **Bot Presence:** 🟢 Online

### **🛡️ Drill Mode (Yellow - Idle)**
- Activated when security drill is running
- Shows drill type and protocol in status
- Rotating messages: "SECURITY DRILL ACTIVE", "DRILL IN PROGRESS", etc.
- **Bot Presence:** 🟡 Idle

### **🟡 Elevated (Yellow - Idle)**
- Triggered by HIGH severity threats
- Indicates increased monitoring and investigation
- Rotating messages: "Elevated threat level", "Monitoring increased activity", etc.
- **Bot Presence:** 🟡 Idle

### **🔴 Panic/Critical (Red - Do Not Disturb)**
- Triggered by CRITICAL severity threats
- Maximum alert state requiring immediate response
- Rotating messages: "CRITICAL THREAT DETECTED", "EMERGENCY RESPONSE ACTIVE", etc.
- **Bot Presence:** 🔴 Do Not Disturb

### **⚫ Lockdown (Red - Do Not Disturb)**
- System under active attack
- All defensive measures activated
- Rotating messages: "LOCKDOWN INITIATED", "SYSTEM UNDER ATTACK", etc.
- **Bot Presence:** 🔴 Do Not Disturb

---

## 🛡️ Security Drill Integration

### **Drill Activation**
When you activate a security drill with `!activate_drill`:

```bash
!activate_drill BREACH BLACK
```

**What happens:**
1. ✅ Drill is created and logged
2. ✅ Bot status changes to **🛡️ DRILL MODE**
3. ✅ Status shows: "🛡️ SECURITY DRILL ACTIVE | BREACH - BLACK"
4. ✅ All guild channels receive drill notification
5. ✅ Bot presence changes to 🟡 Idle

**Status Message Examples:**
- "🛡️ SECURITY DRILL ACTIVE | BREACH - BLACK"
- "🛡️ DRILL IN PROGRESS | RANSOMWARE - RED"
- "🛡️ THIS IS A DRILL | PHISHING - YELLOW"

### **Drill Deactivation**
When you reset the drill with `!drill_reset`:

```bash
!drill_reset
```

**What happens:**
1. ✅ Drill marked as COMPLETED
2. ✅ Bot status returns to **🟢 NORMAL**
3. ✅ Status shows: "🟢 All systems nominal"
4. ✅ Bot presence returns to 🟢 Online

---

## 🚨 Threat Status Integration

### **Adding Critical/High Threats**
When you add a CRITICAL or HIGH severity threat:

```bash
!exec_add_threat critical ransomware Targeted ransomware campaign detected
```

**What happens:**
1. ✅ Threat is logged in executive briefing system
2. ✅ Bot status changes based on severity:
   - **CRITICAL** → 🔴 Panic Mode
   - **HIGH** → 🟡 Elevated Mode
3. ✅ Status shows: "🔴 CRITICAL THREAT DETECTED | ransomware threat"
4. ✅ Bot presence changes to match threat level

**Status Message Examples:**
- "🔴 CRITICAL THREAT DETECTED | ransomware threat"
- "🔴 EMERGENCY RESPONSE ACTIVE | data breach threat"
- "🟡 Elevated threat level | phishing threat"

### **Resolving Threats**
When you resolve a threat:

```bash
!exec_resolve_threat 5
```

**What happens:**
1. ✅ Threat marked as resolved
2. ✅ System checks for other active critical/high threats
3. ✅ If NO other threats: Bot returns to **🟢 NORMAL**
4. ✅ If other threats exist: Bot remains at current threat level

---

## 🔄 Automatic Status Behavior

### **Priority Order**
The bot status follows this priority:

1. **🛡️ Active Drill** (highest priority when drill is running)
2. **🚨 Active Critical/High Threat** (when threat is logged)
3. **🟢 Normal** (default when nothing active)

### **Status Persistence**
- **Drills:** Status remains until `!drill_reset` is called
- **Threats:** Status remains until all critical/high threats are resolved
- **Auto-return:** Elevated/Panic modes auto-return to normal after timeout ONLY if no active drill/threat

### **Status Rotation**
- Messages rotate every **30 seconds**
- Drill/threat info is appended to status message
- Example: "🛡️ DRILL IN PROGRESS | RANSOMWARE - RED"

---

## 📋 Commands

### **Drill Management**
```bash
!activate_drill <type> <protocol>   # Activates drill + changes status
!drill_reset                         # Deactivates drill + returns to normal
!drill_respond <status>              # Log team response (doesn't affect status)
!drill_stats                         # View drill history
```

### **Threat Management**
```bash
!exec_add_threat <severity> <category> <description>   # Add threat (CRITICAL/HIGH changes status)
!exec_resolve_threat <threat_id>                       # Resolve threat (may return to normal)
!exec_briefing                                         # View all active threats
!exec_threat_dashboard                                 # Threat dashboard
```

### **Manual Status Control**
```bash
!setstatus <level>                   # Manually set status (admin override)
# Levels: normal, elevated, panic, lockdown, drill
```

---

## 💡 Usage Examples

### **Example 1: Running a Ransomware Drill**
```bash
# 1. Start the drill
!activate_drill RANSOMWARE RED

# Bot status changes to:
# 🛡️ SECURITY DRILL ACTIVE | RANSOMWARE - RED
# Presence: 🟡 Idle

# 2. Team responds
!drill_respond "IC acknowledged, team mobilized"

# 3. End the drill
!drill_reset

# Bot status returns to:
# 🟢 All systems nominal
# Presence: 🟢 Online
```

### **Example 2: Handling a Critical Threat**
```bash
# 1. Threat detected
!exec_add_threat critical malware APT29 indicators detected in network

# Bot status changes to:
# 🔴 CRITICAL THREAT DETECTED | malware threat
# Presence: 🔴 Do Not Disturb

# 2. Investigate and respond
!exec_briefing

# 3. Threat contained
!exec_resolve_threat 7

# Bot status checks for other threats:
# - If none: Returns to 🟢 NORMAL
# - If others: Remains at current level
```

### **Example 3: Drill During Active Threat**
```bash
# If you activate a drill while a threat is active:
!activate_drill PHISHING YELLOW

# Drill takes priority:
# 🛡️ SECURITY DRILL ACTIVE | PHISHING - YELLOW

# After drill reset:
!drill_reset

# Bot returns to threat status:
# 🔴 CRITICAL THREAT DETECTED | malware threat
```

---

## 🎯 Benefits

### **For Security Teams**
- ✅ **Instant visual feedback** on security status
- ✅ **Clear drill identification** vs real incidents
- ✅ **Persistent status** until resolution
- ✅ **Multi-guild visibility** (status visible across all servers)

### **For Members**
- ✅ **At-a-glance awareness** of security posture
- ✅ **Drill vs real distinction** via status
- ✅ **Confidence in security ops** through transparency

### **For Executives**
- ✅ **Real-time threat awareness** without checking dashboards
- ✅ **Training exercise visibility** for compliance
- ✅ **Quick status assessment** via bot presence

---

## ⚙️ Technical Details

### **Implementation**
- **Dynamic Status Cog:** `cogs/core/dynamic_status.py`
- **Drill System:** `cogs/soc/security_drill_system.py`
- **Threat System:** `cogs/soc/executive_threat_briefing.py`

### **Integration Points**
1. Drill activation → `dynamic_status.activate_drill_status()`
2. Drill reset → `dynamic_status.deactivate_drill_status()`
3. Threat add → `dynamic_status.activate_threat_status()`
4. Threat resolve → `dynamic_status.deactivate_threat_status()`

### **Status Rotation**
- Background task runs every 30 seconds
- Checks for active drills/threats before auto-returning to normal
- Rotates through 5 predefined messages per status level

---

## 🔧 Configuration

### **Status Messages**
Edit `cogs/core/dynamic_status.py` to customize messages:

```python
self.status_messages = {
    'drill': [
        "🛡️ SECURITY DRILL ACTIVE",
        "🛡️ DRILL IN PROGRESS",
        # Add more custom messages
    ]
}
```

### **Timeouts**
- **Elevated:** Returns to normal after 5 minutes (if no drill/threat)
- **Panic:** Returns to normal after 10 minutes (if no drill/threat)
- **Drill:** Never auto-returns (must call `!drill_reset`)
- **Threat:** Never auto-returns (must resolve all critical/high threats)

---

## 🚀 Quick Reference

| Action | Command | Status Change |
|--------|---------|---------------|
| Start drill | `!activate_drill <type> <protocol>` | → 🛡️ Drill Mode |
| End drill | `!drill_reset` | → 🟢 Normal |
| Add CRITICAL threat | `!exec_add_threat critical ...` | → 🔴 Panic |
| Add HIGH threat | `!exec_add_threat high ...` | → 🟡 Elevated |
| Resolve threat | `!exec_resolve_threat <id>` | → 🟢 Normal (if no other threats) |
| Manual override | `!setstatus <level>` | → Custom level |

---

**Status integration is now active!** 🎉  
The bot will automatically reflect your security operations in real-time across all Discord servers.
