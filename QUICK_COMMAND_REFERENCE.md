# 🛡️ Sentinel SOC Bot - Quick Command Reference

## ✅ Bot Status
- **Cogs Loaded**: 174/174 (100% success)
- **Commands**: 42 total registered
- **Discord Status**: Connected ✅
- **API Dashboard**: http://127.0.0.1:8000 ✅
- **API Health**: Healthy ✅

---

## 🎯 Core Threat Detection Commands

### Anti-Cryptocurrency Detection
```
!checkcrypto <text>          # Manually scan text for crypto wallets/scams
!cryptodetections [days]     # View detection history
!cryptostats                 # View crypto detection statistics
```

### Intelligent Threat Response
```
/detectthreat               # Manually trigger threat detection
!threathistory [limit]      # View threat response history
!threatplaybooks            # View automated response playbooks
```

### Phishing Detection
```
# Auto-detection in messages (no commands needed)
# Detected URLs auto-deleted with warning
```

### Anti-Spam & Anti-Raid
```
!spam_check                  # Check spam detection status
!raid_check                  # Check raid detection status
!raid_stats                  # View raid statistics
```

---

## 📊 Dashboard Commands

### Security Dashboard
```
/securitydash               # View real-time security metrics
!securitystatus             # Quick security status check
```

### SOC Dashboard (Master Overview)
```
!socdash                    # Master SOC dashboard
!sockealthcheck             # Security health check
!smetrics [period]          # Detailed metrics (24h, 7d, 30d)
```

### Executive Reporting
```
!executivedashboard         # C-level risk dashboard
!execsummary [period]       # Executive summary report
!boardreport                # Board-level security report
!risktrending               # Risk trending analysis
```

### Incident Management
```
!forecastincidents [period] # Predict upcoming incidents
!forecastdetail [id]        # Detailed incident forecast
!incidenthistory            # View incident history
```

---

## 🔐 Security Configuration Commands

### Moderation & Enforcement
```
!purge [amount] [@user]     # Delete messages (clean, clear aliases)
!kick @user [reason]        # Kick user from server
!ban @user [reason]         # Ban user from server
!unban <user_id> [reason]   # Unban user
!timeout @user [duration]   # Timeout user (10m, 1h, 1d)
!untimeout @user            # Remove timeout
!warn @user [reason]        # Issue warning
!lock [channel]             # Lock channel
!unlock [channel]           # Unlock channel
!slowmode [seconds]         # Set channel slowmode
```

### Audit & Compliance
```
!auditanalyze [hours]       # Analyze Discord audit logs
!permission_audit           # Check for dangerous role permissions
!automodrules               # View Discord automod rules
!automodviolations [days]   # View automod violations
!automodsync                # Manually sync Discord automod
```

### Blacklist Management
```
!addblacklist <type> <id>   # Add to blacklist (user/guild/ip/domain)
!removeblacklist <id>       # Remove from blacklist
!blacklistinfo <id>         # Check blacklist status
!blackliststats             # View blacklist statistics
```

---

## 🧠 Threat Intelligence Commands

### IOC Management
```
!addioc <type> <value> <category> # Add IOC (ip_address, domain, url, file_hash)
!searchioc <query>          # Search IOCs
!iocstats                   # View IOC statistics
!correlationreport [hours]  # View IOC correlation report
!iocaging                   # View IOC aging report
!importiocs                 # Import IOCs from CSV
!exportiocs                 # Export IOCs to CSV
```

### Threat Signals
```
!signalstats                # View signal bus statistics
!executivedashboard         # View signal-driven risk dashboard
```

---

## 📈 Analytics & Metrics

### System Health
```
!serversetup                # Server configuration wizard
!serveranalytics            # Server metrics and statistics
!commandanalytics           # Command usage analytics
!performanceprofile         # Command performance profiling
!errorstats                 # Error tracking and statistics
```

### Compliance & Governance
```
!securitychecklist          # Security setup checklist
!securitytraining           # Security awareness training
!gdprcomply                 # GDPR compliance status
!compliancestatus           # Overall compliance status
```

