# Copilot Instructions for AI Coding Agents

## Project Overview
Advanced Discord SOC (Security Operations Center) bot with 100+ security modules for threat detection, incident response automation, compliance monitoring, and security analytics. The bot provides Discord slash commands and traditional prefix commands. Architecture is modular with security-focused cogs organized by domain (security, moderation, compliance, SOC systems, threat intelligence).

## Core Architecture

### Design Philosophy: Signals, Policies, Confidence, Human-In-Loop, Resilience
- Think in **signals**, not individual features
- All security events flow through **central signal bus** for deduplication, correlation, and human review
- AI systems have **confidence scoring** (0.0-1.0); low confidence triggers escalation
- **Human oversight always required** for critical decisions (tracked in `human_override_tracker`)
- **Feature flags** enable runtime kill-switch for experimental features
- **Graceful degradation** under stress via safe mode

### Entry Point: [bot.py](../bot.py)
- `CustomBot` class with dynamic command prefix: `!` for owner (via `BOT_OWNER_ID`), mentions for others
- Whitelist-based cog loader in `load_cogs()`: Only 100+ essential cogs auto-load
- Cogs loaded recursively from `./cogs/` directories
- Env vars required: `DISCORD_TOKEN`, `BOT_OWNER_ID`, optional `AUDIT_CHANNEL_ID`
- UTF-8 encoding forced for Windows compatibility
- Uptime tracking and startup/shutdown DMs to owner

## Central Signal Pipeline (Critical Concept)

### Signal Bus Architecture: [cogs/core/signal_bus.py](../cogs/core/signal_bus.py)
**ALL security events flow through here** - this is the canonical event pipeline:

```python
# Standard signal structure across entire system
Signal(
    signal_type=SignalType.THREAT_DETECTED,     # Enum: threat, anomaly, policy_violation, etc.
    severity="high",                             # critical, high, medium, low, info
    source="antinuke",                           # Which cog/service emitted
    data={"reason": "channel_deleted"},          # Payload specific to signal type
    confidence=0.95,                             # 0.0-1.0 confidence in signal accuracy
    dedup_key="antinuke:channel_deleted"         # For deduplication/correlation
)
```

**SignalType enum** (in [cogs/core/signal_bus.py](../cogs/core/signal_bus.py)): `THREAT_DETECTED`, `ANOMALY_DETECTED`, `POLICY_VIOLATION`, `COMPLIANCE_ISSUE`, `PII_EXPOSURE`, `UNAUTHORIZED_ACCESS`, `USER_ESCALATION`, `HUMAN_OVERRIDE`, etc.

**Usage pattern in all security cogs**:
```python
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class MyCog(commands.Cog):
    async def detect_threat(self):
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity="high",
            source="mycog",
            data={"reason": "..."},
            confidence=0.85
        ))
```

**Critical**: Every security event must emit a signal - do NOT use raw logging for security events.

### Human Oversight & AI Confidence
- **[human_override_tracker.py](../cogs/core/human_override_tracker.py)**: Tracks all AI decisions and human overrides; reveals bias patterns
- **[abstention_policy.py](../cogs/core/abstention_policy.py)**: AI can abstain if confidence is low; escalation logic
- **[prompt_injection_detector.py](../cogs/core/prompt_injection_detector.py)**: Prevents adversarial attacks on AI

## Cog Structure & Directory Organization

### Directory Layout
```
cogs/
├── core/               # Infrastructure: signal_bus, feature_flags, data management
├── security/          # Threat detection: antinuke, anti-phishing, anti-raid, etc.
├── moderation/        # Moderation: automod, toxicity, verification
├── soc/               # SOC systems: dashboards, incident management, threat hunting
├── threatintel/       # Threat intelligence: IOC manager, threat feeds
├── compliance/        # Compliance: GDPR, data retention, policy monitoring
├── logging/           # Event logging: audit trails, forensics
├── incidents/         # Incident response: automated playbooks, escalation
├── integrations/      # External: Slack, Teams, external APIs
├── utility/           # Misc: DM handler, welcome system, settings manager
└── archives/          # Deprecated systems (low ROI)
```

