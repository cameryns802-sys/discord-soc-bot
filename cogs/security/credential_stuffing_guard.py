import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class CredentialStuffingGuardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attempts_file = "data/credential_stuffing_attempts.json"
        self.attempts = []
        self._load_attempts()

    def _load_attempts(self):
        if os.path.exists(self.attempts_file):
            with open(self.attempts_file) as f:
                self.attempts = json.load(f)
        else:
            self.attempts = []

    def _save_attempts(self):
        os.makedirs("data", exist_ok=True)
        with open(self.attempts_file, "w") as f:
            json.dump(self.attempts, f, indent=2)

    @commands.command()
    async def credstuff_check(self, ctx, account: str, attempts: int):
        """Record a credential stuffing check for an account."""
        risk_score = min(100, max(0, attempts * 7))
        severity = "LOW"
        if risk_score >= 80:
            severity = "CRITICAL"
        elif risk_score >= 60:
            severity = "HIGH"
        elif risk_score >= 35:
            severity = "MEDIUM"

        event = {
            "id": len(self.attempts) + 1,
            "account": account,
            "attempts": attempts,
            "risk_score": risk_score,
            "severity": severity,
            "timestamp": get_now_pst().isoformat(),
        }
        self.attempts.append(event)
        self._save_attempts()

        color_map = {
            "CRITICAL": discord.Color.red(),
            "HIGH": discord.Color.orange(),
            "MEDIUM": discord.Color.gold(),
            "LOW": discord.Color.green(),
        }
        embed = discord.Embed(
            title="🔐 Credential Stuffing Guard",
            description=f"Account: **{account}**",
            color=color_map[severity],
        )
        embed.add_field(name="Attempts", value=str(attempts), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk_score}/100", inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def credstuff_report(self, ctx):
        """Show recent credential stuffing activity."""
        if not self.attempts:
            await ctx.send("✅ No credential stuffing activity recorded yet.")
            return

        latest = sorted(self.attempts, key=lambda a: a["timestamp"], reverse=True)[:5]
        embed = discord.Embed(
            title="📈 Credential Stuffing Report",
            description="Recent high-risk authentication activity",
            color=discord.Color.blue(),
        )
        for event in latest:
            embed.add_field(
                name=f"{event['account']} ({event['severity']})",
                value=f"Attempts: {event['attempts']} | Score: {event['risk_score']}/100",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CredentialStuffingGuardCog(bot))
