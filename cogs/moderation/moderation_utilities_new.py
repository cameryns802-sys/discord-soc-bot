"""
Moderation Utilities: Essential moderation commands
Clean, minimal implementation to replace problematic moderation_utilities.py
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from cogs.core.pst_timezone import get_now_pst

class ModerationUtilities(commands.Cog):
    """Essential moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== BASIC MODERATION ====================
    
    @commands.command(name='purge', aliases=['clear', 'clean'])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10, member: Optional[discord.Member] = None):
        """Delete messages from the channel"""
        if amount < 1 or amount > 1000:
            await ctx.send("❌ Amount must be between 1 and 1000")
            return
        
        def check(msg):
            return msg.author == member if member else True
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=check)
            embed = discord.Embed(
                title="🧹 Messages Purged",
                description=f"Deleted {len(deleted) - 1} message(s)",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ No permission to delete messages")
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Kick a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You cannot kick yourself")
            return
        
        try:
            await member.kick(reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(title="👢 Member Kicked", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to kick members")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Ban a member from the server"""
        if member == ctx.author:
            await ctx.send("❌ You cannot ban yourself")
            return
        
        try:
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
            embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to ban members")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason"):
        """Unban a user by ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(title="✅ User Unbanned", color=discord.Color.green(), timestamp=get_now_pst())
            embed.add_field(name="User", value=f"{user} ({user_id})")
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ This user is not banned")
    
    @commands.command(name='timeout', aliases=['mute'])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason"):
        """Timeout a member"""
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        try:
            if duration[-1] in time_units:
                seconds = int(duration[:-1]) * time_units[duration[-1]]
            else:
                seconds = int(duration) * 60
        except:
            await ctx.send("❌ Invalid duration format (e.g., 10m, 1h, 1d)")
            return
        
        try:
            until = discord.utils.utcnow() + timedelta(seconds=seconds)
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(title="🔇 Member Timed Out", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Duration", value=duration)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to timeout members")
    
    @commands.command(name='untimeout', aliases=['unmute'])
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Remove timeout from a member"""
        try:
            await member.timeout(None, reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(title="🔊 Timeout Removed", color=discord.Color.green(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to remove timeouts")
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Warn a member"""
        try:
            embed = discord.Embed(title="⚠️ Warning", description=f"You have been warned in **{ctx.guild.name}**", color=discord.Color.gold(), timestamp=get_now_pst())
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Moderator", value=str(ctx.author))
            try:
                await member.send(embed=embed)
            except:
                pass
            
            confirm = discord.Embed(title="⚠️ Warning Issued", color=discord.Color.gold(), timestamp=get_now_pst())
            confirm.add_field(name="User", value=member.mention)
            confirm.add_field(name="Reason", value=reason)
            await ctx.send(embed=confirm)
        except Exception as e:
            await ctx.send(f"❌ Failed to warn member: {e}")
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set channel slowmode"""
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Slowmode must be between 0-21600 seconds")
            return
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send("✅ Slowmode disabled")
            else:
                await ctx.send(f"✅ Slowmode set to {seconds}s")
        except discord.Forbidden:
            await ctx.send("❌ No permission to edit channel")
    
    @commands.command(name='softban')
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Softban a member (ban and unban to delete messages)"""
        try:
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=7)
            await ctx.guild.unban(member, reason="Softban unban")
            embed = discord.Embed(title="🔨 Member Softbanned", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to ban members")
    
    @commands.command(name='tempban')
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, duration: str = "7d", *, reason: str = "No reason"):
        """Temporarily ban a member"""
        try:
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
            embed = discord.Embed(title="⏱️ Temporary Ban", color=discord.Color.red(), timestamp=get_now_pst())
            embed.add_field(name="User", value=member.mention)
            embed.add_field(name="Duration", value=duration)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to ban members")
    
    # ==================== UTILITIES ====================
    
    @commands.command(name='notes')
    @commands.has_permissions(manage_messages=True)
    async def notes(self, ctx, member: discord.Member, *, note: str):
        """Add a note to a member"""
        embed = discord.Embed(title="📝 Note Added", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="Member", value=member.mention)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        embed.add_field(name="Note", value=note)
        await ctx.send(embed=embed)
    
    @commands.command(name='report')
    async def report(self, ctx, member: discord.Member, *, reason: str):
        """Report a member to moderators"""
        embed = discord.Embed(title="🚨 User Report", color=discord.Color.red(), timestamp=get_now_pst())
        embed.add_field(name="Reported User", value=member.mention)
        embed.add_field(name="Reporter", value=ctx.author.mention)
        embed.add_field(name="Reason", value=reason)
        
        mod_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if mod_channel:
            try:
                await mod_channel.send(embed=embed)
                await ctx.send("✅ Report submitted to moderators")
            except:
                await ctx.send("❌ Failed to submit report")
        else:
            await ctx.send("❌ mod-logs channel not found")
    
    @commands.command(name='cleanup')
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, amount: int = 10):
        """Delete bot messages"""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Amount must be 1-100")
            return
        
        deleted = 0
        async for message in ctx.channel.history(limit=amount * 2):
            if message.author == ctx.bot.user:
                try:
                    await message.delete()
                    deleted += 1
                except:
                    pass
            if deleted >= amount:
                break
        
        embed = discord.Embed(title="🧹 Cleanup Complete", description=f"Deleted {deleted} bot message(s)", color=discord.Color.green())
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name='announce')
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, channel: Optional[discord.TextChannel] = None, *, message: str):
        """Make an announcement"""
        channel = channel or ctx.channel
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.blue(), timestamp=get_now_pst())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        
        try:
            await channel.send("@everyone", embed=embed)
            await ctx.send(f"✅ Announcement sent to {channel.mention}")
        except discord.Forbidden:
            await ctx.send(f"❌ No permission to send messages in {channel.mention}")
    
    @commands.command(name='restrictions')
    @commands.has_permissions(manage_guild=True)
    async def restrictions(self, ctx, member: discord.Member):
        """Show a member's restrictions"""
        embed = discord.Embed(title=f"Restrictions: {member}", color=discord.Color.orange(), timestamp=get_now_pst())
        
        if member.is_timed_out():
            embed.add_field(name="🔇 Timed Out", value=f"Until <t:{int(member.timed_out_until.timestamp())}:R>", inline=False)
        else:
            embed.add_field(name="🔇 Timed Out", value="No", inline=False)
        
        embed.add_field(name="👤 Roles", value=f"{len(member.roles) - 1} role(s)", inline=True)
        
        if member.guild_permissions.administrator:
            embed.add_field(name="⚠️ Status", value="Administrator", inline=True)
        elif member.guild_permissions.manage_guild:
            embed.add_field(name="⚠️ Status", value="Manager", inline=True)
        else:
            embed.add_field(name="⚠️ Status", value="Regular Member", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='modlogs')
    @commands.has_permissions(view_audit_log=True)
    async def modlogs(self, ctx, member: Optional[discord.Member] = None, limit: int = 10):
        """View moderation logs"""
        embed = discord.Embed(title="📋 Moderation Logs", color=discord.Color.blue(), timestamp=get_now_pst())
        
        if member:
            embed.description = f"Logs for {member.mention}"
        else:
            embed.description = "Recent moderation actions"
        
        try:
            count = 0
            async for entry in ctx.guild.audit_logs(limit=limit * 2):
                if member and entry.target != member:
                    continue
                
                if entry.action in [discord.AuditLogAction.ban, discord.AuditLogAction.kick, discord.AuditLogAction.member_update]:
                    action = str(entry.action).replace("_", " ").title()
                    embed.add_field(
                        name=f"{action} by {entry.user}",
                        value=entry.reason or "No reason",
                        inline=False
                    )
                    count += 1
                
                if count >= limit:
                    break
            
            if count == 0:
                embed.description = "No moderation logs found"
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to view audit logs")
    
    @commands.command(name='probation')
    @commands.has_permissions(manage_guild=True)
    async def probation(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        """Put a member on probation"""
        probation_role = discord.utils.get(ctx.guild.roles, name="Probation")
        
        if not probation_role:
            await ctx.send("❌ Probation role not found. Create a role named 'Probation'")
            return
        
        try:
            await member.add_roles(probation_role, reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(title="⚠️ Member on Probation", color=discord.Color.orange(), timestamp=get_now_pst())
            embed.add_field(name="Member", value=member.mention)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to add roles")
    
    @commands.command(name='unprobation')
    @commands.has_permissions(manage_guild=True)
    async def unprobation(self, ctx, member: discord.Member):
        """Remove probation from a member"""
        probation_role = discord.utils.get(ctx.guild.roles, name="Probation")
        
        if not probation_role:
            await ctx.send("❌ Probation role not found")
            return
        
        try:
            await member.remove_roles(probation_role, reason=f"{ctx.author}: Removed probation")
            await ctx.send(f"✅ {member.mention} is no longer on probation")
        except discord.Forbidden:
            await ctx.send("❌ No permission to remove roles")
    
    @commands.command(name='appeal')
    async def appeal(self, ctx, *, message: str):
        """Appeal a ban or restriction"""
        embed = discord.Embed(title="📬 Ban Appeal", description=f"Appeal from {ctx.author}", color=discord.Color.blue(), timestamp=get_now_pst())
        embed.add_field(name="User", value=ctx.author.mention)
        embed.add_field(name="User ID", value=ctx.author.id)
        embed.add_field(name="Appeal Message", value=message)
        
        appeals_channel = discord.utils.get(ctx.guild.text_channels, name="appeals")
        if appeals_channel:
            try:
                await appeals_channel.send(embed=embed)
                await ctx.send("✅ Your appeal has been submitted to moderators")
            except:
                await ctx.send("❌ Failed to submit appeal")
        else:
            await ctx.send("❌ Appeals channel not found")
    
    @commands.command(name='memberinfo')
    async def memberinfo(self, ctx, member: Optional[discord.Member] = None):
        """Show detailed member information"""
        member = member or ctx.author
        
        embed = discord.Embed(title=f"Member Info: {member}", color=member.top_role.color if member.top_role else discord.Color.blue(), timestamp=get_now_pst())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Total Roles", value=len(member.roles) - 1, inline=True)
        embed.add_field(name="Bot", value="✅ Yes" if member.bot else "❌ No", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel"""
        channel = channel or ctx.channel
        
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(title="🔒 Channel Locked", description=f"{channel.mention} has been locked", color=discord.Color.red(), timestamp=get_now_pst())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to manage channel permissions")
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        channel = channel or ctx.channel
        
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(title="🔓 Channel Unlocked", description=f"{channel.mention} has been unlocked", color=discord.Color.green(), timestamp=get_now_pst())
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ No permission to manage channel permissions")

async def setup(bot):
    await bot.add_cog(ModerationUtilities(bot))
