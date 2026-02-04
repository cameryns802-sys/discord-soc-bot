"""
Fast Logger System - High-performance comprehensive event logging
Replaces slow external logger bots with optimized in-bot logging
Features: Async operations, event batching, smart caching, minimal latency
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta
from typing import Optional, Dict, List
import json
import os
from collections import deque
from cogs.core.pst_timezone import get_now_pst

class FastLogger(commands.Cog):
    """High-performance comprehensive event logger"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/fast_logger_config.json'
        self.cache_file = 'data/fast_logger_cache.json'
        
        # Performance optimizations
        self.log_queue = deque(maxlen=1000)  # Queue for batching
        self.channel_cache = {}  # Cache log channels
        self.config = {}
        self.stats = {'logs_sent': 0, 'logs_queued': 0, 'errors': 0}
        
        # Load config
        self.load_config()
        
        # Start background tasks
        self.batch_processor.start()
        self.cache_cleanup.start()
    
    def cog_unload(self):
        """Cleanup on unload"""
        self.batch_processor.cancel()
        self.cache_cleanup.cancel()
    
    def load_config(self):
        """Load logging configuration"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        
        # Default config structure
        if not self.config:
            self.config = {
                'enabled': True,
                'batch_size': 5,  # Process logs in batches
                'batch_interval': 2.0,  # Seconds between batches
                'guilds': {}  # Per-guild config
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_guild_config(self, guild_id: int) -> Dict:
        """Get guild-specific config"""
        guild_key = str(guild_id)
        if guild_key not in self.config['guilds']:
            self.config['guilds'][guild_key] = {
                'enabled': True,
                'channels': {
                    'messages': None,
                    'members': None,
                    'moderation': None,
                    'server': None,
                    'voice': None,
                    'all': None  # Fallback channel
                }
            }
            self.save_config()
        return self.config['guilds'][guild_key]
    
    def get_log_channel(self, guild: discord.Guild, log_type: str) -> Optional[discord.TextChannel]:
        """Get log channel with caching (FAST)"""
        cache_key = f"{guild.id}:{log_type}"
        
        # Check cache first
        if cache_key in self.channel_cache:
            cached = self.channel_cache[cache_key]
            if cached and cached['expires'] > get_now_pst():
                return cached['channel']
        
        # Get from config
        guild_config = self.get_guild_config(guild.id)
        channel_id = guild_config['channels'].get(log_type) or guild_config['channels'].get('all')
        
        if not channel_id:
            return None
        
        channel = guild.get_channel(channel_id)
        
        # Cache for 5 minutes
        if channel:
            self.channel_cache[cache_key] = {
                'channel': channel,
                'expires': get_now_pst() + timedelta(minutes=5)
            }
        
        return channel
    
    async def queue_log(self, guild: discord.Guild, log_type: str, embed: discord.Embed):
        """Queue log for batch processing (NON-BLOCKING)"""
        if not self.config.get('enabled', True):
            return
        
        guild_config = self.get_guild_config(guild.id)
        if not guild_config.get('enabled', True):
            return
        
        # Add to queue
        self.log_queue.append({
            'guild': guild,
            'log_type': log_type,
            'embed': embed,
            'timestamp': get_now_pst()
        })
        
        self.stats['logs_queued'] += 1
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready - cache warming"""
        print(f"[FastLogger] ⚡ High-performance logger ready")
        print(f"[FastLogger] 📊 Batch size: {self.config.get('batch_size', 5)}, Interval: {self.config.get('batch_interval', 2.0)}s")
    
    # ==================== BACKGROUND TASKS ====================
    
    @commands.Cog.listener()
    async def batch_processor(self):
        """Process log queue in batches (PERFORMANCE)"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                batch_size = self.config.get('batch_size', 5)
                
                if len(self.log_queue) > 0:
                    # Process batch
                    batch = []
                    for _ in range(min(batch_size, len(self.log_queue))):
                        if self.log_queue:
                            batch.append(self.log_queue.popleft())
                    
                    # Send logs concurrently
                    tasks = []
                    for log_entry in batch:
                        task = self.send_log_entry(log_entry)
                        tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next batch
                await asyncio.sleep(self.config.get('batch_interval', 2.0))
                
            except Exception as e:
                print(f"[FastLogger] ❌ Batch processor error: {e}")
                await asyncio.sleep(5)
    
    @commands.Cog.listener()
    async def cache_cleanup(self):
        """Clean expired cache entries"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = get_now_pst()
                expired = [k for k, v in self.channel_cache.items() if v['expires'] < now]
                for key in expired:
                    del self.channel_cache[key]
                
                await asyncio.sleep(300)  # Clean every 5 minutes
            except:
                await asyncio.sleep(300)
    
    async def send_log_entry(self, log_entry: Dict):
        """Send single log entry"""
        try:
            guild = log_entry['guild']
            log_type = log_entry['log_type']
            embed = log_entry['embed']
            
            channel = self.get_log_channel(guild, log_type)
            if channel:
                await channel.send(embed=embed)
                self.stats['logs_sent'] += 1
        except discord.Forbidden:
            self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            print(f"[FastLogger] ❌ Error sending log: {e}")
    
    # ==================== MESSAGE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log deleted messages"""
        if message.author.bot or not message.guild:
            return
        
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Author", value=f"{message.author.mention}", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="ID", value=f"`{message.id}`", inline=True)
        
        content = message.content or "*[No content]*"
        if len(content) > 1024:
            content = content[:1020] + "..."
        embed.add_field(name="Content", value=content, inline=False)
        
        if message.attachments:
            attachments = ", ".join([a.filename for a in message.attachments[:3]])
            embed.add_field(name="Attachments", value=attachments, inline=False)
        
        embed.set_footer(text=f"User ID: {message.author.id}")
        
        await self.queue_log(message.guild, 'messages', embed)
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        """Log bulk message deletions"""
        if not messages or not messages[0].guild:
            return
        
        guild = messages[0].guild
        channel = messages[0].channel
        
        embed = discord.Embed(
            title="🗑️ Bulk Message Delete",
            description=f"{len(messages)} messages deleted",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Count", value=str(len(messages)), inline=True)
        
        await self.queue_log(guild, 'messages', embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log edited messages"""
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Author", value=f"{before.author.mention}", inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Jump", value=f"[Link]({after.jump_url})", inline=True)
        
        before_content = before.content[:500] or "*[No content]*"
        after_content = after.content[:500] or "*[No content]*"
        
        embed.add_field(name="Before", value=before_content, inline=False)
        embed.add_field(name="After", value=after_content, inline=False)
        
        embed.set_footer(text=f"User ID: {before.author.id}")
        
        await self.queue_log(before.guild, 'messages', embed)
    
    # ==================== MEMBER EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log member joins"""
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} joined the server",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        account_age = (get_now_pst() - member.created_at).days
        embed.add_field(name="Account Age", value=f"{account_age} days", inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.set_footer(text=f"ID: {member.id}")
        
        await self.queue_log(member.guild, 'members', embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log member leaves"""
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"{member.mention} left the server",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
        
        roles = [r.mention for r in member.roles if r.name != "@everyone"][:5]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        embed.set_footer(text=f"ID: {member.id}")
        
        await self.queue_log(member.guild, 'members', embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log member updates (roles, nickname)"""
        # Role changes
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            if added or removed:
                embed = discord.Embed(
                    title="👤 Member Roles Updated",
                    description=f"{after.mention}",
                    color=discord.Color.blue(),
                    timestamp=get_now_pst()
                )
                
                if added:
                    embed.add_field(name="➕ Roles Added", value=", ".join([r.mention for r in added]), inline=False)
                if removed:
                    embed.add_field(name="➖ Roles Removed", value=", ".join([r.mention for r in removed]), inline=False)
                
                embed.set_footer(text=f"User ID: {after.id}")
                
                await self.queue_log(after.guild, 'members', embed)
        
        # Nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Nickname Changed",
                description=f"{after.mention}",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Before", value=before.nick or "*[None]*", inline=True)
            embed.add_field(name="After", value=after.nick or "*[None]*", inline=True)
            
            embed.set_footer(text=f"User ID: {after.id}")
            
            await self.queue_log(after.guild, 'members', embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Log bans"""
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{user.mention} was banned",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Username", value=str(user), inline=True)
        embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        embed.set_footer(text=f"ID: {user.id}")
        
        await self.queue_log(guild, 'moderation', embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log unbans"""
        embed = discord.Embed(
            title="✅ Member Unbanned",
            description=f"{user.mention} was unbanned",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Username", value=str(user), inline=True)
        embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        embed.set_footer(text=f"ID: {user.id}")
        
        await self.queue_log(guild, 'moderation', embed)
    
    # ==================== SERVER EVENTS ====================
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """Log channel creations"""
        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"{channel.mention} was created",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Channel Name", value=channel.name, inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel.id}`", inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        
        await self.queue_log(channel.guild, 'server', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Log channel deletions"""
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"**{channel.name}** was deleted",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Channel Name", value=channel.name, inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel.id}`", inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        
        await self.queue_log(channel.guild, 'server', embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Log channel updates"""
        if before.name != after.name:
            embed = discord.Embed(
                title="✏️ Channel Renamed",
                description=f"{after.mention}",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            
            await self.queue_log(after.guild, 'server', embed)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Log role creations"""
        embed = discord.Embed(
            title="🎭 Role Created",
            description=f"**{role.name}** was created",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Role Name", value=role.name, inline=True)
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        
        await self.queue_log(role.guild, 'server', embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Log role deletions"""
        embed = discord.Embed(
            title="🗑️ Role Deleted",
            description=f"**{role.name}** was deleted",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Role Name", value=role.name, inline=True)
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=True)
        
        await self.queue_log(role.guild, 'server', embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Log voice activity"""
        # Join
        if before.channel is None and after.channel:
            embed = discord.Embed(
                title="🔊 Voice Join",
                description=f"{member.mention} joined {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            await self.queue_log(member.guild, 'voice', embed)
        
        # Leave
        elif before.channel and after.channel is None:
            embed = discord.Embed(
                title="🔇 Voice Leave",
                description=f"{member.mention} left {before.channel.mention}",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            await self.queue_log(member.guild, 'voice', embed)
        
        # Move
        elif before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔀 Voice Move",
                description=f"{member.mention} moved channels",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="From", value=before.channel.mention, inline=True)
            embed.add_field(name="To", value=after.channel.mention, inline=True)
            await self.queue_log(member.guild, 'voice', embed)
    
    # ==================== CONFIGURATION COMMANDS ====================
    
    @app_commands.command(name="logsetup", description="Configure logging channels")
    @app_commands.describe(
        log_type="Type: messages, members, moderation, server, voice, all",
        channel="Channel for logs"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def logsetup(self, interaction: discord.Interaction, log_type: str, channel: discord.TextChannel):
        """Configure logging channels"""
        guild_config = self.get_guild_config(interaction.guild.id)
        
        if log_type not in ['messages', 'members', 'moderation', 'server', 'voice', 'all']:
            await interaction.response.send_message("❌ Invalid log type", ephemeral=True)
            return
        
        guild_config['channels'][log_type] = channel.id
        self.save_config()
        
        # Clear cache
        cache_key = f"{interaction.guild.id}:{log_type}"
        if cache_key in self.channel_cache:
            del self.channel_cache[cache_key]
        
        embed = discord.Embed(
            title="✅ Logging Configured",
            description=f"**{log_type.title()}** logs → {channel.mention}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="logstatus", description="View logging status")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def logstatus(self, interaction: discord.Interaction):
        """View logging status and statistics"""
        guild_config = self.get_guild_config(interaction.guild.id)
        
        embed = discord.Embed(
            title="📊 FastLogger Status",
            description="High-performance logging system",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Status", value="✅ ENABLED" if guild_config['enabled'] else "❌ DISABLED", inline=True)
        embed.add_field(name="Queue Size", value=str(len(self.log_queue)), inline=True)
        embed.add_field(name="Batch Size", value=str(self.config.get('batch_size', 5)), inline=True)
        
        embed.add_field(name="Performance", value="━" * 25, inline=False)
        embed.add_field(name="Logs Sent", value=str(self.stats['logs_sent']), inline=True)
        embed.add_field(name="Logs Queued", value=str(self.stats['logs_queued']), inline=True)
        embed.add_field(name="Errors", value=str(self.stats['errors']), inline=True)
        
        # Channel configuration
        channels_config = []
        for log_type, channel_id in guild_config['channels'].items():
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    channels_config.append(f"**{log_type.title()}**: {channel.mention}")
        
        if channels_config:
            embed.add_field(name="Configured Channels", value="\n".join(channels_config), inline=False)
        else:
            embed.add_field(name="Configured Channels", value="*None configured - use `/logsetup`*", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="logtoggle", description="Enable/disable logging")
    @app_commands.checks.has_permissions(administrator=True)
    async def logtoggle(self, interaction: discord.Interaction):
        """Toggle logging on/off"""
        guild_config = self.get_guild_config(interaction.guild.id)
        guild_config['enabled'] = not guild_config['enabled']
        self.save_config()
        
        status = "✅ ENABLED" if guild_config['enabled'] else "❌ DISABLED"
        await interaction.response.send_message(f"Logging {status}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FastLogger(bot))
