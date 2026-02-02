import discord
from discord.ext import commands
import json
import datetime
from pathlib import Path
from collections import defaultdict
import time

class CommandAnalytics(commands.Cog):
    """Command usage analytics and telemetry"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.analytics_file = self.data_dir / 'command_analytics.json'
        self.data = self.load_data()
        
        # Register command listener
        self.bot.add_listener(self.on_command_completion, 'on_command_completion')
        self.bot.add_listener(self.on_command_error_track, 'on_command_error')
    
    def load_data(self):
        """Load analytics data"""
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        return {
            'total_commands': 0,
            'total_errors': 0,
            'commands': {},  # command_name: {count, errors, total_time, avg_time, users}
            'users': {},     # user_id: {count, commands}
            'guilds': {},    # guild_id: {count, commands}
            'hourly': {},    # hour: count
            'daily': {},     # date: count
            'start_time': datetime.datetime.now().isoformat()
        }
    
    def save_data(self):
        """Save analytics data"""
        with open(self.analytics_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    async def on_command_completion(self, ctx):
        """Track command completion"""
        command_name = ctx.command.qualified_name if ctx.command else 'unknown'
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id) if ctx.guild else 'DM'
        
        # Total commands
        self.data['total_commands'] += 1
        
        # Command stats
        if command_name not in self.data['commands']:
            self.data['commands'][command_name] = {
                'count': 0,
                'errors': 0,
                'total_time': 0,
                'users': set(),
                'first_use': datetime.datetime.now().isoformat(),
                'last_use': datetime.datetime.now().isoformat()
            }
        
        cmd_data = self.data['commands'][command_name]
        cmd_data['count'] += 1
        cmd_data['last_use'] = datetime.datetime.now().isoformat()
        
        # Convert set to list for JSON serialization
        if isinstance(cmd_data['users'], set):
            cmd_data['users'] = list(cmd_data['users'])
        if user_id not in cmd_data['users']:
            cmd_data['users'].append(user_id)
        
        # User stats
        if user_id not in self.data['users']:
            self.data['users'][user_id] = {'count': 0, 'commands': {}}
        
        self.data['users'][user_id]['count'] += 1
        if command_name not in self.data['users'][user_id]['commands']:
            self.data['users'][user_id]['commands'][command_name] = 0
        self.data['users'][user_id]['commands'][command_name] += 1
        
        # Guild stats
        if guild_id not in self.data['guilds']:
            self.data['guilds'][guild_id] = {'count': 0, 'commands': {}}
        
        self.data['guilds'][guild_id]['count'] += 1
        if command_name not in self.data['guilds'][guild_id]['commands']:
            self.data['guilds'][guild_id]['commands'][command_name] = 0
        self.data['guilds'][guild_id]['commands'][command_name] += 1
        
        # Hourly/Daily stats
        hour = datetime.datetime.now().strftime('%Y-%m-%d %H:00')
        day = datetime.datetime.now().strftime('%Y-%m-%d')
        
        self.data['hourly'][hour] = self.data['hourly'].get(hour, 0) + 1
        self.data['daily'][day] = self.data['daily'].get(day, 0) + 1
        
        # Save periodically (every 10 commands)
        if self.data['total_commands'] % 10 == 0:
            self.save_data()
    
    async def on_command_error_track(self, ctx, error):
        """Track command errors"""
        command_name = ctx.command.qualified_name if ctx.command else 'unknown'
        
        self.data['total_errors'] += 1
        
        if command_name in self.data['commands']:
            self.data['commands'][command_name]['errors'] += 1
        
        # Save on errors
        self.save_data()
    
    @commands.command(name='analytics')
    @commands.is_owner()
    async def analytics(self, ctx):
        """View command analytics dashboard (owner only)"""
        # Calculate stats
        total_cmds = self.data['total_commands']
        total_errors = self.data['total_errors']
        error_rate = (total_errors / total_cmds * 100) if total_cmds > 0 else 0
        
        # Top commands
        top_commands = sorted(
            self.data['commands'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        
        # Top users
        top_users = sorted(
            self.data['users'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]
        
        embed = discord.Embed(
            title="📊 Command Analytics Dashboard",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        # Overview
        embed.add_field(name="Total Commands", value=f"{total_cmds:,}", inline=True)
        embed.add_field(name="Total Errors", value=f"{total_errors:,}", inline=True)
        embed.add_field(name="Error Rate", value=f"{error_rate:.2f}%", inline=True)
        
        # Top commands
        top_cmd_text = "\n".join([
            f"{i}. `{cmd}`: {data['count']:,} uses"
            for i, (cmd, data) in enumerate(top_commands, 1)
        ])
        embed.add_field(name="🔥 Top Commands", value=top_cmd_text or "No data", inline=False)
        
        # Top users
        top_user_text = "\n".join([
            f"{i}. <@{user_id}>: {data['count']:,} commands"
            for i, (user_id, data) in enumerate(top_users, 1)
        ])
        embed.add_field(name="👥 Top Users", value=top_user_text or "No data", inline=False)
        
        # Time range
        start_time = datetime.datetime.fromisoformat(self.data['start_time'])
        uptime = datetime.datetime.now() - start_time
        embed.add_field(name="📅 Tracking Since", value=f"{uptime.days} days ago", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='command_stats')
    @commands.is_owner()
    async def command_stats(self, ctx, *, command_name: str):
        """View detailed stats for a specific command (owner only)"""
        if command_name not in self.data['commands']:
            await ctx.send(f"❌ No data for command `{command_name}`")
            return
        
        cmd_data = self.data['commands'][command_name]
        
        embed = discord.Embed(
            title=f"📊 Command Stats: {command_name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        embed.add_field(name="Total Uses", value=f"{cmd_data['count']:,}", inline=True)
        embed.add_field(name="Errors", value=f"{cmd_data['errors']:,}", inline=True)
        
        error_rate = (cmd_data['errors'] / cmd_data['count'] * 100) if cmd_data['count'] > 0 else 0
        embed.add_field(name="Error Rate", value=f"{error_rate:.2f}%", inline=True)
        
        embed.add_field(name="Unique Users", value=str(len(cmd_data.get('users', []))), inline=True)
        embed.add_field(name="First Use", value=cmd_data.get('first_use', 'Unknown')[:19], inline=True)
        embed.add_field(name="Last Use", value=cmd_data.get('last_use', 'Unknown')[:19], inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='user_stats')
    @commands.is_owner()
    async def user_stats(self, ctx, user: discord.User = None):
        """View command usage stats for a user (owner only)"""
        user = user or ctx.author
        user_id = str(user.id)
        
        if user_id not in self.data['users']:
            await ctx.send(f"❌ No data for {user.mention}")
            return
        
        user_data = self.data['users'][user_id]
        
        # Top commands for this user
        top_cmds = sorted(
            user_data['commands'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title=f"📊 User Stats: {user.name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Total Commands", value=f"{user_data['count']:,}", inline=True)
        embed.add_field(name="Unique Commands", value=str(len(user_data['commands'])), inline=True)
        
        # Rank among all users
        all_users = sorted(self.data['users'].items(), key=lambda x: x[1]['count'], reverse=True)
        rank = next((i for i, (uid, _) in enumerate(all_users, 1) if uid == user_id), 0)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        
        # Top commands
        top_cmd_text = "\n".join([
            f"{i}. `{cmd}`: {count} uses"
            for i, (cmd, count) in enumerate(top_cmds, 1)
        ])
        embed.add_field(name="🔥 Top Commands", value=top_cmd_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='guild_stats')
    @commands.is_owner()
    async def guild_stats(self, ctx):
        """View command usage stats for current guild (owner only)"""
        guild_id = str(ctx.guild.id) if ctx.guild else 'DM'
        
        if guild_id not in self.data['guilds']:
            await ctx.send(f"❌ No data for this guild")
            return
        
        guild_data = self.data['guilds'][guild_id]
        
        # Top commands in this guild
        top_cmds = sorted(
            guild_data['commands'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title=f"📊 Guild Stats: {ctx.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        if ctx.guild:
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        embed.add_field(name="Total Commands", value=f"{guild_data['count']:,}", inline=True)
        embed.add_field(name="Unique Commands", value=str(len(guild_data['commands'])), inline=True)
        
        # Top commands
        top_cmd_text = "\n".join([
            f"{i}. `{cmd}`: {count} uses"
            for i, (cmd, count) in enumerate(top_cmds, 1)
        ])
        embed.add_field(name="🔥 Top Commands", value=top_cmd_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='analytics_heatmap')
    @commands.is_owner()
    async def analytics_heatmap(self, ctx, days: int = 7):
        """View command usage heatmap (owner only)"""
        # Get last N days
        today = datetime.datetime.now()
        dates = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
        dates.reverse()
        
        embed = discord.Embed(
            title="📊 Command Usage Heatmap",
            description=f"Last {days} days",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        for date in dates:
            count = self.data['daily'].get(date, 0)
            bar_length = min(count // 10, 20)  # Scale to max 20 chars
            bar = '█' * bar_length
            
            embed.add_field(
                name=date,
                value=f"{bar} {count:,} commands",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='export_analytics')
    @commands.is_owner()
    async def export_analytics(self, ctx):
        """Export analytics data as JSON (owner only)"""
        # Create export
        export_data = {
            'exported_at': datetime.datetime.now().isoformat(),
            'total_commands': self.data['total_commands'],
            'total_errors': self.data['total_errors'],
            'tracking_since': self.data['start_time'],
            'top_commands': sorted(
                self.data['commands'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:50],
            'command_count': len(self.data['commands']),
            'user_count': len(self.data['users']),
            'guild_count': len(self.data['guilds'])
        }
        
        export_file = self.data_dir / f'analytics_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        await ctx.send(f"✅ Analytics exported to `{export_file}`")
    
    @commands.command(name='reset_analytics')
    @commands.is_owner()
    async def reset_analytics(self, ctx):
        """Reset all analytics data (owner only)"""
        embed = discord.Embed(
            title="⚠️ Confirm Analytics Reset",
            description="Are you sure you want to reset all analytics data?\n\n**This cannot be undone!**",
            color=discord.Color.red()
        )
        embed.add_field(name="To Proceed", value="React with ✅ within 30 seconds", inline=False)
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                # Backup current data
                backup_file = self.data_dir / f'analytics_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(backup_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                
                # Reset data
                self.data = self.load_data()
                self.save_data()
                
                await ctx.send(f"✅ Analytics reset. Backup saved to `{backup_file}`")
            else:
                await ctx.send("❌ Reset cancelled")
        
        except Exception as e:
            await ctx.send(f"❌ Reset cancelled or timed out")
    
    def cog_unload(self):
        """Save data when cog is unloaded"""
        self.save_data()

async def setup(bot):
    await bot.add_cog(CommandAnalytics(bot))
