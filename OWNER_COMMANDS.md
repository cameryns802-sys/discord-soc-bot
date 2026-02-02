# 👑 Owner Commands Reference

## Overview
Owner-only administrative commands for bot management, maintenance, and control.

---

## 🛑 Shutdown & Restart Commands

### **!shutdown** (Aliases: !stop, !halt)
Gracefully shutdown the bot

**What it does:**
- ✅ Saves all data via DataManager
- ✅ Notifies all guilds about shutdown
- ✅ Deactivates active drill/threat status
- ✅ Closes bot connection
- ✅ Sends confirmation to owner

**Usage:**
```bash
!shutdown
!stop
!halt
```

**Example:**
```
User: !shutdown
Bot: 🛑 Bot Shutdown Initiated
     Initiated By: @Owner
     Status: 🔴 Shutting down...
     Data: ✅ Being saved

[All guilds notified]
[Bot goes offline]
```

---

### **!restart** (Aliases: !reboot)
Restart the bot process

**What it does:**
- ✅ Saves all data via DataManager
- ✅ Notifies all guilds about restart
- ✅ Deactivates active drill/threat status
- ✅ Attempts to restart bot process
- ✅ Expected downtime: 5-10 seconds

**Usage:**
```bash
!restart
!reboot
```

**Requirements:**
- Bot must be run with auto-restart script, systemd, or process manager
- Without auto-restart: Works like `!shutdown`

**Example:**
```
User: !restart
Bot: 🔄 Bot Restart Initiated
     Initiated By: @Owner
     Status: 🔄 Restarting...
     Expected Downtime: ~5-10 seconds

[All guilds notified]
[Bot restarts automatically]
```

---

### **!emergency_stop** (Aliases: !estop, !panic_shutdown)
Emergency shutdown without notifications

**What it does:**
- ✅ Saves critical data immediately
- ❌ Skips guild notifications
- ❌ Skips status cleanup
- 🚨 Forces immediate shutdown

**Usage:**
```bash
!emergency_stop
!estop
!panic_shutdown
```

**When to use:**
- Normal shutdown is failing
- Bot is malfunctioning
- Immediate stop required
- Emergency situations only

**Example:**
```
User: !emergency_stop
Bot: 🚨 EMERGENCY STOP INITIATED - Immediate shutdown...

[Bot immediately goes offline]
```

---

## 📦 Cog Management Commands

### **!reload_cog <cog_name>** (Aliases: !reload)
Reload a specific cog without restarting

**What it does:**
- ✅ Unloads the cog
- ✅ Reloads the cog
- ✅ Applies code changes
- ✅ No downtime for other cogs

**Usage:**
```bash
!reload_cog <cog_name>
!reload <cog_name>
```

**Examples:**
```bash
!reload_cog core.dynamic_status
!reload security.antinuke
!reload moderation.automod
!reload soc.security_drill_system
```

**Format:** Use folder path notation: `folder.filename` (without .py)

---

### **!load_cog <cog_name>** (Aliases: !load)
Load a cog that is not currently loaded

**What it does:**
- ✅ Loads the specified cog
- ✅ Registers commands
- ✅ Enables functionality

**Usage:**
```bash
!load_cog <cog_name>
!load <cog_name>
```

**Examples:**
```bash
!load_cog experimental.explainable_ai
!load_cog archives.bot_personality_system
!load_cog archives.quantum_safe_crypto
```

**Use cases:**
- Load archived/experimental cogs
- Enable disabled systems
- Hot-add new functionality

---

### **!unload_cog <cog_name>** (Aliases: !unload)
Unload a cog without restarting

**What it does:**
- ✅ Unloads the specified cog
- ✅ Disables commands
- ✅ Frees resources

**Usage:**
```bash
!unload_cog <cog_name>
!unload <cog_name>
```

**Examples:**
```bash
!unload_cog experimental.predictive_error_system
!unload_cog security.security_drill
```

**Note:** Cannot unload `owner_commands` cog

---

### **!list_cogs** (Aliases: !cogs)
List all loaded cogs

**What it does:**
- ✅ Shows all loaded cog names
- ✅ Shows total cog count
- ✅ Shows total command count

**Usage:**
```bash
!list_cogs
!cogs
```

**Output:**
```
📦 Loaded Cogs
Total: 112 cogs loaded

Cogs 1-20:
• DynamicStatus
• FeatureFlagsCog
• SignalBusCog
• AbstentionCog
...

Total Commands: 285
```

---

## 📊 Bot Statistics & Info

### **!bot_stats** (Aliases: !stats)
Show detailed bot statistics

**What it does:**
- ✅ Shows bot uptime
- ✅ Shows latency
- ✅ Shows guild/user count
- ✅ Shows command/cog count
- ✅ Shows system resources (CPU, RAM)
- ✅ Shows Python/Discord.py version

**Usage:**
```bash
!bot_stats
!stats
```

**Output:**
```
📊 Bot Statistics

🤖 Bot: Sentinel SOC Bot
⏱️ Uptime: 5:23:45
📡 Latency: 45ms

🏛️ Guilds: 12
👥 Users: 3,456
📝 Text Channels: 234

⚡ Slash Commands: 25
📦 Cogs: 112
💻 Prefix Commands: 285

🧠 Memory: 256.34 MB
💾 CPU: 2.3%
🐍 Python: 3.11.5

📚 Discord.py: 2.3.2
🖥️ System: Windows
⚙️ Architecture: AMD64
```

