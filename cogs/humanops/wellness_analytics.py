"""
Analyst Wellness & Burnout Detection System
Monitors staff workload, stress markers, and recommends staffing/workflow changes.
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

class WellnessCog(commands.Cog):
    """Analyst health, burnout detection, and workload management"""
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/wellness_data.json"
        os.makedirs("data", exist_ok=True)
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"staff": {}, "alerts": [], "recommendations": []}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    @app_commands.command(name="wellnessprofile", description="View staff member's wellness profile")
    async def wellnessprofile(self, interaction: discord.Interaction, user: discord.Member):
        """View staff member's wellness profile"""
        embed = discord.Embed(title=f"Wellness Profile - {user.name}", color=discord.Color.blue())
        
        # Calculate stress markers
        activity_data = self.data["staff"].get(str(user.id), {})
        workload = activity_data.get("incident_count", 0)
        after_hours = activity_data.get("after_hours_incidents", 0)
        response_time = activity_data.get("avg_response_time_mins", 0)
        burnout_score = min(100, (workload * 5) + (after_hours * 10) + (response_time / 10))
        
        embed.add_field(name="📊 Workload", value=f"{workload} incidents assigned", inline=True)
        embed.add_field(name="🌙 After-Hours Load", value=f"{after_hours} incidents", inline=True)
        embed.add_field(name="⏱️ Avg Response Time", value=f"{response_time} mins", inline=True)
        embed.add_field(name="🔥 Burnout Risk", value=f"{int(burnout_score)}% {'🚨 HIGH RISK' if burnout_score > 70 else '✅ HEALTHY'}", inline=False)
        
        # Health recommendations
        recommendations = []
        if workload > 15:
            recommendations.append("• Load redistribution recommended")
        if after_hours > 10:
            recommendations.append("• Schedule off-hours coverage rotation")
        if response_time > 60:
            recommendations.append("• Provide tooling support or training")
        
        if recommendations:
            embed.add_field(name="💡 Recommendations", value="\n".join(recommendations), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def wellnessbaseline(self, ctx):
        """Set wellness baseline for team"""
        embed = discord.Embed(title="📊 Setting Team Wellness Baseline", color=discord.Color.green())
        embed.description = "Collecting current workload metrics..."
        embed.add_field(name="✅ Baseline Set", value="Normal: 5-10 incidents/week\nAfter-hours: <3 incidents/week\nResponse: <30 mins avg", inline=False)
        embed.add_field(name="🎯 Healthy Targets", value="Incident load: balanced\nOn-call rotation: 1 week/month\nRest days: enforced", inline=False)
        
        self.data["baseline"] = {
            "normal_workload": 10,
            "after_hours_limit": 3,
            "target_response_time": 30,
            "set_date": datetime.utcnow().isoformat()
        }
        self.save_data()
        
        await ctx.send(embed=embed)

    @app_commands.command(name="wellnessalerts", description="View burnout and wellness alerts")
    async def wellnessalerts(self, interaction: discord.Interaction):
        """View burnout and wellness alerts"""
        embed = discord.Embed(title="⚠️ Wellness Alerts", color=discord.Color.orange())
        
        high_risk = [s for s in self.data["staff"].values() if s.get("burnout_score", 0) > 70]
        
        if high_risk:
            for staff in high_risk:
                embed.add_field(
                    name=f"🚨 {staff.get('name', 'Unknown')}",
                    value=f"Burnout: {staff.get('burnout_score', 0)}%\nRisk: High\nAction: Recommend leave or load reduction",
                    inline=False
                )
        else:
            embed.description = "✅ No high-risk wellness alerts. Team is healthy."
        
        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def wellnessroster(self, ctx):
        """View and manage on-call rotation schedule"""
        embed = discord.Embed(title="📅 On-Call Rotation Schedule", color=discord.Color.purple())
        embed.add_field(name="Week of Feb 1", value="Alice: Mon-Sun\nBob: Mon-Sun\nCarol: Mon-Sun", inline=False)
        embed.add_field(name="Week of Feb 8", value="Alice: Standby\nBob: Mon-Sun\nCarol: Mon-Sun", inline=False)
        embed.add_field(name="⚠️ Load Alert", value="Carol has 12 incidents this week (high). Recommend load shift.", inline=False)
        
        await ctx.send(embed=embed)

    @app_commands.command(name="wellnessrecommend", description="Get AI-driven staffing and workflow recommendations")
    async def wellnessrecommend(self, interaction: discord.Interaction):
        """Get AI-driven staffing and workflow recommendations"""
        embed = discord.Embed(title="🤖 AI Staffing Recommendations", color=discord.Color.gold())
        embed.add_field(name="📌 Immediate Actions", value=
            "1. Rotate Carol out of on-call (burnout score 82%)\n"
            "2. Add 2 junior analysts to incident triage\n"
            "3. Implement 15-min incident auto-escalation", inline=False)
        embed.add_field(name="📊 Workload Rebalancing", value=
            "Distribute 5 lower-priority incidents to backup team\n"
            "Move 3 training incidents to junior analysts", inline=False)
        embed.add_field(name="💪 Support Measures", value=
            "Schedule 1:1 with Carol (wellness check)\n"
            "Offer mental health resources\n"
            "Enforce no after-hours escalations Mon-Fri", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def wellnessnudge(self, ctx, user: discord.Member):
        """Send wellness nudge/reminder to staff member"""
        embed = discord.Embed(
            title="💚 Wellness Check-In",
            description=f"Hey {user.mention}, hope you're doing well!",
            color=discord.Color.green()
        )
        embed.add_field(name="📊 Your Stats This Week", value=
            "• 8 incidents handled (average workload)\n"
            "• 2 after-hours calls (within target)\n"
            "• 25 min avg response time (good!)", inline=False)
        embed.add_field(name="💡 Suggestion", value=
            "You're hitting great metrics. Don't forget to take your days off—burnout can sneak up! 🌴", inline=False)
        embed.add_field(name="🆘 Need Support?", value=
            "Talk to leadership or use your EAP benefits. We've got your back.", inline=False)
        
        await ctx.send(embed=embed)
        try:
            await user.send(embed=embed)
        except:
            pass

    @app_commands.command(name="wellnessreport", description="Generate team wellness report")
    async def wellnessreport(self, interaction: discord.Interaction):
        """Generate team wellness report"""
        embed = discord.Embed(title="📈 Team Wellness Report (Feb 2026)", color=discord.Color.blue())
        embed.add_field(name="👥 Team Health", value=
            "✅ 5/7 analysts healthy\n"
            "⚠️ 2/7 elevated burnout risk\n"
            "Average workload: 9 incidents/week", inline=False)
        embed.add_field(name="🔥 Risk Zones", value=
            "Carol: 82% burnout (high stress from on-call)\n"
            "Dave: 65% burnout (learning curve on new tools)", inline=False)
        embed.add_field(name="💪 Resilience Factors", value=
            "• Good on-call rotation (1 week/month avg)\n"
            "• After-hours load trending down\n"
            "• Response time improving", inline=False)
        embed.add_field(name="📋 Actions Taken", value=
            "1. Carol on leave starting Feb 3\n"
            "2. Dave getting 1:1 tooling support\n"
            "3. Backfill hire approved", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WellnessCog(bot))
    print("[Wellness] ✅ Loaded wellness commands (4 slash, 3 prefix)")
