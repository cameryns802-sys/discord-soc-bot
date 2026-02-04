"""
Incident Pattern Correlation Engine - Identify patterns across incidents
Detect related incidents, campaign indicators, and attack pattern trends
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class IncidentPatternCorrelation(commands.Cog):
    """Incident pattern detection and correlation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.patterns_file = 'data/incident_patterns.json'
        self.correlations_file = 'data/incident_correlations.json'
        self.load_data()
    
    def load_data(self):
        """Load pattern data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.correlations_file):
            with open(self.correlations_file, 'w') as f:
                json.dump({}, f)
    
    def get_patterns(self, guild_id):
        """Get patterns"""
        with open(self.patterns_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_patterns(self, guild_id, patterns):
        """Save patterns"""
        with open(self.patterns_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = patterns
        with open(self.patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_correlations(self, guild_id):
        """Get correlations"""
        with open(self.correlations_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_correlations(self, guild_id, correlations):
        """Save correlations"""
        with open(self.correlations_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = correlations
        with open(self.correlations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_correlation_score(self, attrs1: dict, attrs2: dict) -> int:
        """Calculate correlation between two incidents (0-100)"""
        score = 0
        
        # Same attack vector
        if attrs1.get('attack_vector') == attrs2.get('attack_vector'):
            score += 25
        
        # Same target type
        if attrs1.get('target_type') == attrs2.get('target_type'):
            score += 20
        
        # Time proximity (within 24 hours)
        time1 = datetime.fromisoformat(attrs1.get('timestamp', ''))
        time2 = datetime.fromisoformat(attrs2.get('timestamp', ''))
        hours_apart = abs((time1 - time2).total_seconds() / 3600)
        
        if hours_apart < 24:
            score += 20
        elif hours_apart < 72:
            score += 10
        
        # Same infrastructure indicators
        if attrs1.get('source_ip_range') == attrs2.get('source_ip_range'):
            score += 20
        
        # Similar TTPs
        if attrs1.get('ttp_category') == attrs2.get('ttp_category'):
            score += 15
        
        return min(100, score)
    
    async def _recordincident_logic(self, ctx, incident_type: str, attack_vector: str, target: str):
        """Record incident for pattern analysis"""
        patterns = self.get_patterns(ctx.guild.id)
        
        incident_id = f"IPC-{str(uuid.uuid4())[:8].upper()}"
        
        incident = {
            'id': incident_id,
            'type': incident_type.lower(),
            'attack_vector': attack_vector.lower(),
            'target_type': target.lower(),
            'timestamp': get_now_pst().isoformat(),
            'source_ip_range': '192.168.1.0/24',
            'ttp_category': 'initial_access',
            'severity': 'high',
            'status': 'new'
        }
        
        patterns[incident_id] = incident
        self.save_patterns(ctx.guild.id, patterns)
        
        embed = discord.Embed(
            title="📝 Incident Recorded",
            description=f"Type: {incident_type}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Incident ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Attack Vector", value=attack_vector.title(), inline=True)
        embed.add_field(name="Target", value=target.title(), inline=True)
        embed.add_field(name="Status", value="🔵 Recorded", inline=False)
        
        embed.set_footer(text="Use !findcorrelations to identify related incidents")
        
        await ctx.send(embed=embed)
    
    async def _findcorrelations_logic(self, ctx, incident_id: str):
        """Find correlated incidents"""
        patterns = self.get_patterns(ctx.guild.id)
        correlations = self.get_correlations(ctx.guild.id)
        
        incident_id = incident_id.upper()
        if not incident_id.startswith('IPC-'):
            incident_id = f"IPC-{incident_id}"
        
        incident = patterns.get(incident_id)
        if not incident:
            await ctx.send(f"❌ Incident not found: {incident_id}")
            return
        
        # Find correlations
        related = {}
        for other_id, other_incident in patterns.items():
            if other_id == incident_id:
                continue
            
            score = self.calculate_correlation_score(incident, other_incident)
            if score >= 30:  # Threshold
                related[other_id] = {
                    'score': score,
                    'incident': other_incident
                }
        
        # Save correlations
        correlation_record = {
            'incident_id': incident_id,
            'found_at': get_now_pst().isoformat(),
            'related_count': len(related),
            'related_incidents': list(related.keys())
        }
        correlations[f"COR-{str(uuid.uuid4())[:8].upper()}"] = correlation_record
        self.save_correlations(ctx.guild.id, correlations)
        
        embed = discord.Embed(
            title="🔗 Incident Correlations",
            description=f"Analyzing: {incident_id}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Related Incidents Found",
            value=f"🔗 {len(related)}",
            inline=False
        )
        
        if related:
            embed.add_field(name="Correlation Details", value="━" * 25, inline=False)
            
            for other_id in sorted(related.keys(), key=lambda x: related[x]['score'], reverse=True)[:5]:
                other = related[other_id]
                score = other['score']
                incident_info = other['incident']
                
                embed.add_field(
                    name=f"🔗 {other_id} ({score}%)",
                    value=f"Vector: {incident_info.get('attack_vector', 'unknown').title()} | Target: {incident_info.get('target_type', 'unknown').title()}",
                    inline=False
                )
        else:
            embed.add_field(name="Status", value="✅ No strong correlations found", inline=False)
        
        embed.add_field(name="Analysis", value="━" * 25, inline=False)
        if len(related) >= 3:
            embed.add_field(
                name="⚠️ Potential Campaign",
                value="Multiple incidents show correlation - may indicate coordinated attack",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def _patternanalysis_logic(self, ctx, days: int = 30):
        """Show pattern analysis over time"""
        patterns = self.get_patterns(ctx.guild.id)
        
        if not patterns:
            await ctx.send("📭 No incidents recorded.")
            return
        
        # Filter by days
        cutoff = (get_now_pst() - timedelta(days=days)).isoformat()
        recent = [i for i in patterns.values() if i['timestamp'] >= cutoff]
        
        # Analyze patterns
        by_vector = {}
        by_target = {}
        by_type = {}
        
        for incident in recent:
            vector = incident['attack_vector']
            target = incident['target_type']
            itype = incident['type']
            
            by_vector[vector] = by_vector.get(vector, 0) + 1
            by_target[target] = by_target.get(target, 0) + 1
            by_type[itype] = by_type.get(itype, 0) + 1
        
        embed = discord.Embed(
            title=f"📊 Incident Pattern Analysis ({days}d)",
            description=f"{len(recent)} incident(s) analyzed",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Attack Vector Breakdown", value="━" * 25, inline=False)
        for vector, count in sorted(by_vector.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=vector.title(), value=f"📊 {count}", inline=True)
        
        embed.add_field(name="Target Type Breakdown", value="━" * 25, inline=False)
        for target, count in sorted(by_target.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=target.title(), value=f"🎯 {count}", inline=True)
        
        embed.add_field(name="Incident Type Breakdown", value="━" * 25, inline=False)
        for itype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=itype.title(), value=f"⚠️ {count}", inline=True)
        
        # Top pattern
        most_common = max(by_vector.items(), key=lambda x: x[1], default=(None, 0))
        if most_common[0]:
            embed.add_field(
                name="Most Common Pattern",
                value=f"🔴 {most_common[0].title()} ({most_common[1]} incident(s))",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def _campaigndetection_logic(self, ctx):
        """Detect potential attack campaigns"""
        patterns = self.get_patterns(ctx.guild.id)
        correlations = self.get_correlations(ctx.guild.id)
        
        embed = discord.Embed(
            title="🚨 Campaign Detection",
            description="Identifying potential coordinated attacks",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        # Find clusters
        campaigns = []
        for cor_id, correlation in correlations.items():
            if correlation['related_count'] >= 3:
                campaigns.append(correlation)
        
        embed.add_field(name="Potential Campaigns", value=f"🚨 {len(campaigns)}", inline=False)
        
        if campaigns:
            for campaign in campaigns[:5]:
                related_ids = ', '.join(campaign['related_incidents'][:3])
                embed.add_field(
                    name=f"Campaign: {campaign['incident_id']}",
                    value=f"Related: {campaign['related_count']} incidents | IDs: {related_ids}",
                    inline=False
                )
        else:
            embed.add_field(name="Status", value="✅ No potential campaigns detected", inline=False)
        
        embed.add_field(name="Recommendations", value="━" * 25, inline=False)
        if campaigns:
            embed.add_field(
                name="⚠️ Action Required",
                value="Multiple related incidents detected. Recommend escalation to threat intelligence team.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='recordincident')
    async def recordincident_prefix(self, ctx, incident_type: str, attack_vector: str, target: str):
        """Record incident - Prefix command"""
        await self._recordincident_logic(ctx, incident_type, attack_vector, target)
    
    @commands.command(name='findcorrelations')
    async def findcorrelations_prefix(self, ctx, incident_id: str):
        """Find correlations - Prefix command"""
        await self._findcorrelations_logic(ctx, incident_id)
    
    @commands.command(name='patternanalysis')
    async def patternanalysis_prefix(self, ctx, days: int = 30):
        """Show pattern analysis - Prefix command"""
        await self._patternanalysis_logic(ctx, days)
    
    @commands.command(name='campaigndetection')
    async def campaigndetection_prefix(self, ctx):
        """Detect campaigns - Prefix command"""
        await self._campaigndetection_logic(ctx)

async def setup(bot):
    await bot.add_cog(IncidentPatternCorrelation(bot))
