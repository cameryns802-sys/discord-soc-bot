# Advanced Cog Development Standards & Requirements

**Purpose**: Define comprehensive standards for all new bot system implementations to ensure production-grade quality, advanced features, and substantial code depth.

---

## 1. Core Code Requirements

### Minimum Code Length
- **Small cogs**: 200+ lines minimum
- **Medium cogs**: 350+ lines minimum  
- **Large cogs**: 600+ lines minimum
- **Complex systems**: 800+ lines minimum

### Advanced Feature Requirements
Every cog must include ALL of the following:

✅ **Full Type Hints**
- Every function parameter must have type hint
- Every return value must have return type hint
- Complex types: `Dict[str, List[int]]`, `Optional[discord.Member]`, etc.
- Use `from typing import Dict, List, Optional, Tuple, Callable, Union`

```python
async def process_threat(self, signal: Signal, severity: str, confidence: float) -> Dict[str, Any]:
    """Process threat with advanced parameters."""
```

✅ **Comprehensive Docstrings**
- Module-level docstring (5-10 lines explaining cog purpose)
- Class-level docstring (3-5 lines)
- Every method docstring with:
  - Brief description
  - Args with types and explanations
  - Returns description
  - Raises documentation for errors
  - Examples where complex

```python
def calculate_risk_score(self, threat_level: str, history_count: int) -> float:
    """
    Calculate dynamic risk score based on threat level and history.
    
    Args:
        threat_level: Severity ('critical', 'high', 'medium', 'low', 'info')
        history_count: Number of similar incidents in past 30 days
        
    Returns:
        Risk score from 0.0 (lowest) to 1.0 (highest)
        
    Raises:
        ValueError: If threat_level not in valid options
        
    Examples:
        >>> cog.calculate_risk_score('critical', 5)
        0.95
        >>> cog.calculate_risk_score('low', 0)
        0.1
    """
```

✅ **Error Handling**
- Try/except blocks around Discord API calls
- Graceful degradation if optional features fail
- Logging of errors for debugging
- Don't silently fail

```python
try:
    await channel.send(embed=embed)
except discord.Forbidden as e:
    logger.error(f"[{self.__class__.__name__}] Cannot send to {channel.id}: {e}")
    # Graceful fallback
except discord.HTTPException as e:
    logger.error(f"[{self.__class__.__name__}] HTTP error: {e}")
```

✅ **Logging**
- Logger instance: `logger = logging.getLogger('soc_bot')`
- Log significant events (cog load, major operations, errors)
- Use consistent format: `[CogName] message`
- Include context (user, guild, etc.)

```python
class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('soc_bot')
        self.logger.info(f"[AdvancedSystem] Cog initialized")
```

---

## 2. Signal Bus Integration (CRITICAL)

✅ **Signal Subscription**
Every cog should subscribe to or emit signals:

```python
from cogs.core.signal_bus import signal_bus, Signal, SignalType

class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Subscribe to all signals OR specific types
        signal_bus.subscribe('*', self.on_signal)  # All signals
        # OR
        signal_bus.subscribe(SignalType.THREAT_DETECTED, self.on_threat)
    
    async def on_signal(self, signal: Signal) -> None:
        """Handle signal bus events."""
        self.logger.info(f"[Advanced] Received signal: {signal.type}")
        # Process signal
    
    async def on_threat(self, signal: Signal) -> None:
        """Handle threat-specific signals."""
        await self.process_threat(signal)
```

✅ **Signal Emission**
Emit signals for security events (not direct logging):

```python
async def detect_anomaly(self, data: Dict[str, Any]) -> None:
    """Detect and emit anomaly signal."""
    signal = Signal(
        signal_type=SignalType.ANOMALY_DETECTED,
        severity='high',
        source=self.__class__.__name__,
        data={
            'anomaly_type': 'unusual_access_pattern',
            'affected_users': len(data['users']),
            'confidence': 0.87,
            'details': data
        },
        timestamp=datetime.utcnow().isoformat()
    )
    await signal_bus.emit(signal)
```

---

## 3. Background Tasks (Required)

✅ **Implement Background Tasks**
Every non-trivial cog needs automated operations:

