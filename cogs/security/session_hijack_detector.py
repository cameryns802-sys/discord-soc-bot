import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class SessionHijackDetectorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions_file = "data/session_hijack_events.json"
        self.session_history = {}
        self._load_sessions()

    def _load_sessions(self):
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file) as f:
                self.session_history = json.load(f)
        else:
            self.session_history = {}

    def _save_sessions(self):
        os.makedirs("data", exist_ok=True)
        with open(self.sessions_file, "w") as f:
            json.dump(self.session_history, f, indent=2)

    @commands.command()
    async def hijack_check(self, ctx, account: str, ip_address: str):
        """Check for session hijack indicators based on new logins."""
        history = self.session_history.get(account, [])
        is_new_ip = ip_address not in [entry["ip"] for entry in history]
        risk_score = 35 if is_new_ip else 10
        severity = "LOW"
        if risk_score >= 70:
            severity = "CRITICAL"
        elif risk_score >= 50:
            severity = "HIGH"
        elif risk_score >= 30:
            severity = "MEDIUM"

        event = {
            "ip": ip_address,
            "risk_score": risk_score,
            "severity": severity,
            "timestamp": get_now_pst().isoformat(),
        }
        history.append(event)
        self.session_history[account] = history[-10:]
        self._save_sessions()

        color_map = {
            "CRITICAL": discord.Color.red(),
            "HIGH": discord.Color.orange(),
            "MEDIUM": discord.Color.gold(),
            "LOW": discord.Color.green(),
        }
        embed = discord.Embed(
            title="🕵️ Session Hijack Check",
            description=f"Account: **{account}**",
            color=color_map[severity],
        )
        embed.add_field(name="IP Address", value=ip_address, inline=True)
        embed.add_field(name="New IP", value="Yes" if is_new_ip else "No", inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def hijack_report(self, ctx, account: str):
        """Show recent session checks for an account."""
        history = self.session_history.get(account)
        if not history:
            await ctx.send("✅ No session activity recorded for that account.")
            return

        embed = discord.Embed(
            title="📌 Session Hijack Report",
            description=f"Recent session checks for {account}",
            color=discord.Color.blue(),
        )
        for entry in sorted(history, key=lambda e: e["timestamp"], reverse=True)[:5]:
            embed.add_field(
                name=f"{entry['ip']} ({entry['severity']})",
                value=f"Score: {entry['risk_score']} | {entry['timestamp']}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SessionHijackDetectorCog(bot))
