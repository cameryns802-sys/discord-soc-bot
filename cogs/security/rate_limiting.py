import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
import time
from pathlib import Path
from collections import defaultdict
from cogs.core.pst_timezone import get_now_pst

class RateLimiting(commands.Cog):
    """Rate limiting and anti-abuse system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path('./data')
        self.data_dir.mkdir(exist_ok=True)
        self.config_file = self.data_dir / 'rate_limit_config.json'
        
        self.config = self.load_config()
        self.user_cooldowns = defaultdict(dict)  # {user_id: {command: last_use_time}}
        self.user_command_count = defaultdict(lambda: defaultdict(int))  # {user_id: {command: count}}
        self.user_violations = defaultdict(int)  # {user_id: violation_count}
        
        # Register before_invoke hook
        self.bot.before_invoke(self.check_rate_limit)
    
    def load_config(self):
        """Load rate limit configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            'enabled': True,
            'default_cooldown': 3,  # seconds
            'burst_limit': 10,      # commands per minute
            'burst_window': 60,     # seconds
            'admin_exempt': True,
            'owner_exempt': True,
            'violation_threshold': 5,  # violations before auto-action
            'violation_action': 'warn',  # warn, timeout, or blacklist
            'custom_cooldowns': {
                # command_name: cooldown_seconds
                'backup_now': 300,
                'restart': 60,
                'shutdown': 60
            }
        }
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def is_exempt(self, user):
        """Check if user is exempt from rate limiting"""
        if not self.config['enabled']:
            return True
        
        # Owner exempt
        if self.config['owner_exempt']:
            import os
            owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
            if user.id == owner_id:
                return True
        
        # Admin exempt
        if self.config['admin_exempt'] and hasattr(user, 'guild_permissions'):
            if user.guild_permissions.administrator:
                return True
        
        return False
    
    async def check_rate_limit(self, ctx):
        """Check if user is rate limited"""
        if self.is_exempt(ctx.author):
            return
        
        user_id = ctx.author.id
        command_name = ctx.command.qualified_name if ctx.command else 'unknown'
        now = time.time()
        
        # Get cooldown for this command
        cooldown = self.config['custom_cooldowns'].get(command_name, self.config['default_cooldown'])
        
        # Check command-specific cooldown
        if command_name in self.user_cooldowns[user_id]:
            last_use = self.user_cooldowns[user_id][command_name]
            time_since = now - last_use
            
            if time_since < cooldown:
                remaining = cooldown - time_since
                self.user_violations[user_id] += 1
                
                embed = discord.Embed(
                    title="⏱️ Rate Limit Exceeded",
                    description=f"Please wait {remaining:.1f} seconds before using `{command_name}` again",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Cooldown", value=f"{cooldown}s", inline=True)
                embed.add_field(name="Remaining", value=f"{remaining:.1f}s", inline=True)
                
                await ctx.send(embed=embed, delete_after=10)
                raise commands.CommandOnCooldown(commands.Cooldown(1, cooldown), remaining, commands.BucketType.user)
        
        # Check burst limit (commands per minute)
        minute_ago = now - self.config['burst_window']
        
        # Clean old entries
        self.user_command_count[user_id] = {
            cmd: count for cmd, count in self.user_command_count[user_id].items()
            if self.user_cooldowns[user_id].get(cmd, 0) > minute_ago
        }
        
        # Count recent commands
        recent_count = sum(self.user_command_count[user_id].values())
        
        if recent_count >= self.config['burst_limit']:
            self.user_violations[user_id] += 1
            
            embed = discord.Embed(
                title="🚫 Burst Limit Exceeded",
                description=f"You've used {recent_count} commands in the last minute. Please slow down!",
                color=discord.Color.red()
            )
            embed.add_field(name="Limit", value=f"{self.config['burst_limit']}/min", inline=True)
            embed.add_field(name="Your Usage", value=f"{recent_count}/min", inline=True)
            
            await ctx.send(embed=embed, delete_after=15)
            
            # Check for violation action
            if self.user_violations[user_id] >= self.config['violation_threshold']:
                await self.handle_violation(ctx)
            
            raise commands.CommandOnCooldown(commands.Cooldown(1, 60), 60, commands.BucketType.user)
        
        # Update tracking
        self.user_cooldowns[user_id][command_name] = now
        self.user_command_count[user_id][command_name] += 1
    
    async def handle_violation(self, ctx):
        """Handle rate limit violation"""
        user_id = ctx.author.id
        action = self.config['violation_action']
        
        if action == 'warn':
            embed = discord.Embed(
                title="⚠️ Rate Limit Warning",
                description="You've exceeded rate limits multiple times. Further violations may result in restrictions.",
                color=discord.Color.red()
            )
            embed.add_field(name="Violations", value=str(self.user_violations[user_id]), inline=True)
            embed.add_field(name="Threshold", value=str(self.config['violation_threshold']), inline=True)
            
            await ctx.author.send(embed=embed)
            print(f"[Rate Limit] Warning sent to {ctx.author} ({user_id}) - {self.user_violations[user_id]} violations")
        
        elif action == 'timeout' and ctx.guild:
            try:
                await ctx.author.timeout(datetime.timedelta(minutes=5), reason="Rate limit violations")
                await ctx.send(f"🔇 {ctx.author.mention} has been timed out for 5 minutes due to rate limit violations")
                print(f"[Rate Limit] {ctx.author} timed out for rate limit violations")
            except:
                pass
        
        elif action == 'blacklist':
            # Add to blacklist (requires blacklist system)
            blacklist_cog = self.bot.get_cog('BlacklistSystem')
            if blacklist_cog:
                await blacklist_cog.add_to_blacklist(user_id, 'user', 'Automatic: Rate limit violations', duration=3600)
                print(f"[Rate Limit] {ctx.author} blacklisted for rate limit violations")
    
    @commands.command(name='rate_limit_status')
    async def rate_limit_status(self, ctx, user: discord.User = None):
        """Check rate limit status for a user"""
        user = user or ctx.author
        user_id = user.id
        
        if self.is_exempt(user):
            await ctx.send(f"✅ {user.mention} is exempt from rate limiting")
            return
        
        # Get recent command count
        now = time.time()
        minute_ago = now - self.config['burst_window']
        
        recent_count = sum(
            1 for cmd, last_use in self.user_cooldowns[user_id].items()
            if last_use > minute_ago
        )
        
        embed = discord.Embed(
            title=f"⏱️ Rate Limit Status: {user.name}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Commands (Last Min)", value=f"{recent_count}/{self.config['burst_limit']}", inline=True)
        embed.add_field(name="Violations", value=str(self.user_violations[user_id]), inline=True)
        embed.add_field(name="Status", value="✅ Good" if recent_count < self.config['burst_limit'] else "⚠️ Near Limit", inline=True)
        
        # Active cooldowns
        active_cooldowns = []
        for cmd, last_use in self.user_cooldowns[user_id].items():
            cooldown = self.config['custom_cooldowns'].get(cmd, self.config['default_cooldown'])
            remaining = cooldown - (now - last_use)
            if remaining > 0:
                active_cooldowns.append(f"`{cmd}`: {remaining:.1f}s")
        
        if active_cooldowns:
            embed.add_field(name="Active Cooldowns", value="\n".join(active_cooldowns[:5]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rate_limit_config')
    @commands.is_owner()
    async def rate_limit_config(self, ctx, setting: str = None, value: str = None):
        """Configure rate limiting (owner only)"""
        if not setting:
            embed = discord.Embed(
                title="⚙️ Rate Limit Configuration",
                color=discord.Color.blue()
            )
            embed.add_field(name="Enabled", value="✅" if self.config['enabled'] else "❌", inline=True)
            embed.add_field(name="Default Cooldown", value=f"{self.config['default_cooldown']}s", inline=True)
            embed.add_field(name="Burst Limit", value=f"{self.config['burst_limit']}/min", inline=True)
            embed.add_field(name="Admin Exempt", value="✅" if self.config['admin_exempt'] else "❌", inline=True)
            embed.add_field(name="Owner Exempt", value="✅" if self.config['owner_exempt'] else "❌", inline=True)
            embed.add_field(name="Violation Threshold", value=str(self.config['violation_threshold']), inline=True)
            embed.add_field(name="Violation Action", value=self.config['violation_action'], inline=True)
            
            await ctx.send(embed=embed)
            return
        
        # Update setting
        if setting in ['enabled', 'admin_exempt', 'owner_exempt']:
            self.config[setting] = value.lower() in ['true', '1', 'yes', 'on']
        elif setting in ['default_cooldown', 'burst_limit', 'burst_window', 'violation_threshold']:
            self.config[setting] = int(value)
        elif setting == 'violation_action':
            if value in ['warn', 'timeout', 'blacklist']:
                self.config['violation_action'] = value
            else:
                await ctx.send("❌ Invalid action. Use: warn, timeout, or blacklist")
                return
        else:
            await ctx.send(f"❌ Unknown setting: {setting}")
            return
        
        self.save_config()
        await ctx.send(f"✅ Updated {setting} to {value}")
    
    @commands.command(name='set_command_cooldown')
    @commands.is_owner()
    async def set_command_cooldown(self, ctx, command_name: str, cooldown: int):
        """Set custom cooldown for a specific command (owner only)"""
        self.config['custom_cooldowns'][command_name] = cooldown
        self.save_config()
        await ctx.send(f"✅ Set cooldown for `{command_name}` to {cooldown} seconds")
    
    @commands.command(name='reset_violations')
    @commands.is_owner()
    async def reset_violations(self, ctx, user: discord.User):
        """Reset violations for a user (owner only)"""
        user_id = user.id
        old_count = self.user_violations[user_id]
        self.user_violations[user_id] = 0
        
        await ctx.send(f"✅ Reset violations for {user.mention} (was: {old_count})")
    
    @commands.command(name='rate_limit_stats')
    @commands.is_owner()
    async def rate_limit_stats(self, ctx):
        """View rate limiting statistics (owner only)"""
        total_users_tracked = len(self.user_cooldowns)
        total_violations = sum(self.user_violations.values())
        
        # Top violators
        top_violators = sorted(
            self.user_violations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        embed = discord.Embed(
            title="📊 Rate Limiting Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Users Tracked", value=str(total_users_tracked), inline=True)
        embed.add_field(name="Total Violations", value=str(total_violations), inline=True)
        embed.add_field(name="Avg Violations", value=f"{total_violations / max(total_users_tracked, 1):.2f}", inline=True)
        
        # Top violators
        if top_violators:
            violators_text = "\n".join([
                f"<@{user_id}>: {count} violations"
                for user_id, count in top_violators
            ])
            embed.add_field(name="🚫 Top Violators", value=violators_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RateLimiting(bot))

