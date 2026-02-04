# 🛡️ Sentinel SOC Bot - Complete Commands List

**Status**: ✅ 174/174 Cogs Loaded | 42+ Commands Available

---

## 📋 Table of Contents
- [Core Utility Commands](#core-utility-commands)
- [Security & Detection Commands](#security--detection-commands)
- [Threat Intelligence Commands](#threat-intelligence-commands)
- [Dashboard & Monitoring Commands](#dashboard--monitoring-commands)
- [Moderation & Enforcement Commands](#moderation--enforcement-commands)
- [Audit & Compliance Commands](#audit--compliance-commands)
- [Analytics & Metrics Commands](#analytics--metrics-commands)
- [Advanced Features Commands](#advanced-features-commands)
- [Owner-Only Commands](#owner-only-commands)
- [Tier-2 Memory & Intelligence Commands](#tier-2-memory--intelligence-commands)
- [Tier-2 Adversary & Decision Commands](#tier-2-adversary--decision-commands)
- [Observability & Health Commands](#observability--health-commands)
- [Resilience & Infrastructure Commands](#resilience--infrastructure-commands)

---

## Core Utility Commands

### Basic Information
```
!ping                       → Check bot latency
!uptime                     → Show bot uptime
!about                      → About the bot
!invite                     → Get bot invite link
!avatar [@user]             → Get user avatar
!userinfo [@user]           → Get detailed user info
!serverinfo                 → Get server statistics
!roll [sides]               → Roll a dice
!choose <option1|option2>   → Make a random choice
!poll "question" "option1" "option2" ...  → Create a poll
```

### Help & Documentation
```
!helpme                     → Get help and command list
!commands                   → View all commands
!docs [topic]               → View documentation
!commandstatus              → Command status check
!quicktest                  → Quick functionality test
!sysinfo                    → System information
!wholsowner                 → Who is the server owner?
!listroles                  → List all roles
!accept_rules               → Accept server rules
!test_alert                 → Test alert system
```

### Settings & Configuration
```
!settings / !config         → View server configuration
/config                     → View config (slash command)
!set_setting <key> <value>  → Change a setting
/set_setting <key> <value>  → Change setting (slash)
!setchannel <channel_type> #channel  → Set channel (welcome, farewell, logs, mod-log)
/setchannel <channel>       → Set channel (slash)
!setmessage <type> <message> → Set welcome/farewell message
/setmessage <type> <message> → Set message (slash)
!setautorole @role          → Set auto-role for new members
/setautorole @role          → Set auto-role (slash)
!toggle_embed               → Toggle embed format
/toggleembed                → Toggle embed (slash)
!reset_settings             → Reset to default settings
```

### Welcome & Farewell
```
!toggle_welcome             → Enable/disable welcome messages
!toggle_farewell            → Enable/disable farewell messages
!welcome_dm                 → Send welcome DM to users
```

### User Notifications
```
!dm_user @user <message>    → DM a user
!alert_user @user <message> → Alert a user
!notify_user @user <message> → Notify a user
!broadcast_dm <message>     → Broadcast DM to all members
```

### Server Management
```
!setup_soc                  → Full SOC role and channel setup wizard
!listroles_sentinel         → List sentinel roles
!listchannels_sentinel      → List sentinel channels
!server_analytics           → View server analytics
!growth_stats               → View growth statistics
!invite_stats               → View invite statistics
!invite_info [code]         → Get invite details
```

### Maintenance & Status
```
!maintenance_on [reason]    → Enable maintenance mode
!maintenance_off            → Disable maintenance mode
!maintenance_status         → Check maintenance status
!scheduled_maintenance <time> <reason>  → Schedule maintenance
```

---

## Security & Detection Commands

### Threat Detection & Response
```
!detectthreat <type> <level> [description]  → Manually trigger threat detection
/detectthreat <type> <level> [description]  → Trigger threat (slash)
!threathistory [limit]      → View threat response history
!threatplaybooks            → View automated threat response playbooks
```

**Threat Types**: spam, raid, phishing, malware, harassment, scam, unauthorized_access  
**Severity Levels**: low, medium, high, critical

### Anti-Cryptocurrency Detection
```
!checkcrypto <text>         → Manually scan text for crypto wallets/scams
!cryptodetections [days]    → View detection history
!cryptostats                → View crypto detection statistics
```

### Anti-Raid System
```
!raid_check                 → Check raid detection status
!raid_stats                 → View raid statistics
```

### Blacklist Management
```
!addblacklist <type> <id>   → Add to blacklist (user/guild/ip/domain)
!removeblacklist <id>       → Remove from blacklist
!blacklistinfo <id>         → Check blacklist status
!blackliststats             → View blacklist statistics
```

### Quarantine System
```
!quarantineuser @user       → Quarantine a user
!unquarantineuser @user     → Release quarantined user
!quarantinestatus           → View quarantine status
!quarantineevidence         → View quarantine evidence
!quarantinestats            → View quarantine statistics
```

### Cloud Security
```
!cloudadd <account>         → Add cloud account for monitoring
!cloudaccounts              → List cloud accounts
!clouddetail <account>      → Get cloud account details
!cloudassess                → Assess cloud security posture
```

---

## Threat Intelligence Commands

### IOC Management (Indicators of Compromise)
```
!addioc <type> <value> <category> [severity] [source]
                            → Add IOC (ip_address, domain, url, file_hash, email)
!searchioc <query>          → Search IOCs
!iocstats                   → View IOC statistics
!correlationreport [hours]  → View IOC correlation report
!iocaging                   → View IOC aging report
!importiocs                 → Import IOCs from CSV attachment
!exportiocs                 → Export IOCs to CSV file
!markfalsepositive <ioc> <reason>  → Mark IOC as false positive
```

### Threat Intelligence Hub
```
!threat_intel               → View threat intelligence overview
!threat <query>             → Search threats
!report_ioc <value>         → Report IOC to hub
!add_threat <name> [details] → Add threat to database
!threat_correlation [hours] → View threat correlations
!threat_hunt                → Conduct threat hunting
!signalstats                → View signal bus statistics
```

### Threat Feeds
```
!threatfeed_add             → Add threat intelligence feed
!threatfeed_list            → List all threat feeds
!threatfeed_update          → Manually update feeds
!threatfeed_indicators      → View threat indicators by severity
```

---

## Dashboard & Monitoring Commands

### Security Dashboards
```
!securitydash               → View real-time security metrics dashboard
!securitystatus             → Quick security status check
!socdash                    → Master SOC dashboard (unified view)
!sockealthcheck             → Security health check
!smetrics [period]          → Detailed metrics (24h, 7d, 30d)
```

### Executive Reporting
```
!executivedashboard         → C-level risk dashboard
!execsummary [period]       → Executive summary report (monthly/quarterly)
!boardreport                → Board-level security report
!risktrending               → Risk trending analysis (12-month trends)
```

### Incident Forecasting
```
!forecastincidents [period] → Predict upcoming incidents (7days, 30days, 90days)
!forecastdetail [id]        → Detailed incident forecast analysis
!forecastaccuracy           → View forecast accuracy metrics
!riskfactors                → View current risk factors
!incidenthistory            → View incident history
```

### Quarterly Reporting
```
!quarterly_report           → Generate quarterly security report
!quarterly_compliance       → Quarterly compliance report
!quarterly_investment       → Security investment analysis
!quarterly_compare          → Compare quarterly trends
!quarterly_dashboard        → Quarterly metrics dashboard
```

### Risk Profiling
```
!riskprofile [@user]        → View user risk profile
!riskaudit                  → Conduct risk audit
!risktimeline               → View risk timeline
!profileuser [@user]        → Profile user behavior
```

---

## Moderation & Enforcement Commands

### Message Management
```
!purge [amount] [@user]     → Delete messages (alias: !clean, !clear)
  Example: !purge 50 → Delete last 50 messages
  Example: !purge 20 @user → Delete last 20 from @user
/purge [amount] [@user]     → Purge messages (slash command)
```

### User Moderation
```
!kick @user [reason]        → Kick user from server
/kick @user [reason]        → Kick user (slash)
!ban @user [reason]         → Ban user from server
/ban @user [reason]         → Ban user (slash)
!unban <user_id> [reason]   → Unban user by ID
/unban <user_id> [reason]   → Unban user (slash)
!timeout @user [duration]   → Timeout user (10m, 1h, 1d, 2d, 1w)
/timeout @user [duration]   → Timeout user (slash)
!untimeout @user [reason]   → Remove timeout
/untimeout @user [reason]   → Remove timeout (slash)
!warn @user [reason]        → Issue warning to user
/warn @user [reason]        → Warn user (slash)
```

### Channel Management
```
!lock [channel]             → Lock channel (prevent @everyone sending)
!unlock [channel]           → Unlock channel
!slowmode [seconds]         → Set channel slowmode (0 to disable)
```

### Moderation Utilities
```
!automodrules               → View synced Discord automod rules
!automodviolations [days]   → View automod violations (last N days)
!automodsync                → Manually sync Discord automod rules
!spam_check                 → Check spam detection status
```

---

## Audit & Compliance Commands

### Audit Logs
```
!auditanalyze [hours]       → Analyze Discord audit logs (default 1h)
/auditanalyze [hours]       → Audit analysis (slash)
!perm_audit                 → Check for dangerous role permissions
```

### Compliance
```
!securitychecklist          → View security setup checklist
/secchecklist               → Security checklist (slash)
!secsetup                   → Guided security setup wizard
/secsetup                   → Setup wizard (slash)
!continuous_compliance_status → View compliance status
!run_compliance_scan        → Run compliance scan
!compliance_violations      → View compliance violations
!create_policy              → Create new compliance policy
!list_policies              → List all policies
!compliance_drift           → Detect configuration drift
!gdprcomply                 → View GDPR compliance status
!compliancestatus           → View overall compliance status
```

### Permissions & Security
```
!permission_audit           → Audit role permissions
!permissionscan             → Scan for dangerous permissions
```

---

## Analytics & Metrics Commands

### Command & Usage Analytics
```
!analytics                  → View command usage analytics
!command_stats              → Detailed command statistics
!user_stats                 → User activity statistics
!guild_stats                → Guild statistics
!analytics_heatmap          → Usage heatmap visualization
!export_analytics           → Export analytics to CSV
!reset_analytics            → Reset analytics data
```

### Performance & Diagnostics
```
!performance                → View command performance metrics
!profile_command            → Profile specific command
!slow_commands              → List slowest commands
!performance_export         → Export performance data
!reset_profile              → Reset performance metrics
!cogperformance             → View cog performance
!cogbenchmark               → Benchmark cogs
!optimizationreport         → Generate optimization report
!health_dashboard           → Bot health dashboard
!health_history             → Historical health data
!uptime_tracker             → Uptime tracking
!api_health_check           → Check API server health
```

### Error Tracking
```
!error_dashboard            → View error dashboard
!recent_errors              → View recent errors
!error_details <error_id>   → Get error details
!error_stats                → Error statistics
!error_config               → Configure error reporting
!clear_errors               → Clear error history
!error_log                  → View error log
```

### System Health
```
!health                     → Overall system health check
!health_history             → Historical health data
!self_repair                → Trigger self-repair
!dephealth                  → Check dependency health
!degradationmode            → View graceful degradation status
!observabilityboard         → Real-time observability dashboard
!observabilityevents        → View recent events
!observabilityalerts        → View alerts
```

---

## Advanced Features Commands

### Event Search & Investigation
```
!search <query>             → Full-text search across all events
!recentevents               → View recent events
!searchstats                → Search statistics
```

### Anomaly Detection
```
/anomalyscan @user          → Scan user for behavioral anomalies
/anomalyreport              → View anomaly detection report
/anomalywhitelist @user     → Whitelist user from detection
!anomalybaseline            → Create baseline for anomalies
!anomalytrain               → Train anomaly model
!anomalyalerts              → View anomaly alerts
/anomalyml                  → ML-guided anomaly detection
```

### Alert Management
```
/alertcreate                → Create new alert
/alertresolve               → Resolve an alert
/alertlist                  → List all active alerts
/alertescalate              → Escalate an alert
!alertack                   → Acknowledge an alert
!alertassign                → Assign alert to someone
!alertdetail                → View alert details
!alertstats                 → Alert statistics
/alertcorrelate             → Correlate related alerts
```

### Task Management
```
!tasks                      → View scheduled tasks
!task_info <task>           → Get task information
!stop_task <task>           → Stop a task
!start_task <task>          → Start a task
!restart_task <task>        → Restart a task
!task_stats                 → Task statistics
```

### Incident Management
```
!incidentplaybook <type>    → View incident response playbook
!playbooks                  → List all playbooks
!playbookstatus             → Playbook execution status
```

### Security Drills
```
!securitydrill <type>       → Run security drill
!drillhistory               → View drill history
!drillscores                → View drill effectiveness scores
```

### Threat Hunting
```
!threat_hunt                → Conduct threat hunting campaign
!securitytraining           → Security awareness training
```

### Advanced Logging (Disabled - Use moderation_logging instead)
```
!advlogs                    → View advanced logs
!log_level                  → Set logging level
!export_logs                → Export logs
!search_logs                → Search logs
!clear_logs                 → Clear logs
!log_config                 → Configure logging
!set_log_size               → Set log size limit
!set_log_backups            → Set backup count
```

---

## Owner-Only Commands

**Prefix**: `!` (Owner-only prefix)

### Bot Control
```
!shutdown / !stop / !halt   → Shut down the bot
!restart / !reboot          → Restart the bot
!emergency_stop / !estop / !panic_shutdown  → Emergency stop
```

### Cog Management
```
!reload_cog <cog> / !reload <cog>  → Reload a cog
!load_cog <cog> / !load <cog>      → Load a cog
!unload_cog <cog> / !unload <cog>  → Unload a cog
!list_cogs / !cogs                 → List all cogs
!sync_commands / !sync              → Sync slash commands
```

### System Information
```
!bot_stats / !stats         → View comprehensive bot statistics
!botstatus                  → Quick bot status
!sysinfo                    → System information
```

### Data Management
```
!savedata                   → Manually save all data
!datastats                  → View data statistics
```

### AI Governance & Control
```
!overridestats              → View AI override statistics
!biasreport                 → Generate bias analysis report
!checkprompt <text>         → Check for prompt injection
!injectionstats             → View injection detection stats
!abstentionpolicy           → View abstention policy settings
!setabstention <param> <value> → Update abstention threshold
!abstentionrate [system]    → View abstention rates
```

### Feature Flags
```
!featureflag <name> <enable|disable>  → Control feature flag
!featureflags               → View all feature flags
```

### Advanced Operations
```
!executeplaybook <name>     → Execute SOAR playbook
!failoversim                → Simulate failover
!blastradius <system>       → Analyze blast radius
!injectchaos                → Inject chaos for testing
!resilience                 → View resilience scorecard
```

---

## Tier-2 Memory & Intelligence Commands

### Context & Memory
```
!cachestats                 → View context cache statistics
!memorylifecycle            → Manage memory lifecycle
!conversationanalysis       → Analyze conversation history
!semanticsearch <query>     → Semantic search across context
!queryindex <query>         → Query knowledge index
!graphstats                 → View knowledge graph statistics
!vectorstats                → View vector embedding statistics
!attacktree <threat>        → Analyze attack tree for threat
!adversaryprofile <actor>   → View adversary profile
```

---

## Tier-2 Adversary & Decision Commands

### Threat Analysis
```
!profileuser [@user]        → Build user threat profile
!adversaryprofile           → View adversary profiles
!attacktree                 → Attack tree analysis
!remediation_recommender    → Get remediation recommendations
```

### Compliance & Training
```
!generate_remediation       → Generate remediation plan
!generate_training          → Generate training plan
!audit_plan                 → Create audit plan
```

---

## Observability & Health Commands

### Continuous Monitoring
```
!continuous_compliance_status → Real-time compliance status
!run_compliance_scan        → Scan compliance
!compliance_violations      → View violations
!create_policy              → Create policy
!list_policies              → List policies
!compliance_drift           → Detect drift
```

### Anomaly & Behavior
```
/anomalyscan @user          → Behavioral anomaly scan
/anomalyreport              → Anomaly report
/anomalywhitelist @user     → Whitelist user
!anomalybaseline            → Create baseline
!anomalytrain               → Train model
!anomalyalerts              → View alerts
/anomalyml                  → ML anomaly detection
```

---

## Resilience & Infrastructure Commands

### Resilience Testing
```
!resilience                 → Resilience scorecard
!dephealth                  → Dependency health matrix
!degradationmode            → Graceful degradation status
!injectchaos                → Chaos injection testing
!failoversim                → Failover simulation
!blastradius                → Blast radius analysis
```

---

## 🎯 Quick Command Groups

### Top 10 Most Used
```
!ping                       Quick latency check
!securitydash               Security overview
!warn @user                 Issue warning
!purge 50                   Cleanup messages
!detectthreat spam high     Simulate threat
!socdash                    SOC overview
!execsummary                Executive report
!serverinfo                 Server stats
!automodsync                Sync automod
!secchecklist               Security setup
```

### Top 5 Security Commands
```
!detectthreat               Threat detection
!securitydash               Security metrics
!socdash                    SOC dashboard
!execsummary                Executive report
!threathistory              Threat history
```

### Top 5 Moderation Commands
```
!purge                      Delete messages
!kick @user                 Kick user
!ban @user                  Ban user
!timeout @user              Mute user
!warn @user                 Issue warning
```

### Top 5 Investigation Commands
```
!search <query>             Search events
!auditanalyze               Analyze audit logs
!riskprofile                Risk assessment
!threathistory              Threat history
!anomalyreport              Anomaly analysis
```

---

## 📱 Dashboard Shortcuts

Access these web interfaces:
```
http://127.0.0.1:8000           → Main dashboard
http://127.0.0.1:8000/health    → Health endpoint
http://127.0.0.1:8000/docs      → API documentation
```

---

## 🔑 Command Syntax Notation

```
!command                    → Prefix command (use ! before command)
/command                    → Slash command (type / to trigger autocomplete)
[optional]                  → Optional parameter
<required>                  → Required parameter
@user                       → Mention a user
#channel                    → Mention a channel
<user_id>                   → Numeric user ID
<role>                      → Role mention or ID
<days|hours|weeks>          → Time duration
[24h|7d|30d]                → Time period choices
```

---

## ⚡ Pro Tips

1. **Slash commands** (`/`) have better autocomplete and help text
2. **Prefix commands** (`!`) work in any context
3. **Owner commands** require `!` prefix (security feature)
4. **Tab completion** works for both types
5. **Help**: Use `!helpme` or `!commands` for quick reference
6. **Documentation**: Use `!docs [topic]` for detailed help

---

**Last Updated**: February 2, 2026  
**Total Commands**: 200+ (across 174 cogs)  
**Status**: ✅ Production Ready
