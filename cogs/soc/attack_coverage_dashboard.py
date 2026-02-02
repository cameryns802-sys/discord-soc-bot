import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from typing import Dict, List

class AttackCoverageDashboard(commands.Cog):
    """
    MITRE ATT&CK Coverage Dashboard
    
    Executive dashboard showing ATT&CK coverage, detection gaps,
    and security posture against the ATT&CK framework.
    
    Features:
    - Coverage percentage by tactic
    - Detection gap analysis
    - Trend analysis over time
    - Executive-ready visualizations
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/attack_coverage'
        os.makedirs(self.data_dir, exist_ok=True)
        self.coverage_data = self.load_coverage_data()
    
    def load_coverage_data(self) -> Dict:
        """Load coverage data from JSON storage"""
        try:
            with open(f'{self.data_dir}/coverage.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_coverage_data(self):
        """Save coverage data to JSON storage"""
        with open(f'{self.data_dir}/coverage.json', 'w') as f:
            json.dump(self.coverage_data, f, indent=2)
    
    def calculate_coverage_percentage(self, guild_id: str) -> float:
        """Calculate overall ATT&CK coverage percentage"""
        # Get mapper cog
        mapper = self.bot.get_cog('MitreAttackMapper')
        if not mapper:
            return 0.0
        
        # Total possible techniques (using sample set)
        total_techniques = len(mapper.techniques)
        
        # Unique techniques detected
        if str(guild_id) not in mapper.mappings:
            return 0.0
        
        detected = set()
        for mapping in mapper.mappings[str(guild_id)]:
            detected.add(mapping['technique_id'])
        
        coverage = (len(detected) / total_techniques) * 100
        return round(coverage, 1)
    
    @commands.command(name='attack_dashboard')
    @commands.has_permissions(administrator=True)
    async def attack_dashboard_cmd(self, ctx):
        """Show comprehensive ATT&CK coverage dashboard"""
        coverage_pct = self.calculate_coverage_percentage(ctx.guild.id)
        
        # Get mapper cog for detailed stats
        mapper = self.bot.get_cog('MitreAttackMapper')
        if not mapper:
            await ctx.send("❌ MITRE ATT&CK Mapper not loaded.")
            return
        
        tactic_coverage = mapper.get_coverage_by_tactic(ctx.guild.id)
        
        embed = discord.Embed(
            title="🎯 ATT&CK Coverage Dashboard",
            description=f"**Overall Coverage**: {coverage_pct}%",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Coverage indicator
        if coverage_pct >= 70:
            embed.add_field(name="📊 Status", value="🟢 **EXCELLENT** Coverage", inline=False)
        elif coverage_pct >= 40:
            embed.add_field(name="📊 Status", value="🟡 **MODERATE** Coverage", inline=False)
        else:
            embed.add_field(name="📊 Status", value="🔴 **LIMITED** Coverage", inline=False)
        
        # Tactic coverage
        if tactic_coverage:
            top_tactics = sorted(tactic_coverage.items(), key=lambda x: x[1], reverse=True)[:5]
            tactic_str = '\n'.join([f"**{mapper.tactic_names.get(t, 'Unknown')}**: {c} detections" 
                                    for t, c in top_tactics])
            embed.add_field(name="📂 Top Covered Tactics", value=tactic_str, inline=False)
        
        # Total mappings
        total_mappings = len(mapper.mappings.get(str(ctx.guild.id), []))
        embed.add_field(name="📈 Total Mappings", value=str(total_mappings), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coverage_report')
    @commands.has_permissions(administrator=True)
    async def coverage_report_cmd(self, ctx):
        """Generate detailed ATT&CK coverage report"""
        mapper = self.bot.get_cog('MitreAttackMapper')
        if not mapper:
            await ctx.send("❌ MITRE ATT&CK Mapper not loaded.")
            return
        
        coverage_pct = self.calculate_coverage_percentage(ctx.guild.id)
        tactic_coverage = mapper.get_coverage_by_tactic(ctx.guild.id)
        
        embed = discord.Embed(
            title="📊 ATT&CK Coverage Report",
            description=f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="🎯 Overall Coverage", value=f"**{coverage_pct}%**", inline=True)
        embed.add_field(name="📂 Tactics Covered", value=str(len(tactic_coverage)), inline=True)
        embed.add_field(name="📈 Total Detections", value=str(sum(tactic_coverage.values())), inline=True)
        
        # Coverage breakdown
        for tactic_id in mapper.tactics[:5]:  # First 5 tactics
            tactic_name = mapper.tactic_names.get(tactic_id, 'Unknown')
            count = tactic_coverage.get(tactic_id, 0)
            status = '✅' if count > 0 else '❌'
            
            embed.add_field(
                name=f"{status} {tactic_name}",
                value=f"{count} detections" if count > 0 else "No coverage",
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AttackCoverageDashboard(bot))
