# 🎮 Dashboard Quick Reference Card

## Main Commands (Copy & Paste Ready)

```
/dashboard    - Open main interactive dashboard
/controls     - Access bot control panel  
/monitor      - Real-time monitoring dashboard
/incidents    - Security incidents view
/status       - Quick bot status
/cogmanager   - Manage cogs (load/reload/unload)
/features     - Toggle feature flags
/security     - Control security settings
/diagnostics  - System diagnostics
```

---

## 🎛️ What You Can Do

### From `/dashboard`
- View bot status, server stats, system info
- Monitor security and recent activity
- Navigate to any dashboard view via dropdown
  - 📊 Overview
  - 🛡️ Security
  - ⚙️ Systems
  - 📈 Analytics
  - 🚨 Incidents
  - 📋 Logs
  - 🔧 Config

### From `/controls`
- 🔄 Reload all cogs (no restart needed)
- 🚀 Restart bot gracefully
- 📊 Refresh live statistics
- ⚙️ Modify configuration (prefix, timeout, log level)

### From `/monitor`
- View system health (CPU, memory, connections)
- Check performance (latency, uptime, command rate)
- Monitor security (threat level, incidents, alerts)
- See activity (users, messages, commands)

### From `/cogmanager`
- 📦 List all loaded cogs
- 🔄 Reload specific cog (no restart)
- ⬇️ Unload a cog
- ⬆️ Load a new cog

### From `/features`
- 🚨 Toggle Signal Bus on/off
- 🎯 Toggle Threat Intel on/off
- 📊 Toggle Security Dashboard on/off
- ✅ Changes apply immediately

### From `/security`
- 🤖 Toggle AI Governance
- ⚡ Toggle Resilience
- 🔐 Toggle Cryptography
- ⚠️ Requires restart for some

---

## 📊 Information at a Glance

### Bot Status
- Ping latency
- Total uptime
- Cogs loaded
- Commands available
- Memory usage

### Server Info
- Guilds connected
- Total users
- Channels
- Roles
- Members

### Security
- Threat level (LOW/MEDIUM/HIGH/CRITICAL)
- Active incidents
- Recent alerts
- IOCs tracked
- Security score (0-100)

### Systems
- Signal Bus ✅
- Feature Flags ✅
- Data Manager ✅
- FastLogger ✅
- Threat Intel ✅
- All 9 core systems ✅

---

## 🔐 Access Control

| Command | Owner Only | Admin+ | Everyone |
|---------|:----------:|:------:|:--------:|
| /dashboard | ❌ | ✅ | ❌ |
| /controls | ✅ | ❌ | ❌ |
| /monitor | ✅ | ❌ | ❌ |
| /incidents | ✅ | ❌ | ❌ |
| /status | ❌ | ❌ | ✅ |
| /cogmanager | ✅ | ❌ | ❌ |
| /features | ✅ | ❌ | ❌ |
| /security | ✅ | ❌ | ❌ |
| /diagnostics | ✅ | ❌ | ❌ |

---

## 🎯 Common Tasks

### Check Bot is Running
```
/status
→ View bot name, ping, uptime, security status
```

### Reload a Cog Without Restarting
```
/cogmanager → Click "Reload Cog" → Type: fast_logger
```

### Enable Threat Intelligence
```
/features → Click "Threat Intel" → Feature toggles immediately
```

### View Security Incidents
```
/incidents → See all active incidents with details
```

### Monitor Bot Health
```
/monitor → View system health, performance, security, activity
```

### Restart Bot Safely
```
/controls → Click "Restart Bot" → Bot restarts gracefully
```

### List All Loaded Cogs
```
/cogmanager → Click "Loaded Cogs" → See all active cogs
```

### Check System Status
```
/diagnostics → View Python, connections, performance metrics
```

---

## ⚡ Key Features

✅ **Real-Time Updates** - Live statistics and metrics
✅ **Interactive Buttons** - Click to perform actions
✅ **Select Menus** - Dropdown to navigate views
✅ **Modal Forms** - Configure settings through forms
✅ **Color Coded** - Green (good), Orange (caution), Red (alert)
✅ **Ephemeral Messages** - Sensitive info visible only to owner
✅ **No Downtime** - Reload cogs and toggle features without restart
✅ **Owner Protected** - All controls require owner verification

---

## 🛡️ Security Modules Visible in Dashboard

1. **Anti-Nuke** - Prevents mass deletion
2. **Anti-Phishing** - Blocks malicious links
3. **Anti-Spam** - Detects spam attacks
4. **Anti-Raid** - Prevents raid attacks
5. **Permission Audit** - Tracks role changes
6. **Threat Intelligence** - IOC tracking
7. **Threat Response** - Automated playbooks
8. **Incident Management** - Case tracking

---

## 📈 Analytics Shown

- **Commands (24h):** Total executed, most used, avg response time
- **Security:** Detected threats, blocked attacks, escalated cases
- **Users:** Active users, new members, violations
- **Performance:** Latency, uptime %, memory usage

---

## 🔧 Configuration Options

**Bot Settings:**
- Command prefix (default: !)
- Command timeout (default: 30s)
- Log level (debug/info/warning/error)

**Security:**
- AI Governance (default: ON)
- Resilience (default: ON)
- Cryptography (default: ON)

**Features:**
- Signal Bus (default: ON)
- Threat Intelligence (default: ON)
- Security Dashboard (default: ON)

---

## ⏱️ Timestamps

All timestamps in the dashboard use **PST timezone** (Pacific Standard Time).

Example: "2 mins ago" = 2 minutes ago in PST

---

## 💡 Tips & Tricks

1. Use `/monitor` continuously during high-activity events
2. Check `/status` quickly for basic health
3. Reload cogs with `/cogmanager` instead of restarting
4. Toggle features with `/features` for testing
5. Review `/incidents` frequently for security threats
6. Keep an eye on `/diagnostics` for memory/latency issues
7. Use `/controls` to safely restart without losing data

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard won't load | Check admin permissions, verify bot is online |
| Buttons not working | Ensure you're bot owner, check permissions |
| Cog reload failed | Check cog name, verify cog file exists |
| Feature toggle failed | Some features need restart, check env vars |
| Dashboard showing wrong info | Click "Refresh Stats" button |
| Can't access admin commands | Verify BOT_OWNER_ID is set correctly |

---

## 📚 Full Documentation

See **DASHBOARD_GUIDE.md** for complete documentation with:
- Detailed command descriptions
- All available dashboard views
- Interactive feature explanations
- Access control details
- Best practices
- Extended troubleshooting

---

**Last Updated:** February 3, 2026
**Dashboard Version:** v1.0 (Advanced Interactive)
**Status:** ✅ Fully Operational
