"""
Fatigue & Alert Monitoring: Monitor mod/on-call time and burnout signals, warn/auto-throttle tasks.
"""
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

class FatigueMonitoringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/fatigue_monitoring.json"
        self.data = self.load_data()
        self.fatigue_check.start()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "mod_activity": {},
            "on_call_schedule": {},
            "fatigue_scores": {},
            "alert_thresholds": {
                "hours_per_day": 8,
                "consecutive_hours": 6,
                "alerts_per_hour": 10,
                "task_overload": 20
            },
            "burnout_signals": {},
            "throttled_users": {},
            "health_check_history": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @tasks.loop(hours=1)
    async def fatigue_check(self):
        """Periodic fatigue monitoring check."""
        try:
            for user_id, activity in self.data["mod_activity"].items():
                fatigue_score = self.calculate_fatigue(activity)
                self.data["fatigue_scores"][user_id] = fatigue_score
                
                if fatigue_score > 0.7:
                    if user_id not in self.data["burnout_signals"]:
                        self.data["burnout_signals"][user_id] = {"level": "WARNING", "detected_at": get_now_pst().isoformat()}
            
            self.save_data(self.data)
        except Exception as e:
            print(f"[FatigueMonitoring] Check error: {e}")

    @fatigue_check.before_loop
    async def before_fatigue_check(self):
        await self.bot.wait_until_ready()

    def calculate_fatigue(self, activity):
        """Calculate fatigue score (0-1) from activity metrics."""
        score = 0
        
        # Hours worked today
        hours_today = activity.get("hours_today", 0)
        if hours_today > 8:
            score += min((hours_today - 8) / 10, 0.3)
        
        # Alerts handled
        alerts_handled = activity.get("alerts_handled", 0)
        if alerts_handled > 10:
            score += min(alerts_handled / 50, 0.3)
        
        # Consecutive hours
        consecutive = activity.get("consecutive_hours", 0)
        if consecutive > 6:
            score += min((consecutive - 6) / 8, 0.2)
        
        # Command execution rate
        commands_executed = activity.get("commands_executed", 0)
        if commands_executed > 30:
            score += min(commands_executed / 100, 0.2)
        
        return min(score, 1.0)

    @commands.command(name="log_mod_activity")
    async def log_mod_activity(self, ctx, hours_worked: float, alerts: int, commands: int):
        """Log moderation activity for fatigue tracking."""
        user_id = str(ctx.author.id)
        
        if user_id not in self.data["mod_activity"]:
            self.data["mod_activity"][user_id] = {
                "user": str(ctx.author),
                "hours_today": 0,
                "alerts_handled": 0,
                "commands_executed": 0,
                "consecutive_hours": 0,
                "last_break": None,
                "shift_start": get_now_pst().isoformat()
            }
        
        activity = self.data["mod_activity"][user_id]
        activity["hours_today"] += hours_worked
        activity["alerts_handled"] += alerts
        activity["commands_executed"] += commands
        activity["last_update"] = get_now_pst().isoformat()
        
        fatigue_score = self.calculate_fatigue(activity)
        self.data["fatigue_scores"][user_id] = fatigue_score
        
        self.save_data(self.data)
        
        # Determine status
        if fatigue_score > 0.8:
            status = "🔴 CRITICAL FATIGUE"
            color = discord.Color.dark_red()
        elif fatigue_score > 0.6:
            status = "🟠 HIGH FATIGUE"
            color = discord.Color.orange()
        else:
            status = "🟢 NORMAL"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title="⚠️ Activity Logged",
            description=f"User: {ctx.author.mention}",
            color=color
        )
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Fatigue Score", value=f"{fatigue_score:.2f}/1.00", inline=True)
        embed.add_field(name="Hours Worked", value=f"{activity['hours_today']:.1f}h", inline=True)
        embed.add_field(name="Alerts Handled", value=str(activity["alerts_handled"]), inline=True)
        embed.add_field(name="Commands Run", value=str(activity["commands_executed"]), inline=True)
        
        if fatigue_score > 0.7:
            embed.add_field(name="⚠️ Recommendation", value="Take a break. Response quality may degrade.", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="check_fatigue_level")
    async def check_fatigue_level(self, ctx, user: discord.Member = None):
        """Check fatigue level for user."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        target = user or ctx.author
        user_id = str(target.id)
        
        if user_id not in self.data["fatigue_scores"]:
            await ctx.send(f"No activity logged for {target.mention} yet.")
            return
        
        score = self.data["fatigue_scores"][user_id]
        activity = self.data["mod_activity"].get(user_id, {})
        
        # Determine level
        if score > 0.8:
            level = "🔴 CRITICAL"
            recommendation = "**URGENT:** Assign tasks to others. Enforce break time."
        elif score > 0.6:
            level = "🟠 HIGH"
            recommendation = "Monitor closely. Reduce alert volume if possible."
        elif score > 0.4:
            level = "🟡 MODERATE"
            recommendation = "Within normal limits. Continue monitoring."
        else:
            level = "🟢 HEALTHY"
            recommendation = "All clear. Continue normal operations."
        
        embed = discord.Embed(
            title="📊 Fatigue Assessment",
            description=f"User: {target.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Fatigue Level", value=level, inline=True)
        embed.add_field(name="Score", value=f"{score:.2f}/1.00", inline=True)
        embed.add_field(name="Hours Today", value=f"{activity.get('hours_today', 0):.1f}h", inline=True)
        embed.add_field(name="Alerts Handled", value=str(activity.get("alerts_handled", 0)), inline=True)
        embed.add_field(name="📋 Recommendation", value=recommendation, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="assign_on_call")
    async def assign_on_call(self, ctx, user: discord.Member, hours: int = 4):
        """Assign user to on-call duty."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        user_id = str(user.id)
        
        on_call_assignment = {
            "user": str(user),
            "assigned_at": get_now_pst().isoformat(),
            "duration_hours": hours,
            "status": "ACTIVE",
            "alerts_responded": 0
        }
        
        self.data["on_call_schedule"][user_id] = on_call_assignment
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="📞 On-Call Assignment",
            description=f"User: {user.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Duration", value=f"{hours} hours", inline=True)
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        embed.add_field(name="Start Time", value=on_call_assignment["assigned_at"], inline=False)
        
        try:
            dm_embed = discord.Embed(
                title="📞 You're On-Call",
                description=f"Assigned for {hours} hours",
                color=discord.Color.blue()
            )
            await user.send(embed=dm_embed)
        except:
            pass
        
        await ctx.send(embed=embed)

    @commands.command(name="burnout_assessment")
    async def burnout_assessment(self, ctx):
        """Run burnout risk assessment for team."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        at_risk = 0
        healthy = 0
        
        for user_id, score in self.data["fatigue_scores"].items():
            if score > 0.65:
                at_risk += 1
            else:
                healthy += 1
        
        embed = discord.Embed(
            title="🧠 Team Burnout Assessment",
            color=discord.Color.orange() if at_risk > 0 else discord.Color.green()
        )
        embed.add_field(name="Total Members", value=str(at_risk + healthy), inline=True)
        embed.add_field(name="At Risk", value=f"{at_risk} 🔴", inline=True)
        embed.add_field(name="Healthy", value=f"{healthy} 🟢", inline=True)
        embed.add_field(name="Risk Percentage", value=f"{(at_risk/(max(at_risk+healthy,1))*100):.1f}%", inline=True)
        
        if at_risk > 0:
            embed.add_field(
                name="⚠️ Actions Recommended",
                value="• Rotate on-call assignments\n• Reduce alert volume\n• Encourage breaks\n• Schedule team wellness check",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="enforce_break")
    async def enforce_break(self, ctx, user: discord.Member, minutes: int = 30):
        """Enforce break time for fatigued user."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        user_id = str(user.id)
        
        self.data["throttled_users"][user_id] = {
            "user": str(user),
            "throttle_reason": "FATIGUE_BREAK",
            "throttle_until": (get_now_pst() + timedelta(minutes=minutes)).isoformat(),
            "tasks_blocked": 0
        }
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🛑 Break Enforced",
            description=f"User: {user.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
        embed.add_field(name="Reason", value="Fatigue Detection", inline=True)
        embed.add_field(name="Tasks Blocked", value="Moderation actions will be throttled", inline=False)
        
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(
                title="🛑 Break Enforcement",
                description=f"You've been flagged for fatigue. Take a {minutes}-minute break.",
                color=discord.Color.orange()
            )
            await user.send(embed=dm_embed)
        except:
            pass

    @commands.command(name="wellness_check")
    async def wellness_check(self, ctx):
        """Run team wellness check survey."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        embed = discord.Embed(
            title="💚 Team Wellness Check",
            description="Anonymous feedback survey",
            color=discord.Color.green()
        )
        embed.add_field(name="Questions", value="1. How is your energy level?\n2. Any stressors affecting performance?\n3. Need time off or support?", inline=False)
        embed.add_field(name="Instructions", value="React to this message with: 😊 (good) 😐 (okay) 😔 (struggling)", inline=False)
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("😊")
        await msg.add_reaction("😐")
        await msg.add_reaction("😔")

    @commands.command(name="fatigue_report")
    async def fatigue_report(self, ctx):
        """Generate team fatigue and wellness report."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        avg_score = sum(self.data["fatigue_scores"].values()) / max(len(self.data["fatigue_scores"]), 1)
        
        embed = discord.Embed(
            title="📈 Fatigue & Wellness Report",
            color=discord.Color.blue()
        )
        embed.add_field(name="Team Avg Fatigue", value=f"{avg_score:.2f}/1.00", inline=True)
        embed.add_field(name="Tracked Members", value=str(len(self.data["mod_activity"])), inline=True)
        embed.add_field(name="At-Risk Members", value=str(len(self.data["burnout_signals"])), inline=True)
        embed.add_field(name="Currently On-Call", value=str(len(self.data["on_call_schedule"])), inline=True)
        
        if avg_score > 0.6:
            embed.add_field(
                name="🔴 Team Status",
                value="Team fatigue is elevated. Consider: rest days, workload redistribution, stress management resources.",
                inline=False
            )
        else:
            embed.add_field(name="🟢 Team Status", value="Healthy fatigue levels. Continue monitoring.", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FatigueMonitoringCog(bot))
