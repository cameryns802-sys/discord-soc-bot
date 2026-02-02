"""
Security Event Correlation Engine - Advanced event correlation for Sentinel
Correlate security events, detect attack patterns, and identify multi-stage attacks
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict

class SecurityEventCorrelation(commands.Cog):
    """Security event correlation and pattern detection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.events_file = 'data/security_events.json'
        self.correlations_file = 'data/event_correlations.json'
        self.patterns_file = 'data/attack_patterns.json'
        self.load_data()
        self.init_attack_patterns()
    
    def load_data(self):
        """Load event correlation data"""
        os.makedirs('data', exist_ok=True)
        
        for file in [self.events_file, self.correlations_file, self.patterns_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def init_attack_patterns(self):
        """Initialize attack pattern definitions"""
        with open(self.patterns_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            patterns = {
                'credential_stuffing': {
                    'name': 'Credential Stuffing Attack',
                    'events': ['failed_login', 'failed_login', 'failed_login', 'successful_login'],
                    'timeframe': 300,  # 5 minutes
                    'severity': 'high',
                    'description': 'Multiple failed logins followed by success'
                },
                'privilege_escalation': {
                    'name': 'Privilege Escalation',
                    'events': ['role_change', 'permission_grant', 'admin_action'],
                    'timeframe': 600,  # 10 minutes
                    'severity': 'critical',
                    'description': 'Role changes followed by privileged actions'
                },
                'data_exfiltration': {
                    'name': 'Data Exfiltration',
                    'events': ['bulk_download', 'bulk_download', 'external_share'],
                    'timeframe': 1800,  # 30 minutes
                    'severity': 'critical',
                    'description': 'Multiple downloads followed by external sharing'
                },
                'account_takeover': {
                    'name': 'Account Takeover',
                    'events': ['password_change', 'email_change', 'suspicious_login'],
                    'timeframe': 900,  # 15 minutes
                    'severity': 'critical',
                    'description': 'Rapid account changes indicating compromise'
                },
                'reconnaissance': {
                    'name': 'Reconnaissance Activity',
                    'events': ['channel_scan', 'member_scan', 'permission_scan'],
                    'timeframe': 600,  # 10 minutes
                    'severity': 'medium',
                    'description': 'Systematic information gathering'
                },
                'brute_force': {
                    'name': 'Brute Force Attack',
                    'events': ['failed_login', 'failed_login', 'failed_login', 'failed_login', 'failed_login'],
                    'timeframe': 180,  # 3 minutes
                    'severity': 'high',
                    'description': 'Rapid repeated failed login attempts'
                }
            }
            
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns, f, indent=2)
    
    def get_guild_events(self, guild_id):
        """Get events for guild"""
        with open(self.events_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_events(self, guild_id, events):
        """Save events"""
        with open(self.events_file, 'r') as f:
            data = json.load(f)
        # Keep last 1000 events
        data[str(guild_id)] = events[-1000:]
        with open(self.events_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_guild_correlations(self, guild_id):
        """Get correlations for guild"""
        with open(self.correlations_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_correlation(self, guild_id, correlation):
        """Save correlation"""
        with open(self.correlations_file, 'r') as f:
            data = json.load(f)
        
        correlations = data.get(str(guild_id), [])
        correlations.append(correlation)
        # Keep last 100 correlations
        data[str(guild_id)] = correlations[-100:]
        
        with open(self.correlations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_attack_patterns(self):
        """Get attack patterns"""
        with open(self.patterns_file, 'r') as f:
            return json.load(f)
    
    def log_event(self, guild_id, event_type, user_id, details=None):
        """Log security event"""
        events = self.get_guild_events(guild_id)
        
        event = {
            'id': hashlib.md5(f"{guild_id}{user_id}{event_type}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12],
            'type': event_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        events.append(event)
        self.save_events(guild_id, events)
        
        # Check for correlations after adding event
        self.check_correlations(guild_id, user_id)
        
        return event
    
    def check_correlations(self, guild_id, user_id):
        """Check for attack pattern correlations"""
        events = self.get_guild_events(guild_id)
        patterns = self.get_attack_patterns()
        
        # Filter events for this user
        user_events = [e for e in events if e['user_id'] == user_id]
        
        # Check each pattern
        for pattern_id, pattern in patterns.items():
            matched = self.match_pattern(user_events, pattern)
            if matched:
                correlation = {
                    'id': hashlib.md5(f"{guild_id}{user_id}{pattern_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12],
                    'pattern_id': pattern_id,
                    'pattern_name': pattern['name'],
                    'user_id': user_id,
                    'severity': pattern['severity'],
                    'events': matched['event_ids'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'active'
                }
                
                self.save_correlation(guild_id, correlation)
                return correlation
        
        return None
    
    def match_pattern(self, events, pattern):
        """Check if events match attack pattern"""
        required_events = pattern['events']
        timeframe = pattern['timeframe']
        
        # Sort events by timestamp (newest first)
        sorted_events = sorted(events, key=lambda e: e['timestamp'], reverse=True)
        
        # Check if we have enough events
        if len(sorted_events) < len(required_events):
            return None
        
        # Try to match pattern in recent events
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=timeframe)
        
        recent_events = [e for e in sorted_events if datetime.fromisoformat(e['timestamp']) > cutoff]
        
        if len(recent_events) < len(required_events):
            return None
        
        # Check if event types match pattern
        event_types = [e['type'] for e in recent_events[:len(required_events)]]
        
        # Allow partial matches (at least 80% match)
        matches = sum(1 for i, req_type in enumerate(required_events) if i < len(event_types) and event_types[i] == req_type)
        match_ratio = matches / len(required_events)
        
        if match_ratio >= 0.8:
            return {
                'event_ids': [e['id'] for e in recent_events[:len(required_events)]],
                'match_ratio': match_ratio
            }
        
        return None
    
    async def _correlatelog_logic(self, ctx, event_type: str, *, details: str = None):
        """Log security event for correlation"""
        valid_types = [
            'failed_login', 'successful_login', 'role_change', 'permission_grant',
            'admin_action', 'bulk_download', 'external_share', 'password_change',
            'email_change', 'suspicious_login', 'channel_scan', 'member_scan',
            'permission_scan', 'webhook_create', 'webhook_delete', 'invite_create'
        ]
        
        if event_type not in valid_types:
            await ctx.send(f"❌ Invalid event type. Use one of: {', '.join(valid_types[:8])}, ...")
            return
        
        event = self.log_event(ctx.guild.id, event_type, ctx.author.id, {'details': details})
        
        embed = discord.Embed(
            title="📝 Event Logged",
            description=f"Event logged for correlation analysis",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Event ID", value=f"`{event['id']}`", inline=True)
        embed.add_field(name="Type", value=event_type, inline=True)
        embed.add_field(name="User", value=ctx.author.mention, inline=True)
        
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        
        embed.set_footer(text="Sentinel Event Correlation | Events are analyzed for attack patterns")
        
        await ctx.send(embed=embed)
    
    async def _correlatecheck_logic(self, ctx):
        """Check for correlated attacks"""
        correlations = self.get_guild_correlations(ctx.guild.id)
        
        if not correlations:
            await ctx.send("✅ No correlated attack patterns detected.")
            return
        
        # Filter active correlations from last 24 hours
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)
        
        active = [c for c in correlations if c['status'] == 'active' and datetime.fromisoformat(c['timestamp']) > cutoff]
        
        if not active:
            await ctx.send("✅ No active correlated attack patterns in last 24 hours.")
            return
        
        embed = discord.Embed(
            title="⚠️ Correlated Attack Patterns Detected",
            description=f"{len(active)} active correlation(s) in last 24 hours",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        for correlation in active[:5]:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(correlation['severity'], '❓')
            
            try:
                user = await self.bot.fetch_user(correlation['user_id'])
                user_str = user.mention
            except:
                user_str = f"User ID: {correlation['user_id']}"
            
            ts = datetime.fromisoformat(correlation['timestamp'])
            relative = self._relative_time(ts)
            
            embed.add_field(
                name=f"{severity_emoji} {correlation['pattern_name']}",
                value=f"User: {user_str}\nEvents: {len(correlation['events'])}\nDetected: {relative}",
                inline=False
            )
        
        if len(active) > 5:
            embed.add_field(name="... and more", value=f"+{len(active) - 5} additional correlations", inline=False)
        
        embed.set_footer(text="Use !correlatedetail <correlation_id> for details")
        
        await ctx.send(embed=embed)
    
    async def _correlatepatterns_logic(self, ctx):
        """Show attack patterns"""
        patterns = self.get_attack_patterns()
        
        embed = discord.Embed(
            title="🎯 Attack Pattern Library",
            description=f"{len(patterns)} pattern(s) monitored",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for pattern_id, pattern in sorted(patterns.items()):
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(pattern['severity'], '❓')
            
            events_str = " → ".join(pattern['events'][:3])
            if len(pattern['events']) > 3:
                events_str += " → ..."
            
            embed.add_field(
                name=f"{severity_emoji} {pattern['name']}",
                value=f"{pattern['description']}\nPattern: {events_str}\nTimeframe: {pattern['timeframe']}s",
                inline=False
            )
        
        embed.set_footer(text="Sentinel Event Correlation | Patterns auto-detected in real-time")
        
        await ctx.send(embed=embed)
    
    async def _correlatestats_logic(self, ctx):
        """Show correlation statistics"""
        events = self.get_guild_events(ctx.guild.id)
        correlations = self.get_guild_correlations(ctx.guild.id)
        
        embed = discord.Embed(
            title="📊 Event Correlation Statistics",
            description=f"{len(events)} events | {len(correlations)} correlations",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Events by type
        by_type = defaultdict(int)
        for event in events:
            by_type[event['type']] += 1
        
        top_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]
        types_str = "\n".join([f"{t}: {c}" for t, c in top_types])
        embed.add_field(name="Top Event Types", value=types_str, inline=True)
        
        # Correlations by severity
        by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for correlation in correlations:
            by_severity[correlation['severity']] = by_severity.get(correlation['severity'], 0) + 1
        
        severity_str = f"🔴 Critical: {by_severity['critical']}\n🟠 High: {by_severity['high']}\n🟡 Medium: {by_severity['medium']}\n🟢 Low: {by_severity['low']}"
        embed.add_field(name="Correlations by Severity", value=severity_str, inline=True)
        
        # Recent activity
        now = datetime.utcnow()
        last_hour = sum(1 for e in events if datetime.fromisoformat(e['timestamp']) > now - timedelta(hours=1))
        last_day = sum(1 for e in events if datetime.fromisoformat(e['timestamp']) > now - timedelta(hours=24))
        
        embed.add_field(name="Recent Activity", value=f"Last hour: {last_hour}\nLast 24h: {last_day}", inline=True)
        
        embed.set_footer(text="Sentinel Event Correlation | Current snapshot")
        
        await ctx.send(embed=embed)
    
    def _relative_time(self, dt):
        """Get relative time string"""
        now = datetime.utcnow()
        delta = now - dt
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"
    
    @commands.command(name='correlatelog')
    async def correlatelog_prefix(self, ctx, event_type: str, *, details: str = None):
        """Log security event - Prefix command"""
        await self._correlatelog_logic(ctx, event_type, details=details)
    
    @commands.command(name='correlatecheck')
    async def correlatecheck_prefix(self, ctx):
        """Check correlations - Prefix command"""
        await self._correlatecheck_logic(ctx)
    
    @commands.command(name='correlatepatterns')
    async def correlatepatterns_prefix(self, ctx):
        """Show attack patterns - Prefix command"""
        await self._correlatepatterns_logic(ctx)
    
    @commands.command(name='correlatestats')
    async def correlatestats_prefix(self, ctx):
        """Show correlation stats - Prefix command"""
        await self._correlatestats_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityEventCorrelation(bot))
