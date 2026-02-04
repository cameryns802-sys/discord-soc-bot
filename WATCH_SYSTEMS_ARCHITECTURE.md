# Watch Systems Architecture Diagram

## System Overview

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     DISCORD BOT - WATCH SYSTEMS (5 TOTAL)                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

                         24/7 MONITORING INFRASTRUCTURE
                                    
        ┌────────────────────────────────────────────────────────────┐
        │            TIME-BASED MONITORING (24-HOUR COVERAGE)        │
        └────────────────────────────────────────────────────────────┘
                                    
        ┌──────────────────────────┐    ┌──────────────────────────┐
        │   🌙 NIGHTWATCH          │    │   ☀️ DAYWATCH           │
        ├──────────────────────────┤    ├──────────────────────────┤
        │ Time: 7 PM - 7 AM        │    │ Time: 7 AM - 7 PM       │
        │ Status: Active (Night)   │    │ Status: Active (Day)    │
        │ Commands: 7              │    │ Commands: 8             │
        │ Features:                │    │ Features:               │
        │ • Session tracking       │    │ • Activity counting     │
        │ • Alert thresholds       │    │ • Peak hour detection   │
        │ • Auto-escalation        │    │ • Engagement tracking   │
        │ • DM notifications       │    │ • Statistics            │
        └──────────────────────────┘    └──────────────────────────┘
                                    
        ┌────────────────────────────────────────────────────────────┐
        │          ACTIVITY-BASED MONITORING (REAL-TIME)             │
        └────────────────────────────────────────────────────────────┘
                                    
        ┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
        │   👤 USERWATCH           │    │   📊 CHANNELWATCH        │    │   🚨 THREATWATCH         │
        ├──────────────────────────┤    ├──────────────────────────┤    ├──────────────────────────┤
        │ Purpose: User Behavior   │    │ Purpose: Channel Info    │    │ Purpose: Security       │
        │ Commands: 9              │    │ Commands: 7              │    │ Commands: 6             │
        │ Tracks:                  │    │ Tracks:                  │    │ Tracks:                 │
        │ • Messages               │    │ • Message count          │    │ • Threats               │
        │ • Joins                  │    │ • User participation     │    │ • Threat actors         │
        │ • Voice activity         │    │ • Activity metrics       │    │ • Severity levels       │
        │ • Role changes           │    │ • Volume alerts          │    │ • Signal emission       │
        └──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘

═════════════════════════════════════════════════════════════════════════════════════════════════════

                              DATA PERSISTENCE LAYER
                                    
        data/nightwatch_system.json       → Night monitoring data
        data/daywatch_system.json         → Day monitoring data
        data/userwatch_system.json        → User activity data
        data/channelwatch_system.json     → Channel activity data
        data/threatwatch_system.json      → Threat data

═════════════════════════════════════════════════════════════════════════════════════════════════════

                            CONFIGURATION (UNIFIED PATTERN)
                                    
        ┌─────────────────────────────┐
        │ /system_config              │ → View all settings
        ├─────────────────────────────┤
        │ /system_toggle              │ → Enable/disable
        ├─────────────────────────────┤
        │ /system_set_<option> <val>  │ → Change setting
        └─────────────────────────────┘

═════════════════════════════════════════════════════════════════════════════════════════════════════
```

## Command Tree

```
WATCH SYSTEMS (37 TOTAL COMMANDS)
│
├── NIGHTWATCH (7 commands)
│   ├── /nightwatch_status
│   ├── /nightwatch_config
│   ├── /nightwatch_set_hours <start> <end>
│   ├── /nightwatch_toggle
│   ├── /nightwatch_set_threshold <num>
│   ├── /nightwatch_auto_escalate
│   └── /nightwatch_dm_alerts
│
├── DAYWATCH (8 commands)
│   ├── /daywatch_status
│   ├── /daywatch_config
│   ├── /daywatch_set_hours <start> <end>
│   ├── /daywatch_toggle
│   ├── /daywatch_toggle_engagement
│   ├── /daywatch_toggle_peak
│   ├── /daywatch_log_activity
│   └── /daywatch_stats
│
├── USERWATCH (9 commands)
│   ├── /userwatch_add <user>
│   ├── /userwatch_remove <user>
│   ├── /userwatch_list
│   ├── /userwatch_view <user>
│   ├── /userwatch_config
│   ├── /userwatch_toggle
│   ├── /userwatch_clear_events <user>
│   └── [2 more internal commands]
│
├── CHANNELWATCH (7 commands)
│   ├── /channelwatch_add <channel>
│   ├── /channelwatch_remove <channel>
│   ├── /channelwatch_list
│   ├── /channelwatch_view <channel>
│   ├── /channelwatch_config
│   ├── /channelwatch_toggle
│   └── /channelwatch_reset <channel>
│
└── THREATWATCH (6 commands)
    ├── /threatwatch_status
    ├── /threatwatch_list [limit]
    ├── /threatwatch_actors
    ├── /threatwatch_config
    ├── /threatwatch_toggle
    └── /threatwatch_clear
