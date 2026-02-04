# Insider Threat Detection: Behavioral analytics, risk scoring, and pattern detection
import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class InsiderThreatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_profiles = {}
        self.risk_scores = {}
        self.behavioral_baseline = {}
        self.suspicious_activities = []
        self.insider_counter = 0

    def calculate_risk_score(self, user_id: int) -> int:
        """Calculate insider threat risk score (0-100)."""
        score = 50  # Baseline
        if user_id in self.risk_scores:
            return self.risk_scores[user_id]
        # Check activity patterns
        profile = self.user_profiles.get(user_id, {})
        if profile.get("late_night_logins", 0) > 3:
            score += 15
        if profile.get("rapid_permission_changes", 0) > 2:
            score += 20
        if profile.get("access_sensitive_channels", 0) > 5:
            score += 10
        if profile.get("failed_auth_attempts", 0) > 5:
            score -= 5
        score = min(100, max(0, score))
        self.risk_scores[user_id] = score
        return score

    @commands.command()
    async def insider_profile(self, ctx, user: discord.Member = None):
        """View user behavioral profile."""
        user = user or ctx.author
        if user.id not in self.user_profiles:
            self.user_profiles[user.id] = {
                "first_seen": datetime.get_now_pst(),
                "late_night_logins": 0,
                "rapid_permission_changes": 0,
                "access_sensitive_channels": 0,
                "failed_auth_attempts": 0
            }
        profile = self.user_profiles[user.id]
        risk = self.calculate_risk_score(user.id)
        color = discord.Color.red() if risk > 70 else discord.Color.orange() if risk > 40 else discord.Color.green()
        embed = discord.Embed(title=f"Behavioral Profile - {user}", color=color)
        embed.add_field(name="Risk Score", value=f"{risk}/100", inline=True)
        embed.add_field(name="Status", value="🔴 HIGH RISK" if risk > 70 else "🟡 MEDIUM" if risk > 40 else "🟢 LOW RISK", inline=True)
        embed.add_field(name="Late Night Logins", value=str(profile["late_night_logins"]), inline=True)
        embed.add_field(name="Rapid Permission Changes", value=str(profile["rapid_permission_changes"]), inline=True)
        embed.add_field(name="Sensitive Channel Access", value=str(profile["access_sensitive_channels"]), inline=True)
        embed.add_field(name="First Seen", value=profile["first_seen"].strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def insider_baseline(self, ctx, user: discord.Member):
        """Set behavioral baseline for user (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        self.behavioral_baseline[user.id] = {
            "avg_daily_logins": 5,
            "typical_active_hours": "09:00-18:00",
            "usual_channels": [],
            "typical_role_count": len(user.roles),
            "baseline_set_at": datetime.get_now_pst()
        }
        embed = discord.Embed(title="Baseline Set", description=f"Behavioral baseline established for {user.mention}", color=discord.Color.green())
        embed.add_field(name="Typical Active Hours", value="09:00-18:00", inline=True)
        embed.add_field(name="Daily Logins", value="5", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def insider_anomaly(self, ctx, user: discord.Member, *, anomaly_type: str):
        """Report suspicious behavior (admin only)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        self.insider_counter += 1
        alert_id = self.insider_counter
        self.suspicious_activities.append({
            "id": alert_id,
            "user_id": user.id,
            "user": user.mention,
            "anomaly_type": anomaly_type,
            "reported_by": ctx.author.mention,
            "time": datetime.get_now_pst()
        })
        # Update risk score
        profile = self.user_profiles.get(user.id, {})
        if "permission" in anomaly_type.lower():
            profile["rapid_permission_changes"] = profile.get("rapid_permission_changes", 0) + 1
        if "night" in anomaly_type.lower():
            profile["late_night_logins"] = profile.get("late_night_logins", 0) + 1
        if "sensitive" in anomaly_type.lower():
            profile["access_sensitive_channels"] = profile.get("access_sensitive_channels", 0) + 1
        self.user_profiles[user.id] = profile
        
        embed = discord.Embed(title="Anomaly Reported", description=anomaly_type, color=discord.Color.orange())
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Alert ID", value=f"#{alert_id}", inline=True)
        new_risk = self.calculate_risk_score(user.id)
        embed.add_field(name="Updated Risk Score", value=f"{new_risk}/100", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def insider_alerts(self, ctx):
        """View insider threat alerts."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.suspicious_activities:
            await ctx.send("No insider threat alerts.")
            return
        recent = self.suspicious_activities[-10:]
        desc = "\n".join([f"**#{a['id']}** {a['user']} - {a['anomaly_type']}" for a in recent])
        embed = discord.Embed(title="Insider Threat Alerts", description=desc, color=discord.Color.orange())
        embed.set_footer(text=f"Total: {len(self.suspicious_activities)} alert(s)")
        await ctx.send(embed=embed)

    @commands.command()
    async def insider_high_risk(self, ctx):
        """List high-risk users."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        high_risk = [(uid, score) for uid, score in self.risk_scores.items() if score > 70]
        if not high_risk:
            await ctx.send("No high-risk users detected.")
            return
        desc = "\n".join([f"<@{uid}> - Risk: {score}/100" for uid, score in high_risk])
        embed = discord.Embed(title="🔴 High-Risk Users", description=desc, color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command()
    async def insider_summary(self, ctx):
        """Insider threat summary."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        high_risk_count = len([s for s in self.risk_scores.values() if s > 70])
        embed = discord.Embed(title="Insider Threat Summary", color=discord.Color.blue())
        embed.add_field(name="Users Profiled", value=str(len(self.user_profiles)), inline=True)
        embed.add_field(name="High-Risk Users", value=str(high_risk_count), inline=True)
        embed.add_field(name="Total Anomalies", value=str(len(self.suspicious_activities)), inline=True)
        avg_risk = sum(self.risk_scores.values()) / len(self.risk_scores) if self.risk_scores else 0
        embed.add_field(name="Avg Risk Score", value=f"{int(avg_risk)}/100", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InsiderThreatCog(bot))
