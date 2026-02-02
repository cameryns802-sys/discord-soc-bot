import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Set

class TechniqueGapAnalyzer(commands.Cog):
    """
    MITRE ATT&CK Technique Gap Analyzer
    
    Identifies blind spots in detection coverage by analyzing
    which ATT&CK techniques are not covered by current detections.
    
    Features:
    - Gap identification by tactic
    - Risk-based gap prioritization
    - Remediation recommendations
    - Executive gap reports
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/technique_gaps'
        os.makedirs(self.data_dir, exist_ok=True)
        self.gap_reports = self.load_gap_reports()
        
        # High-risk techniques (should be prioritized)
        self.high_risk_techniques = [
            'T1078',  # Valid Accounts
            'T1566',  # Phishing
            'T1110',  # Brute Force
            'T1486',  # Data Encrypted for Impact
            'T1041'   # Exfiltration Over C2 Channel
        ]
    
    def load_gap_reports(self) -> Dict:
        """Load gap reports from JSON storage"""
        try:
            with open(f'{self.data_dir}/gap_reports.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_gap_reports(self):
        """Save gap reports to JSON storage"""
        with open(f'{self.data_dir}/gap_reports.json', 'w') as f:
            json.dump(self.gap_reports, f, indent=2)
    
    def identify_gaps(self, guild_id: str) -> Dict[str, List[str]]:
        """
        Identify detection gaps by tactic
        
        Returns:
            Dict of tactic_id -> list of uncovered technique_ids
        """
        mapper = self.bot.get_cog('MitreAttackMapper')
        if not mapper:
            return {}
        
        # Get covered techniques
        covered = set()
        if str(guild_id) in mapper.mappings:
            for mapping in mapper.mappings[str(guild_id)]:
                covered.add(mapping['technique_id'])
        
        # Identify gaps by tactic
        gaps = {}
        for tech_id, tech_data in mapper.techniques.items():
            if tech_id not in covered:
                tactic = tech_data['tactic']
                if tactic not in gaps:
                    gaps[tactic] = []
                gaps[tactic].append(tech_id)
        
        return gaps
    
    def prioritize_gaps(self, guild_id: str) -> List[Dict]:
        """
        Prioritize gaps based on risk level
        
        Returns:
            List of gap dictionaries sorted by priority
        """
        gaps = self.identify_gaps(guild_id)
        mapper = self.bot.get_cog('MitreAttackMapper')
        
        prioritized = []
        
        for tactic_id, tech_ids in gaps.items():
            for tech_id in tech_ids:
                priority = 'HIGH' if tech_id in self.high_risk_techniques else 'MEDIUM'
                
                prioritized.append({
                    'technique_id': tech_id,
                    'technique_name': mapper.techniques.get(tech_id, {}).get('name', 'Unknown'),
                    'tactic_id': tactic_id,
                    'tactic_name': mapper.tactic_names.get(tactic_id, 'Unknown'),
                    'priority': priority
                })
        
        # Sort by priority
        prioritized.sort(key=lambda x: (x['priority'] != 'HIGH', x['technique_id']))
        
        return prioritized
    
    @commands.command(name='gap_analysis')
    @commands.has_permissions(administrator=True)
    async def gap_analysis_cmd(self, ctx):
        """Perform ATT&CK gap analysis and identify blind spots"""
        gaps = self.identify_gaps(ctx.guild.id)
        
        if not gaps:
            await ctx.send("✅ No gaps found - all techniques covered!")
            return
        
        mapper = self.bot.get_cog('MitreAttackMapper')
        
        total_gaps = sum(len(v) for v in gaps.values())
        
        embed = discord.Embed(
            title="🔍 ATT&CK Gap Analysis",
            description=f"**Total Gaps**: {total_gaps} uncovered techniques",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Show gaps by tactic
        for tactic_id, tech_ids in sorted(gaps.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            tactic_name = mapper.tactic_names.get(tactic_id, 'Unknown')
            
            # Show first 3 techniques
            tech_list = []
            for tech_id in tech_ids[:3]:
                tech_name = mapper.techniques.get(tech_id, {}).get('name', 'Unknown')
                priority = '🔴' if tech_id in self.high_risk_techniques else '🟡'
                tech_list.append(f"{priority} **{tech_id}**: {tech_name}")
            
            embed.add_field(
                name=f"📂 {tactic_name} ({len(tech_ids)} gaps)",
                value='\n'.join(tech_list) + (f"\n...and {len(tech_ids) - 3} more" if len(tech_ids) > 3 else ""),
                inline=False
            )
        
        embed.set_footer(text="🔴 High Priority | 🟡 Medium Priority")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='gap_priorities')
    @commands.has_permissions(administrator=True)
    async def gap_priorities_cmd(self, ctx):
        """Show prioritized list of detection gaps"""
        prioritized = self.prioritize_gaps(ctx.guild.id)
        
        if not prioritized:
            await ctx.send("✅ No gaps found!")
            return
        
        embed = discord.Embed(
            title="⚠️ Prioritized Detection Gaps",
            description="High-risk blind spots requiring immediate attention",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Show top 10 gaps
        for i, gap in enumerate(prioritized[:10], 1):
            priority_icon = '🔴' if gap['priority'] == 'HIGH' else '🟡'
            
            embed.add_field(
                name=f"{i}. {priority_icon} {gap['technique_id']}: {gap['technique_name']}",
                value=f"**Tactic**: {gap['tactic_name']}\n**Priority**: {gap['priority']}",
                inline=False
            )
        
        if len(prioritized) > 10:
            embed.set_footer(text=f"Showing top 10 of {len(prioritized)} gaps")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='gap_report')
    @commands.has_permissions(administrator=True)
    async def gap_report_cmd(self, ctx):
        """Generate executive gap report"""
        gaps = self.identify_gaps(ctx.guild.id)
        prioritized = self.prioritize_gaps(ctx.guild.id)
        
        # Count by priority
        high_priority = sum(1 for g in prioritized if g['priority'] == 'HIGH')
        medium_priority = len(prioritized) - high_priority
        
        # Save report
        report = {
            'guild_id': str(ctx.guild.id),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_gaps': len(prioritized),
            'high_priority_gaps': high_priority,
            'medium_priority_gaps': medium_priority,
            'gaps_by_tactic': {k: len(v) for k, v in gaps.items()}
        }
        
        if str(ctx.guild.id) not in self.gap_reports:
            self.gap_reports[str(ctx.guild.id)] = []
        
        self.gap_reports[str(ctx.guild.id)].append(report)
        self.save_gap_reports()
        
        embed = discord.Embed(
            title="📋 Executive Gap Report",
            description=f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="⚠️ Total Gaps", value=str(len(prioritized)), inline=True)
        embed.add_field(name="🔴 High Priority", value=str(high_priority), inline=True)
        embed.add_field(name="🟡 Medium Priority", value=str(medium_priority), inline=True)
        
        # Top 3 tactics with most gaps
        top_tactic_gaps = sorted(gaps.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        
        mapper = self.bot.get_cog('MitreAttackMapper')
        for tactic_id, tech_ids in top_tactic_gaps:
            tactic_name = mapper.tactic_names.get(tactic_id, 'Unknown')
            embed.add_field(
                name=f"📂 {tactic_name}",
                value=f"{len(tech_ids)} gaps",
                inline=True
            )
        
        embed.add_field(
            name="📌 Recommendations",
            value="1. Prioritize high-risk gaps\n2. Implement missing detections\n3. Review coverage quarterly",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TechniqueGapAnalyzer(bot))
