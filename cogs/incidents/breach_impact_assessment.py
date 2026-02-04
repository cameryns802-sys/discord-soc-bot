"""
Breach Impact Assessment System - Quantify damage and impact from security incidents
Calculate financial loss, data exposure, operational impact, and recovery costs
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
from cogs.core.pst_timezone import get_now_pst

class BreachImpactAssessment(commands.Cog):
    """Breach impact quantification and damage assessment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.assessments_file = 'data/breach_assessments.json'
        self.load_data()
    
    def load_data(self):
        """Load assessment data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.assessments_file):
            with open(self.assessments_file, 'w') as f:
                json.dump({}, f)
    
    def get_assessments(self, guild_id):
        """Get breach assessments"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_assessments(self, guild_id, assessments):
        """Save assessments"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = assessments
        with open(self.assessments_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_breach_cost(self, records_exposed, avg_record_value, downtime_hours, employee_count):
        """Calculate total breach cost"""
        # Data exposure cost (average $150-250 per record)
        data_loss_cost = records_exposed * avg_record_value
        
        # Operational downtime cost (avg $10k-20k per hour)
        downtime_cost = downtime_hours * 15000
        
        # Incident response & recovery
        response_cost = min(500000, records_exposed * 50)
        
        # Notification & remediation
        notification_cost = records_exposed * 2
        
        # Reputational & SLA penalties
        reputational_cost = min(1000000, records_exposed * 100)
        
        total = data_loss_cost + downtime_cost + response_cost + notification_cost + reputational_cost
        
        return {
            'total': total,
            'data_loss': data_loss_cost,
            'downtime': downtime_cost,
            'response': response_cost,
            'notification': notification_cost,
            'reputational': reputational_cost
        }
    
    async def _createassessment_logic(self, ctx, incident_name: str, records_exposed: int, downtime_hours: int = 1):
        """Create breach impact assessment"""
        assessments = self.get_assessments(ctx.guild.id)
        
        assessment_id = f"BIA-{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate impact
        costs = self.calculate_breach_cost(records_exposed, 200, downtime_hours, 50)
        
        assessment = {
            'id': assessment_id,
            'name': incident_name,
            'created_at': get_now_pst().isoformat(),
            'records_exposed': records_exposed,
            'downtime_hours': downtime_hours,
            'impact_scores': {
                'data_loss': min(100, (records_exposed / 100000) * 100),
                'operational': min(100, (downtime_hours / 48) * 100),
                'reputational': min(100, (records_exposed / 50000) * 100),
                'financial': min(100, (costs['total'] / 5000000) * 100)
            },
            'costs': costs,
            'affected_entities': {
                'customers': min(records_exposed, 10000),
                'employees': 50,
                'partners': 8
            },
            'status': 'active',
            'containment_status': 'in_progress',
            'recovery_estimate_days': max(1, downtime_hours // 24)
        }
        
        assessments[assessment_id] = assessment
        self.save_assessments(ctx.guild.id, assessments)
        
        embed = discord.Embed(
            title="📊 Breach Impact Assessment",
            description=f"**{incident_name}**",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Assessment ID", value=f"`{assessment_id}`", inline=True)
        embed.add_field(name="Status", value="🔴 ACTIVE", inline=True)
        embed.add_field(name="Created", value=get_now_pst().strftime('%Y-%m-%d %H:%M'), inline=True)
        
        embed.add_field(name="Impact Summary", value="━" * 25, inline=False)
        embed.add_field(name="Records Exposed", value=f"👥 {records_exposed:,}", inline=True)
        embed.add_field(name="Downtime", value=f"⏱️ {downtime_hours} hour(s)", inline=True)
        embed.add_field(name="Recovery Est.", value=f"📅 {assessment['recovery_estimate_days']} day(s)", inline=True)
        
        embed.add_field(name="Impact Scores", value="━" * 25, inline=False)
        embed.add_field(name="🔴 Data Loss", value=f"{assessment['impact_scores']['data_loss']:.0f}/100", inline=True)
        embed.add_field(name="🟠 Operational", value=f"{assessment['impact_scores']['operational']:.0f}/100", inline=True)
        embed.add_field(name="🟠 Reputational", value=f"{assessment['impact_scores']['reputational']:.0f}/100", inline=True)
        
        embed.add_field(name="💰 Financial Impact", value="━" * 25, inline=False)
        embed.add_field(
            name="Total Estimated Cost",
            value=f"💵 ${costs['total']:,.0f}",
            inline=False
        )
        embed.add_field(name="Data Loss", value=f"${costs['data_loss']:,.0f}", inline=True)
        embed.add_field(name="Downtime Cost", value=f"${costs['downtime']:,.0f}", inline=True)
        embed.add_field(name="Response Cost", value=f"${costs['response']:,.0f}", inline=True)
        
        embed.set_footer(text="Use !breachdetail to view full assessment")
        
        await ctx.send(embed=embed)
    
    async def _breachdetail_logic(self, ctx, assessment_id: str):
        """Show breach assessment details"""
        assessments = self.get_assessments(ctx.guild.id)
        
        assessment_id = assessment_id.upper()
        if not assessment_id.startswith('BIA-'):
            assessment_id = f"BIA-{assessment_id}"
        
        assessment = assessments.get(assessment_id)
        if not assessment:
            await ctx.send(f"❌ Assessment not found: {assessment_id}")
            return
        
        embed = discord.Embed(
            title=f"📊 {assessment['name']}",
            description=f"Assessment ID: {assessment_id}",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Status", value=assessment['status'].upper(), inline=True)
        embed.add_field(name="Containment", value=assessment['containment_status'].title(), inline=True)
        embed.add_field(name="Created", value=datetime.fromisoformat(assessment['created_at']).strftime('%Y-%m-%d %H:%M'), inline=True)
        
        embed.add_field(name="Exposure Details", value="━" * 25, inline=False)
        embed.add_field(name="👥 Records Exposed", value=f"{assessment['records_exposed']:,}", inline=True)
        embed.add_field(name="⏱️ Downtime", value=f"{assessment['downtime_hours']}h", inline=True)
        embed.add_field(name="🔄 Recovery Est.", value=f"{assessment['recovery_estimate_days']}d", inline=True)
        
        embed.add_field(name="Affected Entities", value="━" * 25, inline=False)
        for entity, count in assessment['affected_entities'].items():
            embed.add_field(name=entity.title(), value=f"👤 {count}", inline=True)
        
        embed.add_field(name="Impact Scores", value="━" * 25, inline=False)
        impact = assessment['impact_scores']
        embed.add_field(name="🔴 Data Loss", value=f"{impact['data_loss']:.0f}/100", inline=True)
        embed.add_field(name="🟠 Operational", value=f"{impact['operational']:.0f}/100", inline=True)
        embed.add_field(name="🟠 Reputational", value=f"{impact['reputational']:.0f}/100", inline=True)
        embed.add_field(name="💰 Financial", value=f"{impact['financial']:.0f}/100", inline=True)
        
        embed.add_field(name="Financial Breakdown", value="━" * 25, inline=False)
        costs = assessment['costs']
        embed.add_field(
            name="💵 Total Cost",
            value=f"${costs['total']:,.0f}",
            inline=False
        )
        embed.add_field(name="Data Loss", value=f"${costs['data_loss']:,.0f}", inline=True)
        embed.add_field(name="Downtime", value=f"${costs['downtime']:,.0f}", inline=True)
        embed.add_field(name="Response", value=f"${costs['response']:,.0f}", inline=True)
        embed.add_field(name="Notification", value=f"${costs['notification']:,.0f}", inline=True)
        embed.add_field(name="Reputational", value=f"${costs['reputational']:,.0f}", inline=True)
        
        await ctx.send(embed=embed)
    
    async def _breachhistory_logic(self, ctx):
        """Show breach assessment history"""
        assessments = self.get_assessments(ctx.guild.id)
        
        if not assessments:
            await ctx.send("📭 No breach assessments recorded.")
            return
        
        # Sort by creation date
        sorted_assessments = sorted(assessments.values(), key=lambda a: a['created_at'], reverse=True)
        
        embed = discord.Embed(
            title="📊 Breach Assessment History",
            description=f"{len(sorted_assessments)} assessment(s)",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        # Summary
        total_cost = sum(a['costs']['total'] for a in sorted_assessments)
        total_records = sum(a['records_exposed'] for a in sorted_assessments)
        
        embed.add_field(name="Aggregate Impact", value="━" * 25, inline=False)
        embed.add_field(name="Total Financial Impact", value=f"💵 ${total_cost:,.0f}", inline=True)
        embed.add_field(name="Total Records Exposed", value=f"👥 {total_records:,}", inline=True)
        embed.add_field(name="Active Assessments", value=f"🔴 {sum(1 for a in sorted_assessments if a['status'] == 'active')}", inline=True)
        
        embed.add_field(name="Recent Assessments", value="━" * 25, inline=False)
        
        for assessment in sorted_assessments[:8]:
            status_icon = "🔴" if assessment['status'] == 'active' else "✅"
            embed.add_field(
                name=f"{status_icon} {assessment['name']} ({assessment['id']})",
                value=f"Cost: ${assessment['costs']['total']:,.0f} | Records: {assessment['records_exposed']:,} | Recovery: {assessment['recovery_estimate_days']}d",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='createassessment')
    async def createassessment_prefix(self, ctx, incident_name: str, records_exposed: int, downtime_hours: int = 1):
        """Create breach assessment - Prefix command"""
        await self._createassessment_logic(ctx, incident_name, records_exposed, downtime_hours)
    
    @commands.command(name='breachdetail')
    async def breachdetail_prefix(self, ctx, assessment_id: str):
        """Show breach details - Prefix command"""
        await self._breachdetail_logic(ctx, assessment_id)
    
    @commands.command(name='breachhistory')
    async def breachhistory_prefix(self, ctx):
        """Show breach history - Prefix command"""
        await self._breachhistory_logic(ctx)

async def setup(bot):
    await bot.add_cog(BreachImpactAssessment(bot))
