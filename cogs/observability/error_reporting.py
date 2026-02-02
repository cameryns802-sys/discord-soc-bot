import discord
from discord.ext import commands, tasks
import json
import traceback
import datetime
import os
from pathlib import Path
from collections import deque

class ErrorReporting(commands.Cog):
    """Error reporting and monitoring system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.error_file = self.data_dir / 'error_log.json'
        self.config_file = self.data_dir / 'error_config.json'
        
        self.errors = self.load_errors()
        self.config = self.load_config()
        self.recent_errors = deque(maxlen=100)  # Keep last 100 errors in memory
        
        self.error_check.start()
        
        # Register error listener
        self.bot.add_listener(self.on_error_track, 'on_command_error')
    
    def load_errors(self):
        """Load error log"""
        if self.error_file.exists():
            with open(self.error_file, 'r') as f:
                return json.load(f)
        return {
            'total_errors': 0,
            'errors': [],
            'error_types': {},
            'command_errors': {}
        }
    
    def load_config(self):
        """Load error reporting configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            'enabled': True,
            'notify_owner': True,
            'notify_threshold': 5,  # Notify after 5 errors in 5 minutes
            'notify_critical_immediately': True,
            'owner_id': int(os.getenv('BOT_OWNER_ID', '0')),
            'track_commands': True,
            'max_errors_stored': 1000
        }
    
    def save_errors(self):
        """Save error log"""
        # Keep only last N errors
        if len(self.errors['errors']) > self.config['max_errors_stored']:
            self.errors['errors'] = self.errors['errors'][-self.config['max_errors_stored']:]
        
        with open(self.error_file, 'w') as f:
            json.dump(self.errors, f, indent=2)
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def on_error_track(self, ctx, error):
        """Track command errors"""
        if not self.config['enabled']:
            return
        
        # Get error details
        error_type = type(error).__name__
        error_msg = str(error)
        command_name = ctx.command.qualified_name if ctx.command else 'unknown'
        
        # Full traceback
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Create error record
        error_record = {
            'timestamp': datetime.datetime.now().isoformat(),
            'type': error_type,
            'message': error_msg,
            'command': command_name,
            'user_id': ctx.author.id,
            'guild_id': ctx.guild.id if ctx.guild else None,
            'channel_id': ctx.channel.id,
            'traceback': tb,
            'severity': self.classify_severity(error)
        }
        
        # Store error
        self.errors['total_errors'] += 1
        self.errors['errors'].append(error_record)
        self.recent_errors.append(error_record)
        
        # Update error type counter
        if error_type not in self.errors['error_types']:
            self.errors['error_types'][error_type] = 0
        self.errors['error_types'][error_type] += 1
        
        # Update command error counter
        if command_name not in self.errors['command_errors']:
            self.errors['command_errors'][command_name] = 0
        self.errors['command_errors'][command_name] += 1
        
        # Save
        self.save_errors()
        
        # Check if we should notify owner
        if self.config['notify_critical_immediately'] and error_record['severity'] == 'critical':
            await self.notify_owner_critical(error_record)
        
        print(f"[Error Tracking] {error_type} in {command_name}: {error_msg}")
    
    def classify_severity(self, error):
        """Classify error severity"""
        critical_errors = [
            'AttributeError',
            'KeyError',
            'IndexError',
            'TypeError',
            'ValueError',
            'RuntimeError'
        ]
        
        error_type = type(error).__name__
        
        if error_type in critical_errors:
            return 'critical'
        elif 'NotFound' in error_type or 'Forbidden' in error_type:
            return 'warning'
        else:
            return 'info'
    
    async def notify_owner_critical(self, error_record):
        """Notify owner of critical error"""
        if not self.config['notify_owner'] or not self.config['owner_id']:
            return
        
        try:
            owner = await self.bot.fetch_user(self.config['owner_id'])
            
            embed = discord.Embed(
                title="🚨 Critical Error Detected",
                description=f"A critical error occurred in the bot",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.UTC)
            )
            
            embed.add_field(name="Error Type", value=error_record['type'], inline=True)
            embed.add_field(name="Command", value=error_record['command'], inline=True)
            embed.add_field(name="Severity", value=error_record['severity'].upper(), inline=True)
            
            embed.add_field(
                name="Message",
                value=error_record['message'][:1024],
                inline=False
            )
            
            embed.add_field(
                name="Traceback (Last 500 chars)",
                value=f"```{error_record['traceback'][-500:]}```",
                inline=False
            )
            
            await owner.send(embed=embed)
        
        except Exception as e:
            print(f"[Error Reporting] Failed to notify owner: {e}")
    
    @tasks.loop(minutes=5)
    async def error_check(self):
        """Check error rate and notify if threshold exceeded"""
        if not self.config['notify_owner'] or not self.config['owner_id']:
            return
        
        # Count errors in last 5 minutes
        now = datetime.datetime.now()
        recent_count = sum(
            1 for err in self.recent_errors
            if (now - datetime.datetime.fromisoformat(err['timestamp'])).total_seconds() < 300
        )
        
        if recent_count >= self.config['notify_threshold']:
            try:
                owner = await self.bot.fetch_user(self.config['owner_id'])
                
                embed = discord.Embed(
                    title="⚠️ High Error Rate Detected",
                    description=f"{recent_count} errors in the last 5 minutes",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                
                # Top error types
                error_types = {}
                for err in list(self.recent_errors)[-recent_count:]:
                    error_types[err['type']] = error_types.get(err['type'], 0) + 1
                
                top_types = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
                embed.add_field(
                    name="Top Error Types",
                    value="\n".join([f"{t}: {c}" for t, c in top_types]),
                    inline=False
                )
                
                embed.add_field(name="Action", value="Use `!error_dashboard` to investigate", inline=False)
                
                await owner.send(embed=embed)
            
            except Exception as e:
                print(f"[Error Reporting] Failed to notify owner: {e}")
    
    @error_check.before_loop
    async def before_error_check(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='error_dashboard')
    @commands.is_owner()
    async def error_dashboard(self, ctx):
        """View error dashboard (owner only)"""
        total = self.errors['total_errors']
        
        # Recent errors (last hour)
        now = datetime.datetime.now()
        recent_hour = sum(
            1 for err in self.errors['errors']
            if (now - datetime.datetime.fromisoformat(err['timestamp'])).total_seconds() < 3600
        )
        
        # Top error types
        top_types = sorted(
            self.errors['error_types'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Top problematic commands
        top_cmds = sorted(
            self.errors['command_errors'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        embed = discord.Embed(
            title="🚨 Error Dashboard",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        embed.add_field(name="Total Errors", value=f"{total:,}", inline=True)
        embed.add_field(name="Last Hour", value=f"{recent_hour:,}", inline=True)
        embed.add_field(name="Stored", value=f"{len(self.errors['errors']):,}", inline=True)
        
        # Top error types
        types_text = "\n".join([f"{i}. `{t}`: {c:,}" for i, (t, c) in enumerate(top_types, 1)])
        embed.add_field(name="🔥 Top Error Types", value=types_text or "No errors", inline=False)
        
        # Top commands with errors
        cmds_text = "\n".join([f"{i}. `{c}`: {count:,} errors" for i, (c, count) in enumerate(top_cmds, 1)])
        embed.add_field(name="⚠️ Problematic Commands", value=cmds_text or "No errors", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='recent_errors')
    @commands.is_owner()
    async def recent_errors(self, ctx, limit: int = 10):
        """View recent errors (owner only)"""
        if not self.errors['errors']:
            await ctx.send("✅ No errors recorded")
            return
        
        recent = self.errors['errors'][-limit:]
        
        for i, err in enumerate(reversed(recent), 1):
            embed = discord.Embed(
                title=f"Error #{len(self.errors['errors']) - limit + len(recent) - i + 1}",
                color=discord.Color.red()
            )
            
            embed.add_field(name="Type", value=err['type'], inline=True)
            embed.add_field(name="Command", value=err['command'], inline=True)
            embed.add_field(name="Severity", value=err['severity'].upper(), inline=True)
            
            embed.add_field(name="Message", value=err['message'][:1024], inline=False)
            embed.add_field(name="Time", value=err['timestamp'][:19], inline=True)
            
            if ctx.guild:
                embed.add_field(name="Guild", value=str(err.get('guild_id', 'DM')), inline=True)
            
            await ctx.send(embed=embed)
    
    @commands.command(name='error_details')
    @commands.is_owner()
    async def error_details(self, ctx, error_id: int):
        """View detailed error information (owner only)"""
        if error_id < 1 or error_id > len(self.errors['errors']):
            await ctx.send(f"❌ Error #{error_id} not found. Use `!recent_errors` to see available errors.")
            return
        
        err = self.errors['errors'][error_id - 1]
        
        embed = discord.Embed(
            title=f"🔍 Error Details #{error_id}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.fromisoformat(err['timestamp'])
        )
        
        embed.add_field(name="Type", value=err['type'], inline=True)
        embed.add_field(name="Command", value=err['command'], inline=True)
        embed.add_field(name="Severity", value=err['severity'].upper(), inline=True)
        
        embed.add_field(name="User ID", value=str(err['user_id']), inline=True)
        embed.add_field(name="Guild ID", value=str(err.get('guild_id', 'DM')), inline=True)
        embed.add_field(name="Channel ID", value=str(err['channel_id']), inline=True)
        
        embed.add_field(name="Message", value=err['message'][:1024], inline=False)
        
        # Send traceback as file
        tb_content = err['traceback']
        
        await ctx.send(embed=embed)
        
        # Send traceback as text file
        await ctx.send(
            content="**Full Traceback:**",
            file=discord.File(
                fp=tb_content.encode(),
                filename=f"error_{error_id}_traceback.txt"
            )
        )
    
    @commands.command(name='error_stats')
    @commands.is_owner()
    async def error_stats(self, ctx, days: int = 7):
        """View error statistics over time (owner only)"""
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=days)
        
        # Filter errors within time range
        recent_errors = [
            err for err in self.errors['errors']
            if datetime.datetime.fromisoformat(err['timestamp']) > cutoff
        ]
        
        # Group by day
        daily_counts = {}
        for err in recent_errors:
            day = err['timestamp'][:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        embed = discord.Embed(
            title=f"📊 Error Statistics ({days} days)",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.UTC)
        )
        
        embed.add_field(name="Total Errors", value=f"{len(recent_errors):,}", inline=True)
        embed.add_field(name="Avg per Day", value=f"{len(recent_errors) / days:.1f}", inline=True)
        
        # Daily breakdown
        for i in range(days):
            date = (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            count = daily_counts.get(date, 0)
            bar_length = min(count // 2, 20)
            bar = '█' * bar_length
            
            embed.add_field(
                name=date,
                value=f"{bar} {count:,} errors",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='error_config')
    @commands.is_owner()
    async def error_config_cmd(self, ctx, setting: str = None, value: str = None):
        """Configure error reporting settings (owner only)"""
        if not setting:
            embed = discord.Embed(
                title="⚙️ Error Reporting Configuration",
                color=discord.Color.blue()
            )
            embed.add_field(name="Enabled", value="✅" if self.config['enabled'] else "❌", inline=True)
            embed.add_field(name="Notify Owner", value="✅" if self.config['notify_owner'] else "❌", inline=True)
            embed.add_field(name="Notify Threshold", value=str(self.config['notify_threshold']), inline=True)
            embed.add_field(name="Notify Critical", value="✅" if self.config['notify_critical_immediately'] else "❌", inline=True)
            embed.add_field(name="Track Commands", value="✅" if self.config['track_commands'] else "❌", inline=True)
            embed.add_field(name="Max Errors Stored", value=str(self.config['max_errors_stored']), inline=True)
            
            await ctx.send(embed=embed)
            return
        
        # Update setting
        if setting in ['enabled', 'notify_owner', 'notify_critical_immediately', 'track_commands']:
            self.config[setting] = value.lower() in ['true', '1', 'yes', 'on']
        elif setting in ['notify_threshold', 'max_errors_stored']:
            self.config[setting] = int(value)
        else:
            await ctx.send(f"❌ Unknown setting: {setting}")
            return
        
        self.save_config()
        await ctx.send(f"✅ Updated {setting} to {value}")
    
    @commands.command(name='clear_errors')
    @commands.is_owner()
    async def clear_errors(self, ctx):
        """Clear all error logs (owner only)"""
        embed = discord.Embed(
            title="⚠️ Confirm Error Log Clear",
            description="Are you sure you want to clear all error logs?\n\n**This cannot be undone!**",
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
                # Backup before clearing
                backup_file = self.data_dir / f'error_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(backup_file, 'w') as f:
                    json.dump(self.errors, f, indent=2)
                
                # Clear errors
                self.errors = {
                    'total_errors': 0,
                    'errors': [],
                    'error_types': {},
                    'command_errors': {}
                }
                self.recent_errors.clear()
                self.save_errors()
                
                await ctx.send(f"✅ Error logs cleared. Backup saved to `{backup_file}`")
            else:
                await ctx.send("❌ Clear cancelled")
        
        except:
            await ctx.send("❌ Clear cancelled or timed out")
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.error_check.cancel()
        self.save_errors()

async def setup(bot):
    await bot.add_cog(ErrorReporting(bot))
