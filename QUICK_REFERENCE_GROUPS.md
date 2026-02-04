# Quick Reference - New Group Commands

## Phase 5: Group Command Systems

**What's New**: 16 command groups with 60+ organized slash commands

---

## 🛡️ Security Commands (`/threat`, `/ioc`, `/scan`, `/monitor`)

### `/threat` - Threat Management
```
/threat scan              # Scan server for threats
/threat level             # Current threat level
/threat actors            # List threat actors
/threat report [hours]    # Generate threat report
```

### `/ioc` - IOC Management
```
/ioc add <type> <value> <category>  # Add IOC (admin)
/ioc search <query>                 # Search IOC database
/ioc stats                          # View statistics
/ioc list [limit]                   # List recent IOCs
```

### `/scan` - Security Scanning
```
/scan permissions         # Scan role permissions
/scan channels           # Scan channel security
/scan vulnerabilities    # Security vulnerabilities
/scan members            # Scan member accounts
```

### `/monitor` - Monitoring Control
```
/monitor status          # View monitoring status
/monitor alerts [hours]  # View recent alerts
/monitor enable          # Enable monitoring (admin)
/monitor disable         # Disable monitoring (admin)
```

---

## 👮 Moderation Commands (`/infraction`, `/audit`, `/rule`, `/user`)

### `/infraction` - Infraction Management
```
/infraction view <user>      # View user's record
/infraction clear <user>     # Clear infractions (admin)
/infraction history [limit]  # View recent infractions
/infraction stats            # Server statistics
```

### `/audit` - Moderation Audit
```
/audit log [hours]           # View audit log
/audit moderator <mod>       # View mod's actions
/audit stats                 # Team statistics
/audit export [hours]        # Export to CSV (admin)
```

### `/rule` - Custom Automod
```
/rule create <type> <pattern> <action>  # Create rule
/rule list                              # List all rules
/rule delete <rule_id>                  # Delete rule
/rule violations [id] [hours]           # View violations
/rule toggle <id> <enabled>             # Enable/disable
```

### `/user` - User Management
```
/user info <user>            # User information
/user history <user>         # Action history
/user notes <user>           # Mod notes (private)
/user addnote <user> <note>  # Add note
/user cleanup <user> [limit] # Delete messages
```

---

## 📊 SOC Commands (`/incident`, `/dashboard`, `/alert`, `/investigate`, `/report`)

### `/incident` - Incident Management
```
/incident create <title> <severity>  # Create incident
/incident list [status]              # List incidents
/incident view <id>                  # View details
/incident close <id> <resolution>    # Close incident
/incident assign <id> <user>         # Assign to user
```

### `/dashboard` - SOC Dashboards
```
/dashboard security      # Security metrics
/dashboard executive     # C-level overview
/dashboard threats       # Threat intelligence
/dashboard compliance    # Compliance status
```

### `/alert` - Alert Management
```
/alert list [hours]      # List recent alerts
/alert view <id>         # View alert details
/alert acknowledge <id>  # Acknowledge alert
/alert configure         # Configure settings
```

### `/investigate` - Investigation
```
/investigate user <user> [hours]     # Investigate user
/investigate channel <ch> [hours]    # Investigate channel
/investigate ip <ip>                 # Investigate IP
/investigate timeline <incident_id>  # Generate timeline
```

### `/report` - Security Reports
```
/report security [period]         # Security report
/report executive                 # Executive summary
/report compliance <framework>    # Compliance report
/report export <type> [format]    # Export data
```

---

## 📋 Compliance Commands (`/policy`, `/data`, `/consent`, `/compaudit`, `/framework`)

### `/policy` - Policy Management
```
/policy create <name> <category>  # Create policy
/policy list [category]           # List policies
/policy view <id>                 # View details
/policy enforce <id>              # Enforce policy
```

### `/data` - Data Management (GDPR/CCPA)
```
/data request <type> <user>  # Submit data request
/data retention              # View retention policies
/data export <user>          # Export user data
/data delete <user> <confirm># Delete user data
```

### `/consent` - Consent Tracking
```
/consent view <user>    # View consent status
/consent grant <user>   # Grant consent
/consent revoke <user>  # Revoke consent
/consent audit          # Audit records
```

### `/compaudit` - Compliance Auditing
```
/compaudit scan <framework>     # Run compliance scan
/compaudit status               # Current status
/compaudit report <framework>   # Generate report
/compaudit findings [severity]  # View findings
```

### `/framework` - Framework Management
```
/framework list                 # List frameworks
/framework enable <framework>   # Enable framework
/framework configure <fw>       # Configure settings
/framework controls <fw>        # View controls
```

---

## Permission Requirements

| Command Group | Minimum Permission | Admin Only Commands |
|--------------|-------------------|-------------------|
| `/threat` | `manage_guild` | - |
| `/ioc` | `manage_guild` | `/ioc add` |
| `/scan` | `manage_guild` | - |
| `/monitor` | View only | `/monitor enable/disable` |
| `/infraction` | `moderate_members` | `/infraction clear` |
| `/audit` | `manage_guild` | `/audit export` |
| `/rule` | `manage_guild` | `/rule create/delete` |
| `/user` | `moderate_members` | - |
| `/incident` | `manage_guild` | - |
| `/dashboard` | `manage_guild` | `/dashboard executive` |
| `/alert` | `manage_guild` | `/alert configure` |
| `/investigate` | `manage_guild` | `/investigate ip` |
| `/report` | `manage_guild` | `/report export` |
| `/policy` | `manage_guild` | `/policy create/enforce` |
| `/data` | `administrator` | All commands |
| `/consent` | `administrator` | All commands |
| `/compaudit` | `manage_guild` | `/compaudit scan` |
| `/framework` | `manage_guild` | `/framework enable/configure` |

---

## Common Workflows

### Security Incident Response
```
1. /incident create "Phishing attack" high
2. /investigate user @suspect 24
3. /alert list 2
4. /threat scan
5. /incident close INC-123 "Phishing blocked, user warned"
```

### User Moderation
```
1. /user info @user
2. /infraction view @user
3. /user history @user
4. /user notes @user
5. /user addnote @user "Warning given for spam"
```

### Compliance Audit
```
1. /framework list
2. /compaudit scan gdpr
3. /compaudit status
4. /data retention
5. /compaudit report gdpr
```

### Threat Analysis
```
1. /threat scan
2. /ioc search suspicious-domain.com
3. /scan permissions
4. /monitor alerts 24
5. /threat report 24
```

---

## Integration Points

- **ThreatIntelHub**: IOC tracking, threat actors
- **AdvancedInfractions**: User infraction records
- **CustomAutomodRules**: Custom rule engine
- **DataManager**: Consent and data storage

---

## Quick Tips

✅ **Use autocomplete**: Start typing `/threat` and Discord shows all subcommands  
✅ **Check permissions**: Most commands require `manage_guild` or higher  
✅ **Use embeds**: All commands return rich embeds with formatted data  
✅ **Admin commands**: Some commands are restricted to administrators  
✅ **Integration**: Commands work with existing cogs and data

---

## Testing

After bot startup, run:
```
/sync
```
(Owner only - syncs commands to Discord)

Commands appear in 1-5 minutes.

---

## Support

**Files**:
- `cogs/security/security_groups.py`
- `cogs/moderation/moderation_groups.py`
- `cogs/soc/soc_groups.py`
- `cogs/compliance/compliance_groups.py`

**Full Documentation**: See `GROUP_COMMANDS_COMPLETE.md`

---

**Status**: ✅ Complete - 16 groups, 60+ commands ready
