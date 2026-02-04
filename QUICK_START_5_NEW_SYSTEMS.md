# Quick Reference: 5 New Systems Overview

## System Overview

| System | Category | Purpose | Commands |
|--------|----------|---------|----------|
| **Advanced Infractions** | Moderation | Track user infractions with auto-escalation | 5 |
| **Mod Audit Log** | Moderation | Audit mod actions, detect abuse | 4 |
| **Custom Automod Rules** | Security | Custom rules beyond Discord automod | 4 |
| **Invite Link Control** | Security | Manage Discord invite sharing | 6 |
| **Announcement System** | Utility | Announcements & scheduled messages | 7 |

**Total**: 5 systems, 26 commands, 1,750+ lines of code

---

## System 1: Advanced Infractions System

**What it does**: Tracks user warnings, mutes, kicks, bans with progressive escalation

**Key Features**:
- ⚠️ Auto-escalation: 2 warns → mute, 3 warns → kick, 4+ warns → ban
- 📋 Full infraction history per user
- 🎯 User appeals system
- ⏰ Warn expiration (30 days)
- 🔔 User notifications

**Top Commands**:
```
/warn @user reason                 - Issue warning
/mute @user 60 reason             - Mute user (60 minutes)
/userrecord @user                 - View user's record
```

**Data File**: `data/infractions.json`

---

## System 2: Mod Audit Log

**What it does**: Logs every moderator action and detects abuse patterns

**Key Features**:
- 📝 Complete action history
- 📊 Moderator statistics
- 🚨 Abuse detection (high ban rate, reversals, etc.)
- 👁️ Accountability & oversight
- 🔄 Action reversal tracking

**Top Commands**:
```
/modactions [mod]                 - View mod's action history
/useractions @user                - View actions against user
/modstats                         - Show team statistics
```

**Data File**: `data/mod_audit.json`

---

## System 3: Custom Automod Rules

**What it does**: Create custom moderation rules beyond Discord's built-in automod

**Key Features**:
- 4 rule types: keyword, regex, domain, user
- 5 action types: warn, mute, kick, ban, delete
- Real-time message checking
- Enable/disable per rule
- Violation tracking

**Top Commands**:
```
/addrule type pattern action      - Create rule
/rules                            - List all rules
/ruleviolations rule_id           - View violations
```

**Data File**: `data/custom_automod_rules.json`

**Example Rules**:
- `/addrule keyword "badword" ban` - Ban users saying "badword"
- `/addrule regex "discord\.gg/\w+" delete` - Delete Discord invites
- `/addrule domain "scam.com" mute 60` - Mute users posting scam.com

---

## System 4: Invite Link Control

**What it does**: Detect and manage Discord invite link sharing

**Key Features**:
- 🔍 Real-time detection (discord.gg, discord.com/invite)
- 🚫 Auto-delete or warn
- ✅ Whitelist specific invites
- 🔔 User/mod notifications
- 📋 Sharing history

**Top Commands**:
```
/inviteconfig                     - View settings
/setinviteaction delete           - Set to delete invites
/whitelist discord.gg/myserver    - Add to whitelist
```

**Data File**: `data/invite_links.json`

---

## System 5: Announcement System

**What it does**: Create and schedule server announcements with polls

**Key Features**:
- 📢 Send to channels or DM to roles
- ⏰ Schedule for future delivery
- 🗳️ Interactive polls with reactions
- 📋 Announcement history
- 🔄 Automatic scheduled delivery

**Top Commands**:
```
/announce message                 - Send announcement now
/schedule #channel "Title" 24 msg - Schedule for 24 hours
/poll question option1 option2    - Create poll
```

**Data File**: `data/announcements.json`

**Background Task**: Runs every minute to deliver scheduled announcements

---

## Real-World Examples

### Example 1: Warn a Spammer
```
/warn @user@1234 spamming the chat with 50 messages
```
→ User gets DM about warning  
→ Warning recorded in infractions  
→ Action logged in mod audit log  
→ 2nd warn in 30 days triggers auto-mute

### Example 2: Block Invite Sharing
```
/inviteconfig                     # Check settings
/setinviteaction delete           # Auto-delete invites
/whitelist discord.gg/official    # Whitelist official server
```
→ All discord.gg links auto-deleted  
→ Official server invite is whitelisted  
→ User notified and logged

