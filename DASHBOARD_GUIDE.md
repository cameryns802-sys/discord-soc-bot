# 🎮 Advanced Interactive Bot Dashboard - Complete Guide

## Overview

The **Advanced Interactive Bot Dashboard** provides a complete control panel for managing and monitoring your SOC bot with real-time statistics, incident tracking, and full system controls all through Discord embeds and interactive buttons.

---

## 📊 Dashboard Commands

### 1. `/dashboard` - Main Control Panel
**Description:** Open the main interactive dashboard with navigation controls

**Features:**
- 📊 Real-time bot status and statistics
- 🏛️ Server information and metrics
- 🛡️ Security system status
- 📈 Recent activity and event summary
- ✨ Feature status overview
- 🔘 Select dropdown to navigate to specific dashboard views

**Access:** Admin+ (Owner verified)

**Views Available:**
- **Overview** - Main dashboard with all stats
- **Security** - Security system status (8+ security modules)
- **Systems** - Core bot system status (9+ systems)
- **Analytics** - Usage and performance analytics
- **Incidents** - Active security incidents
- **Logs** - Recent audit log entries
- **Configuration** - Current bot settings

---

### 2. `/controls` - Bot Control Panel
**Description:** Access comprehensive bot control buttons

**Control Buttons:**
- 🔄 **Reload Cogs** - Reload all cogs without restarting bot
- 🚀 **Restart Bot** - Gracefully restart the entire bot
- 📊 **Refresh Stats** - Update and view live statistics
- ⚙️ **Configuration** - Open config modal to adjust settings

**Configuration Modal Fields:**
- Command Prefix (e.g., `!`)
- Command Timeout (in seconds)
- Log Level (debug|info|warning|error)

---

### 3. `/monitor` - Real-Time Monitoring Dashboard
**Description:** Monitor bot health, security, and performance in real-time

**Monitoring Sections:**
- 🟢 **System Health** - CPU, memory, connections status
- ⚡ **Performance** - Latency, uptime, command rate, error rate
- 🛡️ **Security** - Threat level, incidents, alerts, IOCs
- 📊 **Activity** - Online users, messages/hour, commands/hour

**Control Buttons:**
- 🛡️ **Security Systems** - View all 8 security modules status
- 📈 **Performance** - Detailed performance metrics
- 🚨 **Active Incidents** - View current security incidents
- ⚠️ **Alerts** - Recent security alerts
- 📋 **Audit Logs** - Recent audit log entries

---

### 4. `/incidents` - Security Incidents Dashboard
**Description:** View and manage active security incidents

**Incident Tracking:**
- 🔴 CRITICAL incidents
- 🟠 HIGH severity incidents  
- 🟡 MEDIUM severity incidents
- 📊 Incident summary statistics

**Control Buttons:**
- 🚨 **Active Incidents** - Detailed incident information
- ⚠️ **Alerts** - Recent security alerts (5 most recent)
- 📋 **Audit Logs** - Audit trail of actions

---

### 5. `/status` - Bot Status Report
**Description:** Get a quick comprehensive bot status overview

**Information Provided:**
- 🤖 Bot name, status, ping, uptime
- 📊 Guild count, cog count, command count, user count
- 🛡️ Security status and threat level
- 🚨 Incident and alert summaries

---

## 🛠️ Admin Control Panel Commands

### 1. `/cogmanager` - Cog Management
**Description:** Load, unload, and reload bot cogs dynamically

**Management Options:**
- 📦 **Show Loaded Cogs** - List all currently loaded cogs
- 🔄 **Reload Cog** - Reload a specific cog (via modal)
- ⬇️ **Unload Cog** - Unload a cog (via modal)
- ⬆️ **Load Cog** - Load a new cog (via modal)

**Cog Name Format:** Use cog name without `.py` extension
- Example: `fast_logger`, `threat_intel_hub`, `signal_bus`

---

### 2. `/features` - Feature Flags Control
**Description:** Enable/disable features at runtime without restarting

**Toggleable Features:**
- 🚨 **Signal Bus** - Central event pipeline
- 🎯 **Threat Intel** - Threat intelligence hub
- 📊 **Security Dashboard** - Real-time security metrics

**Note:** Features toggle immediately without restart

---

### 3. `/security` - Security Settings
**Description:** Control TIER-1 security systems

**Security Systems:**
- 🤖 **AI Governance** - AI decision tracking and oversight
- ⚡ **Resilience** - Graceful degradation and failover
- 🔐 **Cryptography** - Encryption and key management

**Important:** ⚠️ Changes to security settings require bot restart

---

### 4. `/diagnostics` - System Diagnostics
**Description:** Run comprehensive system diagnostics

**Diagnostic Information:**
- 🖥️ Python version and platform
- 🤖 Bot cogs and commands count
- 💾 Storage and data files status
- 🔌 Connection status (Discord, API)
- 📊 Performance metrics (latency, memory)

---

## 🎛️ Interactive Features

### Button Controls
All dashboards feature interactive buttons:
- **Primary Buttons** (Blue) - Main actions
- **Success Buttons** (Green) - Positive actions
- **Danger Buttons** (Red) - Destructive actions
- **Secondary Buttons** (Gray) - Information actions
- **Blurple Buttons** (Purple) - System controls

### Select Menus
Dashboard includes dropdown select menus for navigation:
- **View Selection** - Choose which dashboard section to view
- **Real-time Updates** - Refresh data without reopening dashboard

### Modals
Configuration changes through modal forms:
- **Bot Configuration** - Adjust prefix, timeout, log level
- **Cog Management** - Type cog names to load/unload/reload

---

## 📊 Dashboard Information