---

## 🎮 Advanced Features

### Threat Response Automation
```
/detectthreat spam high     # Manually trigger spam detection
/detectthreat phishing critical  # Manually trigger phishing alert
!escalationhistory          # View escalation routing history
!escalationstats            # Escalation statistics
```

### Incident Playbooks
```
!incidentplaybook <type>    # View incident response playbook
!playbooks                  # List all playbooks
!playbookstatus             # Playbook execution status
```

### Security Drill System
```
!securitydrill <type>       # Run security drill
!drillhistory               # View drill history
!drillscores                # View drill effectiveness scores
```

---

## 🔧 Owner-Only Commands

### System Control
```
!savedata                   # Manually save all data
!datastats                  # View data statistics
!executeplaybook            # Execute SOAR playbook
!kickdllbot                 # Kick DLL analysis bot
!logstats                   # View logging statistics
```

### Feature Flags
```
!featureflag <name> <enable|disable>  # Control feature
!featureflags               # View all feature flags
```

### AI Governance
```
!overridestats              # View AI override statistics
!biasreport                 # Generate bias analysis report
!checkprompt <text>         # Check for prompt injection
!injectionstats             # View injection detection stats
```

---

## 📱 Web Dashboard

Access the comprehensive web dashboard:
```
http://127.0.0.1:8000
```

Features:
- 📊 Real-time security metrics
- 📈 Threat analytics
- 🎯 Executive dashboards
- ⚙️ System controls
- 📋 Incident management
- 🔐 Configuration panels

---

## 🚀 System Status

### Current Configuration
- **AI Governance**: ✅ ENABLED (confidence scoring, human oversight)
- **Resilience**: ✅ ENABLED (graceful degradation, failover)
- **Cryptography**: ✅ ENABLED (encryption, key rotation)
- **Signal Bus**: ✅ ENABLED (central threat coordination)
- **Threat Intel**: ✅ ENABLED (IOC tracking, correlation)

### Security Systems Active
- ✅ Anti-Cryptocurrency (wallets, mining, scams)
- ✅ Anti-Phishing (URL detection)
- ✅ Anti-Spam (message rate limiting)
- ✅ Anti-Raid (mass join detection)
- ✅ Antinuke (mass channel deletion)
- ✅ Permission Auditing
- ✅ Webhook Abuse Prevention
- ✅ Intelligent Threat Response
- ✅ Blacklist Enforcement
- ✅ Toxicity Detection

### Monitoring Systems Active
- ✅ Real-time threat detection
- ✅ Event correlation
- ✅ Incident forecasting
- ✅ Compliance monitoring
- ✅ Audit log analysis
- ✅ Security scorecard
- ✅ Risk trending

---

## 💡 Common Use Cases

### Detect Crypto Scam
```
Text: "Join our exclusive pump and dump group, guaranteed 1000x returns! Send your ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f42e0e"
Action: !checkcrypto <paste above text>
Result: ✅ Detected wallet + scam keywords → Message auto-deleted
```

### Quick Security Audit
```
!securitystatus             # Check basic security
!perm_audit                 # Check dangerous roles
!automodviolations 7        # Check last 7 days violations
Result: ✅ Complete security overview
```

### Investigate Threat
```
!signalstats                # View threat activity
!auditanalyze 6             # Check last 6 hours
!threathistory 10           # Last 10 incidents
Result: ✅ Full threat context
```

### Run Emergency Drill
```
/detectthreat raid high     # Simulate raid
!drillhistory               # Check response time
!drillscores                # Effectiveness rating
Result: ✅ Team readiness validated
```

---

## 📞 Support & Troubleshooting

### Check System Health
```
!serversetup                # Full server configuration check
!securitychecklist          # Security setup wizard
!healthcheck                # Real-time health metrics
```

### Get Help
```
/help [command]             # Command help
/userinfo @user             # User information
/serverinfo                 # Server statistics
```

---

**Last Updated**: February 2, 2026  
**Bot Version**: Sentinel SOC v3.0  
**Status**: ✅ PRODUCTION READY
