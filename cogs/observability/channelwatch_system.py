"""
Channelwatch System: Monitor activity in specific channels.
Tracks message counts, user participation, and channel patterns.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/channelwatch_system.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'watched_channels': {},  # channel_id: {name, added_date, message_count, users: set}
        'config': {
            'enabled': True,
            'count_messages': True,
            'track_users': True,
            'alert_on_volume': False,
            'volume_threshold': 100  # Messages per hour
        }
    }

def save_data(data):
    os.makedirs('data', exist_ok=True)
    # Convert sets to lists for JSON serialization
    data_copy = data.copy()
    for channel_id, info in data_copy.get('watched_channels', {}).items():
        if 'users' in info and isinstance(info['users'], set):
            info['users'] = list(info['users'])
    with open(DATA_FILE, 'w') as f:
        json.dump(data_copy, f, indent=2)

class ChannelwatchCog(commands.Cog):
    """Monitor activity in specific channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        # Convert lists back to sets
        for channel_id, info in self.data.get('watched_channels', {}).items():
            if 'users' in info and isinstance(info['users'], list):
                info['users'] = set(info['users'])

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track messages in watched channels"""
        if not self.data['config'].get('count_messages', True):
            return
        
        channel_id = str(message.channel.id)
        if channel_id in self.data['watched_channels']:
            self.data['watched_channels'][channel_id]['message_count'] = \
                self.data['watched_channels'][channel_id].get('message_count', 0) + 1
            
            if self.data['config'].get('track_users', True):
                if 'users' not in self.data['watched_channels'][channel_id]:
                    self.data['watched_channels'][channel_id]['users'] = set()
                
                self.data['watched_channels'][channel_id]['users'].add(message.author.name)
            
            save_data(self.data)

    @commands.command()
    async def channelwatch_add(self, ctx, channel: discord.TextChannel):
        """Add channel to watchlist"""
        channel_id = str(channel.id)
        
        if channel_id in self.data['watched_channels']:
            await ctx.send(f"⚠️ {channel.mention} is already being watched.")
            return
        
        self.data['watched_channels'][channel_id] = {
            'name': channel.name,
            'added_date': get_now_pst().isoformat(),
            'message_count': 0,
            'users': set()
        }
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Channel Added to Channelwatch",
            description=f"{channel.mention} is now being monitored",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def channelwatch_remove(self, ctx, channel: discord.TextChannel):
        """Remove channel from watchlist"""
        channel_id = str(channel.id)
        
        if channel_id not in self.data['watched_channels']:
            await ctx.send(f"⚠️ {channel.mention} is not being watched.")
            return
        
        del self.data['watched_channels'][channel_id]
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Channel Removed from Channelwatch",
            description=f"{channel.mention} is no longer being monitored",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def channelwatch_list(self, ctx):
        """List all watched channels"""
        if not self.data['watched_channels']:
            await ctx.send("📋 No channels are currently being watched.")
            return
        
        embed = discord.Embed(
            title="📋 Watched Channels",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for channel_id, info in list(self.data['watched_channels'].items())[:10]:
            msg_count = info.get('message_count', 0)
            user_count = len(info.get('users', set()))
            embed.add_field(
                name=f"#{info['name']}",
                value=f"Messages: {msg_count} | Users: {user_count}",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(self.data['watched_channels'])} channels")
        await ctx.send(embed=embed)

    @commands.command()
    async def channelwatch_view(self, ctx, channel: discord.TextChannel):
        """View detailed activity for a watched channel"""
        channel_id = str(channel.id)
        
        if channel_id not in self.data['watched_channels']:
            await ctx.send(f"⚠️ {channel.mention} is not being watched.")
            return
        
        info = self.data['watched_channels'][channel_id]
        msg_count = info.get('message_count', 0)
        users = info.get('users', set())
        
        embed = discord.Embed(
            title=f"📊 Activity Report: #{info['name']}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Messages", value=str(msg_count), inline=True)
        embed.add_field(name="Unique Users", value=str(len(users)), inline=True)
        embed.add_field(name="Added Date", value=info['added_date'], inline=True)
        
        if users:
            users_list = ", ".join(list(users)[:10])
            embed.add_field(name="Active Users", value=users_list, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def channelwatch_config(self, ctx):
        """View channelwatch configuration"""
        config = self.data['config']
        
        embed = discord.Embed(
            title="⚙️ Channelwatch Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Enabled", value="✅ Yes" if config.get('enabled', True) else "❌ No", inline=True)
        embed.add_field(name="Count Messages", value="✅ Yes" if config.get('count_messages', True) else "❌ No", inline=True)
        embed.add_field(name="Track Users", value="✅ Yes" if config.get('track_users', True) else "❌ No", inline=True)
        embed.add_field(name="Volume Threshold", value=f"{config.get('volume_threshold', 100)} msg/hr", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def channelwatch_toggle(self, ctx):
        """Enable/disable channelwatch system"""
        enabled = self.data['config'].get('enabled', True)
        self.data['config']['enabled'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['enabled'] else "❌ DISABLED"
        await ctx.send(f"✅ Channelwatch is now {status}")

    @commands.command()
    async def channelwatch_reset(self, ctx, channel: discord.TextChannel):
        """Reset counters for a watched channel"""
        channel_id = str(channel.id)
        
        if channel_id not in self.data['watched_channels']:
            await ctx.send(f"⚠️ {channel.mention} is not being watched.")
            return
        
        self.data['watched_channels'][channel_id]['message_count'] = 0
        self.data['watched_channels'][channel_id]['users'] = set()
        save_data(self.data)
        
        await ctx.send(f"✅ Counters reset for {channel.mention}")

async def setup(bot):
    await bot.add_cog(ChannelwatchCog(bot))
