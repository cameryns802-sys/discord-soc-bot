import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class PrivilegeEscalationMonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events_file = "data/privilege_escalation_events.json"
        self.events = []
        self._load_events()

    def _load_events(self):
        if os.path.exists(self.events_file):
            with open(self.events_file) as f:
                self.events = json.load(f)
        else:
            self.events = []

    def _save_events(self):
        os.makedirs("data", exist_ok=True)
        with open(self.events_file, "w") as f:
            json.dump(self.events, f, indent=2)

    @commands.command()
    async def privilege_change(self, ctx, member: str, change: str):
        """Record a privilege escalation or role change event."""
        severity = "LOW"
        if "admin" in change.lower() or "owner" in change.lower():
            severity = "HIGH"
        elif "mod" in change.lower() or "manage" in change.lower():
            severity = "MEDIUM"

        event = {
            "id": len(self.events) + 1,
            "member": member,
            "change": change,
            "severity": severity,
            "timestamp": get_now_pst().isoformat(),
        }
        self.events.append(event)
        self._save_events()

        color_map = {
            "HIGH": discord.Color.orange(),
            "MEDIUM": discord.Color.gold(),
            "LOW": discord.Color.green(),
        }
        embed = discord.Embed(
            title="🔐 Privilege Escalation Monitor",
            description=f"Member: **{member}**",
            color=color_map[severity],
        )
        embed.add_field(name="Change", value=change, inline=False)
        embed.add_field(name="Severity", value=severity, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def privilege_report(self, ctx):
        """Show recent privilege escalation activity."""
        if not self.events:
            await ctx.send("✅ No privilege changes recorded yet.")
            return

        latest = sorted(self.events, key=lambda e: e["timestamp"], reverse=True)[:5]
        embed = discord.Embed(
            title="📊 Privilege Escalation Report",
            description="Recent privilege changes",
            color=discord.Color.blue(),
        )
        for event in latest:
            embed.add_field(
                name=f"{event['member']} ({event['severity']})",
                value=f"{event['change']}\n{event['timestamp']}",
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PrivilegeEscalationMonitorCog(bot))
