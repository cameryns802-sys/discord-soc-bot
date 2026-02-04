import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class SecretsExposureWatcherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.findings_file = "data/secrets_exposure_findings.json"
        self.findings = []
        self._load_findings()

    def _load_findings(self):
        if os.path.exists(self.findings_file):
            with open(self.findings_file) as f:
                self.findings = json.load(f)
        else:
            self.findings = []

    def _save_findings(self):
        os.makedirs("data", exist_ok=True)
        with open(self.findings_file, "w") as f:
            json.dump(self.findings, f, indent=2)

    @commands.command()
    async def secret_scan(self, ctx, location: str, findings: int):
        """Record a secrets exposure scan result."""
        severity = "LOW"
        if findings >= 5:
            severity = "HIGH"
        elif findings >= 2:
            severity = "MEDIUM"

        entry = {
            "id": len(self.findings) + 1,
            "location": location,
            "findings": findings,
            "severity": severity,
            "timestamp": get_now_pst().isoformat(),
        }
        self.findings.append(entry)
        self._save_findings()

        color_map = {
            "HIGH": discord.Color.red(),
            "MEDIUM": discord.Color.gold(),
            "LOW": discord.Color.green(),
        }
        embed = discord.Embed(
            title="🔎 Secrets Exposure Watcher",
            description=f"Location: **{location}**",
            color=color_map[severity],
        )
        embed.add_field(name="Findings", value=str(findings), inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def secret_report(self, ctx):
        """Show recent secrets exposure scans."""
        if not self.findings:
            await ctx.send("✅ No secrets exposure findings recorded yet.")
            return

        latest = sorted(self.findings, key=lambda f: f["timestamp"], reverse=True)[:5]
        embed = discord.Embed(
            title="📋 Secrets Exposure Report",
            description="Recent secrets exposure scans",
            color=discord.Color.blue(),
        )
        for entry in latest:
            embed.add_field(
                name=f"{entry['location']} ({entry['severity']})",
                value=f"Findings: {entry['findings']} | {entry['timestamp']}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecretsExposureWatcherCog(bot))
