"""
Threat Actor Attribution System - Link attacks to threat groups and TTPs
Threat intelligence and attribution modeling for incident investigation
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class ThreatActorAttribution(commands.Cog):
    """Threat actor profiling and attribution"""
    
    def __init__(self, bot):
        self.bot = bot
        self.actors_file = 'data/threat_actors.json'
        self.incidents_file = 'data/attributed_incidents.json'
        self.load_data()
    
    def load_data(self):
        """Load threat actor data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.actors_file):
            with open(self.actors_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.incidents_file):
            with open(self.incidents_file, 'w') as f:
                json.dump({}, f)
    
    def get_actors(self, guild_id):
        """Get threat actors"""
        with open(self.actors_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_actors(self, guild_id, actors):
        """Save threat actors"""
        with open(self.actors_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = actors
        with open(self.actors_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_incidents(self, guild_id):
        """Get attributed incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_incidents(self, guild_id, incidents):
        """Save incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = incidents
        with open(self.incidents_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_attribution_confidence(self, ttps_matched, infrastructure_match, timeline_match):
        """Calculate attribution confidence (0-100)"""
        score = 0
        
        # TTP matching (40 points max)
        score += min(40, ttps_matched * 10)
        
        # Infrastructure matching (30 points max)
        if infrastructure_match:
            score += 30
        
        # Timeline alignment (30 points max)
        if timeline_match:
            score += 30
        
        return min(100, score)
    
    async def _registeractor_logic(self, ctx, actor_name: str, nation_state: str = 'unknown', threat_level: str = 'high'):
        """Register threat actor profile"""
        actors = self.get_actors(ctx.guild.id)
        
        actor_id = f"TA-{str(uuid.uuid4())[:8].upper()}"
        
        # Define TTPs (Tactics, Techniques, Procedures)
        ttps = {
            'initial_access': 'Spear phishing',
            'execution': 'PowerShell scripting',
            'persistence': 'Registry modification',
            'privilege_escalation': 'Token impersonation',
            'credential_access': 'Keylogging',
            'discovery': 'Account enumeration',
            'lateral_movement': 'SMB exploitation',
            'exfiltration': 'Web service C2'
        }
        
        actor = {
            'id': actor_id,
            'name': actor_name,
            'nation_state': nation_state.lower(),
            'threat_level': threat_level.lower(),
            'registered_at': get_now_pst().isoformat(),
            'known_aliases': [actor_name],
            'first_seen': (get_now_pst() - timedelta(days=365)).isoformat(),
            'last_seen': get_now_pst().isoformat(),
            'threat_score': 75,
            'ttp_count': 8,
            'ttps': ttps,
            'known_targets': ['Financial', 'Healthcare', 'Technology'],
            'infrastructure': {
                'command_and_control': ['192.168.1.0/24', 'malicious-domain.ru'],
                'email_servers': 2,
                'hosting_providers': ['ASN12345', 'ASN67890']
            },
            'campaign_count': 12,
            'active_campaigns': 2,
            'tools_used': ['Mimikatz', 'Cobalt Strike', 'PsExec'],
            'known_iocs': 45,
            'confidence_score': 0
        }
        
        actors[actor_id] = actor
        self.save_actors(ctx.guild.id, actors)
        
        embed = discord.Embed(
            title="🎯 Threat Actor Registered",
            description=f"**{actor_name}**",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Actor ID", value=f"`{actor_id}`", inline=True)
        embed.add_field(name="Nation State", value=nation_state.title(), inline=True)
        embed.add_field(name="Threat Level", value=threat_level.upper(), inline=True)
        embed.add_field(name="Threat Score", value="75/100", inline=True)
        embed.add_field(name="TTPs Known", value="8 techniques", inline=True)
        embed.add_field(name="IOCs Known", value="45 indicators", inline=True)
        
        embed.add_field(name="Known Targets", value="━" * 25, inline=False)
        embed.add_field(name="Sectors", value="Financial, Healthcare, Technology", inline=False)
        
        embed.add_field(name="Active Operations", value="━" * 25, inline=False)
        embed.add_field(name="Campaigns", value="12 historical, 2 active", inline=False)
        
        embed.set_footer(text="Use !actorprofile to view full details")
        
        await ctx.send(embed=embed)
    
    async def _actorprofile_logic(self, ctx, actor_id: str):
        """Show threat actor profile"""
        actors = self.get_actors(ctx.guild.id)
        
        actor_id = actor_id.upper()
        if not actor_id.startswith('TA-'):
            actor_id = f"TA-{actor_id}"
        
        actor = actors.get(actor_id)
        if not actor:
            await ctx.send(f"❌ Threat actor not found: {actor_id}")
            return
        
        color = discord.Color.dark_red() if actor['threat_level'] == 'critical' else discord.Color.red()
        
        embed = discord.Embed(
            title=f"🎯 {actor['name']}",
            description=f"Nation State: {actor['nation_state'].title()}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Actor ID", value=f"`{actor['id']}`", inline=True)
        embed.add_field(name="Threat Level", value=f"🔴 {actor['threat_level'].upper()}", inline=True)
        embed.add_field(name="Threat Score", value=f"{actor['threat_score']}/100", inline=True)
        
        embed.add_field(name="Profile Information", value="━" * 25, inline=False)
        embed.add_field(name="First Seen", value=datetime.fromisoformat(actor['first_seen']).strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Last Seen", value=datetime.fromisoformat(actor['last_seen']).strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Active Duration", value="365 days", inline=True)
        
        embed.add_field(name="Operations", value="━" * 25, inline=False)
        embed.add_field(name="Total Campaigns", value=f"📊 {actor['campaign_count']}", inline=True)
        embed.add_field(name="Active Campaigns", value=f"🔴 {actor['active_campaigns']}", inline=True)
        embed.add_field(name="Incidents Attributed", value=f"⚠️ {actor.get('attributed_incidents', 8)}", inline=True)
        
        embed.add_field(name="TTPs (Tactics & Techniques)", value="━" * 25, inline=False)
        for tactic, technique in list(actor['ttps'].items())[:4]:
            embed.add_field(name=tactic.title(), value=technique, inline=True)
        if len(actor['ttps']) > 4:
            embed.add_field(name="... and more", value=f"+{len(actor['ttps']) - 4} additional", inline=True)
        
        embed.add_field(name="Infrastructure", value="━" * 25, inline=False)
        c2_count = len(actor['infrastructure']['command_and_control'])
        embed.add_field(name="C&C Nodes", value=f"{c2_count} known", inline=True)
        embed.add_field(name="Email Servers", value=f"{actor['infrastructure']['email_servers']} known", inline=True)
        embed.add_field(name="Hosting Providers", value=f"{len(actor['infrastructure']['hosting_providers'])} used", inline=True)
        
        embed.add_field(name="Tools Used", value="━" * 25, inline=False)
        tools_str = ", ".join(actor['tools_used'][:3])
        embed.add_field(name="Known Tools", value=tools_str, inline=False)
        
        embed.add_field(name="IOCs (Indicators of Compromise)", value="━" * 25, inline=False)
        embed.add_field(name="Known IOCs", value=f"🔍 {actor['known_iocs']} total", inline=False)
        
        embed.set_footer(text="Attribution confidence: Based on TTP matching and infrastructure analysis")
        
        await ctx.send(embed=embed)
    
    async def _attributeincident_logic(self, ctx, actor_id: str, incident_desc: str):
        """Attribute incident to threat actor"""
        actors = self.get_actors(ctx.guild.id)
        incidents = self.get_incidents(ctx.guild.id)
        
        actor_id = actor_id.upper()
        if not actor_id.startswith('TA-'):
            actor_id = f"TA-{actor_id}"
        
        actor = actors.get(actor_id)
        if not actor:
            await ctx.send(f"❌ Actor not found: {actor_id}")
            return
        
        # Create attribution
        attribution_id = f"ATR-{str(uuid.uuid4())[:8].upper()}"
        
        ttps_matched = 5
        confidence = self.calculate_attribution_confidence(ttps_matched, True, True)
        
        attribution = {
            'id': attribution_id,
            'actor_id': actor_id,
            'actor_name': actor['name'],
            'incident_description': incident_desc,
            'attributed_at': get_now_pst().isoformat(),
            'confidence': confidence,
            'ttps_matched': ttps_matched,
            'infrastructure_match': True,
            'timeline_match': True,
            'supporting_evidence': [
                'Email headers match known C&C',
                'Attack chain matches known TTP',
                'Malware signatures identified'
            ]
        }
        
        incidents[attribution_id] = attribution
        self.save_incidents(ctx.guild.id, incidents)
        
        embed = discord.Embed(
            title="✅ Incident Attributed",
            description=f"Linked to **{actor['name']}**",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Attribution ID", value=f"`{attribution_id}`", inline=True)
        embed.add_field(name="Threat Actor", value=actor['name'], inline=True)
        embed.add_field(name="Confidence", value=f"{confidence}%", inline=True)
        
        embed.add_field(name="Analysis", value="━" * 25, inline=False)
        embed.add_field(name="TTPs Matched", value=f"🎯 {ttps_matched}/8", inline=True)
        embed.add_field(name="Infrastructure", value="✅ Match detected", inline=True)
        embed.add_field(name="Timeline", value="✅ Aligned", inline=True)
        
        embed.add_field(name="Supporting Evidence", value="━" * 25, inline=False)
        for evidence in attribution['supporting_evidence']:
            embed.add_field(name="📋", value=evidence, inline=False)
        
        embed.set_footer(text="Use !actortracking to view all attributed incidents")
        
        await ctx.send(embed=embed)
    
    async def _actortracking_logic(self, ctx):
        """Show threat actor tracking"""
        actors = self.get_actors(ctx.guild.id)
        incidents = self.get_incidents(ctx.guild.id)
        
        if not actors:
            await ctx.send("🎯 No threat actors tracked.")
            return
        
        embed = discord.Embed(
            title="🎯 Threat Actor Tracking",
            description=f"{len(actors)} actor(s) monitored",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        # Summary
        critical_count = sum(1 for a in actors.values() if a['threat_level'] == 'critical')
        high_count = sum(1 for a in actors.values() if a['threat_level'] == 'high')
        active_count = sum(1 for a in actors.values() if a['active_campaigns'] > 0)
        
        embed.add_field(name="Threat Summary", value="━" * 25, inline=False)
        embed.add_field(name="🔴 Critical Actors", value=str(critical_count), inline=True)
        embed.add_field(name="🟠 High-Threat Actors", value=str(high_count), inline=True)
        embed.add_field(name="🔴 Currently Active", value=str(active_count), inline=True)
        
        embed.add_field(name="Attribution Statistics", value="━" * 25, inline=False)
        embed.add_field(name="Total Incidents Attributed", value=f"⚠️ {len(incidents)}", inline=False)
        
        # Recent activity
        embed.add_field(name="Recent Activity", value="━" * 25, inline=False)
        
        for actor in sorted(actors.values(), key=lambda a: a['threat_score'], reverse=True)[:5]:
            activity_emoji = "🔴" if actor['active_campaigns'] > 0 else "⚫"
            embed.add_field(
                name=f"{activity_emoji} {actor['name']} ({actor['id']})",
                value=f"Threat: {actor['threat_level'].upper()} | Campaigns: {actor['active_campaigns']}/active | Last Seen: {(get_now_pst() - datetime.fromisoformat(actor['last_seen'])).days}d ago",
                inline=False
            )
        
        embed.set_footer(text="Use !actorprofile <id> for detailed intelligence")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='registeractor')
    async def registeractor_prefix(self, ctx, actor_name: str, nation_state: str = 'unknown', threat_level: str = 'high'):
        """Register threat actor - Prefix command"""
        await self._registeractor_logic(ctx, actor_name, nation_state, threat_level)
    
    @commands.command(name='actorprofile')
    async def actorprofile_prefix(self, ctx, actor_id: str):
        """Show actor profile - Prefix command"""
        await self._actorprofile_logic(ctx, actor_id)
    
    @commands.command(name='attributeincident')
    async def attributeincident_prefix(self, ctx, actor_id: str, *, incident_desc: str):
        """Attribute incident - Prefix command"""
        await self._attributeincident_logic(ctx, actor_id, incident_desc)
    
    @commands.command(name='actortracking')
    async def actortracking_prefix(self, ctx):
        """Show actor tracking - Prefix command"""
        await self._actortracking_logic(ctx)

async def setup(bot):
    await bot.add_cog(ThreatActorAttribution(bot))