```python
from discord.ext import tasks

class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.background_worker.start()
    
    @tasks.loop(hours=1)
    async def background_worker(self) -> None:
        """Hourly background operation."""
        try:
            self.logger.info(f"[Advanced] Running background worker")
            await self._process_queue()
            await self._generate_metrics()
            await self._cleanup_old_data()
        except Exception as e:
            self.logger.error(f"[Advanced] Background task failed: {e}")
    
    @background_worker.before_loop
    async def before_background_worker(self) -> None:
        """Wait until bot is ready."""
        await self.bot.wait_until_ready()
    
    def cog_unload(self) -> None:
        """Stop background tasks on unload."""
        self.background_worker.cancel()
```

---

## 4. Data Persistence (REQUIRED)

✅ **JSON Storage**
Persistent data for all stateful operations:

```python
class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/advanced_system.json'
        self.load_data()
    
    def load_data(self) -> None:
        """Load data from disk."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self.logger.info(f"[Advanced] Loaded data from {self.data_file}")
            except Exception as e:
                self.logger.error(f"[Advanced] Failed to load data: {e}")
                self.data = self._default_data()
        else:
            self.data = self._default_data()
    
    def save_data(self) -> None:
        """Save data to disk."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"[Advanced] Data saved to {self.data_file}")
        except Exception as e:
            self.logger.error(f"[Advanced] Failed to save data: {e}")
    
    def _default_data(self) -> Dict[str, Any]:
        """Return default data structure."""
        return {
            'config': {},
            'metrics': {},
            'events': [],
            'version': '1.0'
        }
    
    def cog_unload(self) -> None:
        """Save data on unload."""
        self.save_data()
```

---

## 5. Slash Commands + Prefix Commands (BOTH REQUIRED)

✅ **Support Both Command Styles**
Modern (slash) AND traditional (prefix):

```python
@commands.command(name='analysis')
@commands.has_permissions(manage_guild=True)
async def analysis_prefix(self, ctx: commands.Context, option: str = 'default') -> None:
    """Prefix command version."""
    await self._analysis_logic(ctx, option)

@app_commands.command(name='analysis', description='Advanced system analysis')
@app_commands.describe(option='Analysis option: default, detailed, verbose')
@app_commands.checks.has_permissions(manage_guild=True)
async def analysis_slash(self, interaction: discord.Interaction, option: str = 'default') -> None:
    """Slash command version."""
    await interaction.response.defer()
    
    class FakeCtx:
        def __init__(self, interaction):
            self.channel = interaction.channel
            self.author = interaction.user
            self.guild = interaction.guild
        
        async def send(self, **kwargs):
            if isinstance(kwargs.get('embed'), discord.Embed):
                return await interaction.followup.send(embed=kwargs['embed'])
            return await interaction.followup.send(content=kwargs.get('content', ''))
    
    ctx = FakeCtx(interaction)
    await self._analysis_logic(ctx, option)

async def _analysis_logic(self, ctx: commands.Context, option: str) -> None:
    """Shared logic for both command types."""
    # Implementation here
```

---

## 6. Rich Discord Embeds (REQUIRED)

✅ **Professional Embed Design**
Every user-facing output must be a formatted embed:

```python
embed = discord.Embed(
    title="🛡️ Advanced System Status",
    description="Comprehensive operational metrics and system health",
    color=discord.Color.blue(),
    timestamp=datetime.utcnow()
)

embed.add_field(
    name="📊 Performance Metrics",
    value=f"**Uptime**: 99.9%\n**Incidents**: 12\n**SLA**: 95% compliant",
    inline=False
)

embed.add_field(
    name="🔴 Critical",
    value="2 issues",
    inline=True
)

embed.add_field(
    name="🟠 High",
    value="5 issues",
    inline=True
)

embed.add_field(
    name="🟡 Medium",
    value="8 issues",
    inline=True
)

embed.set_footer(text=f"ID: {ctx.guild.id} • Data updated every 5 minutes")

await ctx.send(embed=embed)
```

---

## 7. Configuration & Settings (REQUIRED)

✅ **Configurable via Commands**
Don't hardcode settings:

```python
class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {
            'enabled': True,
            'check_interval_hours': 1,
            'alert_threshold': 0.75,
            'max_retries': 3,
            'timeout_seconds': 30,
            'auto_remediate': False
        }
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from data manager."""
        data_manager = self.bot.get_cog('DataManager')
        if data_manager:
            stored_config = data_manager.get_custom_data('advanced_system_config', {})
            self.config.update(stored_config)
    
    @commands.command(name='configset')
    @commands.is_owner()
    async def config_set(self, ctx: commands.Context, key: str, value: str) -> None:
        """Set configuration parameter."""
        if key not in self.config:
            await ctx.send(f"❌ Unknown config key: {key}")
            return
        
        try:
            # Type conversion
            if isinstance(self.config[key], bool):
                self.config[key] = value.lower() in ['true', 'yes', '1']
            elif isinstance(self.config[key], int):
                self.config[key] = int(value)
            elif isinstance(self.config[key], float):
                self.config[key] = float(value)
            else:
                self.config[key] = value
            
            self.save_config()
            await ctx.send(f"✅ Set `{key}` = `{self.config[key]}`")
        except Exception as e:
            await ctx.send(f"❌ Failed to set config: {e}")
```

---

## 8. Advanced Features (REQUIRED - Choose 3-5)

Pick from these advanced patterns for every cog:

### Pattern A: Caching & Performance Optimization
```python
class AdvancedSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.cache_expiry = {}  # Track when cache expires
    
    def get_cached(self, key: str, default: Any = None) -> Any:
        """Get value from cache if not expired."""
        if key in self.cache:
            if key in self.cache_expiry:
                if datetime.utcnow() < self.cache_expiry[key]:
                    return self.cache[key]
                else:
                    del self.cache[key]
        return default
    
    def set_cache(self, key: str, value: Any, ttl_minutes: int = 5) -> None:
        """Set cache with TTL."""
        self.cache[key] = value
        self.cache_expiry[key] = datetime.utcnow() + timedelta(minutes=ttl_minutes)
```

### Pattern B: Confidence Scoring
```python
def calculate_confidence(self, indicators: List[float]) -> float:
    """Calculate confidence score (0.0-1.0) from multiple indicators."""
    if not indicators:
        return 0.0
    
    weights = [0.4, 0.3, 0.2, 0.1]  # Indicator importance
    weighted_sum = sum(ind * weight for ind, weight in zip(indicators, weights))
    avg_confidence = sum(indicators) / len(indicators)
    
    # Apply ML-inspired weighting
    final_confidence = min(1.0, weighted_sum / sum(weights[:len(indicators)]))
    return round(final_confidence, 3)
```

### Pattern C: Event Correlation
```python
def correlate_events(self, events: List[Dict[str, Any]]) -> List[List[Dict]]:
    """Group correlated events together."""
    correlated = []
    used_indices = set()
    
    for i, event1 in enumerate(events):
        if i in used_indices:
            continue
        
        group = [event1]
        for j, event2 in enumerate(events[i+1:], start=i+1):
            if j in used_indices:
                continue
            
            # Check correlation conditions
            if self._events_correlated(event1, event2):
                group.append(event2)
                used_indices.add(j)
        
        correlated.append(group)
        used_indices.add(i)
    
    return correlated
```

### Pattern D: Historical Analysis
```python
def get_historical_trend(self, metric_history: List[float], period_days: int = 30) -> Dict[str, float]:
    """Analyze historical trend of metric."""
    if len(metric_history) < 2:
        return {'trend': 'insufficient_data', 'change_percent': 0.0}
    
    recent = metric_history[-1]
    previous = metric_history[-2]
    change = recent - previous
    change_percent = (change / previous * 100) if previous != 0 else 0
    
    # Trend direction
    avg = sum(metric_history) / len(metric_history)
    recent_avg = sum(metric_history[-7:]) / min(7, len(metric_history))
    trend = 'improving' if recent_avg < avg else 'degrading'
    
    return {
        'trend': trend,
        'change_percent': round(change_percent, 2),
        'current': recent,
        'average': round(avg, 2)
    }
```