### Real-Time Statistics Displayed

**Bot Metrics:**
- Ping latency in milliseconds
- Uptime in days/hours/minutes
- Total cogs loaded
- Total commands available
- Memory usage

**Server Metrics:**
- Total guilds connected
- Total user count
- Bot member count
- Message channels
- Role count

**Security Metrics:**
- Current threat level (🟢 LOW, 🟡 MEDIUM, 🟠 HIGH, 🔴 CRITICAL)
- Number of active incidents
- Number of recent alerts
- IOC tracking statistics

**Activity Metrics:**
- Commands executed per hour
- Messages processed per hour
- Moderation actions taken
- Security violations detected
- User violations recorded

---

## 🔐 Security & Access Control

### Permission Requirements
- **Admin+** - Required for dashboard access
- **Owner Only** - Required for control buttons and admin panels
  - Defined by `BOT_OWNER_ID` environment variable
  - Verified on every button click

### What Owner Can Control
- ✅ Reload/unload/load cogs
- ✅ Restart bot
- ✅ Toggle feature flags
- ✅ Modify security settings
- ✅ View sensitive information (incidents, alerts, logs)
- ✅ Configure bot settings

### Ephemeral Messages
- All sensitive responses sent as ephemeral (visible only to user)
- Admin actions visible to owner only
- Public status information can be posted publicly

---

## 📈 Dashboard Sections Explained

### 🛡️ Security Systems Dashboard
Shows status of 8 core security modules:
1. **Anti-Nuke** - Prevents mass deletion attacks
2. **Anti-Phishing** - Blocks phishing URLs
3. **Anti-Spam** - Detects spam patterns
4. **Anti-Raid** - Prevents raid attacks
5. **Permission Audit** - Tracks permission changes
6. **Threat Intelligence** - IOC tracking
7. **Threat Response** - Automated playbooks
8. **Incident Management** - Case tracking

### ⚙️ Systems Status Dashboard
Core infrastructure status:
- Signal Bus (event pipeline)
- Feature Flags (runtime toggles)
- Data Manager (persistence)
- FastLogger (logging)
- Threat Intel Hub
- IOC Manager
- Human Override Tracker
- Abstention Policy
- Prompt Injection Detector

### 📈 Analytics Dashboard
Usage statistics over 24 hours:
- Command usage (total and top commands)
- Security events (detected, blocked, escalated)
- User activity (active users, new members, violations)
- Performance metrics (latency, uptime, memory)

### 🚨 Incidents Dashboard
Current security incidents:
- CRITICAL incidents (🔴)
- HIGH incidents (🟠)
- MEDIUM incidents (🟡)
- Incident details and detection times
- Total incident summary

### 📋 Audit Logs Dashboard
Recent audit log entries:
- Member joins/leaves
- Message deletions
- Role assignments
- Channel creation
- Member bans
- Webhook changes

### 🔧 Configuration Dashboard
Current bot settings:
- Command prefix
- Timezone
- Safe mode status
- AI governance state
- Resilience state
- Cryptography state
- Integration status

---

## 🚀 Usage Examples

### View Full Dashboard
```
/dashboard
→ Opens main dashboard with select menu
→ Choose "Overview" for main view
→ Choose "Security" for security systems
→ Choose "Systems" for infrastructure status
```

### Reload a Cog
```
/cogmanager
→ Click "Reload Cog" button
→ Type cog name: "fast_logger"
→ See confirmation: "Cog fast_logger reloaded successfully"
```

### Toggle Feature
```
/features
→ Click "Threat Intel" button
→ Get confirmation of new state
→ Feature toggles immediately
```

### Check Bot Status
```
/status
→ Get quick overview of bot health
→ See security status
→ View incident/alert counts
```

### Run Diagnostics
```
/diagnostics
→ See Python version
→ Check system connections
→ View memory and latency
→ Verify all systems operational
```

---

## 🎯 Quick Reference

| Command | Purpose | Access |
|---------|---------|--------|
| `/dashboard` | Main control panel | Admin+ |
| `/controls` | Bot controls | Owner |
| `/monitor` | Real-time monitoring | Owner |
| `/incidents` | Security incidents | Owner |
| `/status` | Quick status | Everyone |
| `/cogmanager` | Manage cogs | Owner |
| `/features` | Toggle features | Owner |
| `/security` | Security settings | Owner |
| `/diagnostics` | System diagnostics | Owner |

---

## 💡 Best Practices

1. **Regular Monitoring** - Check `/monitor` daily for anomalies
2. **Incident Response** - Review `/incidents` frequently during high-activity periods
3. **Cog Management** - Use `/cogmanager` to safely reload cogs without downtime
4. **Feature Testing** - Use `/features` to test new capabilities without restart
5. **Diagnostics** - Run `/diagnostics` weekly to ensure system health

---

## 🔧 Troubleshooting

**Dashboard Not Loading?**
- Verify admin permissions
- Check that bot has message send permissions
- Ensure bot is online

**Controls Not Working?**
- Verify you are bot owner (BOT_OWNER_ID)
- Check bot permissions in channel
- Try in a different channel

**Cog Reload Failed?**
- Check cog name spelling
- Verify cog exists in cogs directory
- Check for import/syntax errors in cog

**Feature Toggle Not Working?**
- Some features require bot restart to take effect
- Check environment variables are set correctly
- Verify feature flag exists

---

## 📝 Notes

- All timestamps displayed in PST timezone
- Dashboard updates in real-time as you navigate
- Select menus allow easy view switching
- Buttons have timeout of 5 minutes
- Ephemeral messages only visible to command author
- All actions logged in audit trail

