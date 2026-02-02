"""
Threat Hunting Campaign System - Proactive threat hunting for Sentinel
Enables security teams to launch and track threat hunting operations
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class ThreatHuntingCampaigns(commands.Cog):
    """Threat hunting campaign management and coordination"""
    
    def __init__(self, bot):
        self.bot = bot
        self.campaign_file = 'data/hunt_campaigns.json'
        self.load_campaigns()
    
    def load_campaigns(self):
        """Load hunt campaigns"""
        if not os.path.exists(self.campaign_file):
            os.makedirs(os.path.dirname(self.campaign_file), exist_ok=True)
            with open(self.campaign_file, 'w') as f:
                json.dump({}, f)
    
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
    
    def create_campaign(self, guild_id, name, description, threat_type, hunt_queries, hunter):
        """Create new hunt campaign"""
        campaigns = self.get_guild_campaigns(guild_id)
        
        campaign_id = str(uuid.uuid4())[:8]
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'description': description,
            'threat_type': threat_type,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'created_by': hunter,
            'hunt_queries': hunt_queries.split('\n') if isinstance(hunt_queries, str) else hunt_queries,
            'findings': [],
            'completed_at': None,
            'findings_count': 0
        }
        
        campaigns[campaign_id] = campaign
        self.save_campaigns(guild_id, campaigns)
        return campaign
    
    def add_finding(self, guild_id, campaign_id, description, severity, evidence):
        """Add finding to campaign"""
        campaigns = self.get_guild_campaigns(guild_id)
        
        if campaign_id not in campaigns:
            return None
        
        finding = {
            'id': str(uuid.uuid4())[:8],
            'description': description,
            'severity': severity,
            'evidence': evidence,
            'found_at': datetime.utcnow().isoformat(),
            'status': 'open'
        }
        
        campaigns[campaign_id]['findings'].append(finding)
        campaigns[campaign_id]['findings_count'] = len(campaigns[campaign_id]['findings'])
        self.save_campaigns(guild_id, campaigns)
        return finding
    
    async def _huntcampaign_logic(self, ctx, name: str, threat_type: str, *, description: str):
        """Create threat hunting campaign"""
        valid_types = ['APT', 'Insider Threat', 'Malware', 'Phishing', 'Privilege Escalation', 'Data Exfil', 'C2', 'Lateral Movement', 'Other']
        
        if threat_type not in valid_types:
            await ctx.send(f"❌ Invalid threat type. Use: {', '.join(valid_types)}")
            return
        
        campaign = self.create_campaign(
            ctx.guild.id,
            name,
            description,
            threat_type,
            "",
            ctx.author.id
        )
        
        embed = discord.Embed(
            title="🔍 Hunt Campaign Created",
            description=f"**{name}**",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Campaign ID", value=f"`{campaign['id']}`", inline=True)
        embed.add_field(name="Threat Type", value=threat_type, inline=True)
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Next Steps", value="```\n!huntsearch <campaign_id> <query>\n!huntfinding <campaign_id> <severity> <description>\n```", inline=False)
        
        embed.set_footer(text="Sentinel Threat Hunting System")
        
        await ctx.send(embed=embed)
    
    async def _huntsearch_logic(self, ctx, campaign_id: str, *, query: str):
        """Add search query to campaign"""
        campaigns = self.get_guild_campaigns(ctx.guild.id)
        
        if campaign_id not in campaigns:
            await ctx.send(f"❌ Campaign `{campaign_id}` not found.")
            return
        
        campaign = campaigns[campaign_id]
        if query not in campaign['hunt_queries']:
            campaign['hunt_queries'].append(query)
        
        self.save_campaigns(ctx.guild.id, campaigns)
        
        embed = discord.Embed(
            title="🔎 Hunt Query Added",
            description=f"Campaign: `{campaign_id}`",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Query", value=f"`{query}`", inline=False)
        embed.add_field(name="Total Queries", value=str(len(campaign['hunt_queries'])), inline=True)
        embed.add_field(name="Campaign", value=campaign['name'], inline=True)
        
        embed.set_footer(text="Query logged | Continue hunting")
        
        await ctx.send(embed=embed)
    
    async def _huntfinding_logic(self, ctx, campaign_id: str, severity: str, *, description: str):
        """Log finding from hunt campaign"""
        valid_severities = ['critical', 'high', 'medium', 'low']
        
        if severity.lower() not in valid_severities:
            await ctx.send(f"❌ Invalid severity. Use: {', '.join(valid_severities)}")
            return
        
        campaigns = self.get_guild_campaigns(ctx.guild.id)
        
        if campaign_id not in campaigns:
            await ctx.send(f"❌ Campaign `{campaign_id}` not found.")
            return
        
        finding = self.add_finding(
            ctx.guild.id,
            campaign_id,
            description,
            severity,
            f"Found by {ctx.author.name}"
        )
        
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity.lower(), '❓')
        
        embed = discord.Embed(
            title=f"{severity_emoji} Hunt Finding",
            description=description,
            color={
                'critical': discord.Color.red(),
                'high': discord.Color.orange(),
                'medium': discord.Color.gold(),
                'low': discord.Color.green()
            }.get(severity.lower(), discord.Color.greyple()),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Campaign", value=campaigns[campaign_id]['name'], inline=True)
        embed.add_field(name="Campaign ID", value=f"`{campaign_id}`", inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Found By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Finding ID", value=f"`{finding['id']}`", inline=True)
        embed.add_field(name="Campaign Finding Count", value=f"{campaigns[campaign_id]['findings_count']}", inline=True)
        
        embed.set_footer(text="Sentinel Threat Hunting | Finding logged")
        
        await ctx.send(embed=embed)
    
    async def _huntlist_logic(self, ctx, status: str = 'active'):
        """List hunt campaigns"""
        campaigns = self.get_guild_campaigns(ctx.guild.id)
        
        filtered = {k: v for k, v in campaigns.items() if v['status'].lower() == status.lower()}
        
        if not filtered:
            await ctx.send(f"📋 No **{status.upper()}** hunts found.")
            return
        
        embed = discord.Embed(
            title=f"🔍 {status.upper()} Hunt Campaigns",
            description=f"{len(filtered)} campaign(s)",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for campaign in list(filtered.values())[:10]:
            embed.add_field(
                name=f"{campaign['name']} (ID: {campaign['id']})",
                value=f"Type: {campaign['threat_type']}\nFindings: {campaign['findings_count']}\nQueries: {len(campaign['hunt_queries'])}",
                inline=False
            )
        
        if len(filtered) > 10:
            embed.add_field(name="... and more", value=f"+{len(filtered) - 10} additional campaigns", inline=False)
        
        embed.set_footer(text="Use !huntdetail <id> for details")
        
        await ctx.send(embed=embed)
    
    async def _huntdetail_logic(self, ctx, campaign_id: str):
        """Show campaign details"""
        campaigns = self.get_guild_campaigns(ctx.guild.id)
        
        if campaign_id not in campaigns:
            await ctx.send(f"❌ Campaign `{campaign_id}` not found.")
            return
        
        campaign = campaigns[campaign_id]
        
        embed = discord.Embed(
            title=f"🔍 Hunt Campaign Details",
            description=campaign['name'],
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Campaign ID", value=f"`{campaign['id']}`", inline=True)
        embed.add_field(name="Status", value=campaign['status'].upper(), inline=True)
        embed.add_field(name="Threat Type", value=campaign['threat_type'], inline=True)
        embed.add_field(name="Created By", value=f"<@{campaign['created_by']}>", inline=True)
        embed.add_field(name="Created At", value=f"<t:{int(datetime.fromisoformat(campaign['created_at']).timestamp())}:R>", inline=True)
        embed.add_field(name="Duration", value=f"{(datetime.utcnow() - datetime.fromisoformat(campaign['created_at'])).days} days", inline=True)
        
        embed.add_field(name="Description", value=campaign['description'], inline=False)
        
        embed.add_field(name=f"🎯 Hunt Queries ({len(campaign['hunt_queries'])})", 
                       value="\n".join([f"• {q}" for q in campaign['hunt_queries'][:5]]) or "No queries yet", 
                       inline=False)
        
        embed.add_field(name=f"📊 Findings ({campaign['findings_count']})", 
                       value="\n".join([f"• {f['description'][:50]}..." for f in campaign['findings'][:5]]) or "No findings yet", 
                       inline=False)
        
        embed.set_footer(text="Sentinel Threat Hunting Campaign")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='huntcampaign')
    async def huntcampaign_prefix(self, ctx, threat_type: str, *, args: str):
        """Create hunt campaign - Prefix command"""
        parts = args.split('|')
        if len(parts) < 2:
            await ctx.send("Usage: `!huntcampaign <threat_type> <name> | <description>`")
            return
        
        name = parts[0].strip()
        description = parts[1].strip()
        await self._huntcampaign_logic(ctx, name, threat_type, description=description)
    
    @commands.command(name='huntsearch')
    async def huntsearch_prefix(self, ctx, campaign_id: str, *, query: str):
        """Add hunt query - Prefix command"""
        await self._huntsearch_logic(ctx, campaign_id, query=query)
    
    @commands.command(name='huntfinding')
    async def huntfinding_prefix(self, ctx, campaign_id: str, severity: str, *, description: str):
        """Log hunt finding - Prefix command"""
        await self._huntfinding_logic(ctx, campaign_id, severity, description=description)
    
    @commands.command(name='huntlist')
    async def huntlist_prefix(self, ctx, status: str = 'active'):
        """List hunt campaigns - Prefix command"""
        await self._huntlist_logic(ctx, status)
    
    @commands.command(name='huntdetail')
    async def huntdetail_prefix(self, ctx, campaign_id: str):
        """Show campaign details - Prefix command"""
        await self._huntdetail_logic(ctx, campaign_id)

async def setup(bot):
    await bot.add_cog(ThreatHuntingCampaigns(bot))
