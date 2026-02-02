"""
Advanced Moderation: Mass actions, raid protection, and advanced moderation tools
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import re

class AdvancedModeration(commands.Cog):
    """Advanced moderation commands for mass actions and raid protection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.raid_mode = {}  # guild_id: bool
        self.verification_mode = {}  # guild_id: role_id
    
    # ==================== MASS BAN ====================
    
    @commands.command(name='massban')
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx, *user_ids: int):
        """Mass ban multiple users by ID"""
        await self._massban_logic(ctx, list(user_ids))
    
    @app_commands.command(name="massban", description="Mass ban multiple users by their IDs")
    @app_commands.describe(user_ids="Space-separated user IDs (e.g., 123 456 789)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def massban_slash(self, interaction: discord.Interaction, user_ids: str):
        """Mass ban using slash command"""
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
        
        # Parse user IDs from string
        try:
            ids = [int(uid.strip()) for uid in user_ids.split()]
        except ValueError:
            await ctx.send("❌ Invalid user ID format. Use space-separated numbers.")
            return
        
        await self._massban_logic(ctx, ids)
    
    async def _massban_logic(self, ctx, user_ids: list):
        if len(user_ids) == 0:
            await ctx.send("❌ No user IDs provided")
            return
        
        if len(user_ids) > 50:
            await ctx.send("❌ Cannot ban more than 50 users at once")
            return
        
        banned = []
        failed = []
        
        embed = discord.Embed(
            title="🔨 Mass Ban in Progress",
            description=f"Banning {len(user_ids)} user(s)...",
            color=discord.Color.orange(),
            timestamp=datetime.now(datetime.UTC)
        )
        status_msg = await ctx.send(embed=embed)
        
        for user_id in user_ids:
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.ban(user, reason=f"Mass ban by {ctx.author}")
                banned.append(f"{user} ({user_id})")
                await asyncio.sleep(0.5)  # Rate limit protection
            except discord.NotFound:
                failed.append(f"❌ {user_id} (User not found)")
            except discord.Forbidden:
                failed.append(f"❌ {user_id} (Permission denied)")
            except discord.HTTPException as e:
                failed.append(f"❌ {user_id} ({str(e)[:50]})")
        
        # Update embed with results
        result_embed = discord.Embed(
            title="🔨 Mass Ban Complete",
            color=discord.Color.red(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        if banned:
            result_embed.add_field(
                name=f"✅ Banned ({len(banned)})",
                value="\n".join(banned[:10]) + (f"\n... and {len(banned) - 10} more" if len(banned) > 10 else ""),
                inline=False
            )
        
        if failed:
            result_embed.add_field(
                name=f"❌ Failed ({len(failed)})",
                value="\n".join(failed[:10]) + (f"\n... and {len(failed) - 10} more" if len(failed) > 10 else ""),
                inline=False
            )
        
        result_embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        result_embed.set_footer(text=f"Total: {len(banned)} banned, {len(failed)} failed")
        
        await status_msg.edit(embed=result_embed)
    
    # ==================== MASS KICK ====================
    
    @commands.command(name='masskick')
    @commands.has_permissions(kick_members=True)
    async def masskick(self, ctx, *members: discord.Member):
        """Mass kick multiple members"""
        await self._masskick_logic(ctx, list(members))
    
    @app_commands.command(name="masskick", description="Mass kick members with a specific role")
    @app_commands.describe(role="Role to kick all members from")
    @app_commands.checks.has_permissions(kick_members=True)
    async def masskick_slash(self, interaction: discord.Interaction, role: discord.Role):
        """Mass kick using slash command"""
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
        members = role.members
        
        if not members:
            await ctx.send(f"❌ No members have the role {role.name}")
            return
        
        await self._masskick_logic(ctx, members)
    
    async def _masskick_logic(self, ctx, members: list):
        if len(members) == 0:
            await ctx.send("❌ No members provided")
            return
        
        if len(members) > 50:
            await ctx.send("❌ Cannot kick more than 50 members at once")
            return
        
        kicked = []
        failed = []
        
        embed = discord.Embed(
            title="👢 Mass Kick in Progress",
            description=f"Kicking {len(members)} member(s)...",
            color=discord.Color.orange(),
            timestamp=datetime.now(datetime.UTC)
        )
        status_msg = await ctx.send(embed=embed)
        
        for member in members:
            try:
                if member.top_role >= ctx.guild.me.top_role:
                    failed.append(f"❌ {member} (Role too high)")
                    continue
                
                await member.kick(reason=f"Mass kick by {ctx.author}")
                kicked.append(str(member))
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                failed.append(f"❌ {member} (Permission denied)")
            except discord.HTTPException as e:
                failed.append(f"❌ {member} ({str(e)[:50]})")
        
        result_embed = discord.Embed(
            title="👢 Mass Kick Complete",
            color=discord.Color.orange(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        if kicked:
            result_embed.add_field(
                name=f"✅ Kicked ({len(kicked)})",
                value="\n".join(kicked[:10]) + (f"\n... and {len(kicked) - 10} more" if len(kicked) > 10 else ""),
                inline=False
            )
        
        if failed:
            result_embed.add_field(
                name=f"❌ Failed ({len(failed)})",
                value="\n".join(failed[:10]),
                inline=False
            )
        
        result_embed.add_field(name="Moderator", value=ctx.author.mention)
        
        await status_msg.edit(embed=result_embed)
    
    # ==================== RAID MODE ====================
    
    @commands.command(name='raidmode')
    @commands.has_permissions(administrator=True)
    async def raidmode(self, ctx, action: str = "status"):
        """Toggle raid mode (on/off/status)"""
        await self._raidmode_logic(ctx, action)
    
    @app_commands.command(name="raidmode", description="Toggle raid mode protection")
    @app_commands.describe(action="Action: on, off, or status")
    @app_commands.checks.has_permissions(administrator=True)
    async def raidmode_slash(self, interaction: discord.Interaction, action: str = "status"):
        """Toggle raid mode using slash command"""
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
        await self._raidmode_logic(ctx, action)
    
    async def _raidmode_logic(self, ctx, action: str):
        action = action.lower()
        
        if action == "on":
            self.raid_mode[ctx.guild.id] = True
            
            embed = discord.Embed(
                title="🛡️ Raid Mode Enabled",
                description="The server is now in raid protection mode",
                color=discord.Color.red(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(
                name="Protections Active",
                value="✅ New member verification required\n✅ Invite link blocking\n✅ Enhanced spam detection\n✅ Auto-kick suspicious accounts",
                inline=False
            )
            embed.add_field(name="Enabled by", value=ctx.author.mention)
            embed.set_footer(text="Use /raidmode off to disable")
            
            await ctx.send(embed=embed)
            
        elif action == "off":
            self.raid_mode[ctx.guild.id] = False
            
            embed = discord.Embed(
                title="🛡️ Raid Mode Disabled",
                description="Raid protection has been disabled",
                color=discord.Color.green(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Disabled by", value=ctx.author.mention)
            
            await ctx.send(embed=embed)
            
        else:  # status
            is_active = self.raid_mode.get(ctx.guild.id, False)
            
            embed = discord.Embed(
                title="🛡️ Raid Mode Status",
                color=discord.Color.red() if is_active else discord.Color.green(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(
                name="Status",
                value="🔴 **ACTIVE**" if is_active else "🟢 **INACTIVE**",
                inline=False
            )
            
            if is_active:
                embed.add_field(
                    name="Active Protections",
                    value="✅ New member verification\n✅ Invite link blocking\n✅ Spam detection\n✅ Auto-kick suspicious accounts",
                    inline=False
                )
            
            await ctx.send(embed=embed)
    
    # ==================== NICKNAME RESET ====================
    
    @commands.command(name='nickreset')
    @commands.has_permissions(manage_nicknames=True)
    async def nickreset(self, ctx, member: discord.Member):
        """Reset a member's nickname"""
        await self._nickreset_logic(ctx, member)
    
    @app_commands.command(name="nickreset", description="Reset a member's nickname to their username")
    @app_commands.describe(member="Member whose nickname to reset")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nickreset_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Reset nickname using slash command"""
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
        await self._nickreset_logic(ctx, member)
    
    async def _nickreset_logic(self, ctx, member: discord.Member):
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot change the nickname of someone with a role equal or higher than mine")
            return
        
        old_nick = member.display_name
        
        try:
            await member.edit(nick=None, reason=f"Nickname reset by {ctx.author}")
            
            embed = discord.Embed(
                title="📝 Nickname Reset",
                color=discord.Color.blue(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Name", value=member.name, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to change nicknames")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to reset nickname: {e}")
    
    # ==================== ROLE STRIP ====================
    
    @commands.command(name='rolestrip')
    @commands.has_permissions(manage_roles=True)
    async def rolestrip(self, ctx, member: discord.Member):
        """Remove all roles from a member"""
        await self._rolestrip_logic(ctx, member)
    
    @app_commands.command(name="rolestrip", description="Remove all roles from a member")
    @app_commands.describe(member="Member to strip roles from")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolestrip_slash(self, interaction: discord.Interaction, member: discord.Member):
        """Strip roles using slash command"""
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
        await self._rolestrip_logic(ctx, member)
    
    async def _rolestrip_logic(self, ctx, member: discord.Member):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot strip roles from someone with a role equal or higher than yours")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot strip roles from someone with a role equal or higher than mine")
            return
        
        removable_roles = [role for role in member.roles if role != ctx.guild.default_role and role < ctx.guild.me.top_role]
        
        if not removable_roles:
            await ctx.send("❌ This member has no removable roles")
            return
        
        try:
            await member.remove_roles(*removable_roles, reason=f"Role strip by {ctx.author}")
            
            embed = discord.Embed(
                title="🗑️ Roles Stripped",
                description=f"Removed {len(removable_roles)} role(s) from {member.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now(datetime.UTC)
            )
            embed.add_field(
                name="Removed Roles",
                value=", ".join([role.name for role in removable_roles[:10]]) + (f" (+{len(removable_roles) - 10} more)" if len(removable_roles) > 10 else ""),
                inline=False
            )
            embed.add_field(name="Moderator", value=ctx.author.mention)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage roles")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to strip roles: {e}")
    
    # ==================== LOCKDOWN ====================
    
    @commands.command(name='lockdown')
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        """Lock down all channels in the server"""
        await self._lockdown_logic(ctx)
    
    @app_commands.command(name="lockdown", description="Lock down all channels in the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def lockdown_slash(self, interaction: discord.Interaction):
        """Lockdown using slash command"""
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
        await self._lockdown_logic(ctx)
    
    async def _lockdown_logic(self, ctx):
        embed = discord.Embed(
            title="🔒 Server Lockdown in Progress",
            description="Locking all channels...",
            color=discord.Color.red(),
            timestamp=datetime.now(datetime.UTC)
        )
        status_msg = await ctx.send(embed=embed)
        
        locked = 0
        failed = 0
        
        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                locked += 1
                await asyncio.sleep(0.5)
            except:
                failed += 1
        
        result_embed = discord.Embed(
            title="🔒 Server Lockdown Complete",
            description=f"All text channels have been locked",
            color=discord.Color.red(),
            timestamp=datetime.now(datetime.UTC)
        )
        result_embed.add_field(name="Channels Locked", value=str(locked), inline=True)
        result_embed.add_field(name="Failed", value=str(failed), inline=True)
        result_embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        result_embed.set_footer(text="Use /unlockdown to reverse")
        
        await status_msg.edit(embed=result_embed)
    
    @commands.command(name='unlockdown')
    @commands.has_permissions(administrator=True)
    async def unlockdown(self, ctx):
        """Unlock all channels in the server"""
        await self._unlockdown_logic(ctx)
    
    @app_commands.command(name="unlockdown", description="Unlock all channels in the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlockdown_slash(self, interaction: discord.Interaction):
        """Unlockdown using slash command"""
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
        await self._unlockdown_logic(ctx)
    
    async def _unlockdown_logic(self, ctx):
        embed = discord.Embed(
            title="🔓 Server Unlock in Progress",
            description="Unlocking all channels...",
            color=discord.Color.green(),
            timestamp=datetime.now(datetime.UTC)
        )
        status_msg = await ctx.send(embed=embed)
        
        unlocked = 0
        failed = 0
        
        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                unlocked += 1
                await asyncio.sleep(0.5)
            except:
                failed += 1
        
        result_embed = discord.Embed(
            title="🔓 Server Unlock Complete",
            description=f"All text channels have been unlocked",
            color=discord.Color.green(),
            timestamp=datetime.now(datetime.UTC)
        )
        result_embed.add_field(name="Channels Unlocked", value=str(unlocked), inline=True)
        result_embed.add_field(name="Failed", value=str(failed), inline=True)
        result_embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await status_msg.edit(embed=result_embed)

async def setup(bot):
    await bot.add_cog(AdvancedModeration(bot))