### Pattern E: Multi-Step Workflows
```python
async def execute_workflow(self, workflow_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute multi-step workflow with error recovery."""
    workflow_steps = {
        'validation': self._validate_data,
        'preprocessing': self._preprocess_data,
        'analysis': self._analyze_data,
        'remediation': self._remediate_issues,
        'reporting': self._generate_report
    }
    
    results = {}
    for step_name, step_func in workflow_steps.items():
        try:
            self.logger.info(f"[Advanced] Executing workflow step: {step_name}")
            results[step_name] = await step_func(data)
        except Exception as e:
            self.logger.error(f"[Advanced] Workflow step {step_name} failed: {e}")
            results[step_name] = {'status': 'failed', 'error': str(e)}
            # Continue to next step (graceful degradation)
    
    return results
```

---

## 9. Testing & Validation

✅ **Built-in Validation**
Every cog should validate inputs:

```python
def validate_input(self, user_input: str, input_type: str) -> Tuple[bool, str]:
    """Validate user input."""
    if not user_input:
        return False, "Input cannot be empty"
    
    if input_type == 'severity':
        valid_values = ['critical', 'high', 'medium', 'low', 'info']
        if user_input.lower() not in valid_values:
            return False, f"Severity must be one of: {', '.join(valid_values)}"
    
    elif input_type == 'integer':
        try:
            int(user_input)
        except ValueError:
            return False, "Value must be a valid integer"
    
    return True, "Valid"
```

---

## 10. Template for New Advanced Cog

Use this as a starting point for ANY new cog request:

```python
"""
[SYSTEM_NAME]: [DESCRIPTION]

Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Data Storage: data/[name].json
Signal Bus: Subscribes to [SIGNAL_TYPE], emits [SIGNAL_TYPE]
Background Tasks: [TASK_NAME] every [INTERVAL]
Commands: /command1, /command2, /command3
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from cogs.core.signal_bus import signal_bus, Signal, SignalType

logger = logging.getLogger('soc_bot')


class AdvancedSystemCog(commands.Cog):
    """Advanced system implementation with production-grade features."""
    
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize cog."""
        self.bot = bot
        self.logger = logger
        self.data_file = 'data/advanced_system.json'
        self.config = {}
        self.cache = {}
        
        # Setup
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self.load_data()
        self.load_config()
        
        # Signal subscriptions
        signal_bus.subscribe(SignalType.THREAT_DETECTED, self.on_threat)
        
        # Start background tasks
        self.background_worker.start()
        
        self.logger.info(f"[AdvancedSystem] Cog initialized with {len(self.data)} items")
    
    # ==================== DATA MANAGEMENT ====================
    
    def load_data(self) -> None:
        """Load data from disk."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                self.logger.error(f"[AdvancedSystem] Load error: {e}")
                self.data = self._default_data()
        else:
            self.data = self._default_data()
    
    def save_data(self) -> None:
        """Save data to disk."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"[AdvancedSystem] Save error: {e}")
    
    def _default_data(self) -> Dict[str, Any]:
        """Default data structure."""
        return {'events': [], 'metrics': {}, 'config': {}}
    
    def load_config(self) -> None:
        """Load configuration."""
        self.config = {
            'enabled': True,
            'check_interval_hours': 1,
            'alert_threshold': 0.75,
            'max_retries': 3
        }
    
    # ==================== BACKGROUND TASKS ====================
    
    @tasks.loop(hours=1)
    async def background_worker(self) -> None:
        """Hourly background processing."""
        try:
            self.logger.info(f"[AdvancedSystem] Running background worker")
            await self._process_queue()
        except Exception as e:
            self.logger.error(f"[AdvancedSystem] Background task error: {e}")
    
    @background_worker.before_loop
    async def before_background_worker(self) -> None:
        """Wait until bot is ready."""
        await self.bot.wait_until_ready()
    
    # ==================== SIGNAL BUS HANDLERS ====================
    
    async def on_threat(self, signal: Signal) -> None:
        """Handle threat signals."""
        try:
            self.logger.info(f"[AdvancedSystem] Processing threat: {signal.data}")
            await self._process_threat(signal)
        except Exception as e:
            self.logger.error(f"[AdvancedSystem] Error processing threat: {e}")
    
    # ==================== CORE LOGIC ====================
    
    async def _process_queue(self) -> None:
        """Process event queue."""
        pass
    
    async def _process_threat(self, signal: Signal) -> None:
        """Process threat signal."""
        pass
    
    # ==================== COMMANDS ====================
    
    @commands.command(name='advanced')
    @commands.has_permissions(manage_guild=True)
    async def advanced_prefix(self, ctx: commands.Context) -> None:
        """Prefix command."""
        await self._advanced_logic(ctx)
    
    @app_commands.command(name='advanced', description='Advanced system command')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def advanced_slash(self, interaction: discord.Interaction) -> None:
        """Slash command."""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, i):
                self.channel = i.channel
                self.author = i.user
            async def send(self, **kwargs):
                return await interaction.followup.send(**kwargs)
        
        await self._advanced_logic(FakeCtx(interaction))
    
    async def _advanced_logic(self, ctx) -> None:
        """Shared command logic."""
        embed = discord.Embed(
            title="🛡️ Advanced System",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)
    
    # ==================== CLEANUP ====================
    
    def cog_unload(self) -> None:
        """Cleanup on unload."""
        self.background_worker.cancel()
        self.save_data()
        self.logger.info(f"[AdvancedSystem] Cog unloaded")


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loader."""
    await bot.add_cog(AdvancedSystemCog(bot))
    logger.info(f"[AdvancedSystem] Cog setup complete")
```

