"""
Forensics & Evidence Management - Chain of custody and evidence collection for Sentinel
Manages evidence collection, storage, and timeline reconstruction for incident investigations
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

class ForensicsEvidenceManager(commands.Cog):
    """Forensic evidence management and chain of custody"""
    
    def __init__(self, bot):
        self.bot = bot
        self.evidence_file = 'data/evidence.json'
        self.load_evidence()
    
    def load_evidence(self):
        """Load evidence records"""
        if not os.path.exists(self.evidence_file):
            os.makedirs(os.path.dirname(self.evidence_file), exist_ok=True)
            with open(self.evidence_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_evidence(self, guild_id):
        """Get evidence for a guild"""
        with open(self.evidence_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_evidence(self, guild_id, evidence):
        """Save evidence"""
        with open(self.evidence_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = evidence
        with open(self.evidence_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_evidence_hash(self, content):
        """Create SHA256 hash of evidence"""
        return hashlib.sha256(str(content).encode()).hexdigest()[:16]
    
    def add_evidence(self, guild_id, incident_id, evidence_type, description, content, collector):
        """Add evidence to an incident"""
        evidence_dict = self.get_guild_evidence(guild_id)
        
        if incident_id not in evidence_dict:
            evidence_dict[incident_id] = []
        
        evidence = {
            'id': str(uuid.uuid4())[:8],
            'type': evidence_type,
            'description': description,
            'content_hash': self.create_evidence_hash(content),
            'content_preview': str(content)[:200],
            'collected_at': get_now_pst().isoformat(),
            'collected_by': collector,
            'chain_of_custody': [
                {
                    'action': 'collected',
                    'user': collector,
                    'timestamp': get_now_pst().isoformat()
                }
            ]
        }
        
        evidence_dict[incident_id].append(evidence)
        self.save_evidence(guild_id, evidence_dict)
        return evidence
    
    def get_evidence_type_emoji(self, evidence_type):
        """Get emoji for evidence type"""
        emoji_map = {
            'screenshot': '📸',
            'log': '📋',
            'message': '💬',
            'user_activity': '👤',
            'audit_log': '📊',
            'code': '💻',
            'file': '📁',
            'other': '📌'
        }
        return emoji_map.get(evidence_type.lower(), '📌')
    
    async def _evidencecollect_logic(self, ctx, incident_id: str, evidence_type: str, *, description: str):
        """Collect evidence for an incident"""
        valid_types = ['screenshot', 'log', 'message', 'user_activity', 'audit_log', 'code', 'file', 'other']
        
        if evidence_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid evidence type. Use: {', '.join(valid_types)}")
            return
        
        evidence = self.add_evidence(
            ctx.guild.id,
            incident_id,
            evidence_type,
            description,
            f"Evidence collected: {description}",
            ctx.author.id
        )
        
        emoji = self.get_evidence_type_emoji(evidence_type)
        
        embed = discord.Embed(
            title=f"{emoji} Evidence Collected",
            description=f"Incident: `{incident_id}`",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Evidence ID", value=f"`{evidence['id']}`", inline=True)
        embed.add_field(name="Type", value=evidence_type.upper(), inline=True)
        embed.add_field(name="Collected By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Hash (Integrity)", value=f"`{evidence['content_hash']}`", inline=True)
        embed.add_field(name="Status", value="✅ Admitted to Evidence", inline=True)
        embed.set_footer(text="Chain of custody initialized")
        
        await ctx.send(embed=embed)
    
    async def _evidencelist_logic(self, ctx, incident_id: str):
        """List all evidence for an incident"""
        evidence_dict = self.get_guild_evidence(ctx.guild.id)
        
        if incident_id not in evidence_dict or not evidence_dict[incident_id]:
            await ctx.send(f"❌ No evidence found for incident `{incident_id}`")
            return
        
        evidence_list = evidence_dict[incident_id]
        
        embed = discord.Embed(
            title="📋 Incident Evidence Chain",
            description=f"Incident: `{incident_id}` | {len(evidence_list)} item(s)",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        for evidence in evidence_list[:8]:
            emoji = self.get_evidence_type_emoji(evidence['type'])
            embed.add_field(
                name=f"{emoji} {evidence['type'].upper()} (ID: {evidence['id']})",
                value=f"Collected: <t:{int(datetime.fromisoformat(evidence['collected_at']).timestamp())}:R>\nHash: `{evidence['content_hash']}`",
                inline=False
            )
        
        if len(evidence_list) > 8:
            embed.add_field(name="... and more", value=f"+{len(evidence_list) - 8} additional evidence items", inline=False)
        
        embed.set_footer(text="Sentinel Forensics System")
        
        await ctx.send(embed=embed)
    
    async def _evidencedetail_logic(self, ctx, incident_id: str, evidence_id: str):
        """Show detailed evidence information"""
        evidence_dict = self.get_guild_evidence(ctx.guild.id)
        
        if incident_id not in evidence_dict:
            await ctx.send(f"❌ Incident `{incident_id}` not found")
            return
        
        evidence_list = evidence_dict[incident_id]
        evidence = next((e for e in evidence_list if e['id'] == evidence_id), None)
        
        if not evidence:
            await ctx.send(f"❌ Evidence `{evidence_id}` not found in incident `{incident_id}`")
            return
        
        emoji = self.get_evidence_type_emoji(evidence['type'])
        
        embed = discord.Embed(
            title=f"{emoji} Evidence Details",
            description=evidence['description'],
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Evidence ID", value=f"`{evidence['id']}`", inline=True)
        embed.add_field(name="Incident ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Type", value=evidence['type'].upper(), inline=True)
        embed.add_field(name="Collected At", value=f"<t:{int(datetime.fromisoformat(evidence['collected_at']).timestamp())}:F>", inline=True)
        embed.add_field(name="Collected By", value=f"<@{evidence['collected_by']}>", inline=True)
        embed.add_field(name="Integrity Hash", value=f"`{evidence['content_hash']}`", inline=True)
        embed.add_field(name="Content Preview", value=f"```{evidence['content_preview']}...```", inline=False)
        
        # Chain of custody
        coc_str = ""
        for action in evidence['chain_of_custody']:
            coc_str += f"• {action['action'].upper()}: <@{action['user']}> at <t:{int(datetime.fromisoformat(action['timestamp']).timestamp())}:R>\n"
        
        embed.add_field(name="⛓️ Chain of Custody", value=coc_str or "No custody transfers", inline=False)
        
        embed.set_footer(text="Sentinel Forensics | Integrity verified")
        
        await ctx.send(embed=embed)
    
    async def _timeline_logic(self, ctx, incident_id: str):
        """Show forensic timeline for incident"""
        evidence_dict = self.get_guild_evidence(ctx.guild.id)
        
        if incident_id not in evidence_dict or not evidence_dict[incident_id]:
            await ctx.send(f"❌ No evidence timeline for incident `{incident_id}`")
            return
        
        evidence_list = sorted(
            evidence_dict[incident_id],
            key=lambda e: e['collected_at']
        )
        
        embed = discord.Embed(
            title="🕐 Forensic Timeline",
            description=f"Incident: `{incident_id}` | {len(evidence_list)} events",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        timeline_str = ""
        for i, evidence in enumerate(evidence_list, 1):
            emoji = self.get_evidence_type_emoji(evidence['type'])
            timestamp = datetime.fromisoformat(evidence['collected_at']).timestamp()
            timeline_str += f"{i}. <t:{int(timestamp)}:R> - {emoji} {evidence['type'].upper()}\n"
        
        if timeline_str:
            embed.add_field(name="📋 Event Sequence", value=timeline_str, inline=False)
        
        embed.add_field(name="Total Evidence Items", value=str(len(evidence_list)), inline=True)
        embed.add_field(name="First Event", value=f"<t:{int(datetime.fromisoformat(evidence_list[0]['collected_at']).timestamp())}:R>", inline=True)
        embed.add_field(name="Last Event", value=f"<t:{int(datetime.fromisoformat(evidence_list[-1]['collected_at']).timestamp())}:R>", inline=True)
        
        embed.set_footer(text="Sentinel Forensics Timeline | Chronological view")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='evidencecollect')
    async def evidencecollect_prefix(self, ctx, incident_id: str, evidence_type: str, *, description: str):
        """Collect evidence for incident - Prefix command"""
        await self._evidencecollect_logic(ctx, incident_id, evidence_type, description=description)
    
    @commands.command(name='evidencelist')
    async def evidencelist_prefix(self, ctx, incident_id: str):
        """List evidence for incident - Prefix command"""
        await self._evidencelist_logic(ctx, incident_id)
    
    @commands.command(name='evidencedetail')
    async def evidencedetail_prefix(self, ctx, incident_id: str, evidence_id: str):
        """Show evidence details - Prefix command"""
        await self._evidencedetail_logic(ctx, incident_id, evidence_id)
    
    @commands.command(name='timeline')
    async def timeline_prefix(self, ctx, incident_id: str):
        """Show forensic timeline - Prefix command"""
        await self._timeline_logic(ctx, incident_id)

async def setup(bot):
    await bot.add_cog(ForensicsEvidenceManager(bot))
