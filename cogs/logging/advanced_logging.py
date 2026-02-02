"""
Advanced Logging System
Comprehensive event logging for audit trails and security monitoring.
Tracks messages, members, roles, channels, moderation actions, and server changes.
"""

import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
from typing import Optional

class AdvancedLogging(commands.Cog):
    """Comprehensive logging system for security and audit purposes"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/logging_config.json'
        self.load_config()
    
    def load_config(self):
        """Load logging configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
    
    def save_config(self):
        """Save logging configuration"""
        os.makedirs('data', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get_log_channel(self, guild_id: int, log_type: str) -> Optional[int]:
        """Get configured log channel for specific event type"""
        guild_config = self.config.get(str(guild_id), {})
        return guild_config.get(log_type) or guild_config.get('default')
    
    async def send_log(self, guild: discord.Guild, log_type: str, embed: discord.Embed):
        """Send log embed to configured channel"""
        channel_id = self.get_log_channel(guild.id, log_type)
        if not channel_id:
            return
        
        channel = guild.get_channel(channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass  # No permission to send
            except Exception as e:
                print(f"[AdvancedLogging] Error sending log: {e}")
    
    # ==================== MESSAGE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log deleted messages"""
        if message.author.bot or not message.guild:
            return
        
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=str(message.id), inline=True)
        
        # Message content (truncate if too long)
        content = message.content or "*[No text content]*"
        if len(content) > 1024:
            content = content[:1020] + "..."
        embed.add_field(name="Content", value=content, inline=False)
        
        # Attachments
        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            embed.add_field(name="Attachments", value=attachments, inline=False)
        
        embed.set_footer(text=f"User ID: {message.author.id}")
        if message.author.avatar:
            embed.set_thumbnail(url=message.author.avatar.url)
        
        await self.send_log(message.guild, 'message_delete', embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log edited messages"""
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=f"[Jump to Message]({after.jump_url})", inline=True)
        
        # Before content
        before_content = before.content or "*[No content]*"
        if len(before_content) > 512:
            before_content = before_content[:509] + "..."
        embed.add_field(name="Before", value=before_content, inline=False)
        
        # After content
        after_content = after.content or "*[No content]*"
        if len(after_content) > 512:
            after_content = after_content[:509] + "..."
        embed.add_field(name="After", value=after_content, inline=False)
        
        embed.set_footer(text=f"User ID: {before.author.id}")
        if before.author.avatar:
            embed.set_thumbnail(url=before.author.avatar.url)
        
        await self.send_log(before.guild, 'message_edit', embed)
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Log bulk message deletions"""
        if not messages or not messages[0].guild:
            return
        
        guild = messages[0].guild
        channel = messages[0].channel
        
        embed = discord.Embed(
            title="🗑️ Bulk Message Delete",
            description=f"{len(messages)} messages deleted in {channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Group by author
        authors = {}
        for msg in messages:
            author_name = str(msg.author)
            authors[author_name] = authors.get(author_name, 0) + 1
        
        author_list = "\n".join([f"{name}: {count}" for name, count in sorted(authors.items(), key=lambda x: -x[1])[:10]])
        embed.add_field(name="Messages by Author", value=author_list or "Unknown", inline=False)
        
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Total Deleted", value=str(len(messages)), inline=True)
        
        await self.send_log(guild, 'message_bulk_delete', embed)
    
    # ==================== MEMBER EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log member joins"""
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} joined the server",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        
        # Account age warning
        account_age = (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        if account_age < 7:
            embed.add_field(name="⚠️ Warning", value=f"New account ({account_age} days old)", inline=False)
        
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await self.send_log(member.guild, 'member_join', embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log member leaves/kicks"""
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"{member.mention} left the server",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
        
        # Show roles
        if len(member.roles) > 1:
            roles = ", ".join([r.mention for r in member.roles[1:] if r.name != "@everyone"][:10])
            if roles:
                embed.add_field(name="Roles", value=roles, inline=False)
        
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await self.send_log(member.guild, 'member_leave', embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log member updates (roles, nickname, timeout)"""
        changes = []
        embed = discord.Embed(
            title="👤 Member Updated",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Nickname change
        if before.nick != after.nick:
            changes.append("Nickname")
            embed.add_field(
                name="Nickname Changed",
                value=f"**Before:** {before.nick or '*None*'}\n**After:** {after.nick or '*None*'}",
                inline=False
            )
        
        # Role changes
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            if added:
                changes.append("Roles Added")
                embed.add_field(name="➕ Roles Added", value=", ".join([r.mention for r in added]), inline=False)
            
            if removed:
                changes.append("Roles Removed")
                embed.add_field(name="➖ Roles Removed", value=", ".join([r.mention for r in removed]), inline=False)
        
        # Timeout changes
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                changes.append("Timed Out")
                embed.add_field(
                    name="⏰ Timed Out",
                    value=f"Until <t:{int(after.timed_out_until.timestamp())}:F>",
                    inline=False
                )
                embed.color = discord.Color.orange()
            else:
                changes.append("Timeout Removed")
                embed.add_field(name="✅ Timeout Removed", value="User can now interact again", inline=False)
                embed.color = discord.Color.green()
        
        if not changes:
            return  # No relevant changes
        
        embed.description = f"{after.mention} was updated"
        embed.add_field(name="User", value=f"{after} ({after.id})", inline=True)
        embed.add_field(name="Changes", value=", ".join(changes), inline=True)
        
        embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
        embed.set_footer(text=f"User ID: {after.id}")
        
        await self.send_log(after.guild, 'member_update', embed)
    
    # ==================== MODERATION EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Log bans"""
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{user.mention} was banned from the server",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        
        # Try to get ban reason from audit log
        try:
            await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).flatten()
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="Banned By", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason, inline=False)
                    break
        except:
            pass
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        await self.send_log(guild, 'member_ban', embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log unbans"""
        embed = discord.Embed(
            title="✅ Member Unbanned",
            description=f"{user.mention} was unbanned",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        
        # Try to get unban info from audit log
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    embed.add_field(name="Unbanned By", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Reason", value=entry.reason, inline=False)
                    break
        except:
            pass
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        await self.send_log(guild, 'member_unban', embed)
    
    # ==================== CHANNEL EVENTS ====================
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        embed = discord.Embed(
            title="➕ Channel Created",
            description=f"{channel.mention} was created",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Channel", value=f"{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)
        
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_log(channel.guild, 'channel_create', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        embed = discord.Embed(
            title="➖ Channel Deleted",
            description=f"#{channel.name} was deleted",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Channel", value=f"{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)
        
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_log(channel.guild, 'channel_delete', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Log channel updates"""
        changes = []
        embed = discord.Embed(
            title="🔧 Channel Updated",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Name change
        if before.name != after.name:
            changes.append("Name")
            embed.add_field(name="Name Changed", value=f"**Before:** {before.name}\n**After:** {after.name}", inline=False)
        
        # Topic change (text channels)
        if hasattr(before, 'topic') and before.topic != after.topic:
            changes.append("Topic")
            before_topic = before.topic or "*None*"
            after_topic = after.topic or "*None*"
            if len(before_topic) > 100:
                before_topic = before_topic[:97] + "..."
            if len(after_topic) > 100:
                after_topic = after_topic[:97] + "..."
            embed.add_field(name="Topic Changed", value=f"**Before:** {before_topic}\n**After:** {after_topic}", inline=False)
        
        # Slowmode change
        if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append("Slowmode")
            embed.add_field(
                name="Slowmode Changed",
                value=f"**Before:** {before.slowmode_delay}s\n**After:** {after.slowmode_delay}s",
                inline=False
            )
        
        # NSFW toggle
        if hasattr(before, 'nsfw') and before.nsfw != after.nsfw:
            changes.append("NSFW")
            embed.add_field(name="NSFW Changed", value=f"Now: {'Enabled' if after.nsfw else 'Disabled'}", inline=False)
        
        if not changes:
            return  # No relevant changes
        
        embed.description = f"{after.mention} was updated"
        embed.add_field(name="Channel", value=f"{after.name} ({after.id})", inline=True)
        embed.add_field(name="Changes", value=", ".join(changes), inline=True)
        
        embed.set_footer(text=f"Channel ID: {after.id}")
        
        await self.send_log(after.guild, 'channel_update', embed)
    
    # ==================== ROLE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Log role creation"""
        embed = discord.Embed(
            title="🎭 Role Created",
            description=f"{role.mention} was created",
            color=role.color if role.color != discord.Color.default() else discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Role", value=f"{role.name} ({role.id})", inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        
        embed.set_footer(text=f"Role ID: {role.id}")
        
        await self.send_log(role.guild, 'role_create', embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Log role deletion"""
        embed = discord.Embed(
            title="🎭 Role Deleted",
            description=f"**{role.name}** was deleted",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Role", value=f"{role.name} ({role.id})", inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        
        embed.set_footer(text=f"Role ID: {role.id}")
        
        await self.send_log(role.guild, 'role_delete', embed)
    
    # ==================== SERVER EVENTS ====================
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Log server updates"""
        changes = []
        embed = discord.Embed(
            title="🏛️ Server Updated",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Name change
        if before.name != after.name:
            changes.append("Name")
            embed.add_field(name="Name Changed", value=f"**Before:** {before.name}\n**After:** {after.name}", inline=False)
        
        # Verification level
        if before.verification_level != after.verification_level:
            changes.append("Verification Level")
            embed.add_field(
                name="Verification Level Changed",
                value=f"**Before:** {before.verification_level}\n**After:** {after.verification_level}",
                inline=False
            )
        
        # Owner transfer
        if before.owner_id != after.owner_id:
            changes.append("Owner")
            embed.add_field(
                name="Owner Changed",
                value=f"**Before:** <@{before.owner_id}>\n**After:** <@{after.owner_id}>",
                inline=False
            )
            embed.color = discord.Color.orange()
        
        if not changes:
            return
        
        embed.add_field(name="Changes", value=", ".join(changes), inline=True)
        
        if after.icon:
            embed.set_thumbnail(url=after.icon.url)
        
        await self.send_log(after, 'guild_update', embed)
    
    # ==================== CONFIGURATION COMMANDS ====================
    
    @commands.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, log_type: str, channel: discord.TextChannel = None):
        """
        Configure log channels for specific event types
        
        Usage:
        !setlog default #logs - Set default log channel for all events
        !setlog message_delete #message-logs - Set channel for deleted messages
        !setlog member_join #joins - Set channel for member joins
        
        Event types:
        - default (all events)
        - message_delete, message_edit, message_bulk_delete
        - member_join, member_leave, member_update
        - member_ban, member_unban
        - channel_create, channel_delete, channel_update
        - role_create, role_delete
        - guild_update
        """
        await self._set_log_channel_logic(ctx, log_type, channel)
    
    @app_commands.command(name="setlog", description="Configure logging channels")
    @app_commands.describe(log_type="Log type to configure", channel="Channel to log to")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel_slash(self, interaction: discord.Interaction, log_type: str, channel: discord.TextChannel = None):
        """
        Configure log channels using slash command
        """
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    await interaction.followup.send(embed=kwargs['embed'])
                else:
                    await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._set_log_channel_logic(ctx, log_type, channel)
    
    async def _set_log_channel_logic(self, ctx, log_type: str, channel: discord.TextChannel = None):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        if channel:
            self.config[guild_id][log_type] = channel.id
            self.save_config()
            
            embed = discord.Embed(
                title="✅ Log Channel Set",
                description=f"**{log_type}** logs will now be sent to {channel.mention}",
                color=discord.Color.green()
            )
        else:
            # Remove configuration
            if log_type in self.config[guild_id]:
                del self.config[guild_id][log_type]
                self.save_config()
                
                embed = discord.Embed(
                    title="✅ Log Channel Removed",
                    description=f"**{log_type}** logging has been disabled",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="❌ Not Configured",
                    description=f"**{log_type}** was not configured",
                    color=discord.Color.red()
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='logs')
    @commands.has_permissions(administrator=True)
    async def view_log_config(self, ctx):
        """View current logging configuration"""
        guild_id = str(ctx.guild.id)
        guild_config = self.config.get(guild_id, {})
        
        embed = discord.Embed(
            title="📋 Logging Configuration",
            description="Current log channel settings",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        if not guild_config:
            embed.description = "No logging channels configured.\nUse `!setlog <type> <channel>` to set up logging."
            embed.color = discord.Color.orange()
        else:
            for log_type, channel_id in guild_config.items():
                channel = ctx.guild.get_channel(channel_id)
                channel_mention = channel.mention if channel else f"*Deleted Channel ({channel_id})*"
                embed.add_field(name=log_type.replace('_', ' ').title(), value=channel_mention, inline=True)
        
        embed.set_footer(text=f"Use !setlog <type> <channel> to configure")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedLogging(bot))
