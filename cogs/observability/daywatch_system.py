"""
Daywatch System: Monitoring and activity tracking during day hours (7 AM to 7 PM).
Complements Nightwatch by providing daytime monitoring and metrics.
"""
import discord
from discord.ext import commands, tasks
import json
import os
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/daywatch_system.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'daywatch_active': False,
        'last_activation': None,
        'last_deactivation': None,
        'sessions': [],
        'activity_count': 0,
        'peak_hours': {},
        'config': {
            'enabled': True,
            'start_hour': 7,   # 7 AM
            'end_hour': 19,    # 7 PM
            'track_engagement': True,
            'peak_detection': True,
            'activity_alerts': False
        }
    }

def save_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class DaywatchCog(commands.Cog):
    """Monitor activity during daytime hours"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.daywatch_monitor.start()

    @tasks.loop(minutes=1)
    async def daywatch_monitor(self):
        """Check time and activate/deactivate daywatch every minute"""
        if not self.data.get('config', {}).get('enabled', True):
            return
        
        now = get_now_pst()
        current_hour = now.hour
        
        start_hour = self.data.get('config', {}).get('start_hour', 7)
        end_hour = self.data.get('config', {}).get('end_hour', 19)
        
        is_daywatch_time = start_hour <= current_hour < end_hour
        
        if is_daywatch_time and not self.data['daywatch_active']:
            self.data['daywatch_active'] = True
            self.data['last_activation'] = now.isoformat()
            self.data['activity_count'] = 0
            save_data(self.data)
            print(f"[Daywatch] ☀️ ACTIVATED at {now.strftime('%H:%M')}")
        
        elif not is_daywatch_time and self.data['daywatch_active']:
            self.data['daywatch_active'] = False
            self.data['last_deactivation'] = now.isoformat()
            session = {
                'activation': self.data['last_activation'],
                'deactivation': now.isoformat(),
                'activity': self.data['activity_count']
            }
            self.data['sessions'].append(session)
            save_data(self.data)
            print(f"[Daywatch] 🌙 DEACTIVATED at {now.strftime('%H:%M')}")

    @daywatch_monitor.before_loop
    async def before_daywatch_monitor(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def daywatch_status(self, ctx):
        """View current daywatch status"""
        config = self.data.get('config', {})
        start_hour = config.get('start_hour', 7)
        end_hour = config.get('end_hour', 19)
        
        embed = discord.Embed(
            title="☀️ Daywatch Status",
            color=discord.Color.gold() if self.data['daywatch_active'] else discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        status = "🟢 ACTIVE" if self.data['daywatch_active'] else "🔴 INACTIVE"
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Active Hours", value=f"{start_hour:02d}:00 - {end_hour:02d}:00", inline=True)
        embed.add_field(name="Activity Count", value=str(self.data['activity_count']), inline=True)
        embed.add_field(name="Peak Detection", value="✅ Enabled" if config.get('peak_detection', True) else "❌ Disabled", inline=True)
        
        if self.data['last_activation']:
            embed.add_field(name="Last Activated", value=self.data['last_activation'], inline=False)
        
        embed.set_footer(text="Daywatch tracks activity during day hours")
        await ctx.send(embed=embed)

    @commands.command()
    async def daywatch_config(self, ctx):
        """View daywatch configuration"""
        config = self.data.get('config', {})
        
        embed = discord.Embed(
            title="⚙️ Daywatch Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Active Hours",
            value=f"{config.get('start_hour', 7):02d}:00 - {config.get('end_hour', 19):02d}:00",
            inline=True
        )
        embed.add_field(name="Enabled", value="✅ Yes" if config.get('enabled', True) else "❌ No", inline=True)
        embed.add_field(name="Track Engagement", value="✅ Yes" if config.get('track_engagement', True) else "❌ No", inline=True)
        embed.add_field(name="Peak Detection", value="✅ Yes" if config.get('peak_detection', True) else "❌ No", inline=True)
        embed.add_field(name="Activity Alerts", value="✅ Yes" if config.get('activity_alerts', False) else "❌ No", inline=True)
        
        embed.set_footer(text="Use /daywatch_toggle, /daywatch_set_hours to configure")
        await ctx.send(embed=embed)

    @commands.command()
    async def daywatch_set_hours(self, ctx, start_hour: int, end_hour: int):
        """Set custom daywatch active hours"""
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            await ctx.send("❌ Hours must be between 0 and 23")
            return
        
        self.data['config']['start_hour'] = start_hour
        self.data['config']['end_hour'] = end_hour
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Daywatch Hours Updated",
            description=f"Daywatch now active from {start_hour:02d}:00 to {end_hour:02d}:00",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def daywatch_toggle(self, ctx):
        """Enable/disable daywatch system"""
        enabled = self.data['config'].get('enabled', True)
        self.data['config']['enabled'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['enabled'] else "❌ DISABLED"
        embed = discord.Embed(
            title="Daywatch Status Updated",
            description=f"Daywatch is now {status}",
            color=discord.Color.green() if self.data['config']['enabled'] else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def daywatch_toggle_engagement(self, ctx):
        """Toggle engagement tracking"""
        enabled = self.data['config'].get('track_engagement', True)
        self.data['config']['track_engagement'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['track_engagement'] else "❌ DISABLED"
        await ctx.send(f"✅ Engagement tracking is now {status}")

    @commands.command()
    async def daywatch_toggle_peak(self, ctx):
        """Toggle peak hour detection"""
        enabled = self.data['config'].get('peak_detection', True)
        self.data['config']['peak_detection'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['peak_detection'] else "❌ DISABLED"
        await ctx.send(f"✅ Peak detection is now {status}")

    @commands.command()
    async def daywatch_log_activity(self, ctx):
        """Log activity during daywatch"""
        if self.data['daywatch_active']:
            self.data['activity_count'] += 1
            
            now = get_now_pst()
            hour = now.hour
            if hour not in self.data['peak_hours']:
                self.data['peak_hours'][str(hour)] = 0
            self.data['peak_hours'][str(hour)] += 1
            
            save_data(self.data)
            embed = discord.Embed(
                title="📊 Activity Logged",
                description=f"Total activities: {self.data['activity_count']}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ Daywatch is not currently active.")

    @commands.command()
    async def daywatch_stats(self, ctx):
        """View daywatch statistics"""
        total_sessions = len(self.data['sessions'])
        total_activity = sum(s['activity'] for s in self.data['sessions'])
        
        embed = discord.Embed(
            title="📈 Daywatch Statistics",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Sessions", value=str(total_sessions), inline=True)
        embed.add_field(name="Total Activity", value=str(total_activity), inline=True)
        embed.add_field(name="Current Session Activity", value=str(self.data['activity_count']), inline=True)
        
        if total_sessions > 0:
            avg_activity = total_activity / total_sessions
            embed.add_field(name="Avg Activity/Session", value=f"{avg_activity:.2f}", inline=True)
        
        if self.data['peak_hours']:
            peak_hour = max(self.data['peak_hours'], key=self.data['peak_hours'].get)
            embed.add_field(name="Peak Hour", value=f"{peak_hour}:00", inline=True)
        
        embed.set_footer(text="Daywatch: 7 AM - 7 PM")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DaywatchCog(bot))
