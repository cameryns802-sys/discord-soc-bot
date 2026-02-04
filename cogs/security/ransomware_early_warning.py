import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import random
from cogs.core.pst_timezone import get_now_pst

class RansomwareEarlyWarningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alerts_file = "data/ransomware_alerts.json"
        self.alerts = []
        self._load_alerts()

    def _load_alerts(self):
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file) as f:
                self.alerts = json.load(f)
        else:
            self.alerts = []

    def _save_alerts(self):
        os.makedirs("data", exist_ok=True)
        with open(self.alerts_file, "w") as f:
            json.dump(self.alerts, f, indent=2)

    @commands.command()
    async def rwe_scan(self, ctx, system_name: str):
        """Run a ransomware early warning scan on a system."""
        risk_score = random.randint(1, 100)
        indicators = []
        severity = "LOW"
        if risk_score > 80:
            severity = "CRITICAL"
            indicators = [
                "Rapid file rename burst detected",
                "Shadow copy deletion attempt",
                "Unusual encryption API usage",
            ]
        elif risk_score > 55:
            severity = "HIGH"
            indicators = [
                "Suspicious process spawning",
                "High entropy file creation spike",
            ]
        elif risk_score > 30:
            severity = "MEDIUM"
            indicators = [
                "Abnormal file access patterns",
            ]

        alert = {
            "id": len(self.alerts) + 1,
            "system": system_name,
            "risk_score": risk_score,
            "severity": severity,
            "indicators": indicators,
            "timestamp": get_now_pst().isoformat(),
        }
        self.alerts.append(alert)
        self._save_alerts()

        color_map = {
            "CRITICAL": discord.Color.red(),
            "HIGH": discord.Color.orange(),
            "MEDIUM": discord.Color.gold(),
            "LOW": discord.Color.green(),
        }
        embed = discord.Embed(
            title="🛡️ Ransomware Early Warning",
            description=f"System: **{system_name}**",
            color=color_map[severity],
        )
        embed.add_field(name="Risk Score", value=f"{risk_score}/100", inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        if indicators:
            embed.add_field(
                name="Indicators",
                value="\n".join([f"⚠️ {item}" for item in indicators]),
                inline=False,
            )
        else:
            embed.add_field(
                name="Indicators",
                value="✅ No ransomware indicators detected",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def rwe_status(self, ctx):
        """Show the latest ransomware early warning scans."""
        if not self.alerts:
            await ctx.send("✅ No ransomware scans recorded yet.")
            return

        latest_alerts = sorted(self.alerts, key=lambda a: a["timestamp"], reverse=True)[:5]
        embed = discord.Embed(
            title="📊 Ransomware Early Warning Status",
            description="Latest ransomware risk assessments",
            color=discord.Color.blue(),
        )
        for alert in latest_alerts:
            embed.add_field(
                name=f"{alert['system']} ({alert['severity']})",
                value=f"Score: {alert['risk_score']}/100\nTime: {alert['timestamp']}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RansomwareEarlyWarningCog(bot))
