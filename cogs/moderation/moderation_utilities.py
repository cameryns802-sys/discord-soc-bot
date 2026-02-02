"""
Moderation Utilities: Essential moderation commands (purge, kick, ban, mute, etc.)
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio

class ModerationUtilities(commands.Cog):
    """Essential moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='purge', aliases=['clear', 'clean'])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10, member: discord.Member = None):
        """
        Purge messages from the channel
        
        Usage:
            !purge 50 - Delete last 50 messages
            !purge 20 @user - Delete last 20 messages from specific user
        """
        await self._purge_logic(ctx, amount, member)
    
    @app_commands.command(name="purge", description="Delete messages from the channel")
    @app_commands.describe(amount="Number of messages to delete (1-1000)", member="Optional: Delete only from specific user")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_slash(self, interaction: discord.Interaction, amount: int = 10, member: discord.Member = None):
        """Purge messages using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    msg = await interaction.followup.send(embed=kwargs['embed'])
                else:
                    msg = await interaction.followup.send(content=kwargs.get('content', ''))
                return msg
        
        ctx = FakeCtx(interaction)
        await self._purge_logic(ctx, amount, member)
    
    async def _purge_logic(self, ctx, amount: int, member: discord.Member = None):
        if amount < 1 or amount > 1000:
            await ctx.send("❌ Amount must be between 1 and 1000", delete_after=5)
            return
        
        def check(msg):
            if member:
                return msg.author == member
            return True
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)
            
            embed = discord.Embed(
                title="🧹 Messages Purged",
                description=f"Deleted {len(deleted) - 1} message(s)",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            if member:
                embed.add_field(name="Target", value=member.mention, inline=True)
            
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"Channel: {ctx.channel.name}")
            
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to purge messages: {e}", delete_after=5)
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        await self._kick_logic(ctx, member, reason)
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member using slash command"""
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
        await self._kick_logic(ctx, member, reason)
    
    async def _kick_logic(self, ctx, member: discord.Member, reason: str):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot kick someone with a role equal or higher than yours")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot kick someone with a role equal or higher than mine")
            return
        
        try:
            # Send DM to user
            try:
                embed = discord.Embed(
                    title="⚠️ You've been kicked",
                    description=f"You were kicked from **{ctx.guild.name}**",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
            
            # Kick the member
            await member.kick(reason=f"{ctx.author}: {reason}")
            
            # Confirmation embed
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick members")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick member: {e}")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        await self._ban_logic(ctx, member, reason)
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Ban a member using slash command"""
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
        await self._ban_logic(ctx, member, reason)
    
    async def _ban_logic(self, ctx, member: discord.Member, reason: str):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with a role equal or higher than yours")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot ban someone with a role equal or higher than mine")
            return
        
        try:
            # Send DM to user
            try:
                embed = discord.Embed(
                    title="🔨 You've been banned",
                    description=f"You were banned from **{ctx.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
            
            # Ban the member
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
            
            # Confirmation embed
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban members")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban member: {e}")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user by their ID"""
        await self._unban_logic(ctx, user_id, reason)
    
    @app_commands.command(name="unban", description="Unban a user by their ID")
    @app_commands.describe(user_id="User ID to unban", reason="Reason for unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_slash(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Unban a user using slash command"""
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
        try:
            user_id_int = int(user_id)
        except ValueError:
            await ctx.send("❌ Invalid user ID. Must be a number.")
            return
        await self._unban_logic(ctx, user_id_int, reason)
    
    async def _unban_logic(self, ctx, user_id: int, reason: str):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            await ctx.send("❌ This user is not banned")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban members")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unban user: {e}")
    
    @commands.command(name='timeout', aliases=['mute'])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Timeout (mute) a member for a specified duration"""
        await self._timeout_logic(ctx, member, duration, reason)
    
    @app_commands.command(name="timeout", description="Timeout (mute) a member for a specified duration")
    @app_commands.describe(member="Member to timeout", duration="Duration (e.g., 10m, 1h, 1d)", reason="Reason for timeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_slash(self, interaction: discord.Interaction, member: discord.Member, duration: str = "10m", reason: str = "No reason provided"):
        """Timeout a member using slash command"""
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
        await self._timeout_logic(ctx, member, duration, reason)
    
    async def _timeout_logic(self, ctx, member: discord.Member, duration: str, reason: str):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot timeout someone with a role equal or higher than yours")
            return
        
        # Parse duration
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration_seconds = 0
        
        try:
            if duration[-1] in time_units:
                duration_seconds = int(duration[:-1]) * time_units[duration[-1]]
            else:
                duration_seconds = int(duration) * 60  # Default to minutes
        except:
            await ctx.send("❌ Invalid duration format. Use: 10m, 1h, 1d, etc.")
            return
        
        if duration_seconds > 2419200:  # 28 days max
            await ctx.send("❌ Duration cannot exceed 28 days")
            return
        
        try:
            until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="🔇 Member Timed Out",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Expires", value=f"<t:{int(until.timestamp())}:R>", inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to timeout members")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to timeout member: {e}")
    
    @commands.command(name='untimeout', aliases=['unmute'])
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        await self._untimeout_logic(ctx, member, reason)
    
    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="Member to untimeout", reason="Reason for removal")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Remove timeout using slash command"""
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
        await self._untimeout_logic(ctx, member, reason)
    
    async def _untimeout_logic(self, ctx, member: discord.Member, reason: str):
        try:
            await member.timeout(None, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="🔊 Timeout Removed",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove timeouts")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to remove timeout: {e}")
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        await self._warn_logic(ctx, member, reason)
    
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn using slash command"""
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
        await self._warn_logic(ctx, member, reason)
    
    async def _warn_logic(self, ctx, member: discord.Member, reason: str):
        try:
            # Send DM warning
            embed = discord.Embed(
                title="⚠️ Warning",
                description=f"You have been warned in **{ctx.guild.name}**",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
            embed.set_footer(text="Please review the server rules")
            
            try:
                await member.send(embed=embed)
                dm_status = "✅ DM sent"
            except:
                dm_status = "❌ DM failed (user has DMs disabled)"
            
            # Confirmation
            confirm_embed = discord.Embed(
                title="⚠️ Warning Issued",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            confirm_embed.add_field(name="User", value=member.mention, inline=True)
            confirm_embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            confirm_embed.add_field(name="Reason", value=reason, inline=False)
            confirm_embed.add_field(name="DM Status", value=dm_status, inline=False)
            
            await ctx.send(embed=confirm_embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to issue warning: {e}")
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set channel slowmode"""
        await self._slowmode_logic(ctx, seconds)
    
    @app_commands.command(name="slowmode", description="Set channel slowmode delay")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode_slash(self, interaction: discord.Interaction, seconds: int = 0):
        """Slowmode using slash command"""
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
        await self._slowmode_logic(ctx, seconds)
    
    async def _slowmode_logic(self, ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Slowmode must be between 0 and 21600 seconds (6 hours)")
            return
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                await ctx.send("✅ Slowmode disabled")
            else:
                await ctx.send(f"✅ Slowmode set to {seconds} second(s)")
                
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to edit channels")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to set slowmode: {e}")
    
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel"""
        await self._lock_logic(ctx, channel)
    
    @app_commands.command(name="lock", description="Lock a channel (prevent @everyone from sending messages)")
    @app_commands.describe(channel="Channel to lock (current channel if not specified)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock_slash(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Lock using slash command"""
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
        await self._lock_logic(ctx, channel)
    
    async def _lock_logic(self, ctx, channel: Optional[discord.TextChannel]):
        channel = channel or ctx.channel
        
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Moderator", value=ctx.author.mention)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage channel permissions")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to lock channel: {e}")
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        await self._unlock_logic(ctx, channel)
    
    @app_commands.command(name="unlock", description="Unlock a channel (allow @everyone to send messages)")
    @app_commands.describe(channel="Channel to unlock (current channel if not specified)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock_slash(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Unlock using slash command"""
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
        await self._unlock_logic(ctx, channel)
    
    async def _unlock_logic(self, ctx, channel: Optional[discord.TextChannel]):
        channel = channel or ctx.channel
        
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Moderator", value=ctx.author.mention)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage channel permissions")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unlock channel: {e}")

async def setup(bot):
    await bot.add_cog(ModerationUtilities(bot))
