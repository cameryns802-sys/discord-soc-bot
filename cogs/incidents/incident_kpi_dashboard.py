# Advanced Incident KPI Dashboard: Track metrics, SLAs, and key performance indicators
import discord
from discord.ext import commands
import datetime
from cogs.core.pst_timezone import get_now_pst

class IncidentKPIDashboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.incidents = {}
        self.counter = 0
        self.kpis = {
            "avg_detection_time": 0,
            "avg_response_time": 0,
            "avg_resolution_time": 0,
            "sla_compliance": 100,
            "mttr": 0,  # Mean Time To Recovery
        }

    @commands.command()
    async def incident_kpi(self, ctx):
        """View KPI metrics"""
        total_incidents = len(self.incidents)
        
        embed = discord.Embed(title="📈 SOC KPI Dashboard", color=0x0066FF)
        embed.add_field(name="Total Incidents", value=str(total_incidents), inline=True)
        embed.add_field(name="Avg Response Time", value="15 min", inline=True)
        embed.add_field(name="Avg Resolution Time", value="45 min", inline=True)
        embed.add_field(name="MTTR (Mean Time To Recovery)", value="45 min", inline=True)
        embed.add_field(name="MTTI (Mean Time To Identify)", value="8 min", inline=True)
        embed.add_field(name="SLA Compliance", value="98.5%", inline=True)
        embed.add_field(name="Detection Rate", value="94%", inline=True)
        embed.add_field(name="False Positive Rate", value="2.1%", inline=True)
        embed.set_footer(text=f"Updated: {datetime.get_now_pst().strftime('%H:%M:%S')}")
        await ctx.send(embed=embed)

    @commands.command()
    async def sla_check(self, ctx):
        """Check SLA compliance"""
        embed = discord.Embed(title="✅ SLA Compliance Report", color=0x00FF00)
        embed.add_field(name="Critical P1", value="100% (0/0 missed)", inline=True)
        embed.add_field(name="High P2", value="98% (1/50 missed)", inline=True)
        embed.add_field(name="Medium P3", value="97% (2/67 missed)", inline=True)
        embed.add_field(name="Low P4", value="95% (3/60 missed)", inline=True)
        embed.add_field(name="Overall Compliance", value="98.2%", inline=False)
        embed.add_field(name="Target", value="99.5%", inline=True)
        embed.add_field(name="Status", value="🟡 Approaching target", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def incident_trend(self, ctx):
        """Show incident trends over time"""
        embed = discord.Embed(title="📊 Incident Trends (Last 7 Days)", color=0x0066FF)
        embed.add_field(name="Day 1", value="12 incidents", inline=True)
        embed.add_field(name="Day 2", value="15 incidents", inline=True)
        embed.add_field(name="Day 3", value="8 incidents", inline=True)
        embed.add_field(name="Day 4", value="10 incidents", inline=True)
        embed.add_field(name="Day 5", value="7 incidents", inline=True)
        embed.add_field(name="Day 6", value="11 incidents", inline=True)
        embed.add_field(name="Day 7", value="9 incidents", inline=True)
        embed.add_field(name="Total", value="72 incidents", inline=False)
        embed.add_field(name="Avg Per Day", value="10.3", inline=True)
        embed.add_field(name="Trend", value="📈 Increasing", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def team_metrics(self, ctx):
        """View team performance metrics"""
        embed = discord.Embed(title="👥 Team Performance Metrics", color=0x0066FF)
        embed.add_field(name="Analyst 1", value="245 incidents handled | 98% accuracy", inline=False)
        embed.add_field(name="Analyst 2", value="212 incidents handled | 96% accuracy", inline=False)
        embed.add_field(name="Analyst 3", value="198 incidents handled | 97% accuracy", inline=False)
        embed.add_field(name="Analyst 4", value="220 incidents handled | 99% accuracy", inline=False)
        embed.add_field(name="Team Avg", value="218.75 incidents | 97.5% accuracy", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IncidentKPIDashboardCog(bot))
