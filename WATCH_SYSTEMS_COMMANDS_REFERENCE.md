# Complete Watch Systems Command Reference

## Nightwatch Commands (7)

### View & Monitor
```
!nightwatch_status                View nightwatch status and current session info
```

### Configuration
```
!nightwatch_config                View all configuration settings
!nightwatch_set_hours START END   Set custom night hours (0-23 format)
!nightwatch_toggle                Enable or disable the entire nightwatch system
!nightwatch_set_threshold NUM     Set alert threshold (number of events)
!nightwatch_auto_escalate         Toggle automatic escalation on high alerts
!nightwatch_dm_alerts             Toggle DM notifications to admins
```

**Example Usage**:
```
!nightwatch_set_hours 21 06       # 9 PM to 6 AM
!nightwatch_set_threshold 15      # Alert after 15 events
!nightwatch_dm_alerts             # Toggle DM notifications
```

---

## Daywatch Commands (8)

### View & Monitor
```
!daywatch_status                  View daywatch status and current activity
!daywatch_stats                   View detailed statistics and peak hours
```

### Configuration
```
!daywatch_config                  View all configuration settings
!daywatch_set_hours START END     Set custom day hours (0-23 format)
!daywatch_toggle                  Enable or disable the entire daywatch system
!daywatch_toggle_engagement       Toggle engagement metrics tracking
!daywatch_toggle_peak             Toggle peak hour detection
!daywatch_log_activity            Manually log current activity
```

**Example Usage**:
```
!daywatch_set_hours 8 18          # 8 AM to 6 PM
!daywatch_toggle_engagement       # Toggle engagement tracking
!daywatch_stats                   # View statistics
```

---

## Userwatch Commands (9)

### Add/Remove Users
```
!userwatch_add @user              Add a user to the watchlist
!userwatch_remove @user           Remove a user from the watchlist
```

### View & Monitor
```
!userwatch_list                   List all currently watched users
!userwatch_view @user             View detailed activity for a specific user
```

### Configuration
```
!userwatch_config                 View all configuration settings
!userwatch_toggle                 Enable or disable the entire userwatch system
!userwatch_clear_events @user     Clear all recorded events for a user
```

**Tracked Events**:
- Messages (with content preview)
- Server joins
- Voice channel activity
- Role changes (added/removed)

**Example Usage**:
```
!userwatch_add @suspicious_user   # Start monitoring user
!userwatch_view @suspicious_user  # See all activity
!userwatch_clear_events @user     # Clear history
```

---

## Channelwatch Commands (7)

### Add/Remove Channels
```
!channelwatch_add #channel        Add a channel to the watchlist
!channelwatch_remove #channel     Remove a channel from the watchlist
```

### View & Monitor
```
!channelwatch_list                List all currently watched channels
!channelwatch_view #channel       View detailed activity for a channel
```

### Configuration
```
!channelwatch_config              View all configuration settings
!channelwatch_toggle              Enable or disable the entire channelwatch system
!channelwatch_reset #channel      Reset message counters for a channel
```

**Tracked Metrics**:
- Total message count
- Number of unique users posting
- User participation list
- Activity over time

**Example Usage**:
```
!channelwatch_add #announcements  # Start monitoring channel
!channelwatch_view #announcements # See channel stats
!channelwatch_reset #channel      # Reset counters
```

---

## Threatwatch Commands (6)

### View & Monitor
```
!threatwatch_status               View current threat status and summary
!threatwatch_list [LIMIT]         List recent detected threats (default 10)
!threatwatch_actors               Show all identified threat actors
```

### Configuration
```
!threatwatch_config               View all configuration settings
!threatwatch_toggle               Enable or disable the entire threatwatch system
!threatwatch_clear                Clear all threat logs (careful with this!)
```

**Threat Categories**:
- Member removal (kick/ban)
- Permission changes
- Mass deletion patterns
- Role escalations

**Example Usage**:
```
!threatwatch_status               # Check threat level
!threatwatch_list 20              # See last 20 threats
!threatwatch_actors               # View threat actors
```

---

## Configuration Command Pattern

### All Systems Support This Pattern

**View Configuration**:
```
!SYSTEM_config
```
Shows all current settings for that watch system.

**Enable/Disable**:
```
!SYSTEM_toggle
```
Turns the system on or off.

**Change Settings**:
```
!SYSTEM_set_OPTION VALUE
```
Changes specific configuration option.

---

## Example Monitoring Scenarios

### Scenario 1: Monitor Suspicious User 24/7
```
!userwatch_add @suspect_user
!userwatch_view @suspect_user      # Check activity at any time
!nightwatch_dm_alerts              # Get alerts at night
!daywatch_stats                    # Check stats during day
```

### Scenario 2: Monitor Channel for Spam
```
!channelwatch_add #announcements
!channelwatch_config               # View current settings
!channelwatch_view #announcements  # Check metrics
!channelwatch_reset #announcements # Clear counts
```

### Scenario 3: Track Security Threats
```
!threatwatch_status                # Check if threats detected
!threatwatch_list                  # See recent threats
!threatwatch_actors                # Who's causing threats
```

### Scenario 4: Custom Night Monitoring
```
!nightwatch_set_hours 22 06        # 10 PM - 6 AM
!nightwatch_set_threshold 20       # Alert after 20 events
!nightwatch_auto_escalate          # Auto-escalate high alerts
!nightwatch_dm_alerts              # Send DMs at night
```

### Scenario 5: Custom Day Monitoring
```
!daywatch_set_hours 9 17           # 9 AM - 5 PM (business hours)
!daywatch_toggle_peak              # Track peak activity times
!daywatch_stats                    # View engagement metrics
```

---

## Command Availability

### User-Accessible Commands
- All `/SYSTEM_status` commands
- All `/SYSTEM_view` commands
- All `/SYSTEM_list` commands
- `/SYSTEM_config` (informational)

### Admin-Level Commands
- All add/remove commands
- All configuration/toggle commands
- All reset/clear commands

### Owner-Only Commands
- May be restricted based on permissions (configurable)

---

## Total Command Count

| System | Count |
|--------|-------|
| Nightwatch | 7 |
| Daywatch | 8 |
| Userwatch | 9 |
| Channelwatch | 7 |
| Threatwatch | 6 |
| **TOTAL** | **37** |

---

## Data Files Generated

Each system creates a JSON data file automatically:

```
data/nightwatch_system.json      # Night sessions and config
data/daywatch_system.json        # Day sessions and config
data/userwatch_system.json       # User activity data
data/channelwatch_system.json    # Channel activity data
data/threatwatch_system.json     # Threat logs and actors
```

These files are automatically created on first use and updated with each command or event.

---

## Quick Reference Card

### Monitor Users
```
!userwatch_add @user              Start monitoring
!userwatch_view @user             See activity
!userwatch_remove @user           Stop monitoring
```

### Monitor Channels
```
!channelwatch_add #channel        Start monitoring
!channelwatch_view #channel       See activity
!channelwatch_remove #channel     Stop monitoring
```

### Monitor Threats
```
!threatwatch_status               Check threats
!threatwatch_list                 List threats
!threatwatch_actors               See who's causing trouble
```

### Configure Time
```
!nightwatch_set_hours 21 06       Night: 9 PM - 6 AM
!daywatch_set_hours 8 18          Day: 8 AM - 6 PM
```

### Configure Alerts
```
!nightwatch_set_threshold 10      Alert after 10 events
!nightwatch_dm_alerts             Send DM alerts
```

---

**Last Updated**: February 3, 2025  
**Total Commands**: 37 across 5 systems  
**Status**: All systems operational ✅