### Cog Pattern (Enforced Convention)
Every cog file MUST follow this pattern:

```python
import discord
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize cog state

    @commands.command()
    async def my_command(self, ctx):
        await ctx.send("response")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Hook Discord events"""
        if message.author.bot:
            return
        # Process message

async def setup(bot):
    """Required by discord.py loader - do NOT rename"""
    await bot.add_cog(MyCog(bot))
```

**Critical**: Every cog file must have `async def setup(bot)` at module level or discord.py loader will fail.

### Command Patterns
1. **Slash commands** (preferred, modern): `@bot.tree.command()` - respond via `interaction.response.send_message()`
2. **Prefix commands** (in cogs): `@commands.command()` - respond via `ctx.send()`

### Data Persistence: [cogs/data_manager.py](../cogs/data_manager.py)
Central JSON-based storage (NOT a cog, loaded early):
- Stores: warns, reputation, levels, guild/user settings, consent, etc.
- Auto-saves every 5 minutes
- Access via `bot.get_cog('DataManager').data`
- Pattern: Load data on cog init, save during `cog_unload()`

## Security Cogs & Their Patterns

### Threat Emission Pattern
All security cogs should emit signals to signal bus:

```python
# Pattern used in antinuke.py, anti_phishing.py, etc.
from cogs.core.signal_bus import signal_bus, Signal, SignalType

async def emit_threat_signal(self, reason: str, severity: str = "high"):
    await signal_bus.emit(Signal(
        signal_type=SignalType.THREAT_DETECTED,
        severity=severity,
        source=self.__class__.__name__,
        data={'reason': reason},
        confidence=0.95,
        dedup_key=f'{self.__class__.__name__}:{reason}'
    ))
```

### Event Listeners
Security cogs hook Discord events via `@commands.Cog.listener()`:

```python
@commands.Cog.listener()
async def on_member_join(self, member):
    """Verify members on join"""
    await self.verify_member(member)

@commands.Cog.listener()
async def on_guild_channel_delete(self, channel):
    """Detect mass channel deletion"""
    await self.emit_threat_signal(f"channel_deleted: {channel.name}", "high")
```

### Permission Checks
Always validate permissions:

```python
@commands.command()
@commands.has_permissions(manage_messages=True)
async def my_admin_command(self, ctx):
    await ctx.send("Admin action executed")

@commands.command()
@commands.is_owner()
async def owner_command(self, ctx):
    await ctx.send("Owner-only action")
```

## Key Cogs by Category

### Core Infrastructure (always loaded)
- **signal_bus**: Central event pipeline
- **feature_flags**: Runtime feature toggles & kill switches
- **human_override_tracker**: Track AI decisions & interventions
- **abstention_policy**: AI confidence & escalation
- **data_manager**: Persistent JSON storage
- **dynamic_status**: Bot status reflects threat level
- **automated_playbook_executor**: SOAR playbook automation
- **on_call_manager**: On-call and escalation management

### Security Systems
- **[antinuke.py](../cogs/security/antinuke.py)**: Detect/prevent channel/role mass deletions
- **[anti_phishing.py](../cogs/security/anti_phishing.py)**: Phishing URL detection
- **[anti_spam_system.py](../cogs/security/anti_spam_system.py)**: Spam detection
- **[anti_raid_system.py](../cogs/security/anti_raid_system.py)**: Raid detection
- **[permission_audit.py](../cogs/security/permission_audit.py)**: Track permission changes
- **[webhook_abuse_prevention.py](../cogs/security/webhook_abuse_prevention.py)**: Webhook security
- **[intelligent_threat_response.py](../cogs/security/intelligent_threat_response.py)**: Automated response

### Moderation Systems
- **[automod.py](../cogs/moderation/automod.py)**: Syncs with Discord native automod; tracks violations
- **[toxicity_detection.py](../cogs/moderation/toxicity_detection.py)**: Content toxicity scanning
- **[verification_system.py](../cogs/moderation/verification_system.py)**: Role assignment on verify
- **[moderation_utilities.py](../cogs/moderation/moderation_utilities.py)**: Core mod commands (kick, ban, warn)

