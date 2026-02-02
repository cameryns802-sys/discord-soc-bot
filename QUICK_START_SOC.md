# Quick Start: New SOC Systems

## What Was Added

**5 powerful new systems for monitoring, analyzing, and securing your server:**

### 🛡️ Security Dashboard
```
/dashboard              → Real-time security score & metrics
/securitystatus         → Quick status check
```
**See:** Server health, member stats, role security, 2FA status, recommendations

---

### 📊 Audit Log Analyzer
```
/auditanalyze 1         → Analyze last hour
/auditanalyze 24        → Analyze last 24 hours
```
**Finds:** Ban sprees, mass kicks, channel deletions, suspicious moderators

---

### 🔑 Permission Auditor
```
/permaudit              → Scan for permission misconfigurations
```
**Detects:** @everyone with admin, guest permissions, unsafe channel overrides

---

### 📈 Security Reports
```
/securityreport day     → 24-hour report
/securityreport week    → 7-day report
/securityreport month   → 30-day report
/threatsummary          → Today's threat summary
```
**Shows:** Threat analytics, response times, patterns, recommendations

---

### ✅ Security Checklist & Setup
```
/secchecklist           → Track your progress (0-100%)
/secsetup               → Step-by-step setup wizard
```
**Includes:** 10 security items, prioritized, with guidance

---

## Quick Workflow

### 🚀 First Time Setup (5 min)
```
1. /secsetup                    # Read the setup guide
2. /secchecklist                # See what needs doing
3. Manually configure items 1-3 in Discord settings
4. /permaudit                   # Check for permission issues
5. /dashboard                   # View your security score
```

### 📅 Daily Ops
```
1. /dashboard                   # Morning security check
2. /threatsummary               # Today's threat summary
3. /auditanalyze 1              # Check for overnight activity
```

### 📊 Weekly Review
```
1. /securityreport week         # Weekly analytics
2. /secchecklist                # Update progress
3. /permaudit                   # Verify permissions stable
```

---

## Command Permissions

| Command | Requires |
|---------|----------|
| `/dashboard` | Manage Server |
| `/securitystatus` | Manage Server |
| `/auditanalyze` | View Audit Log |
| `/permaudit` | Manage Roles |
| `/securityreport` | Manage Server |
| `/threatsummary` | Manage Server |
| `/secchecklist` | Manage Server |
| `/secsetup` | Administrator |

---

## Example Outputs

### Security Score: 72/100
```
✅ Good security posture
⚠️ Suggestions: Enable verification, reduce admin count
```

### Audit Analysis Result
```
🚨 High ban rate: 8 bans (SUSPICIOUS)
👀 High activity from @Moderator: 15 actions (NORMAL)
✅ No channel deletions
```

### Permission Audit
```
✅ @everyone permissions safe
⚠️ 2 roles have excessive admin perms
⚠️ Channel override: #general allows @everyone to manage messages
```

### Security Report
```
📊 Last 24 Hours
- 5 threats detected
- 12 automated responses
- 1.2s avg response time
- Top threat: Spam (3 incidents)
💡 Recommendation: Increase slowmode in #general
```

---

## Data Files Created

```
data/security_checklist.json    # Your progress tracking
data/threat_responses.json      # Used by reports (already existed)
```

---

## Integration with Existing Systems

These new systems **automatically work with** your existing systems:

✅ **security_dashboard** + threat_response = Better recommendations
✅ **audit_log_analyzer** + intelligent_threat_response = Spot issues faster
✅ **permission_auditor** + moderation = Ensure secure roles
✅ **security_reports** + threat_responses = Historical analytics
✅ **security_checklist** + all systems = Track progress

---

## Tips & Tricks

### 🎯 Smart Security Score
The dashboard calculates your score based on:
- Verification level (0-20 pts)
- Content filter status (+10 pts)
- Admin 2FA adoption (0-10 pts)
- Default notifications
- Overall posture

**How to improve:**
1. Enable verification → +5 to +20
2. Enable content filter → +10
3. Get admins on 2FA → +1 per admin

### 🔍 Audit Analysis Pro Tips
- Run `/auditanalyze 1` after suspicious activity
- Look for actors with high action counts
- Critical issues highlighted in red 🔴
- Use with `/dashboard` for context

### 🛡️ Permission Audit Best Practice
- Run after any role changes
- Address 🔴 CRITICAL issues immediately
- Review ⚠️ WARNING items within 24h
- Use `/secsetup` to fix issues

### 📊 Report Insights
- Compare reports across time periods
- High spam = need stricter automod
- Raid detected = review verification
- High response time = automate more
- Phishing detected = alert community

### ✅ Checklist Pro Tips
- Start with 🔴 CRITICAL items
- Move to ⚠️ HIGH PRIORITY after that
- Complete MEDIUM priority weekly
- LOW priority items are optional
- Checklist auto-updates as you configure things

---

## Still Need Help?

**See detailed docs:** `SOC_MONITORING_SYSTEMS.md`

**Quick reference by system:**
- Dashboard: Security metrics & recommendations
- Audit Analyzer: Threat pattern detection
- Permission Auditor: Permission security
- Reports: Historical analytics
- Checklist: Setup guidance

All commands are self-documenting with `/command` slash command help.
