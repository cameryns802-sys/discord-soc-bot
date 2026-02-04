# Watch Systems Quick Reference

## 5 Watch Systems for 24/7 Monitoring

### 🌙 Nightwatch (Night Hours: 7 PM - 7 AM)
```
!nightwatch_status              View night monitoring status
!nightwatch_config              View configuration
!nightwatch_set_hours 21 06     Set custom hours (9 PM - 6 AM)
!nightwatch_toggle              Enable/disable system
!nightwatch_set_threshold 5     Alert threshold
!nightwatch_auto_escalate       Toggle auto-escalation
!nightwatch_dm_alerts           Toggle DM notifications
```

### ☀️ Daywatch (Day Hours: 7 AM - 7 PM)
```
!daywatch_status                View day monitoring status
!daywatch_config                View configuration
!daywatch_set_hours 8 18        Set custom hours (8 AM - 6 PM)
!daywatch_toggle                Enable/disable system
!daywatch_toggle_engagement     Toggle engagement tracking
!daywatch_toggle_peak           Toggle peak detection
!daywatch_log_activity          Log activity
!daywatch_stats                 View statistics
```

### 👤 Userwatch (User Activity Tracking)
```
!userwatch_add @user            Add user to watchlist
!userwatch_remove @user         Remove from watchlist
!userwatch_list                 List all watched users
!userwatch_view @user           View user's activity details
!userwatch_config               View configuration
!userwatch_toggle               Enable/disable system
!userwatch_clear_events @user   Clear all events for user
```

**Tracked Events**: Messages, Joins, Voice, Role Changes

### 📊 Channelwatch (Channel Activity Tracking)
```
!channelwatch_add #channel      Add channel to watchlist
!channelwatch_remove #channel   Remove from watchlist
!channelwatch_list              List all watched channels
!channelwatch_view #channel     View channel's activity
!channelwatch_config            View configuration
!channelwatch_toggle            Enable/disable system
!channelwatch_reset #channel    Reset counters
```

**Tracked Metrics**: Message count, Unique users, Activity

### 🚨 Threatwatch (Security Threat Detection)
```
!threatwatch_status             View threat status
!threatwatch_list [10]          List recent threats
!threatwatch_actors             Show threat actors
!threatwatch_config             View configuration
!threatwatch_toggle             Enable/disable system
!threatwatch_clear              Clear threat logs
```

**Threat Types**: Member removal, Permission changes, Deletions

---

## Configuration Structure

**All systems support**:
- Enable/disable toggle
- Custom hour ranges
- Alert thresholds
- DM notifications
- Activity logging

**Data Location**: `data/` folder as JSON files

---

## Command Count by System

- Nightwatch: 7 commands
- Daywatch: 8 commands
- Userwatch: 9 commands
- Channelwatch: 7 commands
- Threatwatch: 6 commands
- **Total: 37 commands**

---

## Timeline

| System | Added | Status |
|--------|-------|--------|
| Nightwatch | Phase 4 | ✅ Enhanced Feb 3 |
| Daywatch | Phase 5 | ✅ Created Feb 3 |
| Userwatch | Today | ✅ Created Feb 3 |
| Channelwatch | Today | ✅ Created Feb 3 |
| Threatwatch | Today | ✅ Created Feb 3 |

---

## Monitor Setup Example

**Monitor a suspicious user 24/7**:
```
!userwatch_add @suspicious_user
```

**Monitor #general channel for spam**:
```
!channelwatch_add #general
```

**Track security threats**:
```
!threatwatch_status
!threatwatch_list
```

**Configure night monitoring**:
```
!nightwatch_set_hours 22 06      # 10 PM - 6 AM
!nightwatch_set_threshold 15     # Alert after 15 events
!nightwatch_dm_alerts            # Enable DM notifications
```

---

## Data Management

**Automatic Cleanup**:
- Nightwatch: Keeps last 100 sessions
- Daywatch: Keeps last 100 sessions
- Userwatch: Keeps last 100 events per user
- Channelwatch: Tracks unlimited metrics
- Threatwatch: Keeps last 500 threats

**Manual Cleanup**:
```
!userwatch_clear_events @user          # Clear user events
!channelwatch_reset #channel           # Reset channel counters
!threatwatch_clear                     # Clear all threats
```

---

## Integration Status

✅ All 5 systems registered in bot.py  
✅ All cogs have valid Python syntax  
✅ All configuration commands implemented  
✅ All data persistence configured  
✅ Ready for bot startup and testing

---

*Last Updated: February 3, 2025*  
*Created by: GitHub Copilot*  
*Part of Phase 5: Watch Systems Expansion*
