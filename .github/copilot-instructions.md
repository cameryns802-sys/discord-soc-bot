# Copilot Instructions for AI Coding Agents

## Project Overview
Advanced Discord SOC (Security Operations Center) bot with 40+ specialized security AI modules. The bot provides threat detection, incident response automation, compliance monitoring, and security analytics through Discord slash commands and traditional commands. Architecture is modular with security-focused cogs organized by domain.

## Architecture & Key Components

### Core Entry Point
- **[bot.py](../bot.py)**: Main bot initialization, slash command definitions, and cog loader. Uses `CustomBot` with dynamic command prefix (owner uses `!`, others use mentions). Cogs are auto-loaded from `./cogs/` recursively via `load_cogs()` async function.

### Cog Structure (Module Pattern)
Cogs are Discord.py extensions organized by domain:
- **[cogs/](../cogs/)**: All cogs auto-loaded at startup
  - **meta_systems.py**: 40+ AI commands (RL defender, threat clustering, pattern analysis)
  - **ai/**: AI-specific modules (moderation, image scanning, FAQ)
  - **security/**, **defense/**, **threat_intel/**: Security-domain cogs
  - **compliance/**, **governance/**, **ethics/**: Compliance & policy cogs
  - **owner.py**: Admin commands, audit logging, permission checks (requires `BOT_OWNER_ID`)

### AI Module System
- **AI/**: 40+ specialized modules implementing threat detection and response algorithms
  - Each module is a simple class (e.g., `ReinforcementLearningDefender`) with async methods
  - Imported on-demand within cog methods to avoid startup overhead
  - Examples: `ai_rl_defender`, `suspicious_pattern_clusterer`, `multi_agent_defense_coordination`

### Config & Secrets
- **Bot tokens**: `DISCORD_TOKEN` in `.env` (required)
- **Owner permissions**: `BOT_OWNER_ID` in `.env` (required for admin commands)
- **Optional audit logging**: `AUDIT_CHANNEL_ID` for audit log destination
- Use `.env` (gitignore'd) for all secrets

## Development Patterns

### Command Pattern
Two command styles in use:
1. **Slash commands**: `@bot.tree.command()` (preferred, modern)
   - Example: `@bot.tree.command(name="ping", description="Show bot latency.")`
   - Respond via `interaction.response.send_message()`
2. **Prefix commands**: `@commands.command()` (in cogs)
   - Used in cogs via `@commands.Cog` inheritance
   - Respond via `ctx.send()`

### Cog Pattern (Enforced)
```python
# Each cog file (e.g., cogs/security/threat_detection.py)
import discord
from discord.ext import commands

class ThreatDetectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def detect_threat(self, ctx):
        # Command logic
        await ctx.send("Threat detected")

async def setup(bot):
    await bot.add_cog(ThreatDetectionCog(bot))
```
- All cogs must have a `setup(bot)` async function for discord.py loader
- Cog classes inherit from `commands.Cog`

### AI Module Usage Pattern
AI modules are instantiated inside cog methods (lazy-loaded):
```python
@commands.command()
async def ai_rl_defender(self, ctx):
    from AI.reinforcement_learning_defender import ReinforcementLearningDefender
    ai = ReinforcementLearningDefender(self.bot)
    result = await ai.learn()
    await ctx.send(f"[AI] RL Defender: {result}")
```

### Error Handling
- Global error handler: `@bot.event async def on_command_error(ctx, error)`
- Validate permissions before executing moderation commands
- Example: `if not interaction.channel.permissions_for(interaction.user).manage_messages: return`

## Running & Testing

### Launch Bot
```powershell
# Windows
python bot.py
```
Requires `.env` with `DISCORD_TOKEN` and `BOT_OWNER_ID`.

### Testing Commands in Discord
1. Set bot to online (bot.py running)
2. Use slash commands: `/ping`, `/userinfo @user`, `/warn @user reason`, etc.
3. Owner commands: `!ai_rl_defender`, `!ai_cluster`, etc. (requires `BOT_OWNER_ID` and `!` prefix)
4. Check audit logs: `AUDIT_CHANNEL_ID` channel or owner DM

## Key Conventions

- **Async-first**: All Discord operations and AI module methods are async
- **Embeds for output**: Use `discord.Embed()` for rich command responses (seen throughout)
- **Lazy imports**: Import AI modules inside cog methods to avoid startup bloat
- **Owner-only commands**: Leverage `is_owner()` check or `commands.is_owner()` decorator
- **Audit trail**: Use `OwnerCog.audit_log()` to log admin actions

## File Organization
```
bot.py                      # Entry point, slash commands, cog loader
requirements.txt            # discord.py, python-dotenv, aiohttp, pydantic
.env                        # DISCORD_TOKEN, BOT_OWNER_ID, AUDIT_CHANNEL_ID
cogs/                       # All bot extensions (auto-loaded)
  owner.py                  # Admin & audit commands
  meta_systems.py           # 40+ AI command wrappers
  ai/, security/, etc.      # Domain-specific cogs
AI/                         # 40+ AI algorithm modules
```

## Integration Points
- **Discord.py library**: All Discord interactions via `discord.Interaction` or `discord.Message` context
- **Async runtime**: `asyncio.run(main())` in bot.py; all I/O operations async
- **Environment variables**: `.env` via `python-dotenv` for `DISCORD_TOKEN`, `BOT_OWNER_ID`, `AUDIT_CHANNEL_ID`
