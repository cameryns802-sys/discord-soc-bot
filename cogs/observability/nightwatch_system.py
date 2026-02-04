"""
Nightwatch System: Automated monitoring and presence tracking from 7 PM to 7 AM.
Monitors server activity, user status, and provides enhanced security during night hours.
"""
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

DATA_FILE = 'data/nightwatch_system.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'nightwatch_active': False,
        'last_activation': None,
        'last_deactivation': None,
        'sessions': [],
        'alerts_tonight': 0,
        'monitored_users': [],
        'blackout_channels': [],
        'config': {
            'enabled': True,
            'start_hour': 19,  # 7 PM
            'end_hour': 7,     # 7 AM
            'alert_threshold': None,  # Alert if exceeds this per session
            'auto_escalate': False,  # Auto-escalate high alert counts
            'dm_alerts': False,  # DM admin on alerts
            'log_all_activity': False  # Log all activity vs just alerts
        }
    }

def save_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class NightwatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.nightwatch_monitor.start()

    @tasks.loop(minutes=1)
    async def nightwatch_monitor(self):
        """Check time and activate/deactivate nightwatch every minute"""
        # Check if nightwatch is enabled
        if not self.data.get('config', {}).get('enabled', True):
            return
        
        now = datetime.now()
        current_hour = now.hour
        
        # Get configured hours
        start_hour = self.data.get('config', {}).get('start_hour', 19)
        end_hour = self.data.get('config', {}).get('end_hour', 7)
        
        # Nightwatch is active between start_hour and end_hour
        if start_hour < end_hour:
            # Normal case (e.g., 9 AM to 5 PM)
            is_nightwatch_time = start_hour <= current_hour < end_hour
        else:
            # Overnight case (e.g., 7 PM to 7 AM)
            is_nightwatch_time = current_hour >= start_hour or current_hour < end_hour
        
        if is_nightwatch_time and not self.data['nightwatch_active']:
            # Activate nightwatch
            self.data['nightwatch_active'] = True
            self.data['last_activation'] = now.isoformat()
            self.data['alerts_tonight'] = 0
            save_data(self.data)
            print(f"[Nightwatch] 🌙 ACTIVATED at {now.strftime('%H:%M')}")
        
        elif not is_nightwatch_time and self.data['nightwatch_active']:
            # Deactivate nightwatch
            self.data['nightwatch_active'] = False
            self.data['last_deactivation'] = now.isoformat()
            # Log session
            session = {
                'activation': self.data['last_activation'],
                'deactivation': now.isoformat(),
                'alerts': self.data['alerts_tonight']
            }
            self.data['sessions'].append(session)
            save_data(self.data)
            print(f"[Nightwatch] ☀️  DEACTIVATED at {now.strftime('%H:%M')}")

    @nightwatch_monitor.before_loop
    async def before_nightwatch_monitor(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def nightwatch_config(self, ctx):
        """View current nightwatch configuration"""
        config = self.data.get('config', {})
        
        embed = discord.Embed(
            title="⚙️ Nightwatch Configuration",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="Active Hours",
            value=f"{config.get('start_hour', 19):02d}:00 - {config.get('end_hour', 7):02d}:00",
            inline=True
        )
        embed.add_field(
            name="Enabled",
            value="✅ Yes" if config.get('enabled', True) else "❌ No",
            inline=True
        )
        embed.add_field(
            name="Alert Threshold",
            value=config.get('alert_threshold', 'Not set') if config.get('alert_threshold') else "Not set",
            inline=True
        )
        embed.add_field(
            name="Auto-Escalate",
            value="✅ Enabled" if config.get('auto_escalate', False) else "❌ Disabled",
            inline=True
        )
        embed.add_field(
            name="DM Alerts",
            value="✅ Enabled" if config.get('dm_alerts', False) else "❌ Disabled",
            inline=True
        )
        embed.add_field(
            name="Log All Activity",
            value="✅ Enabled" if config.get('log_all_activity', False) else "❌ Disabled",
            inline=True
        )
        
        embed.add_field(
            name="Monitored Users",
            value=str(len(self.data.get('monitored_users', []))),
            inline=True
        )
        embed.add_field(
            name="Blackout Channels",
            value=str(len(self.data.get('blackout_channels', []))),
            inline=True
        )
        
        embed.set_footer(text="Use /nightwatch_set_hours, /nightwatch_toggle, etc. to configure")
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_set_hours(self, ctx, start_hour: int, end_hour: int):
        """Set custom nightwatch active hours (0-23)"""
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            await ctx.send("❌ Hours must be between 0 and 23")
            return
        
        self.data['config']['start_hour'] = start_hour
        self.data['config']['end_hour'] = end_hour
        save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Nightwatch Hours Updated",
            description=f"Nightwatch now active from {start_hour:02d}:00 to {end_hour:02d}:00",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_toggle(self, ctx):
        """Enable/disable nightwatch system"""
        enabled = self.data['config'].get('enabled', True)
        self.data['config']['enabled'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['enabled'] else "❌ DISABLED"
        embed = discord.Embed(
            title="Nightwatch Status Updated",
            description=f"Nightwatch is now {status}",
            color=discord.Color.green() if self.data['config']['enabled'] else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_set_threshold(self, ctx, threshold: int = None):
        """Set alert threshold (alerts per session before escalation)"""
        if threshold is None:
            # Disable threshold
            self.data['config']['alert_threshold'] = None
            save_data(self.data)
            await ctx.send("✅ Alert threshold disabled")
        elif threshold > 0:
            self.data['config']['alert_threshold'] = threshold
            save_data(self.data)
            embed = discord.Embed(
                title="✅ Alert Threshold Updated",
                description=f"Will escalate if alerts exceed {threshold} per session",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Threshold must be a positive number")

    @commands.command()
    async def nightwatch_auto_escalate(self, ctx):
        """Toggle automatic escalation on high alert count"""
        enabled = self.data['config'].get('auto_escalate', False)
        self.data['config']['auto_escalate'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['auto_escalate'] else "❌ DISABLED"
        embed = discord.Embed(
            title="Auto-Escalation Updated",
            description=f"Auto-escalation is now {status}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_dm_alerts(self, ctx):
        """Toggle DM alerts to admin on detected activity"""
        enabled = self.data['config'].get('dm_alerts', False)
        self.data['config']['dm_alerts'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['dm_alerts'] else "❌ DISABLED"
        embed = discord.Embed(
            title="DM Alerts Updated",
            description=f"DM alerts are now {status}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_log_activity(self, ctx):
        """Toggle logging of all activity (not just alerts)"""
        enabled = self.data['config'].get('log_all_activity', False)
        self.data['config']['log_all_activity'] = not enabled
        save_data(self.data)
        
        status = "✅ ENABLED" if self.data['config']['log_all_activity'] else "❌ DISABLED"
        embed = discord.Embed(
            title="Activity Logging Updated",
            description=f"Full activity logging is now {status}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_status(self, ctx):
        """View current nightwatch status"""
        config = self.data.get('config', {})
        start_hour = config.get('start_hour', 19)
        end_hour = config.get('end_hour', 7)
        
        embed = discord.Embed(
            title="🌙 Nightwatch Status",
            color=discord.Color.dark_gray() if self.data['nightwatch_active'] else discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        status = "🟢 ACTIVE" if self.data['nightwatch_active'] else "🔴 INACTIVE"
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Active Hours", value=f"{start_hour:02d}:00 - {end_hour:02d}:00", inline=True)
        embed.add_field(name="Alerts Tonight", value=str(self.data['alerts_tonight']), inline=True)
        
        if self.data['last_activation']:
            embed.add_field(name="Last Activated", value=self.data['last_activation'], inline=False)
        
        if self.data['monitored_users']:
            embed.add_field(name="Monitored Users", value=str(len(self.data['monitored_users'])), inline=True)
        
        if self.data['blackout_channels']:
            embed.add_field(name="Blackout Channels", value=str(len(self.data['blackout_channels'])), inline=True)
        
        embed.set_footer(text="Nightwatch monitors activity during night hours")
        await ctx.send(embed=embed)

    @commands.command()
    async def watch_user(self, ctx, user: discord.Member):
        """Add user to nightwatch monitoring list"""
        if user.id not in self.data['monitored_users']:
            self.data['monitored_users'].append(user.id)
            save_data(self.data)
            embed = discord.Embed(
                title="✅ User Added to Nightwatch",
                description=f"{user.mention} will be monitored during night hours",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠️ {user.mention} is already being monitored.")

    @commands.command()
    async def unwatch_user(self, ctx, user: discord.Member):
        """Remove user from nightwatch monitoring list"""
        if user.id in self.data['monitored_users']:
            self.data['monitored_users'].remove(user.id)
            save_data(self.data)
            embed = discord.Embed(
                title="✅ User Removed from Nightwatch",
                description=f"{user.mention} monitoring disabled",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠️ {user.mention} is not being monitored.")

    @commands.command()
    async def nightwatch_blackout(self, ctx, channel: discord.TextChannel = None):
        """Add or list blackout channels (no alerts during nightwatch)"""
        if channel is None:
            # List blackout channels
            if self.data['blackout_channels']:
                channel_names = []
                for ch_id in self.data['blackout_channels']:
                    ch = self.bot.get_channel(ch_id)
                    if ch:
                        channel_names.append(f"#{ch.name}")
                embed = discord.Embed(
                    title="🚫 Blackout Channels",
                    description="\n".join(channel_names) if channel_names else "None",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="🚫 Blackout Channels",
                    description="No channels blacklisted",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)
        else:
            # Add blackout channel
            if channel.id not in self.data['blackout_channels']:
                self.data['blackout_channels'].append(channel.id)
                save_data(self.data)
                embed = discord.Embed(
                    title="✅ Blackout Channel Added",
                    description=f"{channel.mention} will have no alerts during nightwatch",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"⚠️ {channel.mention} is already blacklisted.")

    @commands.command()
    async def nightwatch_sessions(self, ctx, limit: int = 5):
        """View recent nightwatch sessions and statistics"""
        sessions = self.data['sessions'][-limit:]
        
        embed = discord.Embed(
            title=f"📊 Recent Nightwatch Sessions (Last {limit})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        if sessions:
            for idx, session in enumerate(sessions, 1):
                activation = datetime.fromisoformat(session['activation'])
                deactivation = datetime.fromisoformat(session['deactivation'])
                duration = (deactivation - activation).total_seconds() / 3600
                
                field_value = (
                    f"Duration: {duration:.1f}h\n"
                    f"Alerts: {session['alerts']}\n"
                    f"Ended: {deactivation.strftime('%m/%d %H:%M')}"
                )
                embed.add_field(name=f"Session {idx}", value=field_value, inline=True)
            
            # Calculate stats
            total_sessions = len(self.data['sessions'])
            total_alerts = sum(s['alerts'] for s in self.data['sessions'])
            avg_alerts = total_alerts / total_sessions if total_sessions > 0 else 0
            
            embed.add_field(
                name="All-Time Stats",
                value=f"Sessions: {total_sessions}\nTotal Alerts: {total_alerts}\nAvg/Session: {avg_alerts:.1f}",
                inline=False
            )
        else:
            embed.description = "No sessions recorded yet"
        
        embed.set_footer(text="Nightwatch tracks all night hours activity")
        await ctx.send(embed=embed)

    @commands.command()
    async def nightwatch_alert(self, ctx):
        """Log an alert during nightwatch"""
        if self.data['nightwatch_active']:
            self.data['alerts_tonight'] += 1
            save_data(self.data)
            embed = discord.Embed(
                title="🚨 Nightwatch Alert Logged",
                description=f"Total alerts tonight: {self.data['alerts_tonight']}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ Nightwatch is not currently active.")

    @commands.command()
    async def nightwatch_stats(self, ctx):
        """View nightwatch statistics and settings"""
        total_sessions = len(self.data['sessions'])
        total_alerts = sum(s['alerts'] for s in self.data['sessions'])
        
        embed = discord.Embed(
            title="📈 Nightwatch Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Sessions", value=str(total_sessions), inline=True)
        embed.add_field(name="Total Alerts", value=str(total_alerts), inline=True)
        embed.add_field(name="Alerts Tonight", value=str(self.data['alerts_tonight']), inline=True)
        
        embed.add_field(name="Monitored Users", value=str(len(self.data['monitored_users'])), inline=True)
        embed.add_field(name="Blackout Channels", value=str(len(self.data['blackout_channels'])), inline=True)
        
        if total_sessions > 0:
            avg_alerts = total_alerts / total_sessions
            embed.add_field(name="Avg Alerts/Session", value=f"{avg_alerts:.2f}", inline=True)
        
        embed.set_footer(text="Nightwatch: 7 PM - 7 AM")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NightwatchCog(bot))
