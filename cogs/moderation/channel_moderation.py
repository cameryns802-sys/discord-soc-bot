import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from cogs.core.pst_timezone import get_now_pst

class ChannelModeration(commands.Cog):
    """Channel moderation and member management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_rules = {}
    
    # ==================== CHANNEL RULES ====================
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setchannelrule(self, ctx, channel: discord.TextChannel, *, rule):
        """Set a rule for a channel (no_links, no_images, etc.)"""
        cid = channel.id
        self.channel_rules.setdefault(cid, []).append(rule)
        await ctx.send(f"Rule '{rule}' added for {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        rules = self.channel_rules.get(message.channel.id, [])
        if "no_links" in rules and "http" in message.content:
            try:
                await message.delete()
            except Exception:
                pass
        if "no_images" in rules and any(attachment.content_type and attachment.content_type.startswith("image") for attachment in message.attachments):
            try:
                await message.delete()
            except Exception:
                pass
    
    # ==================== MODERATION COMMANDS ====================
    @commands.command(name='purge', aliases=['clear', 'clean'])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10, member: discord.Member = None):
        """Delete messages from the channel"""
        if amount < 1 or amount > 1000:
            await ctx.send("❌ Amount must be between 1 and 1000", delete_after=5)
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
            if member:
                embed.add_field(name="Target", value=member.mention, inline=True)
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages", delete_after=5)
    
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel (disable message sending)"""
        channel = channel or ctx.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} is now locked",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to lock this channel")
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel (enable message sending)"""
        channel = channel or ctx.channel
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} is now unlocked",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unlock this channel")
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set slowmode for the channel"""
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Slowmode must be between 0 and 21600 seconds")
            return
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            status = "disabled" if seconds == 0 else f"set to {seconds}s"
            embed = discord.Embed(
                title="⏱️ Slowmode Updated",
                description=f"Slowmode {status}",
                color=discord.Color.blue(),
                timestamp=get_now_pst()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to change slowmode")
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot kick someone with a role equal or higher than yours")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot kick someone with a role equal or higher than mine")
            return
        
        try:
            await member.kick(reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked",
                color=discord.Color.orange(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick members")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with a role equal or higher than yours")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot ban someone with a role equal or higher than mine")
            return
        
        try:
            await member.ban(reason=f"{ctx.author}: {reason}")
            embed = discord.Embed(
                title="⛔ Member Banned",
                description=f"{member.mention} has been banned",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban members")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unban a user by ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{user.mention} has been unbanned",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ User not found or not banned")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban")
    
    @commands.command(name='timeout', aliases=['mute'])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str = "1h", *, reason: str = "No reason provided"):
        """Timeout a member (mute them)"""
        try:
            # Parse duration (1h, 30m, 1d, etc.)
            duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            amount = int(duration[:-1])
            unit = duration[-1]
            seconds = amount * duration_map.get(unit, 3600)
            
            await member.timeout(timedelta(seconds=seconds), reason=reason)
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{member.mention} has been muted",
                color=discord.Color.orange(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to timeout member: {str(e)[:100]}")
    
    @commands.command(name='untimeout', aliases=['unmute'])
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Remove timeout from a member (unmute them)"""
        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify timeouts")
    
    @commands.command(name='warn')
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChannelModeration(bot))
