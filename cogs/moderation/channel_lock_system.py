"""
Channel Lock System - Lock/unlock channels
Temporarily restrict channel access
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ChannelLockSystem(commands.Cog):
    """Lock and unlock channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.locked_channels = {}
    
    @commands.command(name='lock_channel')
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel (read-only for members)"""
        if not channel:
            channel = ctx.channel
        
        # Get @everyone role
        everyone_role = ctx.guild.default_role
        
        try:
            # Set permissions: deny send_messages
            await channel.set_permissions(
                everyone_role,
                send_messages=False,
                reason=f"Channel locked by {ctx.author}"
            )
            
            self.locked_channels[channel.id] = get_now_pst()
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} is now read-only",
                color=discord.Color.red()
            )
            embed.add_field(name="Status", value="🔴 LOCKED", inline=True)
            embed.add_field(name="Time", value=get_now_pst().strftime('%H:%M:%S'), inline=True)
            embed.add_field(name="Locked By", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to lock channel: {e}")
    
    @commands.command(name='unlock_channel')
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        if not channel:
            channel = ctx.channel
        
        # Get @everyone role
        everyone_role = ctx.guild.default_role
        
        try:
            # Reset permissions
            await channel.set_permissions(
                everyone_role,
                send_messages=None,
                reason=f"Channel unlocked by {ctx.author}"
            )
            
            if channel.id in self.locked_channels:
                del self.locked_channels[channel.id]
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} is now open",
                color=discord.Color.green()
            )
            embed.add_field(name="Status", value="🟢 UNLOCKED", inline=True)
            embed.add_field(name="Time", value=get_now_pst().strftime('%H:%M:%S'), inline=True)
            embed.add_field(name="Unlocked By", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to unlock channel: {e}")
    
    @commands.command(name='channel_status')
    @commands.has_permissions(manage_channels=True)
    async def channel_status(self, ctx):
        """Show locked channels status"""
        embed = discord.Embed(
            title="🔐 Channel Lock Status",
            description=f"{ctx.guild.name} - Locked channels",
            color=discord.Color.blue()
        )
        
        if self.locked_channels:
            embed.add_field(name="Locked Channels", value=str(len(self.locked_channels)), inline=True)
            for channel_id in self.locked_channels:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    embed.add_field(name=f"🔒 {channel.name}", value="Read-only", inline=False)
        else:
            embed.add_field(name="Status", value="✅ No locked channels", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChannelLockSystem(bot))