### Example 3: Create Auto-Moderation Rule
```
/addrule keyword "badword" ban
```
→ Anyone saying "badword" gets auto-banned  
→ Message deleted automatically  
→ Violation logged with timestamp

### Example 4: Schedule Announcement
```
/schedule #announcements "Weekly Update" 24 "Server maintenance at 2PM UTC tomorrow"
```
→ Message scheduled for 24 hours from now  
→ Auto-sends when time arrives  
→ Recorded in announcement history

### Example 5: Check Mod Accountability
```
/modstats
/auditlog 24
```
→ See which mods took what actions  
→ Detect abuse patterns  
→ View complete audit trail

---

## Configuration Reference

### Infractions
```
Max warns before mute: 2
Max warns before kick: 3
Max warns before ban: 4
Warn expiration: 30 days
```

### Invite Control
```
Action: "delete" or "warn"
Notify user: Yes/No
Notify mods: Yes/No
Whitelist enabled: Yes/No
```

### Custom Rules
```
Patterns: keyword, regex, domain, user
Actions: warn, mute (duration), kick, ban, delete
Enable/disable: Per rule
```

### Announcements
```
Max options per poll: 10
Poll duration: Until removed
Scheduled: Background task (every minute)
History: Last 500 announcements
```

---

## Command Categories

### Moderator Commands (Primary)
- `/warn` - Issue warnings
- `/mute` - Mute users
- `/inviteconfig` - Manage invite settings
- `/addrule` - Create auto-rules
- `/modactions` - View mod history
- `/useractions` - View user actions
- `/announce` - Send announcements

### Admin Commands (Configuration)
- `/modstats` - Show mod performance
- `/rules` - List all rules
- `/setinviteaction` - Set invite action
- `/whitelist` - Manage whitelist
- `/schedule` - Schedule announcement
- `/poll` - Create polls

### User Commands
- `/appeal` - Appeal infraction
- `/userrecord` - View own record (if allowed)

### View-Only Commands
- `/appeals` - View pending appeals
- `/auditlog` - View action history
- `/scheduled` - View pending announcements
- `/announcehistory` - View past announcements
- `/whitelistshow` - List whitelisted invites
- `/invitehistory` - View invite sharing history

---

## Data Files Created Automatically

When commands are first used, these files auto-create:

| File | Size | Contents |
|------|------|----------|
| `data/infractions.json` | ~500B | Infractions & appeals |
| `data/mod_audit.json` | ~500B | Audit log & mod stats |
| `data/custom_automod_rules.json` | ~500B | Rules & violations |
| `data/invite_links.json` | ~500B | Config, whitelist, log |
| `data/announcements.json` | ~500B | Announcements, polls |

**Auto-Create**: Yes - No manual creation needed!

---

## Integration with Existing Systems

### Signal Bus Integration
- Advanced Infractions → emits ESCALATION_REQUIRED signal
- Invite Link Control → emits THREAT_DETECTED signal
- Custom Rules → emits POLICY_VIOLATION signals

### Timezone
- All timestamps use PST (America/Los_Angeles)
- Consistent with existing bot timezone

### Data Manager
- Coordinates with DataManager for configuration
- Respects per-guild settings

### Message Listeners
- Custom Automod Rules: Real-time checking
- Invite Link Control: Real-time detection
- Non-blocking, efficient implementations

---

## Status Check

**All 5 Systems**: ✅ READY

- ✅ Advanced Infractions: Created, tested, loaded
- ✅ Mod Audit Log: Created, tested, loaded
- ✅ Custom Automod Rules: Created, tested, loaded
- ✅ Invite Link Control: Created, tested, loaded
- ✅ Announcement System: Created, tested, loaded

**Bot Status**: ✅ All 87 commands synced to Discord

---

## Recommended Next Steps

1. ✅ **Deploy to Production** - Systems are ready
2. **Configure Rules** - Set up custom automod rules for your server
3. **Test Commands** - Try warnings, announcements, etc.
4. **Monitor Audit Log** - Check `/modstats` to verify everything working
5. **Set Mod Roles** - Ensure moderators have proper permissions

---

*Last Updated: February 3, 2025*  
*Phase 4 - Advanced Moderation & Security Systems*

