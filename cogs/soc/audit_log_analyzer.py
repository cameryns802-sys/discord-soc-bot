"""
Audit Log Analyzer: Automatically analyze Discord audit logs for threats
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import json
from cogs.core.pst_timezone import get_now_pst

class AuditLogAnalyzer(commands.Cog):
    """Analyze audit logs for suspicious activity"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='auditanalyze')
    @commands.has_permissions(view_audit_log=True)
    async def auditanalyze(self, ctx, hours: int = 1):
        """Analyze audit logs for threats"""
        await self._auditanalyze_logic(ctx, hours)
    
    @app_commands.command(name="auditanalyze", description="Analyze audit logs for threats")
    @app_commands.checks.has_permissions(view_audit_log=True)
    async def auditanalyze_slash(self, interaction: discord.Interaction, hours: int = 1):
        """Audit analysis using slash command"""
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
        await self._auditanalyze_logic(ctx, hours)
    
    async def _auditanalyze_logic(self, ctx, hours: int):
        guild = ctx.guild
        
        if hours < 1 or hours > 24:
            hours = 1
        
        # Fetch audit logs
        time_filter = get_now_pst() - timedelta(hours=hours)
        
        audit_data = {
            'kicks': 0,
            'bans': 0,
            'timeouts': 0,
            'role_changes': 0,
            'channel_changes': 0,
            'permission_changes': 0,
            'deletions': 0,
            'suspicious_actors': {}
        }
        
        try:
            async for entry in guild.audit_logs(limit=500, oldest_first=False):
                if entry.created_at < time_filter:
                    break
                
                # Track by actor
                actor_name = str(entry.user)
                if actor_name not in audit_data['suspicious_actors']:
                    audit_data['suspicious_actors'][actor_name] = 0
                
                # Categorize actions
                if entry.action == discord.AuditLogAction.kick:
                    audit_data['kicks'] += 1
                    audit_data['suspicious_actors'][actor_name] += 1
                
                elif entry.action == discord.AuditLogAction.ban:
                    audit_data['bans'] += 1
                    audit_data['suspicious_actors'][actor_name] += 1
                
                elif entry.action == discord.AuditLogAction.member_update:
                    if entry.changes and hasattr(entry.changes, 'communication_disabled_since'):
                        audit_data['timeouts'] += 1
                
                elif entry.action == discord.AuditLogAction.member_role_update:
                    audit_data['role_changes'] += 1
                    audit_data['suspicious_actors'][actor_name] += 0.5
                
                elif entry.action == discord.AuditLogAction.channel_update:
                    audit_data['channel_changes'] += 1
                    audit_data['suspicious_actors'][actor_name] += 0.5
                
                elif entry.action == discord.AuditLogAction.channel_delete:
                    audit_data['deletions'] += 1
                    audit_data['suspicious_actors'][actor_name] += 2
                
                elif entry.action == discord.AuditLogAction.overwrite_create:
                    audit_data['permission_changes'] += 1
                
                elif entry.action == discord.AuditLogAction.overwrite_delete:
                    audit_data['deletions'] += 1
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Audit Log Access Denied",
                description="Bot lacks permission to view audit logs",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Analyze suspicious activity
        suspicious = []
        
        if audit_data['bans'] > 5:
            suspicious.append(f"🚨 High ban rate: {audit_data['bans']} bans")
        
        if audit_data['kicks'] > 10:
            suspicious.append(f"⚠️ High kick rate: {audit_data['kicks']} kicks")
        
        if audit_data['deletions'] > 3:
            suspicious.append(f"🔴 Channel/content deletions: {audit_data['deletions']}")
        
        # Find top actor
        top_actor = max(audit_data['suspicious_actors'].items(), key=lambda x: x[1], default=None)
        if top_actor and top_actor[1] > 5:
            suspicious.append(f"👀 High activity from {top_actor[0]}: {int(top_actor[1])} actions")
        
        # Create report
        embed = discord.Embed(
            title=f"📊 Audit Log Analysis ({hours}h)",
            color=discord.Color.blue() if not suspicious else discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="📋 Actions Summary",
            value=f"**Bans:** {audit_data['bans']}\n**Kicks:** {audit_data['kicks']}\n**Timeouts:** {audit_data['timeouts']}\n**Role Changes:** {audit_data['role_changes']}",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Configuration Changes",
            value=f"**Channel Changes:** {audit_data['channel_changes']}\n**Permission Changes:** {audit_data['permission_changes']}\n**Deletions:** {audit_data['deletions']}",
            inline=True
        )
        
        if suspicious:
            embed.add_field(
                name="🚨 Suspicious Activity Detected",
                value="\n".join(suspicious),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ No Suspicious Activity",
                value="Audit logs appear normal",
                inline=False
            )
        
        embed.set_footer(text=f"Analyzed {sum(audit_data.values())} actions")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AuditLogAnalyzer(bot))

