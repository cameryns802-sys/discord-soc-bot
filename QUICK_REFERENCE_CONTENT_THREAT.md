# ⚡ Quick Reference - Content & Threat Response

## 📋 Generate Server Content

### Rules
```
/generaterules style:default        - Standard rules
/generaterules style:strict         - Strict enforcement
/generaterules style:casual         - Relaxed tone
/generaterules style:gaming         - Gaming community
/generaterules style:professional   - Business/professional
```

### Terms of Service
```
/generatetos                        - Full ToS (8 sections)
```

### Community Guidelines
```
/generateguidelines                 - 10 positive guidelines
```

### Manage Rules
```
/addrule rule:"Your custom rule"
/removerule rule_number:5
```

---

## 🚨 Threat Response

### Detect Threats
```
/detectthreat threat_type:spam level:high description:"Details here"
/detectthreat threat_type:raid level:critical description:"Bot invasion"
/detectthreat threat_type:phishing level:high description:"Fake link posted"
```

### View Information
```
/threathistory limit:10             - Recent threats
/threatplaybooks                    - All response plans
```

---

## 🎯 Threat Types

| Type | Description | Levels Available |
|------|-------------|------------------|
| **spam** | Message flooding | Low, Medium, High, Critical |
| **raid** | Coordinated attack | Medium, High, Critical |
| **phishing** | Fake login links | Medium, High, Critical |
| **malware** | Infected files | High, Critical |
| **harassment** | Targeted abuse | Low, Medium, High, Critical |
| **scam** | Fraudulent schemes | Medium, High, Critical |
| **unauthorized_access** | Permission abuse | High, Critical |

---

## 🛡️ What The Bot Does Automatically

### Spam Threat
- **Low:** Delete → Warn → Slowmode
- **High:** Delete → Timeout 1h → Alert mods
- **Critical:** Delete → Ban → Alert admins → Lock channel

### Raid Threat
- **Medium:** Raid mode → Alert → Verification
- **Critical:** Raid mode → Lockdown → Mass ban → Disable invites

### Phishing Threat
- **High:** Delete → Timeout → Alert community → Report
- **Critical:** Ban → Purge → Alert all → Contact Discord

### Malware Threat
- **High:** Delete → Ban → Scan → Quarantine
- **Critical:** Ban → Purge → Lockdown → Report

### Harassment Threat
- **Low:** Warn → Log → Alert mods
- **Critical:** Ban → Report → Alert owner → Support victim

---

## 📊 Automated Actions

The bot can automatically:
- ✅ Delete violating messages
- ✅ Timeout/ban users (10m, 1h, 1d, permanent)
- ✅ Enable slowmode (5s)
- ✅ Lock channels/server
- ✅ Enable raid mode
- ✅ Mass kick/ban new accounts
- ✅ Alert mods/admins/owner/community
- ✅ Log evidence
- ✅ Scan links and attachments
- ✅ Revoke permissions
- ✅ Create investigation cases
- ✅ Report to Discord Trust & Safety

---

## 💡 Tips

**Content Generation:**
- Use `/generaterules` before opening your server
- Generate ToS and pin it to #rules
- Customize with `/addrule` for your specific needs
- Different styles work for different communities

**Threat Response:**
- The bot automatically responds based on severity
- Use `/detectthreat` to manually trigger responses
- Check `/threathistory` to review past incidents
- Review `/threatplaybooks` to understand what will happen
- Higher severity = more aggressive response

**Best Practices:**
- Generate rules when setting up server
- Review threat playbooks with your mod team
- Use manual detection for real threats
- Check history regularly for patterns
- Trust the automation - it's designed to protect

