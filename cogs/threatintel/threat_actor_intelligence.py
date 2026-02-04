"""
Threat Actor Intelligence - Advanced threat actor profiling for Sentinel
Track threat actors, TTPs (Tactics, Techniques, Procedures), and campaign attribution
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
import hashlib
from cogs.core.pst_timezone import get_now_pst

class ThreatActorIntelligence(commands.Cog):
    """Threat actor profiling and TTP tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.actor_file = 'data/threat_actors.json'
        self.campaign_file = 'data/campaigns.json'
        self.ttp_file = 'data/ttps.json'
        self.load_data()
    
    def load_data(self):
        """Load threat intelligence data"""
        os.makedirs('data', exist_ok=True)
        
        for file in [self.actor_file, self.campaign_file, self.ttp_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def get_guild_actors(self, guild_id):
        """Get threat actors for guild"""
        with open(self.actor_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_actors(self, guild_id, actors):
        """Save threat actors"""
        with open(self.actor_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = actors
        with open(self.actor_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_guild_campaigns(self, guild_id):
        """Get campaigns for guild"""
        with open(self.campaign_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_campaigns(self, guild_id, campaigns):
        """Save campaigns"""
        with open(self.campaign_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = campaigns
        with open(self.campaign_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_actor_id(self, name):
        """Generate threat actor ID"""
        hash_val = hashlib.md5(name.lower().encode()).hexdigest()[:8].upper()
        return f"TA-{hash_val}"
    
    async def _actorcreate_logic(self, ctx, sophistication: str, *, description: str):
        """Create threat actor profile"""
        valid_sophistication = ['nation_state', 'organized_crime', 'hacktivist', 'script_kiddie', 'insider', 'unknown']
        
        if sophistication.lower() not in valid_sophistication:
            await ctx.send(f"❌ Invalid sophistication. Use: {', '.join(valid_sophistication)}")
            return
        
        parts = description.split('|')
        if len(parts) < 2:
            await ctx.send("Usage: `!actorcreate <sophistication> <name> | <description> | [observed_ttps]`")
            return
        
        name = parts[0].strip()
        desc = parts[1].strip()
        ttps = parts[2].strip() if len(parts) > 2 else None
        
        actors = self.get_guild_actors(ctx.guild.id)
        actor_id = self.generate_actor_id(name)
        
        # Threat level based on sophistication
        threat_level_map = {
            'nation_state': ('critical', '🔴', discord.Color.red()),
            'organized_crime': ('high', '🟠', discord.Color.orange()),
            'hacktivist': ('medium', '🟡', discord.Color.gold()),
            'script_kiddie': ('low', '🟢', discord.Color.green()),
            'insider': ('high', '🟠', discord.Color.orange()),
            'unknown': ('medium', '⚪', discord.Color.greyple())
        }
        
        threat_level, emoji, color = threat_level_map[sophistication.lower()]
        
        actor = {
            'id': actor_id,
            'name': name,
            'description': desc,
            'sophistication': sophistication.lower(),
            'threat_level': threat_level,
            'first_seen': get_now_pst().isoformat(),
            'last_seen': get_now_pst().isoformat(),
            'observed_ttps': ttps.split(',') if ttps else [],
            'campaigns': [],
            'targets': [],
            'aliases': [],
            'motivation': None,
            'attribution_confidence': 'low',
            'activity_status': 'active',
            'incident_count': 0
        }
        
        actors[actor_id] = actor
        self.save_actors(ctx.guild.id, actors)
        
        embed = discord.Embed(
            title=f"{emoji} Threat Actor Profile Created",
            description=f"**{name}** ({actor_id})",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Actor ID", value=f"`{actor_id}`", inline=True)
        embed.add_field(name="Sophistication", value=sophistication.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Threat Level", value=threat_level.upper(), inline=True)
        embed.add_field(name="Description", value=desc, inline=False)
        
        if ttps:
            embed.add_field(name="Observed TTPs", value=ttps, inline=False)
        
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="First Seen", value=get_now_pst().strftime('%Y-%m-%d'), inline=True)
        embed.set_footer(text="Sentinel Threat Intelligence | Use !actorlink to associate with campaigns")
        
        await ctx.send(embed=embed)
    
    async def _actorlist_logic(self, ctx, status: str = 'active'):
        """List threat actors"""
        actors = self.get_guild_actors(ctx.guild.id)
        
        if not actors:
            await ctx.send("📋 No threat actors tracked yet.")
            return
        
        # Filter by status
        filtered = {k: v for k, v in actors.items() if v.get('activity_status', 'active') == status.lower()}
        
        if not filtered:
            await ctx.send(f"📋 No {status} threat actors found.")
            return
        
        # Sort by threat level
        level_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_actors = sorted(filtered.values(), key=lambda a: level_order.get(a['threat_level'], 4))
        
        embed = discord.Embed(
            title="🎯 Threat Actor Intelligence",
            description=f"{len(sorted_actors)} {status} threat actor(s)",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for actor in sorted_actors[:10]:
            level_map = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
            emoji = level_map.get(actor['threat_level'], '⚪')
            
            campaigns_str = f"{len(actor['campaigns'])} campaign(s)" if actor['campaigns'] else "No campaigns"
            incidents_str = f"{actor['incident_count']} incident(s)"
            
            embed.add_field(
                name=f"{emoji} {actor['name']} ({actor['id']})",
                value=f"{actor['sophistication'].replace('_', ' ').title()} | {campaigns_str} | {incidents_str}",
                inline=False
            )
        
        if len(sorted_actors) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_actors) - 10} additional actors", inline=False)
        
        embed.set_footer(text="Use !actordetail <id> for full profile")
        
        await ctx.send(embed=embed)
    
    async def _actordetail_logic(self, ctx, actor_id: str):
        """Show threat actor details"""
        actors = self.get_guild_actors(ctx.guild.id)
        
        actor_id = actor_id.upper()
        if not actor_id.startswith('TA-'):
            actor_id = f"TA-{actor_id}"
        
        actor = actors.get(actor_id)
        if not actor:
            await ctx.send(f"❌ Threat actor not found: {actor_id}")
            return
        
        level_map = {'critical': ('🔴', discord.Color.red()), 'high': ('🟠', discord.Color.orange()), 
                     'medium': ('🟡', discord.Color.gold()), 'low': ('🟢', discord.Color.green())}
        emoji, color = level_map.get(actor['threat_level'], ('⚪', discord.Color.greyple()))
        
        embed = discord.Embed(
            title=f"{emoji} Threat Actor Profile: {actor['name']}",
            description=actor['description'],
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Actor ID", value=f"`{actor['id']}`", inline=True)
        embed.add_field(name="Threat Level", value=actor['threat_level'].upper(), inline=True)
        embed.add_field(name="Status", value=actor['activity_status'].title(), inline=True)
        
        embed.add_field(name="Sophistication", value=actor['sophistication'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Attribution", value=actor['attribution_confidence'].title(), inline=True)
        embed.add_field(name="Incidents", value=str(actor['incident_count']), inline=True)
        
        first_seen = datetime.fromisoformat(actor['first_seen']).strftime('%Y-%m-%d')
        last_seen = datetime.fromisoformat(actor['last_seen']).strftime('%Y-%m-%d')
        embed.add_field(name="First Seen", value=first_seen, inline=True)
        embed.add_field(name="Last Seen", value=last_seen, inline=True)
        embed.add_field(name="Campaigns", value=str(len(actor['campaigns'])), inline=True)
        
        if actor['observed_ttps']:
            ttps_str = ", ".join(actor['observed_ttps'][:5])
            if len(actor['observed_ttps']) > 5:
                ttps_str += f" (+{len(actor['observed_ttps']) - 5} more)"
            embed.add_field(name="🎯 Observed TTPs", value=ttps_str, inline=False)
        
        if actor['motivation']:
            embed.add_field(name="Motivation", value=actor['motivation'], inline=False)
        
        if actor['aliases']:
            embed.add_field(name="Aliases", value=", ".join(actor['aliases']), inline=False)
        
        if actor['targets']:
            targets_str = ", ".join(actor['targets'][:3])
            if len(actor['targets']) > 3:
                targets_str += f" (+{len(actor['targets']) - 3} more)"
            embed.add_field(name="Known Targets", value=targets_str, inline=False)
        
        embed.set_footer(text="Sentinel Threat Intelligence")
        
        await ctx.send(embed=embed)
    
    async def _actorstats_logic(self, ctx):
        """Show threat actor statistics"""
        actors = self.get_guild_actors(ctx.guild.id)
        
        if not actors:
            await ctx.send("📊 No threat actors tracked yet.")
            return
        
        # Calculate stats
        total = len(actors)
        by_sophistication = {}
        by_level = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        by_status = {'active': 0, 'dormant': 0, 'inactive': 0}
        total_incidents = 0
        total_campaigns = 0
        
        for actor in actors.values():
            by_sophistication[actor['sophistication']] = by_sophistication.get(actor['sophistication'], 0) + 1
            by_level[actor['threat_level']] = by_level.get(actor['threat_level'], 0) + 1
            by_status[actor.get('activity_status', 'active')] = by_status.get(actor.get('activity_status', 'active'), 0) + 1
            total_incidents += actor['incident_count']
            total_campaigns += len(actor['campaigns'])
        
        embed = discord.Embed(
            title="📊 Threat Actor Intelligence Statistics",
            description=f"Total: {total} actors | {total_incidents} incidents | {total_campaigns} campaigns",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        level_str = f"🔴 Critical: {by_level['critical']}\n🟠 High: {by_level['high']}\n🟡 Medium: {by_level['medium']}\n🟢 Low: {by_level['low']}"
        embed.add_field(name="📈 By Threat Level", value=level_str, inline=True)
        
        status_str = f"🟢 Active: {by_status['active']}\n🟡 Dormant: {by_status.get('dormant', 0)}\n⚪ Inactive: {by_status.get('inactive', 0)}"
        embed.add_field(name="📊 By Status", value=status_str, inline=True)
        
        soph_str = "\n".join([f"{soph.replace('_', ' ').title()}: {count}" for soph, count in sorted(by_sophistication.items(), key=lambda x: x[1], reverse=True)])
        embed.add_field(name="🎯 By Sophistication", value=soph_str, inline=True)
        
        embed.set_footer(text="Sentinel Threat Intelligence | Current snapshot")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='actorcreate')
    async def actorcreate_prefix(self, ctx, sophistication: str, *, description: str):
        """Create threat actor - Prefix command"""
        await self._actorcreate_logic(ctx, sophistication, description=description)
    
    @commands.command(name='actorlist')
    async def actorlist_prefix(self, ctx, status: str = 'active'):
        """List threat actors - Prefix command"""
        await self._actorlist_logic(ctx, status)
    
    @commands.command(name='actordetail')
    async def actordetail_prefix(self, ctx, actor_id: str):
        """Show threat actor details - Prefix command"""
        await self._actordetail_logic(ctx, actor_id)
    
    @commands.command(name='actorstats')
    async def actorstats_prefix(self, ctx):
        """Show threat actor stats - Prefix command"""
        await self._actorstats_logic(ctx)

async def setup(bot):
    await bot.add_cog(ThreatActorIntelligence(bot))
