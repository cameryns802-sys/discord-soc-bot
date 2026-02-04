import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class BreachImpactAssessorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assessments_file = "data/breach_assessments.json"
        self.load_assessments()

    def load_assessments(self):
        if os.path.exists(self.assessments_file):
            with open(self.assessments_file) as f:
                self.assessments = json.load(f)
        else:
            self.assessments = []

    def save_assessments(self):
        os.makedirs("data", exist_ok=True)
        with open(self.assessments_file, 'w') as f:
            json.dump(self.assessments, f, indent=2)

    @commands.command()
    async def assessbreach(self, ctx, affected_accounts: int, severity: str):
        """Assess potential impact of a breach (severity: low/medium/high/critical)"""
        if severity.lower() not in ["low", "medium", "high", "critical"]:
            await ctx.send("❌ Severity must be: low, medium, high, or critical")
            return
        
        severity_map = {
            "low": (1, discord.Color.green()),
            "medium": (2, discord.Color.yellow()),
            "high": (3, discord.Color.orange()),
            "critical": (4, discord.Color.red())
        }
        
        severity_level, color = severity_map[severity.lower()]
        blast_radius = min(affected_accounts * severity_level * 1.5, 100)
        
        assessment = {
            "id": len(self.assessments) + 1,
            "affected_accounts": affected_accounts,
            "severity": severity.lower(),
            "blast_radius": blast_radius,
            "estimated_cost": affected_accounts * (500 * severity_level),
            "created": get_now_pst().isoformat()
        }
        self.assessments.append(assessment)
        self.save_assessments()
        
        embed = discord.Embed(
            title="🚨 Breach Impact Assessment",
            color=color
        )
        embed.add_field(name="Affected Accounts", value=str(affected_accounts), inline=True)
        embed.add_field(name="Severity Level", value=severity.upper(), inline=True)
        embed.add_field(name="Assessment ID", value=f"#{assessment['id']}", inline=True)
        embed.add_field(name="Blast Radius", value=f"{blast_radius:.1f}%", inline=True)
        embed.add_field(name="Estimated Cost", value=f"${assessment['estimated_cost']:,}", inline=True)
        
        if severity.lower() == "critical":
            embed.add_field(
                name="⚠️ CRITICAL ACTION REQUIRED",
                value="Activate incident response playbook BREACH-001",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def blastradius(self, ctx, affected_accounts: int):
        """Calculate blast radius for affected accounts"""
        blast_radius = min(affected_accounts * 2, 100)
        
        embed = discord.Embed(
            title="📊 Blast Radius Calculation",
            color=discord.Color.orange()
        )
        embed.add_field(name="Affected Accounts", value=str(affected_accounts), inline=True)
        embed.add_field(name="Blast Radius", value=f"{blast_radius:.1f}%", inline=True)
        embed.add_field(
            name="Exposed Systems",
            value=f"Estimated {int(affected_accounts * 0.7)} systems impacted",
            inline=False
        )
        embed.add_field(
            name="Risk Assessment",
            value="🟡 MEDIUM - Containment possible within 2-4 hours",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def costanalysis(self, ctx, assessment_id: int):
        """Analyze financial impact of a breach assessment"""
        assessment = next((a for a in self.assessments if a["id"] == assessment_id), None)
        if not assessment:
            await ctx.send("❌ Assessment not found")
            return
        
        cost = assessment["estimated_cost"]
        response_cost = cost * 0.15
        recovery_cost = cost * 0.25
        total = cost + response_cost + recovery_cost
        
        embed = discord.Embed(
            title=f"💰 Cost Analysis - Assessment #{assessment_id}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Direct Loss", value=f"${cost:,.0f}", inline=True)
        embed.add_field(name="Response Cost", value=f"${response_cost:,.0f}", inline=True)
        embed.add_field(name="Recovery Cost", value=f"${recovery_cost:,.0f}", inline=True)
        embed.add_field(name="**Total Estimated Cost**", value=f"**${total:,.0f}**", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def assessmentlist(self, ctx):
        """List all breach assessments"""
        if not self.assessments:
            await ctx.send("❌ No assessments found")
            return
        
        embed = discord.Embed(
            title="📋 Breach Impact Assessments",
            color=discord.Color.blue()
        )
        
        for a in self.assessments[-10:]:
            embed.add_field(
                name=f"#{a['id']} - {a['severity'].upper()}",
                value=f"{a['affected_accounts']} accounts | ${a['estimated_cost']:,}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BreachImpactAssessorCog(bot))