### SOC Systems (Monitoring & Dashboards)
- **[security_dashboard.py](../cogs/soc/security_dashboard.py)**: Real-time security metrics
- **[executive_risk_dashboard.py](../cogs/soc/executive_risk_dashboard.py)**: C-level threat reporting
- **[audit_log_analyzer.py](../cogs/soc/audit_log_analyzer.py)**: Auto-analyze logs for threats
- **[incident_forecasting.py](../cogs/soc/incident_forecasting.py)**: Predict upcoming incidents

### Threat Intelligence
- **[threat_intel_hub.py](../cogs/core/threat_intel_hub.py)**: IOC aggregation & threat feeds
- **[ioc_manager.py](../cogs/core/ioc_manager.py)**: IOC lifecycle management

## Running & Testing

### Launch Bot
```powershell
# Windows PowerShell
python bot.py
```

**Environment setup**:
```bash
# .env file (git ignored)
DISCORD_TOKEN=your_token_here
BOT_OWNER_ID=your_discord_id
AUDIT_CHANNEL_ID=optional_audit_channel_id
```

### Testing Commands
1. Slash commands: `/ping`, `/userinfo @user`, `/warn @user reason`
2. Owner commands: `!ai_rl_defender` (requires `!` prefix + owner ID)
3. Check audit logs: `AUDIT_CHANNEL_ID` channel or owner DMs

### Debugging
- Console output shows `[Loader]` prefix for cog load status
- Startup/shutdown DMs confirm connection state
- Use `logging.getLogger('soc_bot')` for debugging
- Cog failures include error traceback in console

## Key Conventions

- **Async-first**: All operations async, no blocking I/O
- **Embeds**: Use `discord.Embed()` for formatted responses
- **Lazy imports**: Import AI modules inside methods to avoid startup bloat
- **Signal bus**: Emit signals for all security events (not raw logging)
- **Error handling**: Use `@bot.event async def on_command_error(ctx, error)`
- **Owner-only**: Use `@commands.is_owner()` decorator or check `ctx.author.id == OWNER_ID`

## Adding New Cogs

1. Create file in `cogs/{category}/{name}.py`
2. Implement `MyNewCog(commands.Cog)` class
3. Add `async def setup(bot)` at module level
4. Add cog name to `essential_cogs` whitelist in [bot.py](../bot.py#L97)
5. Emit signals to signal bus for security events
6. Cog auto-loads on next bot restart

Example new security cog:
```python
# cogs/security/my_new_detector.py
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class MyDetectorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if is_threat(message):
            await signal_bus.emit(Signal(
                signal_type=SignalType.THREAT_DETECTED,
                severity="high",
                source="my_detector",
                data={"message_id": message.id},
                confidence=0.9
            ))

async def setup(bot):
    await bot.add_cog(MyDetectorCog(bot))
```

Then add `'my_detector'` to `essential_cogs` in `bot.py`.

## File Organization
```
bot.py                      # Entry point, cog loader
requirements.txt            # discord.py, python-dotenv, aiohttp, pydantic, psutil
.env                        # DISCORD_TOKEN, BOT_OWNER_ID, AUDIT_CHANNEL_ID
cogs/                       # All bot extensions (auto-loaded)
  core/                     # Infrastructure & signal bus
  security/                 # Threat detection systems
  moderation/               # Moderation systems
  soc/                      # SOC dashboards & monitoring
  threatintel/              # Threat intelligence
  compliance/               # Compliance & governance
AI/                         # AI algorithm modules (lazy-loaded)
```

## Integration Points
- **Discord.py library**: All interactions via `discord.Interaction` or `discord.Context`
- **Async runtime**: `asyncio.run(main())` in bot.py
- **Environment variables**: `.env` via `python-dotenv`
- **External APIs**: Slack, Teams, threat feeds (in `cogs/integrations/`)
- **FastAPI backend**: `/api/main.py` serves optional SOC dashboard data
