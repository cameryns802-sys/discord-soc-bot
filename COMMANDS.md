# Discord SOC Bot - Complete Command Reference
**Bot Status:** 🟢 ONLINE & OPERATIONAL | **Version:** Advanced SOC 2.0 | **Loaded Cogs:** 357/396

---

## Table of Contents
1. [Core Commands](#core-commands)
2. [Incident Management](#incident-management)
3. [Alert & Rules Engine](#alert--rules-engine)
4. [Metrics & Analytics](#metrics--analytics)
5. [Threat Intelligence](#threat-intelligence)
6. [Integration Hub](#integration-hub)
7. [Automation Systems](#automation-systems)
8. [Alert Management](#alert-management)
9. [Security Systems](#security-systems)
10. [Evidence & Forensics](#evidence--forensics)
11. [Knowledge Base](#knowledge-base)
12. [Status & Reporting](#status--reporting)
13. [Nightwatch Monitoring](#nightwatch-monitoring)
14. [Configuration Management](#configuration-management)
15. [Disaster Recovery](#disaster-recovery)
16. [Workflow Automation](#workflow-automation)
17. [Role Management](#role-management)
18. [On-Call Scheduler](#on-call-scheduler)
19. [Team Management](#team-management)
20. [User Commands](#user-commands)
21. [Slash Commands (/)](#slash-commands-)

---

## Core Commands

### Slash Commands (/)
| Command | Description | Usage |
|---------|-------------|-------|
| `/ping` | Show bot latency | `/ping` |
| `/uptime` | Show bot uptime | `/uptime` |
| `/userinfo` | Show user information | `/userinfo [@user]` |
| `/serverinfo` | Show server information | `/serverinfo` |
| `/helpme` | Show all available commands | `/helpme` |
| `/whoisowner` | Show bot owner | `/whoisowner` |

---

## Incident Management

### Commands (Prefix: !)

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!createincident` | Create new incident | `!createincident <title> <severity>` | Admin |
| `!viewincident` | View incident details | `!viewincident <incident_id>` | Any |
| `!assignincident` | Assign incident to user | `!assignincident <incident_id> @user` | Admin |
| `!escalateincident` | Escalate incident | `!escalateincident <incident_id>` | Admin |
| `!resolveincident` | Mark incident resolved | `!resolveincident <incident_id> <reason>` | Admin |
| `!listincidents` | List all incidents | `!listincidents [status]` | Any |
| `!incidentstats` | View incident statistics | `!incidentstats` | Any |
| `!incident_status` | Update incident status | `!incident_status <incident_id> <status>` | Admin |

**Incident Statuses:** open, acknowledged, investigating, mitigating, resolved, closed

---

## Alert & Rules Engine

### Alert Rules Commands

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!createrule` | Create alert rule | `!createrule <name> <trigger> <action>` | Admin |
| `!viewrule` | View rule details | `!viewrule <rule_id>` | Any |
| `!triggeritrule` | Manually trigger rule | `!triggeritrule <rule_id>` | Admin |
| `!disablerule` | Disable alert rule | `!disablerule <rule_id>` | Admin |
| `!enablerule` | Enable alert rule | `!enablerule <rule_id>` | Admin |
| `!listrules` | List all alert rules | `!listrules [status]` | Any |
| `!rulestats` | View rule statistics | `!rulestats` | Any |

---

## Metrics & Analytics

### Dashboard Commands

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!dashboard` | View metrics dashboard | `!dashboard [timeframe]` | Any |
| `!recordalert` | Record alert metric | `!recordalert <type>` | Admin |
| `!recordresolution` | Record resolution metric | `!recordresolution <type>` | Admin |
| `!updateincidents` | Update incident metrics | `!updateincidents` | Admin |
| `!kpis` | View key performance indicators | `!kpis` | Any |

### Analytics & Reporting

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!generatereport` | Generate analytics report | `!generatereport <type> [days]` | Admin |
| `!viewreport` | View generated report | `!viewreport <report_id>` | Any |
| `!reportstatus` | View report status | `!reportstatus` | Any |
| `!exportreport` | Export report to file | `!exportreport <report_id>` | Admin |
| `!archivenreport` | Archive old report | `!archivereport <report_id>` | Admin |
| `!analyzecommunity` | Analyze community data | `!analyzecommunity` | Admin |

---

## Threat Intelligence

### Threat Reporting & Analytics

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!reportthreat` | Report threat | `!reportthreat <type> <severity> [details]` | Any |
| `!threatpatterns` | View threat patterns | `!threatpatterns [days]` | Any |
| `!threattrends` | View threat trends | `!threattrends [days]` | Any |
| `!threattypes` | List threat types | `!threattypes` | Any |
| `!threatstats` | View threat statistics | `!threatstats` | Any |
| `!viewthreat` | View threat details | `!viewthreat <threat_id>` | Any |

### Threat Hunting

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!starthunt` | Start threat hunt | `!starthunt <target> <hunt_type>` | Admin |
| `!addhuntclue` | Add hunt clue | `!addhuntclue <hunt_id> <clue>` | Admin |
| `!concludehunt` | Conclude hunt | `!concludehunt <hunt_id> <findings>` | Admin |
| `!listhunts` | List active hunts | `!listhunts [status]` | Any |
| `!huntprogress` | View hunt progress | `!huntprogress <hunt_id>` | Any |
| `!huntstats` | View hunting statistics | `!huntstats` | Any |
| `!proposehunt` | Propose hunt hypothesis | `!proposehunt <target> <hypothesis>` | Any |
| `!validatehunt` | Validate hunt findings | `!validatehunt <hunt_id>` | Admin |
| `!reporthunt` | Generate hunt report | `!reporthunt <hunt_id>` | Admin |
| `!archivehunt` | Archive hunt data | `!archivehunt <hunt_id>` | Admin |

---

## Integration Hub

### Third-Party Integration Commands

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!addintegration` | Add new integration | `!addintegration <name> <type> <config>` | Admin |
| `!listintegrations` | List integrations | `!listintegrations [status]` | Any |
| `!syncintegration` | Sync with integration | `!syncintegration <integration_id>` | Admin |
| `!testintegration` | Test integration | `!testintegration <integration_id>` | Admin |
| `!disableintegration` | Disable integration | `!disableintegration <integration_id>` | Admin |
| `!enableintegration` | Enable integration | `!enableintegration <integration_id>` | Admin |
| `!integrationlogs` | View integration logs | `!integrationlogs <integration_id>` | Admin |
| `!integrationstats` | View integration stats | `!integrationstats` | Any |

---

## Automation Systems

### Auto Escalation

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!setescalationrule` | Set escalation rule | `!setescalationrule <condition> <action>` | Admin |
| `!viewescalationrules` | View escalation rules | `!viewescalationrules` | Any |
| `!triggerescalation` | Manually trigger escalation | `!triggerescalation <target>` | Admin |

### Auto Evidence Collector

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!startevidencecollection` | Start collecting evidence | `!startevidencecollection <incident_id>` | Admin |
| `!addevidence` | Add evidence item | `!addevidence <incident_id> <type> <details>` | Any |
| `!viewevidence` | View collected evidence | `!viewevidence <incident_id>` | Any |
| `!exportevidence` | Export evidence | `!exportevidence <incident_id>` | Admin |
| `!validateevidence` | Validate evidence | `!validateevidence <incident_id>` | Admin |
| `!archivetevidence` | Archive evidence | `!archiveevidence <incident_id>` | Admin |

### Auto Health Checker

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!runhealthcheck` | Run system health check | `!runhealthcheck` | Admin |
| `!viewhealthstatus` | View health status | `!viewhealthstatus` | Any |
| `!schedulehealthcheck` | Schedule regular checks | `!schedulehealthcheck <interval>` | Admin |
| `!healthcheckhistory` | View check history | `!healthcheckhistory [limit]` | Any |
| `!healthcheckalerts` | View health alerts | `!healthcheckalerts` | Any |

### Auto Learning System

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!startlearning` | Start ML learning session | `!startlearning <model_type>` | Admin |
| `!trainmodel` | Train model with data | `!trainmodel <model_id> [dataset]` | Admin |
| `!evaluatemodel` | Evaluate model performance | `!evaluatemodel <model_id>` | Admin |
| `!deploymodel` | Deploy trained model | `!deploymodel <model_id>` | Admin |
| `!modelstatus` | View model status | `!modelstatus <model_id>` | Any |
| `!listmodels` | List all models | `!listmodels` | Any |
| `!modelmetrics` | View model metrics | `!modelmetrics <model_id>` | Any |
| `!predictiveanalysis` | Run predictive analysis | `!predictiveanalysis <type>` | Any |

### Auto Containment

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!initiatecontainment` | Start containment procedure | `!initiatecontainment <target>` | Admin |
| `!applycontainment` | Apply containment rule | `!applycontainment <rule_id>` | Admin |
| `!escapecontainment` | Check containment escape risk | `!escapecontainment <target>` | Admin |
| `!expandcontainment` | Expand containment scope | `!expandcontainment <target>` | Admin |
| `!releasecontainment` | Release from containment | `!releasecontainment <target>` | Admin |
| `!containmentstatus` | View containment status | `!containmentstatus` | Any |

### Auto Response System

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!setautoresponse` | Configure auto-response | `!setautoresponse <trigger> <response>` | Admin |
| `!viewresponses` | View auto-responses | `!viewresponses` | Any |
| `!tesrespone` | Test response | `!testresponse <response_id>` | Admin |
| `!disableresponse` | Disable response | `!disableresponse <response_id>` | Admin |
| `!enableresponse` | Enable response | `!enableresponse <response_id>` | Admin |
| `!responsehistory` | View response history | `!responsehistory [limit]` | Any |

---

## Alert Management

### Alert Control Commands

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!creattalert` | Create manual alert | `!createalert <type> <message> <severity>` | Admin |
| `!viewalert` | View alert details | `!viewalert <alert_id>` | Any |
| `!acknowledgealert` | Acknowledge alert | `!acknowledgealert <alert_id>` | Any |
| `!resolvealert` | Resolve alert | `!resolvealert <alert_id>` | Any |
| `!dismissalert` | Dismiss alert | `!dismissalert <alert_id>` | Admin |
| `!listalerts` | List alerts | `!listalerts [status]` | Any |
| `!alertstats` | View alert statistics | `!alertstats` | Any |

### Notification Management

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!setnotification` | Configure notifications | `!setnotification <type> <channel>` | Admin |
| `!testnotification` | Send test notification | `!testnotification <type>` | Admin |
| `!mutenotifications` | Mute notifications | `!mutenotifications <duration>` | Admin |
| `!unmutenotifications` | Unmute notifications | `!unmutenotifications` | Admin |
| `!notificationstatus` | View notification status | `!notificationstatus` | Any |
| `!notificationhistory` | View notification history | `!notificationhistory [limit]` | Any |
| `!schedulenotification` | Schedule notification | `!schedulenotification <time> <message>` | Admin |
| `!cancelnotification` | Cancel scheduled notification | `!cancelnotification <notification_id>` | Admin |
| `!notificationstats` | View notification stats | `!notificationstats` | Any |

---

## Security Systems

### Anti-Attack Systems

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!startdefense` | Start defense system | `!startdefense <type>` | Admin |
| `!activatedefense` | Activate defense | `!activatedefense <defense_id>` | Admin |
| `!disabledefense` | Disable defense | `!disabledefense <defense_id>` | Admin |
| `!defensehealth` | View defense health | `!defensehealth [defense_id]` | Any |
| `!defensestats` | View defense statistics | `!defensestats` | Any |
| `!defensesettings` | View/modify defense settings | `!defensesettings [defense_id] [setting] [value]` | Admin |

### Asset Management

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!addasset` | Register asset | `!addasset <name> <type> <owner>` | Admin |
| `!viewasset` | View asset details | `!viewasset <asset_id>` | Any |
| `!updateasset` | Update asset info | `!updateasset <asset_id> <field> <value>` | Admin |
| `!listassets` | List all assets | `!listassets [type]` | Any |
| `!protectasset` | Protect asset | `!protectasset <asset_id>` | Admin |
| `!unprotectasset` | Remove protection | `!unprotectasset <asset_id>` | Admin |

---

## Evidence & Forensics

### Evidence Manager

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!storeevidience` | Store evidence item | `!storevidence <case_id> <type> <details>` | Admin |
| `!chainofevidance` | View evidence chain | `!chainofevidence <evidence_id>` | Any |
| `!preserveevidence` | Preserve evidence | `!preserveevidence <evidence_id>` | Admin |
| `!releaseevidence` | Release evidence | `!releaseevidence <evidence_id>` | Admin |
| `!evidenceintegrity` | Check evidence integrity | `!evidenceintegrity <evidence_id>` | Admin |
| `!evidencehistory` | View evidence history | `!evidencehistory <evidence_id>` | Any |
| `!listevidence` | List all evidence | `!listevidence [case_id]` | Any |

---

## Knowledge Base

### Knowledge Management

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!addknowledge` | Add KB article | `!addknowledge <title> <content> <category>` | Admin |
| `!viewknowledge` | View KB article | `!viewknowledge <article_id>` | Any |
| `!searchknowledge` | Search KB | `!searchknowledge <query>` | Any |
| `!updateknowledge` | Update KB article | `!updateknowledge <article_id> <new_content>` | Admin |
| `!deleteknowledge` | Delete KB article | `!deleteknowledge <article_id>` | Admin |
| `!listknowledge` | List KB articles | `!listknowledge [category]` | Any |
| `!kbstats` | View KB statistics | `!kbstats` | Any |

---

## Status & Reporting

### Bot Status System

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!status_set` | Set bot status level | `!status_set <level>` | Admin |
| `!status_current` | View current status | `!status_current` | Any |
| `!status_history` | View status history | `!status_history [limit]` | Any |
| `!togglestatusupdate` | Toggle status updates | `!togglestatusupdate` | Admin |
| `!setstatus` | Set status mode (slash) | `/setstatus <mode>` | Admin |

**Status Levels:** normal 🟢, elevated 🟡, panic 🔴, lockdown ⚫

### Announcements & Alerts

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!setannouncements` | Set announcement channel | `!setannouncements [#channel]` | Admin |
| `!toggleannounce` | Toggle announcements | `!toggleannounce` | Admin |
| `!announcedrill` | Announce security drill | `!announcedrill <type> [details]` | Admin |
| `!announcethreat` | Announce threat | `!announcethreat <level> <info>` | Admin |
| `!resetthreat` | Reset threat level | `!resetthreat` | Admin |
| `!threatstatus` | View threat status | `!threatstatus` | Any |
| `!statushistory` | View status history | `!statushistory [limit]` | Any |

---

## Nightwatch Monitoring

### Night Monitoring System (7 PM - 7 AM)

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!nightwatch_status` | View nightwatch status | `!nightwatch_status` | Any |
| `!watch_user` | Monitor specific user | `!watch_user @user [duration]` | Admin |
| `!watch_channel` | Monitor channel | `!watch_channel #channel [duration]` | Admin |
| `!watch_server` | Monitor entire server | `!watch_server [duration]` | Admin |
| `!unwatch_user` | Stop monitoring user | `!unwatch_user @user` | Admin |
| `!unwatch_channel` | Stop monitoring channel | `!unwatch_channel #channel` | Admin |
| `!unwatch_server` | Stop monitoring server | `!unwatch_server` | Admin |
| `!nightwatch_alerts` | View alerts from overnight | `!nightwatch_alerts` | Any |
| `!nightwatch_report` | Generate night report | `!nightwatch_report` | Admin |

---

## Configuration Management

### Change Tracking

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!trackchange` | Track configuration change | `!trackchange <component> <change>` | Admin |
| `!viewchanges` | View recent changes | `!viewchanges [limit]` | Any |
| `!approvechange` | Approve pending change | `!approvechange <change_id>` | Admin |
| `!rejectchange` | Reject change | `!rejectchange <change_id>` | Admin |
| `!changehistory` | View change history | `!changehistory [component]` | Any |
| `!rollbackchange` | Rollback change | `!rollbackchange <change_id>` | Admin |
| `!changeauditor` | View change audits | `!changeauditor [limit]` | Admin |
| `!changestats` | View change statistics | `!changestats` | Any |

### Change Management

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!proposechange` | Propose system change | `!proposechange <description>` | Any |
| `!reviewchange` | Review change proposal | `!reviewchange <proposal_id> <approval>` | Admin |
| `!implementchange` | Implement approved change | `!implementchange <proposal_id>` | Admin |
| `!validatechange` | Validate change | `!validatechange <change_id>` | Admin |
| `!communitychange` | Community vote on change | `!communitychange <proposal_id>` | Any |
| `!changeimpact` | Analyze change impact | `!changeimpact <change_id>` | Admin |

---

## Disaster Recovery

### Recovery System

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!initiaterecovery` | Start disaster recovery | `!initiaterecovery [recovery_point]` | Admin |
| `!backupnow` | Backup immediately | `!backupnow` | Admin |
| `!restorebackup` | Restore from backup | `!restorebackup <backup_id>` | Admin |
| `!verifybackup` | Verify backup integrity | `!verifybackup <backup_id>` | Admin |
| `!listbackups` | List all backups | `!listbackups [limit]` | Any |
| `!recoveryestimate` | Estimate recovery time | `!recoveryestimate` | Admin |
| `!recoverystatus` | View recovery status | `!recoverystatus` | Any |

---

## Workflow Automation

### Automation Control

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!createworkflow` | Create automation workflow | `!createworkflow <name> <steps>` | Admin |
| `!viewworkflow` | View workflow details | `!viewworkflow <workflow_id>` | Any |
| `!runworkflow` | Execute workflow | `!runworkflow <workflow_id>` | Admin |
| `!pauseworkflow` | Pause workflow | `!pauseworkflow <workflow_id>` | Admin |
| `!resumeworkflow` | Resume workflow | `!resumeworkflow <workflow_id>` | Admin |
| `!listworkflows` | List workflows | `!listworkflows [status]` | Any |
| `!workflowstatus` | View workflow status | `!workflowstatus <workflow_id>` | Any |

---

## Role Management

### Role Control

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!addrole` | Create custom role | `!addrole <name> <permissions>` | Admin |
| `!removerole` | Delete role | `!removerole <role_id>` | Admin |
| `!grantrole` | Assign role to user | `!grantrole @user <role_id>` | Admin |
| `!revokerole` | Remove role from user | `!revokerole @user <role_id>` | Admin |
| `!viewrole` | View role details | `!viewrole <role_id>` | Any |
| `!listroles` | List all roles | `!listroles` | Any |
| `!rolepermissions` | View role permissions | `!rolepermissions <role_id>` | Any |
| `!updatepermissions` | Update role permissions | `!updatepermissions <role_id> <perms>` | Admin |
| `!rolestats` | View role statistics | `!rolestats` | Any |
| `!rolemembers` | View role members | `!rolemembers <role_id>` | Any |
| `!audituseroles` | Audit user roles | `!audituser roles @user` | Admin |
| `!approverolechange` | Approve role change | `!approverolechange <change_id>` | Admin |

---

## On-Call Scheduler

### Schedule Management

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!createrotation` | Create on-call rotation | `!createrotation <name> [shift_hours]` | Admin |
| `!addrotationmember` | Add rotation member | `!addrotationmember <rotation_id> @user` | Admin |
| `!startshift` | Start next shift | `!startshift <rotation_id>` | Admin |
| `!whoisoncall` | View current on-call | `!whoisoncall [rotation_id]` | Any |
| `!rotationstats` | View rotation stats | `!rotationstats` | Any |

---

## Team Management

### Team Setup & Control

| Command | Description | Usage | Permissions |
|---------|-------------|-------|-------------|
| `!addteammember` | Add team member | `!addteammember @user <role>` | Admin |
| `!removeteammember` | Remove team member | `!removeteammember @user` | Admin |
| `!updatestatus` | Update member status | `!updatestatus @user [active\|unavailable\|on-leave]` | Manage Guild |
| `!assignteam` | Assign to team | `!assignteam @user <team_name>` | Admin |
| `!viewteam` | View team info | `!viewteam [team_name]` | Any |
| `!teamstats` | View team statistics | `!teamstats` | Any |

---

## User Commands

### User-Facing Features

| Command | Description | Usage |
|---------|-------------|-------|
| `/level` | View your level/XP | `/level [@user]` |
| `/leaderboard` | View server leaderboard | `/leaderboard` |
| `/rep` | View your reputation | `/rep [@user]` |
| `/giverep` | Give reputation | `/giverep @user [reason]` |
| `/avatar` | View user avatar | `/avatar [@user]` |
| `/myactivity` | View your activity | `/myactivity` |
| `/myreceipts` | View moderation receipts | `/myreceipts` |
| `/remindme` | Set a reminder | `/remindme <time> <reminder>` |
| `/reminders` | View your reminders | `/reminders` |
| `/trivia` | Start trivia | `/trivia` |
| `/answer` | Answer trivia | `/answer <answer>` |
| `/suggest` | Submit suggestion | `/suggest <suggestion>` |
| `/checkconsent` | Check consent status | `/checkconsent` |
| `/giveconsent` | Give data consent | `/giveconsent` |
| `/privacyaccept` | Accept privacy policy | `/privacyaccept` |
| `/tosaccept` | Accept terms of service | `/tosaccept` |
| `/joininterest` | Join interest role | `/joininterest <interest>` |
| `/challenge` | Start security challenge | `/challenge` |
| `/healthcheck` | System health check | `/healthcheck` |
| `/systemstatus` | View system status | `/systemstatus` |
| `/sentiment` | Analyze server sentiment | `/sentiment` |
| `/achievements` | View achievements | `/achievements` |
| `/welcome_stats` | Welcome system stats | `/welcome_stats` |
| `/verify_status` | Verification status | `/verify_status` |
| `/communitystats` | Community analytics | `/communitystats` |
| `/rules` | View server rules | `/rules` |
| `/tos` | View terms of service | `/tos` |
| `/privacy` | View privacy policy | `/privacy` |

---

## Slash Commands (/)

### System Slash Commands
These are Discord slash commands (not prefix-based).

| Command | Description | Usage |
|---------|-------------|-------|
| `/ping` | Bot latency | `/ping` |
| `/uptime` | Bot uptime | `/uptime` |
| `/userinfo` | User information | `/userinfo [@user]` |
| `/serverinfo` | Server information | `/serverinfo` |
| `/helpme` | Show all commands | `/helpme` |
| `/whoisowner` | Bot owner info | `/whoisowner` |
| `/setstatus` | Set bot status (Admin) | `/setstatus <normal\|elevated\|panic\|lockdown>` |

---

## Command Prefixes & Usage

### Prefix Commands
- **Standard Prefix:** `!` (for owner/admin) or mention bot
- **Example:** `!createincident "Title" high`

### Slash Commands
- **Prefix:** `/`
- **Example:** `/ping`

---

## Permission Levels

| Level | Description | Examples |
|-------|-------------|----------|
| Any | All users | view, list, status commands |
| Manage Guild | Manage guild permission | role updates, team assignments |
| Admin | Administrator permission | create, delete, modify, escalate |
| Owner Only | Bot owner only | system configuration |

---

## Statuses & Levels

### Bot Status Levels
- 🟢 **NORMAL** - All systems operational
- 🟡 **ELEVATED** - Enhanced monitoring active
- 🔴 **PANIC** - Critical threat active  
- ⚫ **LOCKDOWN** - Emergency protocols engaged

### Threat Levels
- **Low** - Minor suspicious activity
- **Medium** - Moderate threat detected
- **High** - Critical threat active
- **Critical** - System-wide emergency

### Incident Status
- **open** - New incident created
- **acknowledged** - Staff aware
- **investigating** - Actively investigating
- **mitigating** - Mitigation in progress
- **resolved** - Issue resolved
- **closed** - Incident closed

---

## Availability Notes

**Note:** Some commands may show warnings if duplicate implementations exist. The bot remains fully operational with 357/396 cogs loaded. Primary implementations are prioritized.

**Status Rotation:** Bot status rotates every 30 seconds with system health and threat level information.

---

**Last Updated:** February 1, 2026 | **Bot Version:** SOC 2.0 Advanced
