"""
Incident Management: Create, track, and manage security incidents
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os
import uuid
from cogs.core.pst_timezone import get_now_pst

class IncidentManagement(commands.Cog):
    """Security incident case management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.incidents_file = 'data/incidents.json'
        os.makedirs('data', exist_ok=True)
        self._init_incidents()
    
    def _init_incidents(self):
        """Initialize incidents file"""
        if not os.path.exists(self.incidents_file):
            with open(self.incidents_file, 'w') as f:
                json.dump({}, f)
    
    def _load_incidents(self) -> dict:
        """Load incidents"""
        try:
            with open(self.incidents_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_incidents(self, incidents: dict):
        """Save incidents"""
        with open(self.incidents_file, 'w') as f:
            json.dump(incidents, f, indent=2)
    
    @commands.command(name='incidentcreate')
    @commands.has_permissions(manage_guild=True)
    async def incidentcreate(self, ctx, title: str, severity: str = "medium"):
        """Create new incident"""
        await self._incidentcreate_logic(ctx, title, severity)
    
    @app_commands.command(name="incidentcreate", description="Create a new security incident")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentcreate_slash(
        self,
        interaction: discord.Interaction,
        title: str,
        severity: str = "medium"
    ):
        """Create incident using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._incidentcreate_logic(ctx, title, severity.lower())
    
    async def _incidentcreate_logic(self, ctx, title: str, severity: str):
        """Create incident implementation"""
        if severity not in ['low', 'medium', 'high', 'critical']:
            severity = 'medium'
        
        incidents = self._load_incidents()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in incidents:
            incidents[guild_id] = {}
        
        incident_id = str(uuid.uuid4())[:8]
        
        incident = {
            'id': incident_id,
            'title': title,
            'severity': severity,
            'status': 'open',
            'created_at': get_now_pst().isoformat(),
            'created_by': str(ctx.author.id),
            'notes': [],
            'evidence': []
        }
        
        incidents[guild_id][incident_id] = incident
        self._save_incidents(incidents)
        
        embed = discord.Embed(
            title="✅ Incident Created",
            description=f"**{title}**",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        embed.add_field(name="ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Severity", value=f"{severity_emoji.get(severity, '?')} {severity.upper()}", inline=True)
        embed.add_field(name="Status", value="🔓 OPEN", inline=True)
        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Next Steps", value=f"Use `/incidentaddnote {incident_id}` to add details", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='incidentlist')
    @commands.has_permissions(manage_guild=True)
    async def incidentlist(self, ctx, status: str = "open"):
        """List incidents"""
        await self._incidentlist_logic(ctx, status)
    
    @app_commands.command(name="incidentlist", description="List security incidents")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentlist_slash(
        self,
        interaction: discord.Interaction,
        status: str = "open"
    ):
        """List incidents using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._incidentlist_logic(ctx, status.lower())
    
    async def _incidentlist_logic(self, ctx, status: str):
        """List incidents implementation"""
        incidents = self._load_incidents()
        guild_id = str(ctx.guild.id)
        
        guild_incidents = incidents.get(guild_id, {})
        
        # Filter by status
        filtered = {k: v for k, v in guild_incidents.items() if v.get('status') == status}
        
        if not filtered:
            await ctx.send(f"No **{status}** incidents found.")
            return
        
        embed = discord.Embed(
            title=f"📋 {status.upper()} Incidents",
            description=f"Total: {len(filtered)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        for inc_id, incident in list(filtered.items())[:10]:
            emoji = severity_emoji.get(incident.get('severity'), '?')
            
            created = datetime.fromisoformat(incident['created_at'])
            age = (get_now_pst() - created).total_seconds() / 3600
            age_text = f"{int(age)}h ago" if age < 24 else f"{int(age/24)}d ago"
            
            embed.add_field(
                name=f"{emoji} {incident['title']}",
                value=f"ID: `{inc_id}` | {age_text}\nNotes: {len(incident.get('notes', []))}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='incidentaddnote')
    @commands.has_permissions(manage_guild=True)
    async def incidentaddnote(self, ctx, incident_id: str, *, note: str):
        """Add note to incident"""
        await self._incidentaddnote_logic(ctx, incident_id, note)
    
    @app_commands.command(name="incidentaddnote", description="Add note to incident")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentaddnote_slash(
        self,
        interaction: discord.Interaction,
        incident_id: str,
        note: str
    ):
        """Add note using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._incidentaddnote_logic(ctx, incident_id, note)
    
    async def _incidentaddnote_logic(self, ctx, incident_id: str, note: str):
        """Add note implementation"""
        incidents = self._load_incidents()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in incidents or incident_id not in incidents[guild_id]:
            await ctx.send(f"❌ Incident `{incident_id}` not found.")
            return
        
        incident = incidents[guild_id][incident_id]
        
        note_entry = {
            'timestamp': get_now_pst().isoformat(),
            'author': str(ctx.author.id),
            'text': note
        }
        
        if 'notes' not in incident:
            incident['notes'] = []
        
        incident['notes'].append(note_entry)
        self._save_incidents(incidents)
        
        embed = discord.Embed(
            title="✅ Note Added",
            description=note,
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Incident", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Total Notes", value=str(len(incident['notes'])), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='incidentclose')
    @commands.has_permissions(manage_guild=True)
    async def incidentclose(self, ctx, incident_id: str):
        """Close an incident"""
        await self._incidentclose_logic(ctx, incident_id)
    
    @app_commands.command(name="incidentclose", description="Close a security incident")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentclose_slash(
        self,
        interaction: discord.Interaction,
        incident_id: str
    ):
        """Close incident using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._incidentclose_logic(ctx, incident_id)
    
    async def _incidentclose_logic(self, ctx, incident_id: str):
        """Close incident implementation"""
        incidents = self._load_incidents()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in incidents or incident_id not in incidents[guild_id]:
            await ctx.send(f"❌ Incident `{incident_id}` not found.")
            return
        
        incident = incidents[guild_id][incident_id]
        incident['status'] = 'closed'
        incident['closed_at'] = get_now_pst().isoformat()
        incident['closed_by'] = str(ctx.author.id)
        
        self._save_incidents(incidents)
        
        embed = discord.Embed(
            title="✅ Incident Closed",
            description=incident['title'],
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Status", value="🔒 CLOSED", inline=True)
        embed.add_field(name="Total Notes", value=str(len(incident.get('notes', []))), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='incidentdetail')
    @commands.has_permissions(manage_guild=True)
    async def incidentdetail(self, ctx, incident_id: str):
        """View incident details"""
        await self._incidentdetail_logic(ctx, incident_id)
    
    @app_commands.command(name="incidentdetail", description="View incident details")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def incidentdetail_slash(
        self,
        interaction: discord.Interaction,
        incident_id: str
    ):
        """Detail using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._incidentdetail_logic(ctx, incident_id)
    
    async def _incidentdetail_logic(self, ctx, incident_id: str):
        """Detail implementation"""
        incidents = self._load_incidents()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in incidents or incident_id not in incidents[guild_id]:
            await ctx.send(f"❌ Incident `{incident_id}` not found.")
            return
        
        incident = incidents[guild_id][incident_id]
        
        severity_color = {
            'low': discord.Color.green(),
            'medium': discord.Color.gold(),
            'high': discord.Color.orange(),
            'critical': discord.Color.red()
        }
        
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        embed = discord.Embed(
            title=f"{severity_emoji.get(incident['severity'], '?')} {incident['title']}",
            color=severity_color.get(incident['severity'], discord.Color.blue()),
            timestamp=get_now_pst()
        )
        
        # Status
        status_emoji = '🔒' if incident['status'] == 'closed' else '🔓'
        embed.add_field(
            name="Status",
            value=f"{status_emoji} {incident['status'].upper()}",
            inline=True
        )
        
        embed.add_field(name="ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Severity", value=incident['severity'].upper(), inline=True)
        
        # Timeline
        created = datetime.fromisoformat(incident['created_at'])
        embed.add_field(name="Created", value=f"<t:{int(created.timestamp())}:R>", inline=True)
        
        if incident['status'] == 'closed':
            closed = datetime.fromisoformat(incident['closed_at'])
            embed.add_field(name="Closed", value=f"<t:{int(closed.timestamp())}:R>", inline=True)
        
        # Notes
        notes = incident.get('notes', [])
        if notes:
            notes_text = ""
            for note in notes[-3:]:  # Last 3 notes
                try:
                    note_time = datetime.fromisoformat(note['timestamp'])
                    notes_text += f"• {note['text'][:50]}... <t:{int(note_time.timestamp())}:R>\n"
                except:
                    notes_text += f"• {note['text'][:50]}...\n"
            
            embed.add_field(
                name=f"📝 Recent Notes ({len(notes)} total)",
                value=notes_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IncidentManagement(bot))

