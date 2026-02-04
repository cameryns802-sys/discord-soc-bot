"""
Userwatch System: Monitor specific user activities and behavior patterns.
Tracks user actions, patterns, and generates behavioral analytics.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/userwatch_system.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'watched_users': {},  # user_id: {name, added_date, events: []}
        'config': {
            'enabled': True,
            'track_messages': True,
            'track_joins': True,
            'track_voice': True,
            'track_roles': True,
            'alert_on_pattern': False,
            'pattern_threshold': 5  # Alert if X events in Y minutes
        }
    }

def save_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class UserwatchCog(commands.Cog):
    """Monitor user activities and behavioral patterns"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Log messages from watched users"""
        if not self.data['config'].get('track_messages', True):
            return
        
        user_id = str(message.author.id)
        if user_id in self.data['watched_users']:
            event = {
                'type': 'message',
                'timestamp': get_now_pst().isoformat(),
                'channel': str(message.channel),
                'content': message.content[:100]
            }
            self.data['watched_users'][user_id]['events'].append(event)
            
            # Keep only last 100 events
            if len(self.data['watched_users'][user_id]['events']) > 100:
                self.data['watched_users'][user_id]['events'] = self.data['watched_users'][user_id]['events'][-100:]
            
            save_data(self.data)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log member joins for watched users"""
        if not self.data['config'].get('track_joins', True):
            return
        
        user_id = str(member.id)
        if user_id in self.data['watched_users']:
            event = {
                'type': 'join',
                'timestamp': get_now_pst().isoformat(),
                'guild': str(member.guild)
            }
            self.data['watched_users'][user_id]['events'].append(event)
            save_data(self.data)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log role changes for watched users"""
        if not self.data['config'].get('track_roles', True):
            return
        
        user_id = str(after.id)
        if user_id in self.data['watched_users']:
            if before.roles != after.roles:
                added = set(after.roles) - set(before.roles)
                removed = set(before.roles) - set(after.roles)
                
                event = {
                    'type': 'role_change',
                    'timestamp': get_now_pst().isoformat(),
                    'added': [r.name for r in added],
                    'removed': [r.name for r in removed]
                }
                self.data['watched_users'][user_id]['events'].append(event)
                save_data(self.data)

    @commands.command()
    async def userwatch_add(self, ctx, user: discord.Member):
        """Add user to watchlist"""
        user_id = str(user.id)
        
        if user_id in self.data['watched_users']:
            await ctx.send(f"⚠️ {user.mention} is already being watched.")
            return
        
        self.data['watched_users'][user_id] = {
            'name': user.name,
            'added_date': get_now_pst().isoformat(),
            'events': []
        }
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ User Added to Userwatch",
            description=f"{user.mention} is now being monitored",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def userwatch_remove(self, ctx, user: discord.Member):
        """Remove user from watchlist"""
        user_id = str(user.id)
        
        if user_id not in self.data['watched_users']:
            await ctx.send(f"⚠️ {user.mention} is not being watched.")
            return
        
        del self.data['watched_users'][user_id]
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ User Removed from Userwatch",
            description=f"{user.mention} is no longer being monitored",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def userwatch_list(self, ctx):
        """List all watched users"""
        if not self.data['watched_users']:
            await ctx.send("📋 No users are currently being watched.")
            return
        
        embed = discord.Embed(
            title="📋 Watched Users",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for user_id, info in list(self.data['watched_users'].items())[:10]:
            events = len(info.get('events', []))
            embed.add_field(
                name=f"{info['name']} (ID: {user_id})",
                value=f"Events: {events}\nAdded: {info['added_date']}",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(self.data['watched_users'])} users")
        await ctx.send(embed=embed)

    @commands.command()
    async def userwatch_view(self, ctx, user: discord.Member):
        """View detailed activity for a watched user"""
        user_id = str(user.id)
        
        if user_id not in self.data['watched_users']:
            await ctx.send(f"⚠️ {user.mention} is not being watched.")
            return
        
        info = self.data['watched_users'][user_id]
        events = info.get('events', [])
        
        embed = discord.Embed(
            title=f"👤 Activity Report: {info['name']}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Events", value=str(len(events)), inline=True)
        embed.add_field(name="Added Date", value=info['added_date'], inline=True)
        
        # Count event types
        event_types = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if event_types:
            types_str = "\n".join([f"• {k}: {v}" for k, v in event_types.items()])
            embed.add_field(name="Event Types", value=types_str, inline=False)
        
        # Show recent events
        if events:
            recent = events[-5:]
            recent_str = "\n".join([
                f"[{e.get('type', '?')}] {e.get('timestamp', '?')[:16]}"
                for e in recent
            ])
            embed.add_field(name="Recent Events", value=recent_str, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def userwatch_config(self, ctx):
        """View userwatch configuration"""
        config = self.data['config']
        
        embed = discord.Embed(
            title="⚙️ Userwatch Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Enabled", value="✅ Yes" if config.get('enabled', True) else "❌ No", inline=True)
        embed.add_field(name="Track Messages", value="✅ Yes" if config.get('track_messages', True) else "❌ No", inline=True)
        embed.add_field(name="Track Joins", value="✅ Yes" if config.get('track_joins', True) else "❌ No", inline=True)
        embed.add_field(name="Track Voice", value="✅ Yes" if config.get('track_voice', True) else "❌ No", inline=True)
        embed.add_field(name="Track Roles", value="✅ Yes" if config.get('track_roles', True) else "❌ No", inline=True)
        embed.add_field(name="Alert on Pattern", value="✅ Yes" if config.get('alert_on_pattern', False) else "❌ No", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def userwatch_toggle(self, ctx):
        """Enable/disable userwatch system"""
        enabled = self.data['config'].get('enabled', True)
        self.data['config']['enabled'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['enabled'] else "❌ DISABLED"
        await ctx.send(f"✅ Userwatch is now {status}")

    @commands.command()
    async def userwatch_clear_events(self, ctx, user: discord.Member):
        """Clear all events for a watched user"""
        user_id = str(user.id)
        
        if user_id not in self.data['watched_users']:
            await ctx.send(f"⚠️ {user.mention} is not being watched.")
            return
        
        self.data['watched_users'][user_id]['events'] = []
        save_data(self.data)
        
        await ctx.send(f"✅ Events cleared for {user.mention}")

async def setup(bot):
    await bot.add_cog(UserwatchCog(bot))