---

## 11. When Requesting New Systems

### Use This Format:
```
Create a NEW ADVANCED SYSTEM cog: [NAME]

Purpose: [What it does in 1-2 sentences]

Key Features:
1. [Feature 1 - specific, measurable]
2. [Feature 2 - specific, measurable]
3. [Feature 3 - specific, measurable]
4. [Feature 4 - optional, special requirement]

Target Size: [200+ / 400+ / 600+ / 800+ lines]

Background Tasks: [Task description, frequency]

Commands Required:
- /command1 - description
- /command2 - description

Signal Bus:
- Subscribes to: [SIGNAL_TYPE]
- Emits: [SIGNAL_TYPE]

Advanced Patterns: [Pick 2-3: Caching, Confidence Scoring, Event Correlation, Historical Analysis, Multi-Step Workflows]

Special Requirements: [Any unique needs]
```

### Example Request:
```
Create a NEW ADVANCED SYSTEM cog: User Behavior Anomaly Detector

Purpose: Detect unusual user behavior patterns and anomalies in real-time using statistical analysis and ML-inspired confidence scoring.

Key Features:
1. Real-time user activity monitoring (messages, reactions, joins)
2. Statistical baseline calculation (mean, stddev, moving averages)
3. Anomaly detection with confidence scoring (0.0-1.0)
4. Historical trend analysis (7-day, 30-day, 90-day patterns)
5. Automated alerts for high-confidence anomalies (>0.85)
6. Per-user behavior profiles with activity metrics
7. Temporal analysis (time-of-day patterns, weekday/weekend differences)
8. Correlation of multiple anomalies to detect coordinated attacks

Target Size: 800+ lines (substantial system)

Background Tasks:
- update_baselines() - recalculate user baselines every 6 hours
- detect_anomalies() - scan for anomalies every 30 minutes
- cleanup_old_data() - purge data older than 90 days

Commands Required:
- /anomalycheck <user> - show current anomaly score
- /userprofile <user> - view user behavior profile
- /baselineupdate - manually recalculate baselines
- /anomalyalerts - view recent anomalies (last 10)
- /anomalyconfig <key> <value> - set anomaly detection config

Signal Bus:
- Subscribes to: ANOMALY_DETECTED (from other systems)
- Emits: ANOMALY_DETECTED (when threshold exceeded)

Advanced Patterns: 
1. Confidence Scoring (multi-factor anomaly scoring)
2. Historical Analysis (trend detection over time)
3. Event Correlation (link related anomalies)

Special Requirements:
- Integration with DataManager for user activity history
- Graceful handling of new users (no baseline data)
- Per-guild configuration (different thresholds per server)
```

---

## Summary

When requesting new systems, ALWAYS expect:
- ✅ 400+ lines minimum (substantial code)
- ✅ Full type hints and docstrings
- ✅ Signal bus integration
- ✅ Background tasks
- ✅ Data persistence
- ✅ Both slash and prefix commands
- ✅ Advanced features (3+ patterns)
- ✅ Professional embeds
- ✅ Error handling throughout
- ✅ Comprehensive logging
- ✅ Configuration management

**Result**: Production-grade, maintainable, feature-rich systems ready for enterprise deployment.
