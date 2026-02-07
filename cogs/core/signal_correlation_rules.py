"""
Signal Correlation Rules
Create and manage correlation rules that watch the signal bus and emit aggregated signals.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst


class SignalCorrelationRules(commands.Cog):
    """Correlation rules for signal aggregation"""

    def __init__(self, bot):
        self.bot = bot
        self.rules_file = "data/correlation_rules.json"
        self.rules: Dict[str, Dict] = self._load_rules()
        self.buffers: Dict[str, List[datetime]] = {}
        self.setup_signal_listeners()

    def setup_signal_listeners(self):
        """Subscribe to all signals"""
        signal_bus.subscribe("signal_correlation_rules", self.on_signal)

    def _resolve_signal_type(self, value: str) -> Optional[SignalType]:
        if not value:
            return None
        value_norm = value.strip().lower()
        for signal_type in SignalType:
            if value_norm == signal_type.value or value_norm == signal_type.name.lower():
                return signal_type
        return None

    def _get_signal_type(self, signal: Signal) -> Optional[SignalType]:
        signal_type = getattr(signal, "signal_type", None)
        if isinstance(signal_type, SignalType):
            return signal_type
        if signal_type is None:
            signal_type = getattr(signal, "type", None)
        if isinstance(signal_type, SignalType):
            return signal_type
        if isinstance(signal_type, str):
            return self._resolve_signal_type(signal_type)
        return None

    def _normalize_rule(self, rule_id: str, rule: Dict) -> Optional[Dict]:
        signal_types = rule.get("signal_types", [])
        normalized_types = []
        for item in signal_types:
            if isinstance(item, SignalType):
                normalized_types.append(item)
            elif isinstance(item, str):
                resolved = self._resolve_signal_type(item)
                if resolved:
                    normalized_types.append(resolved)

        if not normalized_types:
            return None

        emit_type = rule.get("emit_type", SignalType.ANOMALY_DETECTED.value)
        emit_resolved = emit_type if isinstance(emit_type, SignalType) else self._resolve_signal_type(str(emit_type))
        if not emit_resolved:
            emit_resolved = SignalType.ANOMALY_DETECTED

        window_seconds = int(rule.get("window_seconds", 300))
        min_count = int(rule.get("min_count", 3))
        cooldown_seconds = int(rule.get("cooldown_seconds", window_seconds))
        severity = str(rule.get("severity", "medium")).lower()
        confidence = float(rule.get("confidence", 0.75))

        return {
            "id": rule_id,
            "name": rule.get("name", rule_id),
            "signal_types": normalized_types,
            "window_seconds": max(10, window_seconds),
            "min_count": max(2, min_count),
            "severity": severity,
            "emit_type": emit_resolved,
            "confidence": max(0.0, min(1.0, confidence)),
            "cooldown_seconds": max(10, cooldown_seconds),
            "enabled": bool(rule.get("enabled", True)),
            "last_triggered": rule.get("last_triggered")
        }

    def _serialize_rule(self, rule: Dict) -> Dict:
        return {
            "name": rule.get("name"),
            "signal_types": [t.value if isinstance(t, SignalType) else str(t) for t in rule.get("signal_types", [])],
            "window_seconds": rule.get("window_seconds"),
            "min_count": rule.get("min_count"),
            "severity": rule.get("severity"),
            "emit_type": rule.get("emit_type").value if isinstance(rule.get("emit_type"), SignalType) else str(rule.get("emit_type")),
            "confidence": rule.get("confidence"),
            "cooldown_seconds": rule.get("cooldown_seconds"),
            "enabled": rule.get("enabled", True),
            "last_triggered": rule.get("last_triggered")
        }

    def _load_rules(self) -> Dict[str, Dict]:
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r") as f:
                    raw = json.load(f)
            except Exception:
                raw = {}
        else:
            raw = {}

        normalized = {}
        for rule_id, rule in raw.items():
            normalized_rule = self._normalize_rule(rule_id, rule)
            if normalized_rule:
                normalized[rule_id] = normalized_rule
        return normalized

    def _save_rules(self) -> None:
        os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
        payload = {rule_id: self._serialize_rule(rule) for rule_id, rule in self.rules.items()}
        with open(self.rules_file, "w") as f:
            json.dump(payload, f, indent=2)

    async def on_signal(self, signal: Signal):
        signal_type = self._get_signal_type(signal)
        if not signal_type:
            return

        now = get_now_pst()
        for rule_id, rule in self.rules.items():
            if not rule.get("enabled", True):
                continue
            if signal_type not in rule["signal_types"]:
                continue

            buffer = self.buffers.setdefault(rule_id, [])
            window = timedelta(seconds=rule["window_seconds"])
            cutoff = now - window
            buffer.append(now)
            buffer[:] = [ts for ts in buffer if ts > cutoff]

            last_triggered = rule.get("last_triggered")
            if last_triggered:
                last_triggered_dt = datetime.fromisoformat(last_triggered)
                if (now - last_triggered_dt).total_seconds() < rule["cooldown_seconds"]:
                    continue

            if len(buffer) >= rule["min_count"]:
                await self.emit_correlated_signal(rule, signal, len(buffer))
                rule["last_triggered"] = now.isoformat()
                self._save_rules()

    async def emit_correlated_signal(self, rule: Dict, signal: Signal, count: int) -> None:
        emit_type = rule.get("emit_type", SignalType.ANOMALY_DETECTED)
        correlated = Signal(
            signal_type=emit_type,
            severity=rule.get("severity", "medium"),
            source="signal_correlation_rules",
            data={
                "rule_id": rule["id"],
                "rule_name": rule.get("name", rule["id"]),
                "matched_signal": emit_type.value,
                "signal_count": count,
                "window_seconds": rule["window_seconds"],
                "confidence": rule.get("confidence", 0.75),
                "dedup_key": f"corr:{rule['id']}"
            }
        )
        await signal_bus.emit(correlated)

    @commands.command(name="corr_list")
    @commands.has_permissions(administrator=True)
    async def corr_list(self, ctx):
        """List correlation rules"""
        if not self.rules:
            await ctx.send("✅ No correlation rules configured")
            return

        embed = discord.Embed(
            title="🔗 Signal Correlation Rules",
            description=f"Total rules: {len(self.rules)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )

        for rule_id, rule in sorted(self.rules.items()):
            signal_types = ", ".join([t.value for t in rule["signal_types"]])
            status = "✅ enabled" if rule.get("enabled", True) else "⏸️ disabled"
            value = (
                f"Signals: {signal_types}\n"
                f"Window: {rule['window_seconds']}s | Count: {rule['min_count']}\n"
                f"Severity: {rule['severity']} | Emit: {rule['emit_type'].value}\n"
                f"Cooldown: {rule['cooldown_seconds']}s | {status}"
            )
            embed.add_field(name=rule_id, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="corr_show")
    @commands.has_permissions(administrator=True)
    async def corr_show(self, ctx, rule_id: str):
        """Show correlation rule details"""
        rule = self.rules.get(rule_id)
        if not rule:
            await ctx.send("❌ Rule not found")
            return

        embed = discord.Embed(
            title=f"🔍 Rule: {rule_id}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Name", value=rule.get("name", rule_id), inline=False)
        embed.add_field(name="Signals", value=", ".join([t.value for t in rule["signal_types"]]), inline=False)
        embed.add_field(name="Window", value=f"{rule['window_seconds']} seconds", inline=True)
        embed.add_field(name="Min Count", value=str(rule["min_count"]), inline=True)
        embed.add_field(name="Severity", value=rule["severity"], inline=True)
        embed.add_field(name="Emit Type", value=rule["emit_type"].value, inline=True)
        embed.add_field(name="Confidence", value=f"{rule['confidence']:.2f}", inline=True)
        embed.add_field(name="Cooldown", value=f"{rule['cooldown_seconds']} seconds", inline=True)
        embed.add_field(name="Enabled", value=str(rule.get("enabled", True)), inline=True)
        embed.add_field(name="Last Triggered", value=rule.get("last_triggered") or "Never", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="corr_add")
    @commands.is_owner()
    async def corr_add(self, ctx, rule_id: str, signal_types_csv: str, window_seconds: int, min_count: int, severity: str, emit_type: str = None, cooldown_seconds: int = None, *, name: str = None):
        """Create a correlation rule"""
        if rule_id in self.rules:
            await ctx.send("❌ Rule already exists")
            return

        signal_types = []
        for item in signal_types_csv.split(","):
            resolved = self._resolve_signal_type(item)
            if resolved:
                signal_types.append(resolved)

        if not signal_types:
            await ctx.send("❌ No valid signal types")
            return

        emit_resolved = self._resolve_signal_type(emit_type) if emit_type else SignalType.ANOMALY_DETECTED
        if not emit_resolved:
            emit_resolved = SignalType.ANOMALY_DETECTED

        rule = {
            "id": rule_id,
            "name": name or rule_id,
            "signal_types": signal_types,
            "window_seconds": window_seconds,
            "min_count": min_count,
            "severity": severity.lower(),
            "emit_type": emit_resolved,
            "confidence": 0.75,
            "cooldown_seconds": cooldown_seconds or window_seconds,
            "enabled": True,
            "last_triggered": None
        }
        normalized = self._normalize_rule(rule_id, rule)
        if not normalized:
            await ctx.send("❌ Invalid rule configuration")
            return

        self.rules[rule_id] = normalized
        self._save_rules()
        await ctx.send(f"✅ Created correlation rule `{rule_id}`")

    @commands.command(name="corr_remove")
    @commands.is_owner()
    async def corr_remove(self, ctx, rule_id: str):
        """Remove a correlation rule"""
        if rule_id not in self.rules:
            await ctx.send("❌ Rule not found")
            return
        del self.rules[rule_id]
        self._save_rules()
        await ctx.send(f"✅ Removed correlation rule `{rule_id}`")

    @commands.command(name="corr_enable")
    @commands.is_owner()
    async def corr_enable(self, ctx, rule_id: str):
        """Enable a correlation rule"""
        rule = self.rules.get(rule_id)
        if not rule:
            await ctx.send("❌ Rule not found")
            return
        rule["enabled"] = True
        self._save_rules()
        await ctx.send(f"✅ Enabled correlation rule `{rule_id}`")

    @commands.command(name="corr_disable")
    @commands.is_owner()
    async def corr_disable(self, ctx, rule_id: str):
        """Disable a correlation rule"""
        rule = self.rules.get(rule_id)
        if not rule:
            await ctx.send("❌ Rule not found")
            return
        rule["enabled"] = False
        self._save_rules()
        await ctx.send(f"✅ Disabled correlation rule `{rule_id}`")

    @commands.command(name="corr_set")
    @commands.is_owner()
    async def corr_set(self, ctx, rule_id: str, field: str, value: str):
        """Update a correlation rule field"""
        rule = self.rules.get(rule_id)
        if not rule:
            await ctx.send("❌ Rule not found")
            return

        field_key = field.lower()
        if field_key in {"window", "window_seconds"}:
            rule["window_seconds"] = max(10, int(value))
        elif field_key in {"min_count", "count"}:
            rule["min_count"] = max(2, int(value))
        elif field_key == "severity":
            rule["severity"] = value.lower()
        elif field_key in {"emit", "emit_type"}:
            resolved = self._resolve_signal_type(value)
            if not resolved:
                await ctx.send("❌ Invalid emit signal type")
                return
            rule["emit_type"] = resolved
        elif field_key == "confidence":
            rule["confidence"] = max(0.0, min(1.0, float(value)))
        elif field_key in {"cooldown", "cooldown_seconds"}:
            rule["cooldown_seconds"] = max(10, int(value))
        else:
            await ctx.send("❌ Unsupported field")
            return

        normalized = self._normalize_rule(rule_id, rule)
        if not normalized:
            await ctx.send("❌ Invalid rule configuration")
            return
        self.rules[rule_id] = normalized
        self._save_rules()
        await ctx.send(f"✅ Updated correlation rule `{rule_id}`")


async def setup(bot):
    await bot.add_cog(SignalCorrelationRules(bot))