```

## Data Flow Diagram

```
Discord Events
│
├─→ Member Join      ──→ Userwatch (track join)
├─→ Message Posted   ──→ Userwatch (track msg) ──→ Channelwatch (count msg)
├─→ Role Change      ──→ Userwatch (track role)
├─→ Member Removed   ──→ Threatwatch (detect threat) ──→ Signal Bus
└─→ Time Update      ──→ Nightwatch (activate/deactivate)
                      ──→ Daywatch (activate/deactivate)

        ↓
        
    JSON Data Files
    ├── userwatch_system.json
    ├── channelwatch_system.json
    ├── threatwatch_system.json
    ├── nightwatch_system.json
    └── daywatch_system.json
```

## Configuration Hierarchy

```
ALL WATCH SYSTEMS
│
├── ENABLED (boolean)
│   ├── true   → System active and monitoring
│   └── false  → System disabled
│
├── TIME CONFIG (where applicable)
│   ├── start_hour (0-23)
│   └── end_hour (0-23)
│
├── ALERT CONFIG (where applicable)
│   ├── alert_threshold
│   ├── alert_on_pattern
│   └── alert_on_volume
│
├── FEATURE TOGGLES
│   ├── track_messages
│   ├── track_activity
│   ├── auto_escalate
│   └── dm_alerts
│
└── LOGGING
    └── log_all_activity (boolean)
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCORD.PY EVENTS                        │
├─────────────────────────────────────────────────────────────┤
│  on_message()          → Userwatch, Channelwatch            │
│  on_member_join()      → Userwatch                          │
│  on_member_update()    → Userwatch (role changes)           │
│  on_member_remove()    → Threatwatch                        │
│  on_ready()            → Nightwatch, Daywatch              │
└─────────────────────────────────────────────────────────────┘
                              ↓
                        ┌────────────┐
                        │ WATCH COGS │
                        └────────────┘
                              ↓
         ┌────────────────────┼────────────────────┐
         ↓                    ↓                    ↓
    ┌─────────┐          ┌──────────┐       ┌──────────────┐
    │ Commands │          │ Listeners │       │ Signal Bus   │
    ├─────────┤          ├──────────┤       ├──────────────┤
    │/config  │          │Monitor   │       │Emit signals  │
    │/toggle  │          │Tasks     │       │(Threatwatch) │
    │/view    │          │Events    │       │Integration   │
    └─────────┘          └──────────┘       └──────────────┘
         ↓                    ↓                    ↓
    ┌──────────────────────────────────────────────────┐
    │         JSON DATA PERSISTENCE LAYER              │
    └──────────────────────────────────────────────────┘
```

## Deployment Status

```
Phase 5: Watch Systems Expansion
│
├── Development ✅
│   ├── Userwatch
│   ├── Channelwatch
│   └── Threatwatch
│
├── Integration ✅
│   ├── Added to bot.py cog loader
│   └── Registered in essential_cogs
│
├── Testing ✅
│   ├── Syntax validation (all pass)
│   ├── Data structure verification
│   └── Configuration command testing
│
├── Documentation ✅
│   ├── Technical guide (WATCH_SYSTEMS_EXPANSION.md)
│   ├── Quick reference (WATCH_SYSTEMS_QUICK_REFERENCE.md)
│   └── Session summary (this document)
│
└── Ready for Deployment ✅
    └── All systems ready for bot startup
```

---

**Created**: February 3, 2025  
**Status**: Production Ready ✅  
**Total Systems**: 5 Watch Systems  
**Total Commands**: 37  
**Documentation**: Complete
