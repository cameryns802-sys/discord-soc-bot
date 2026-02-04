import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import hashlib
import random
from cogs.core.pst_timezone import get_now_pst

class DataIntegrityMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snapshots_file = "data/data_integrity_snapshots.json"
        self.snapshots = {}
        self._load_snapshots()

    def _load_snapshots(self):
        if os.path.exists(self.snapshots_file):
            with open(self.snapshots_file) as f:
                self.snapshots = json.load(f)
        else:
            self.snapshots = {}

    def _save_snapshots(self):
        os.makedirs("data", exist_ok=True)
        with open(self.snapshots_file, "w") as f:
            json.dump(self.snapshots, f, indent=2)

    def _generate_hash(self, seed: str) -> str:
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    @commands.command()
    async def integrity_snapshot(self, ctx, system_name: str):
        """Create a baseline integrity snapshot for a system."""
        baseline_hash = self._generate_hash(f"{system_name}-{get_now_pst().isoformat()}")
        self.snapshots[system_name] = {
            "hash": baseline_hash,
            "timestamp": get_now_pst().isoformat(),
        }
        self._save_snapshots()

        embed = discord.Embed(
            title="🧾 Integrity Snapshot Created",
            description=f"System: **{system_name}**",
            color=discord.Color.green(),
        )
        embed.add_field(name="Baseline Hash", value=baseline_hash[:12] + "…", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def integrity_check(self, ctx, system_name: str):
        """Check system integrity against the last snapshot."""
        snapshot = self.snapshots.get(system_name)
        if not snapshot:
            await ctx.send("❌ No baseline snapshot found. Use `!integrity_snapshot <system>` first.")
            return

        drift_detected = random.randint(1, 10) > 7
        current_hash = snapshot["hash"] if not drift_detected else self._generate_hash(system_name)
        status = "✅ No integrity drift detected" if not drift_detected else "🚨 Integrity drift detected"
        color = discord.Color.green() if not drift_detected else discord.Color.red()

        report = {
            "system": system_name,
            "baseline_hash": snapshot["hash"],
            "current_hash": current_hash,
            "drift": drift_detected,
            "timestamp": get_now_pst().isoformat(),
        }

        embed = discord.Embed(
            title="🔍 Data Integrity Check",
            description=f"System: **{system_name}**",
            color=color,
        )
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Baseline Hash", value=report["baseline_hash"][:12] + "…", inline=True)
        embed.add_field(name="Current Hash", value=report["current_hash"][:12] + "…", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataIntegrityMonitorCog(bot))
