import discord
from discord.ext import commands
import time
import functools
import json
from pathlib import Path
from collections import defaultdict

class PerformanceProfiler(commands.Cog):
    """Performance profiling and monitoring"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.profile_file = self.data_dir / 'performance_profile.json'
        
        self.command_times = defaultdict(list)  # {command: [execution_times]}
        self.command_stats = {}  # {command: {count, total_time, avg_time, min_time, max_time}}
        self.slow_commands = []  # [(command, time, timestamp)]
        
        self.load_profile()
        
        # Register before/after hooks
        self.bot.before_invoke(self.before_command)
        self.bot.after_invoke(self.after_command)
    
    def load_profile(self):
        """Load performance profile"""
        if self.profile_file.exists():
            with open(self.profile_file, 'r') as f:
                data = json.load(f)
                self.command_stats = data.get('command_stats', {})
                self.slow_commands = data.get('slow_commands', [])
    
    def save_profile(self):
        """Save performance profile"""
        data = {
            'command_stats': self.command_stats,
            'slow_commands': self.slow_commands[-100:]  # Keep last 100
        }
        with open(self.profile_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def before_command(self, ctx):
        """Record command start time"""
        ctx.command_start_time = time.perf_counter()
    
    async def after_command(self, ctx):
        """Record command execution time"""
        if not hasattr(ctx, 'command_start_time'):
            return
        
        execution_time = time.perf_counter() - ctx.command_start_time
        command_name = ctx.command.qualified_name if ctx.command else 'unknown'
        
        # Store execution time
        self.command_times[command_name].append(execution_time)
        
        # Keep only last 100 executions
        if len(self.command_times[command_name]) > 100:
            self.command_times[command_name] = self.command_times[command_name][-100:]
        
        # Update stats
        if command_name not in self.command_stats:
            self.command_stats[command_name] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        stats = self.command_stats[command_name]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        # Track slow commands (>1 second)
        if execution_time > 1.0:
            import datetime
            self.slow_commands.append({
                'command': command_name,
                'time': execution_time,
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': ctx.author.id,
                'guild_id': ctx.guild.id if ctx.guild else None
            })
            print(f"[Performance] Slow command detected: {command_name} took {execution_time:.2f}s")
        
        # Save periodically
        if stats['count'] % 50 == 0:
            self.save_profile()
    
    @commands.command(name='performance')
    @commands.is_owner()
    async def performance(self, ctx):
        """View performance dashboard (owner only)"""
        # Calculate overall stats
        total_commands = sum(s['count'] for s in self.command_stats.values())
        total_time = sum(s['total_time'] for s in self.command_stats.values())
        avg_time = total_time / total_commands if total_commands > 0 else 0
        
        # Slowest commands (by average)
        slowest_avg = sorted(
            self.command_stats.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:5]
        
        # Most used commands
        most_used = sorted(
            self.command_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]
        
        embed = discord.Embed(
            title="⚡ Performance Dashboard",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Total Commands", value=f"{total_commands:,}", inline=True)
        embed.add_field(name="Total Time", value=f"{total_time:.2f}s", inline=True)
        embed.add_field(name="Avg Time", value=f"{avg_time*1000:.1f}ms", inline=True)
        
        # Slowest by average
        slowest_text = "\n".join([
            f"`{cmd}`: {stats['avg_time']*1000:.1f}ms avg ({stats['count']} uses)"
            for cmd, stats in slowest_avg
        ])
        embed.add_field(name="🐌 Slowest Commands (Avg)", value=slowest_text or "No data", inline=False)
        
        # Most used
        used_text = "\n".join([
            f"`{cmd}`: {stats['count']:,} uses ({stats['avg_time']*1000:.1f}ms avg)"
            for cmd, stats in most_used
        ])
        embed.add_field(name="🔥 Most Used", value=used_text or "No data", inline=False)
        
        # Recent slow commands
        recent_slow = len([s for s in self.slow_commands[-50:]])
        embed.add_field(name="Slow Commands (>1s)", value=f"{recent_slow} in last 50 executions", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='profile_command')
    @commands.is_owner()
    async def profile_command(self, ctx, *, command_name: str):
        """View detailed performance profile for a command (owner only)"""
        if command_name not in self.command_stats:
            await ctx.send(f"❌ No performance data for `{command_name}`")
            return
        
        stats = self.command_stats[command_name]
        recent_times = self.command_times.get(command_name, [])
        
        embed = discord.Embed(
            title=f"⚡ Performance Profile: {command_name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Executions", value=f"{stats['count']:,}", inline=True)
        embed.add_field(name="Total Time", value=f"{stats['total_time']:.2f}s", inline=True)
        embed.add_field(name="Average", value=f"{stats['avg_time']*1000:.1f}ms", inline=True)
        
        embed.add_field(name="Min Time", value=f"{stats['min_time']*1000:.1f}ms", inline=True)
        embed.add_field(name="Max Time", value=f"{stats['max_time']*1000:.1f}ms", inline=True)
        
        # Calculate percentiles if we have recent times
        if recent_times:
            sorted_times = sorted(recent_times)
            p50 = sorted_times[len(sorted_times)//2]
            p95 = sorted_times[int(len(sorted_times)*0.95)]
            p99 = sorted_times[int(len(sorted_times)*0.99)]
            
            embed.add_field(name="P50 (Median)", value=f"{p50*1000:.1f}ms", inline=True)
            embed.add_field(name="P95", value=f"{p95*1000:.1f}ms", inline=True)
            embed.add_field(name="P99", value=f"{p99*1000:.1f}ms", inline=True)
        
        # Performance rating
        if stats['avg_time'] < 0.1:
            rating = "⚡ Excellent"
            color = discord.Color.green()
        elif stats['avg_time'] < 0.5:
            rating = "✅ Good"
            color = discord.Color.blue()
        elif stats['avg_time'] < 1.0:
            rating = "⚠️ Acceptable"
            color = discord.Color.orange()
        else:
            rating = "🐌 Slow"
            color = discord.Color.red()
        
        embed.add_field(name="Performance Rating", value=rating, inline=False)
        embed.color = color
        
        await ctx.send(embed=embed)
    
    @commands.command(name='slow_commands')
    @commands.is_owner()
    async def slow_commands_list(self, ctx, limit: int = 10):
        """View recent slow commands (owner only)"""
        if not self.slow_commands:
            await ctx.send("✅ No slow commands recorded")
            return
        
        recent = self.slow_commands[-limit:]
        
        embed = discord.Embed(
            title="🐌 Recent Slow Commands (>1s)",
            description=f"Showing last {len(recent)} slow executions",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        for i, slow in enumerate(reversed(recent), 1):
            embed.add_field(
                name=f"{i}. {slow['command']}",
                value=f"**Time:** {slow['time']:.2f}s\n**When:** {slow['timestamp'][:19]}\n**User:** <@{slow['user_id']}>",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='performance_export')
    @commands.is_owner()
    async def performance_export(self, ctx):
        """Export performance data (owner only)"""
        self.save_profile()
        await ctx.send(f"✅ Performance data exported to `{self.profile_file}`")
    
    @commands.command(name='reset_profile')
    @commands.is_owner()
    async def reset_profile(self, ctx):
        """Reset all performance data (owner only)"""
        self.command_times.clear()
        self.command_stats.clear()
        self.slow_commands.clear()
        self.save_profile()
        
        await ctx.send("✅ Performance profile reset")
    
    def cog_unload(self):
        """Save profile when cog is unloaded"""
        self.save_profile()

async def setup(bot):
    await bot.add_cog(PerformanceProfiler(bot))
