"""
Auto Policy Drift Detector - Detect unauthorized permission and role changes
Monitors guild configuration for policy violations and security baseline drift
Alerts when permissions deviate from baseline or established patterns
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class PolicyDriftDetector(commands.Cog):
    """Detect and alert on policy violations and configuration drift"""
    
    def __init__(self, bot):
        self.bot = bot
        self.baseline_file = 'data/policy_baseline.json'
        self.drift_file = 'data/policy_drift_alerts.json'
        self.baselines = {}  # guild_id -> baseline config
        self.drift_alerts = []
        self.load_baselines()
        self.monitor_drift.start()
    
    def load_baselines(self):
        """Load policy baselines"""
        if os.path.exists(self.baseline_file):
            try:
                with open(self.baseline_file, 'r') as f:
                    self.baselines = json.load(f)
            except:
                self.baselines = {}
        
        if os.path.exists(self.drift_file):
            try:
                with open(self.drift_file, 'r') as f:
                    self.drift_alerts = json.load(f)
            except:
                self.drift_alerts = []
    
    def save_baselines(self):
        """Save policy baselines"""
        os.makedirs(os.path.dirname(self.baseline_file), exist_ok=True)
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)
    
    def save_alerts(self):
        """Save drift alerts"""
        os.makedirs(os.path.dirname(self.drift_file), exist_ok=True)
        with open(self.drift_file, 'w') as f:
            json.dump(self.drift_alerts[-1000:], f, indent=2)  # Keep last 1000
    
    async def capture_baseline(self, guild: discord.Guild):
        """Capture current guild configuration as baseline"""
        baseline = {
            'captured_at': get_now_pst().isoformat(),
            'roles': {},
            'permissions': {},
            'channels': {},
            'verification_level': str(guild.verification_level),
            'explicit_content_filter': str(guild.explicit_content_filter)
        }
        
        # Capture roles
        for role in guild.roles:
            baseline['roles'][str(role.id)] = {
                'name': role.name,
                'permissions': role.permissions.value,
                'position': role.position
            }
        
        # Capture channel perms
        for channel in guild.channels:
            baseline['channels'][str(channel.id)] = {
                'name': channel.name,
                'type': str(channel.type)
            }
        
        self.baselines[str(guild.id)] = baseline
        self.save_baselines()
    
    @tasks.loop(hours=24)
    async def monitor_drift(self):
        """Monitor for policy drift across all guilds"""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            
            # Initialize baseline if missing
            if guild_id not in self.baselines:
                await self.capture_baseline(guild)
                continue
            
            baseline = self.baselines[guild_id]
            drift_detected = []
            
            # Check role changes
            for role in guild.roles:
                role_id = str(role.id)
                
                if role_id in baseline['roles']:
                    baseline_role = baseline['roles'][role_id]
                    
                    # Check for permission changes
                    if baseline_role['permissions'] != role.permissions.value:
                        drift = {
                            'type': 'role_permission_change',
                            'role_id': role_id,
                            'role_name': role.name,
                            'change': 'permissions modified',
                            'severity': 'high'
                        }
                        drift_detected.append(drift)
                    
                    # Check for position changes
                    if baseline_role['position'] != role.position:
                        drift = {
                            'type': 'role_position_change',
                            'role_id': role_id,
                            'role_name': role.name,
                            'change': f"position: {baseline_role['position']} → {role.position}",
                            'severity': 'medium'
                        }
                        drift_detected.append(drift)
            
            # Check for new roles
            for role in guild.roles:
                role_id = str(role.id)
                if role_id not in baseline['roles']:
                    # Check if role has dangerous permissions
                    if role.permissions.administrator or role.permissions.manage_guild:
                        drift = {
                            'type': 'new_privileged_role',
                            'role_id': role_id,
                            'role_name': role.name,
                            'change': 'new privileged role created',
                            'severity': 'critical'
                        }
                        drift_detected.append(drift)
            
            # Check verification level changes
            if str(guild.verification_level) != baseline['verification_level']:
                drift = {
                    'type': 'verification_level_change',
                    'change': f"{baseline['verification_level']} → {str(guild.verification_level)}",
                    'severity': 'high'
                }
                drift_detected.append(drift)
            
            # Emit alerts for detected drift
            for drift in drift_detected:
                await self.emit_drift_alert(guild, drift)
    
    async def emit_drift_alert(self, guild: discord.Guild, drift: Dict):
        """Emit policy violation signal"""
        alert = {
            'timestamp': get_now_pst().isoformat(),
            'guild_id': guild.id,
            'guild_name': guild.name,
            'drift': drift
        }
        self.drift_alerts.append(alert)
        self.save_alerts()
        
        # Emit signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.POLICY_VIOLATION,
            severity=drift.get('severity', 'medium').upper(),
            source='policy_drift_detector',
            data={
                'drift_type': drift['type'],
                'change_description': drift.get('change', 'unknown'),
                'guild_id': guild.id,
                'confidence': 0.99
            }
        ))
        
        print(f"[Policy Drift] ⚠️ {guild.name}: {drift['type']} detected")
    
    @tasks.loop()
    async def monitor_drift(self):
        """Monitor for policy drift (wait 1 hour before first check)"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                
                if guild_id not in self.baselines:
                    await self.capture_baseline(guild)
            
            # Check every 6 hours
            await self.wait_for_timeout_seconds(21600)
    
    async def wait_for_timeout_seconds(self, seconds: float):
        """Wait for timeout in seconds"""
        import asyncio
        await asyncio.sleep(seconds)
    
    @commands.command(name='capturebaseline')
    @commands.has_permissions(manage_guild=True)
    async def capture_baseline_cmd(self, ctx):
        """Capture current configuration as baseline"""
        await self.capture_baseline(ctx.guild)
        
        embed = discord.Embed(
            title="✅ Baseline Captured",
            description="Current configuration saved as baseline",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Roles Recorded", value=len(ctx.guild.roles), inline=True)
        embed.add_field(name="Channels Recorded", value=len(ctx.guild.channels), inline=True)
        embed.add_field(name="Status", value="✅ Ready for drift detection", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='driftalerts')
    @commands.has_permissions(administrator=True)
    async def drift_alerts_cmd(self, ctx, days: int = 7):
        """View policy drift alerts"""
        cutoff = (get_now_pst() - timedelta(days=days)).isoformat()
        
        recent = [a for a in self.drift_alerts if a['timestamp'] > cutoff and a['guild_id'] == ctx.guild.id]
        
        if not recent:
            await ctx.send("✅ No policy drift alerts in the past 7 days")
            return
        
        embed = discord.Embed(
            title="📋 Policy Drift Alerts",
            description=f"Last {days} days",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        # Group by type
        by_type = {}
        for alert in recent:
            dtype = alert['drift'].get('type', 'unknown')
            by_type[dtype] = by_type.get(dtype, 0) + 1
        
        for dtype, count in by_type.items():
            severity = 'critical' if count > 5 else 'high' if count > 2 else 'medium'
            emoji = '🔴' if severity == 'critical' else '🟠' if severity == 'high' else '🟡'
            embed.add_field(name=f"{emoji} {dtype}", value=f"{count} alert(s)", inline=True)
        
        embed.add_field(name="Action", value="Review changes and restore baseline if needed", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='driftdetails')
    @commands.has_permissions(administrator=True)
    async def drift_details_cmd(self, ctx, limit: int = 10):
        """View detailed drift alerts"""
        guild_alerts = [a for a in self.drift_alerts if a['guild_id'] == ctx.guild.id]
        
        recent = guild_alerts[-limit:]
        
        embed = discord.Embed(
            title="📊 Drift Alert Details",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for alert in recent[-5:]:
            timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d %H:%M')
            drift = alert['drift']
            
            field_value = f"**Type:** {drift.get('type', 'unknown')}\n"
            field_value += f"**Change:** {drift.get('change', 'N/A')}\n"
            field_value += f"**Severity:** {drift.get('severity', 'medium').upper()}"
            
            embed.add_field(name=timestamp, value=field_value, inline=False)
        
        embed.set_footer(text=f"Total: {len(guild_alerts)} drift(s) detected")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PolicyDriftDetector(bot))