---

## ⚡ Command Sync

### **!sync_commands [guild_id]** (Aliases: !sync)
Sync slash commands to Discord

**What it does:**
- ✅ Syncs slash commands to Discord API
- ✅ Updates command definitions
- ✅ Makes new commands available

**Usage:**
```bash
!sync_commands              # Global sync (takes up to 1 hour)
!sync [guild_id]            # Guild-specific sync (instant)
```

**Examples:**
```bash
!sync                       # Sync globally to all guilds
!sync 1234567890            # Sync to specific guild (instant)
```

**Global vs Guild:**
- **Global:** Takes up to 1 hour to propagate, affects all guilds
- **Guild:** Instant, affects only specified guild

**When to use:**
- After adding new slash commands
- After modifying slash command definitions
- When commands don't appear in Discord

---

## 🎯 Command Summary

| Command | Purpose | Aliases |
|---------|---------|---------|
| `!shutdown` | Graceful shutdown | !stop, !halt |
| `!restart` | Restart bot | !reboot |
| `!emergency_stop` | Emergency shutdown | !estop, !panic_shutdown |
| `!reload_cog <name>` | Reload cog | !reload |
| `!load_cog <name>` | Load cog | !load |
| `!unload_cog <name>` | Unload cog | !unload |
| `!list_cogs` | List all cogs | !cogs |
| `!bot_stats` | Show statistics | !stats |
| `!sync_commands [id]` | Sync slash commands | !sync |

---

## 🔐 Security

### Access Control
- ✅ All commands require `BOT_OWNER_ID` match
- ✅ Commands fail silently for non-owners
- ✅ Owner ID from `.env` file

### Owner Check
```python
async def cog_check(self, ctx):
    return ctx.author.id == self.owner_id
```

### Setting Owner ID
In `.env` file:
```env
BOT_OWNER_ID=123456789012345678
```

---

## 💡 Usage Examples

### Scenario 1: Restart after code changes
```bash
# 1. Make code changes to file
# 2. Reload the specific cog
!reload_cog soc.security_drill_system

# Or restart entirely
!restart
```

### Scenario 2: Enable experimental feature
```bash
# Load experimental cog
!load_cog experimental.explainable_ai

# Test the feature
!explainable_action <action>

# If it doesn't work, unload it
!unload_cog experimental.explainable_ai
```

### Scenario 3: Emergency shutdown
```bash
# Normal shutdown
!shutdown

# If bot is frozen/unresponsive
!emergency_stop
```

### Scenario 4: Check bot health
```bash
# View detailed stats
!bot_stats

# View loaded cogs
!list_cogs

# Check specific cog status
!reload_cog core.dynamic_status
```

### Scenario 5: Deploy new slash commands
```bash
# After adding new slash commands to code
!sync                        # Global (1 hour)

# Or for testing in specific guild
!sync 1234567890            # Instant for that guild
```

---

## 🚨 Important Notes

### Restart Requirements
- **Auto-restart:** Bot must be run with systemd, supervisor, or restart script
- **Without auto-restart:** `!restart` works like `!shutdown`
- **Windows:** Use Task Scheduler with restart on failure
- **Linux:** Use systemd service with `Restart=always`

### Data Safety
- All shutdown/restart commands save data via DataManager
- Emergency stop saves critical data only
- Always use graceful shutdown when possible

### Status Cleanup
- Shutdown/restart deactivates active drill status
- Shutdown/restart deactivates active threat status
- Status returns to normal on bot startup

### Notifications
- Normal shutdown: Notifies all guilds
- Restart: Notifies all guilds
- Emergency stop: No notifications (immediate)

---

## 🔧 Troubleshooting

### Command not working
```bash
# Check if you're the owner
!bot_stats

# Verify owner ID matches
# Check .env: BOT_OWNER_ID=<your_discord_id>
```

### Cog reload failing
```bash
# Check cog name format
!list_cogs                  # See exact cog names

# Try unload + load instead
!unload_cog cog.name
!load_cog cog.name
```

### Restart not working
- Check if bot is run with auto-restart
- Use `!shutdown` instead and manually restart
- Set up systemd/supervisor for automatic restarts

### Emergency stop not responding
- Bot may be completely frozen
- Kill process manually: `Ctrl+C` or `kill <pid>`
- Check logs for errors

---

## 📋 Maintenance Workflow

### Daily Operations
1. Check bot health: `!bot_stats`
2. Monitor loaded cogs: `!list_cogs`
3. Review logs for errors

### Code Deployment
1. Edit code files
2. Reload affected cogs: `!reload_cog <name>`
3. Test functionality
4. If major changes: `!restart`

### Scheduled Maintenance
1. Announce maintenance in all guilds manually or use `!maintenance_on`
2. Use `!restart` for bot restart
3. Verify startup: `!bot_stats`
4. Announce completion: `!maintenance_off`

### Emergency Response
1. Identify issue
2. If critical: `!emergency_stop`
3. Fix issue in code
4. Restart bot manually
5. Verify: `!bot_stats`

---

**All commands are owner-only!** 👑  
Owner ID must be set in `.env` as `BOT_OWNER_ID=<your_discord_id>`
