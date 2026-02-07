"""
Moderation History & Appeals: Track moderation actions and handle appeals
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import json
import os
from cogs.core.pst_timezone import get_now_pst

class ModerationHistory(commands.Cog):
    """Moderation history tracking and appeals system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.history_file = os.path.join(self.data_dir, "moderation_history.json")
        self.appeals_file = os.path.join(self.data_dir, "moderation_appeals.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.history = self._load_history()
        self.appeals = self._load_appeals()
    
    def _load_history(self):
        """Load moderation history from file"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_history(self):
        """Save moderation history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _load_appeals(self):
        """Load appeals from file"""
        if os.path.exists(self.appeals_file):
            with open(self.appeals_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_appeals(self):
        """Save appeals to file"""
        with open(self.appeals_file, 'w') as f:
            json.dump(self.appeals, f, indent=2)
    
    def log_action(self, guild_id: int, user_id: int, action_type: str, moderator_id: int, reason: str):
        """Log a moderation action"""
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key not in self.history:
            self.history[guild_key] = {}
        
        if user_key not in self.history[guild_key]:
            self.history[guild_key][user_key] = []
        
        action = {
            'type': action_type,
            'moderator_id': moderator_id,
            'reason': reason,
            'timestamp': get_now_pst().isoformat()
        }
        
        self.history[guild_key][user_key].append(action)
        self._save_history()
    
    # ==================== MODERATION HISTORY ====================
    
    @commands.command(name='modhistory')
    @commands.has_permissions(manage_messages=True)
    async def modhistory(self, ctx, member: discord.Member):
        """View a member's moderation history"""
        await self._modhistory_logic(ctx, member)
    
    @app_commands.command(name="modhistory", description="View a member's moderation history")
    @app_commands.describe(member="Member to view history for")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def modhistory_slash(self, interaction: discord.Interaction, member: discord.Member):
        """View history using slash command"""
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
        await self._modhistory_logic(ctx, member)
    
    async def _modhistory_logic(self, ctx, member: discord.Member):
        guild_key = str(ctx.guild.id)
        user_key = str(member.id)
        
        if guild_key not in self.history or user_key not in self.history[guild_key]:
            await ctx.send(f"📋 No moderation history found for {member.mention}")
            return
        
        actions = self.history[guild_key][user_key]
        
        embed = discord.Embed(
            title=f"📋 Moderation History: {member.name}",
            description=f"User: {member.mention} ({member.id})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Count action types
        action_counts = {}
        for action in actions:
            action_type = action['type']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # Add summary
        summary = "\n".join([f"• {type.title()}: {count}" for type, count in action_counts.items()])
        embed.add_field(name="Summary", value=summary or "No actions", inline=False)
        
        # Add recent actions (last 5)
        recent = actions[-5:]
        recent.reverse()
        
        for i, action in enumerate(recent, 1):
            try:
                moderator = await self.bot.fetch_user(action['moderator_id'])
                mod_name = str(moderator)
            except:
                mod_name = f"Unknown ({action['moderator_id']})"
            
            timestamp = datetime.fromisoformat(action['timestamp'])
            
            field_value = f"**Moderator:** {mod_name}\n"
            field_value += f"**Reason:** {action['reason'][:100]}\n"
            field_value += f"**Date:** <t:{int(timestamp.timestamp())}:R>"
            
            embed.add_field(
                name=f"{i}. {action['type'].title()}",
                value=field_value,
                inline=False
            )
        
        if len(actions) > 5:
            embed.set_footer(text=f"Showing 5 of {len(actions)} total actions")
        
        await ctx.send(embed=embed)
    
    # ==================== APPEALS ====================
    
    @commands.command(name='mod_appeal')
    async def appeal(self, ctx, *, reason: str = None):
        """Submit a ban/mute appeal"""
        await self._appeal_logic(ctx, reason)
    
    @app_commands.command(name="appeal", description="Submit a ban/mute appeal")
    @app_commands.describe(reason="Why should your punishment be lifted?")
    async def appeal_slash(self, interaction: discord.Interaction, reason: Optional[str] = None):
        """Submit appeal using slash command"""
        await interaction.response.defer(ephemeral=True)
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                kwargs['ephemeral'] = True
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'], ephemeral=True)
                return await interaction.followup.send(content=kwargs.get('content', ''), ephemeral=True)
        
        ctx = FakeCtx(interaction)
        await self._appeal_logic(ctx, reason)
    
    async def _appeal_logic(self, ctx, reason: Optional[str]):
        if not reason:
            await ctx.send("❌ Please provide a reason for your appeal")
            return
        
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.appeals:
            self.appeals[guild_key] = []
        
        appeal_id = len(self.appeals[guild_key]) + 1
        
        appeal = {
            'id': appeal_id,
            'user_id': ctx.author.id,
            'user_name': str(ctx.author),
            'reason': reason,
            'status': 'pending',
            'timestamp': get_now_pst().isoformat(),
            'reviewed_by': None,
            'review_note': None
        }
        
        self.appeals[guild_key].append(appeal)
        self._save_appeals()
        
        # Send confirmation to user
        embed = discord.Embed(
            title="✅ Appeal Submitted",
            description="Your appeal has been submitted for review",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Appeal ID", value=f"#{appeal_id}", inline=True)
        embed.add_field(name="Status", value="⏳ Pending", inline=True)
        embed.add_field(name="Your Reason", value=reason[:1000], inline=False)
        embed.set_footer(text="You will be notified when your appeal is reviewed")
        
        await ctx.send(embed=embed)
        
        # Notify moderators (find mod channel or use system channel)
        try:
            # Try to find a channel with "mod" in the name
            mod_channel = None
            for channel in ctx.guild.text_channels:
                if 'mod' in channel.name.lower():
                    mod_channel = channel
                    break
            
            if mod_channel:
                notif_embed = discord.Embed(
                    title="📝 New Appeal Submitted",
                    description=f"Appeal #{appeal_id}",
                    color=discord.Color.gold(),
                    timestamp=get_now_pst()
                )
                notif_embed.add_field(name="User", value=ctx.author.mention, inline=True)
                notif_embed.add_field(name="Status", value="⏳ Pending", inline=True)
                notif_embed.add_field(name="Reason", value=reason[:1000], inline=False)
                notif_embed.set_footer(text=f"Use /reviewappeal {appeal_id} <approve/deny> <note> to review")
                
                await mod_channel.send(embed=notif_embed)
        except:
            pass
    
    # ==================== REVIEW APPEAL ====================
    
    @commands.command(name='mod_reviewappeal')
    @commands.has_permissions(manage_guild=True)
    async def reviewappeal(self, ctx, appeal_id: int, decision: str, *, note: str = "No note provided"):
        """Review a pending appeal"""
        await self._reviewappeal_logic(ctx, appeal_id, decision, note)
    
    @app_commands.command(name="reviewappeal", description="Review a pending appeal")
    @app_commands.describe(
        appeal_id="Appeal ID to review",
        decision="Decision: approve or deny",
        note="Note for the user"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reviewappeal_slash(self, interaction: discord.Interaction, appeal_id: int, decision: str, note: str = "No note provided"):
        """Review appeal using slash command"""
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
        await self._reviewappeal_logic(ctx, appeal_id, decision, note)
    
    async def _reviewappeal_logic(self, ctx, appeal_id: int, decision: str, note: str):
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.appeals:
            await ctx.send("❌ No appeals found for this server")
            return
        
        appeal = None
        for a in self.appeals[guild_key]:
            if a['id'] == appeal_id:
                appeal = a
                break
        
        if not appeal:
            await ctx.send(f"❌ Appeal #{appeal_id} not found")
            return
        
        if appeal['status'] != 'pending':
            await ctx.send(f"❌ Appeal #{appeal_id} has already been reviewed ({appeal['status']})")
            return
        
        decision = decision.lower()
        if decision not in ['approve', 'deny', 'approved', 'denied']:
            await ctx.send("❌ Decision must be 'approve' or 'deny'")
            return
        
        # Update appeal
        appeal['status'] = 'approved' if decision.startswith('approve') else 'denied'
        appeal['reviewed_by'] = ctx.author.id
        appeal['review_note'] = note
        appeal['reviewed_at'] = get_now_pst().isoformat()
        
        self._save_appeals()
        
        # Notify user
        try:
            user = await self.bot.fetch_user(appeal['user_id'])
            
            user_embed = discord.Embed(
                title=f"{'✅ Appeal Approved' if appeal['status'] == 'approved' else '❌ Appeal Denied'}",
                description=f"Your appeal (#{appeal_id}) has been reviewed",
                color=discord.Color.green() if appeal['status'] == 'approved' else discord.Color.red(),
                timestamp=get_now_pst()
            )
            user_embed.add_field(name="Decision", value=appeal['status'].title(), inline=True)
            user_embed.add_field(name="Reviewed by", value=str(ctx.author), inline=True)
            user_embed.add_field(name="Note", value=note, inline=False)
            user_embed.set_footer(text=f"Server: {ctx.guild.name}")
            
            await user.send(embed=user_embed)
        except:
            pass
        
        # Confirmation
        confirm_embed = discord.Embed(
            title=f"{'✅ Appeal Approved' if appeal['status'] == 'approved' else '❌ Appeal Denied'}",
            description=f"Appeal #{appeal_id} has been {appeal['status']}",
            color=discord.Color.green() if appeal['status'] == 'approved' else discord.Color.red(),
            timestamp=get_now_pst()
        )
        confirm_embed.add_field(name="User", value=f"<@{appeal['user_id']}>", inline=True)
        confirm_embed.add_field(name="Reviewer", value=ctx.author.mention, inline=True)
        confirm_embed.add_field(name="Decision Note", value=note, inline=False)
        
        await ctx.send(embed=confirm_embed)
    
    # ==================== LIST APPEALS ====================
    
    @commands.command(name='listappeals')
    @commands.has_permissions(manage_guild=True)
    async def listappeals(self, ctx, status: str = "pending"):
        """List appeals by status"""
        await self._listappeals_logic(ctx, status)
    
    @app_commands.command(name="listappeals", description="List appeals by status")
    @app_commands.describe(status="Filter by status: pending, approved, denied, all")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def listappeals_slash(self, interaction: discord.Interaction, status: str = "pending"):
        """List appeals using slash command"""
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
        await self._listappeals_logic(ctx, status)
    
    async def _listappeals_logic(self, ctx, status: str):
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.appeals or not self.appeals[guild_key]:
            await ctx.send("📋 No appeals found for this server")
            return
        
        status = status.lower()
        
        if status == "all":
            filtered = self.appeals[guild_key]
        else:
            filtered = [a for a in self.appeals[guild_key] if a['status'] == status]
        
        if not filtered:
            await ctx.send(f"📋 No {status} appeals found")
            return
        
        embed = discord.Embed(
            title=f"📋 Appeals ({status.title()})",
            description=f"Total: {len(filtered)} appeal(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for appeal in filtered[-10:]:  # Last 10
            timestamp = datetime.fromisoformat(appeal['timestamp'])
            
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'denied': '❌'
            }.get(appeal['status'], '❓')
            
            field_value = f"**User:** <@{appeal['user_id']}>\n"
            field_value += f"**Status:** {status_emoji} {appeal['status'].title()}\n"
            field_value += f"**Submitted:** <t:{int(timestamp.timestamp())}:R>\n"
            field_value += f"**Reason:** {appeal['reason'][:100]}"
            
            embed.add_field(
                name=f"Appeal #{appeal['id']}",
                value=field_value,
                inline=False
            )
        
        if len(filtered) > 10:
            embed.set_footer(text=f"Showing 10 of {len(filtered)} total appeals")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationHistory(bot))

