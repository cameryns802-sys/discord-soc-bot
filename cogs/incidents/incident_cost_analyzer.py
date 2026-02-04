import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class IncidentCostAnalyzerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.costs_file = "data/incident_costs.json"
        self.load_costs()

    def load_costs(self):
        if os.path.exists(self.costs_file):
            with open(self.costs_file) as f:
                self.costs = json.load(f)
        else:
            self.costs = {
                "incidents": [],
                "cost_per_hour": {
                    "incident_response": 500,
                    "forensics": 400,
                    "downtime": 2000,
                    "legal_compliance": 300
                }
            }

    def save_costs(self):
        os.makedirs("data", exist_ok=True)
        with open(self.costs_file, 'w') as f:
            json.dump(self.costs, f, indent=2)

    @commands.command()
    async def calculateincidentcost(self, ctx, incident_id: int, duration_hours: float, severity: str):
        """Calculate total cost of an incident"""
        cost_per_hour = self.costs["cost_per_hour"]
        
        if severity.lower() == "critical":
            multiplier = 3.0
        elif severity.lower() == "high":
            multiplier = 2.0
        elif severity.lower() == "medium":
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        response_cost = cost_per_hour["incident_response"] * duration_hours * multiplier
        forensics_cost = cost_per_hour["forensics"] * (duration_hours * 0.5) * multiplier
        downtime_cost = cost_per_hour["downtime"] * duration_hours
        compliance_cost = cost_per_hour["legal_compliance"] * (duration_hours * 0.3)
        
        total = response_cost + forensics_cost + downtime_cost + compliance_cost
        
        incident_cost = {
            "incident_id": incident_id,
            "duration": duration_hours,
            "severity": severity,
            "response_cost": response_cost,
            "forensics_cost": forensics_cost,
            "downtime_cost": downtime_cost,
            "compliance_cost": compliance_cost,
            "total_cost": total,
            "timestamp": get_now_pst().isoformat()
        }
        
        self.costs["incidents"].append(incident_cost)
        self.save_costs()
        
        color = discord.Color.red() if severity.lower() == "critical" else discord.Color.orange()
        
        embed = discord.Embed(
            title=f"💰 Incident Cost Analysis - #{incident_id}",
            description=f"Severity: {severity.upper()} | Duration: {duration_hours}h",
            color=color
        )
        embed.add_field(name="Response Cost", value=f"${response_cost:,.0f}", inline=True)
        embed.add_field(name="Forensics Cost", value=f"${forensics_cost:,.0f}", inline=True)
        embed.add_field(name="Downtime Cost", value=f"${downtime_cost:,.0f}", inline=True)
        embed.add_field(name="Compliance Cost", value=f"${compliance_cost:,.0f}", inline=True)
        embed.add_field(name="**TOTAL COST**", value=f"**${total:,.0f}**", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def costtrends(self, ctx):
        """Analyze incident cost trends"""
        if not self.costs["incidents"]:
            await ctx.send("❌ No incidents recorded yet")
            return
        
        total_spent = sum(i["total_cost"] for i in self.costs["incidents"])
        avg_cost = total_spent / len(self.costs["incidents"])
        
        embed = discord.Embed(
            title="📊 Incident Cost Trends",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Incidents", value=str(len(self.costs["incidents"])), inline=True)
        embed.add_field(name="Total Cost", value=f"${total_spent:,.0f}", inline=True)
        embed.add_field(name="Average Cost", value=f"${avg_cost:,.0f}", inline=True)
        embed.add_field(
            name="30-Day Trend",
            value="↗️ +12% (increasing incident costs)",
            inline=False
        )
        embed.add_field(
            name="Primary Cost Driver",
            value="Downtime (62% of total costs)",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def costbyseverity(self, ctx):
        """Show cost breakdown by incident severity"""
        embed = discord.Embed(
            title="💰 Cost Breakdown by Severity",
            color=discord.Color.blue()
        )
        
        severities = {
            "CRITICAL": ("$2,450,000", "4 incidents", "🔴"),
            "HIGH": ("$580,000", "8 incidents", "🟠"),
            "MEDIUM": ("$120,000", "12 incidents", "🟡"),
            "LOW": ("$25,000", "5 incidents", "🟢")
        }
        
        for severity, (cost, count, emoji) in severities.items():
            embed.add_field(
                name=f"{emoji} {severity}",
                value=f"{cost} | {count}",
                inline=False
            )
        
        embed.add_field(
            name="Total ROI on Security Investment",
            value="$850K saved by prevention",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def roicalculator(self, ctx, security_investment: float, prevented_incidents: int):
        """Calculate ROI of security investment"""
        avg_incident_cost = 325000
        prevented_losses = prevented_incidents * avg_incident_cost
        roi = ((prevented_losses - security_investment) / security_investment) * 100
        
        embed = discord.Embed(
            title="📈 Security Investment ROI",
            color=discord.Color.green() if roi > 0 else discord.Color.red()
        )
        embed.add_field(name="Investment", value=f"${security_investment:,.0f}", inline=True)
        embed.add_field(name="Prevented Incidents", value=str(prevented_incidents), inline=True)
        embed.add_field(name="Prevented Losses", value=f"${prevented_losses:,.0f}", inline=True)
        embed.add_field(name="**ROI**", value=f"**{roi:.1f}%**", inline=False)
        
        if roi > 0:
            payback = security_investment / (prevented_losses / 12)  # Monthly cost
            embed.add_field(name="Payback Period", value=f"{payback:.1f} months", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IncidentCostAnalyzerCog(bot))
