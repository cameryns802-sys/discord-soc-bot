import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
import re

class LogNormalizationEngine(commands.Cog):
    """
    SIEM-Grade Log Normalization Engine
    
    Normalizes logs from diverse sources (Discord events, security alerts, audit logs)
    into a unified format for cross-source correlation and analysis.
    
    Features:
    - Multi-source event normalization
    - Field extraction and standardization
    - Taxonomy mapping (ECS/CEF-inspired)
    - Cross-server event correlation
    - Temporal reconstruction
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = 'data/log_normalization'
        os.makedirs(self.data_dir, exist_ok=True)
        self.normalized_logs = self.load_normalized_logs()
        
        # Standard field taxonomy (ECS-inspired)
        self.standard_fields = {
            'event.timestamp': 'ISO 8601 timestamp',
            'event.type': 'Type of event (security, moderation, audit, threat)',
            'event.category': 'Category (authentication, network, process, user)',
            'event.action': 'Action taken (ban, kick, alert, block)',
            'event.severity': 'Severity level (critical, high, medium, low)',
            'event.source': 'Source system (discord, bot, external)',
            'user.id': 'User ID',
            'user.name': 'Username',
            'guild.id': 'Guild ID',
            'guild.name': 'Guild name',
            'channel.id': 'Channel ID',
            'threat.indicator': 'IOC or threat indicator',
            'threat.type': 'Threat classification',
            'message.content': 'Message or event description',
            'network.remote_ip': 'Remote IP address',
            'file.hash': 'File hash (if applicable)'
        }
    
    def load_normalized_logs(self) -> Dict:
        """Load normalized logs from JSON storage"""
        try:
            with open(f'{self.data_dir}/normalized_logs.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_normalized_logs(self):
        """Save normalized logs to JSON storage"""
        with open(f'{self.data_dir}/normalized_logs.json', 'w') as f:
            json.dump(self.normalized_logs, f, indent=2)
    
    def normalize_discord_event(self, event_type: str, event_data: Dict) -> Dict:
        """
        Normalize a Discord event into standard taxonomy
        
        Args:
            event_type: Type of Discord event (MESSAGE, MEMBER_JOIN, BAN, etc.)
            event_data: Raw event data
        
        Returns:
            Normalized event dictionary
        """
        normalized = {
            'event.timestamp': datetime.now(timezone.utc).isoformat(),
            'event.type': 'discord_event',
            'event.category': self._categorize_event(event_type),
            'event.action': event_type.lower(),
            'event.severity': self._calculate_severity(event_type, event_data),
            'event.source': 'discord',
            'raw_data': event_data
        }
        
        # Extract standard fields from event_data
        if 'user_id' in event_data:
            normalized['user.id'] = event_data['user_id']
        if 'user_name' in event_data:
            normalized['user.name'] = event_data['user_name']
        if 'guild_id' in event_data:
            normalized['guild.id'] = event_data['guild_id']
        if 'guild_name' in event_data:
            normalized['guild.name'] = event_data['guild_name']
        if 'channel_id' in event_data:
            normalized['channel.id'] = event_data['channel_id']
        if 'content' in event_data:
            normalized['message.content'] = event_data['content']
        
        return normalized
    
    def _categorize_event(self, event_type: str) -> str:
        """Categorize event into standard taxonomy"""
        if event_type in ['MEMBER_JOIN', 'MEMBER_LEAVE', 'MEMBER_UPDATE']:
            return 'user'
        elif event_type in ['MESSAGE_CREATE', 'MESSAGE_DELETE', 'MESSAGE_UPDATE']:
            return 'communication'
        elif event_type in ['BAN_ADD', 'BAN_REMOVE', 'KICK']:
            return 'moderation'
        elif event_type in ['ROLE_CREATE', 'ROLE_DELETE', 'ROLE_UPDATE', 'PERMISSION_UPDATE']:
            return 'access_control'
        elif event_type in ['CHANNEL_CREATE', 'CHANNEL_DELETE', 'GUILD_UPDATE']:
            return 'configuration'
        else:
            return 'other'
    
    def _calculate_severity(self, event_type: str, event_data: Dict) -> str:
        """Calculate severity level based on event type and context"""
        high_severity = ['BAN_ADD', 'GUILD_DELETE', 'ROLE_DELETE', 'PERMISSION_UPDATE']
        medium_severity = ['KICK', 'MESSAGE_DELETE', 'MEMBER_UPDATE']
        
        if event_type in high_severity:
            return 'high'
        elif event_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def normalize_security_alert(self, alert_data: Dict) -> Dict:
        """Normalize a security alert into standard taxonomy"""
        normalized = {
            'event.timestamp': alert_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'event.type': 'security_alert',
            'event.category': 'threat',
            'event.action': alert_data.get('action', 'alert'),
            'event.severity': alert_data.get('severity', 'medium'),
            'event.source': alert_data.get('source', 'sentinel_bot'),
            'threat.indicator': alert_data.get('indicator', ''),
            'threat.type': alert_data.get('threat_type', 'unknown'),
            'raw_data': alert_data
        }
        
        # Extract user/guild context
        if 'user_id' in alert_data:
            normalized['user.id'] = alert_data['user_id']
        if 'guild_id' in alert_data:
            normalized['guild.id'] = alert_data['guild_id']
        
        return normalized
    
    def store_normalized_event(self, guild_id: str, normalized_event: Dict):
        """Store a normalized event for future querying"""
        if str(guild_id) not in self.normalized_logs:
            self.normalized_logs[str(guild_id)] = []
        
        self.normalized_logs[str(guild_id)].append(normalized_event)
        self.save_normalized_logs()
    
    def query_events(self, guild_id: str, filters: Dict) -> List[Dict]:
        """
        Query normalized events with filters
        
        Args:
            guild_id: Guild ID to query
            filters: Dict of field filters (e.g., {'event.type': 'security_alert', 'event.severity': 'high'})
        
        Returns:
            List of matching events
        """
        if str(guild_id) not in self.normalized_logs:
            return []
        
        events = self.normalized_logs[str(guild_id)]
        
        # Apply filters
        for field, value in filters.items():
            events = [e for e in events if e.get(field) == value]
        
        return events
    
    @commands.command(name='normalize_event')
    @commands.has_permissions(administrator=True)
    async def normalize_event_cmd(self, ctx, event_type: str, *, event_data: str):
        """
        Manually normalize an event
        
        Usage: !normalize_event MESSAGE_CREATE user_id=123456 content="Test message"
        """
        try:
            # Parse event_data (key=value pairs)
            data = {}
            for pair in event_data.split():
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    data[key] = value.strip('"')
            
            normalized = self.normalize_discord_event(event_type.upper(), data)
            self.store_normalized_event(ctx.guild.id, normalized)
            
            embed = discord.Embed(
                title="✅ Event Normalized",
                description=f"Event `{event_type}` has been normalized and stored.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Event Type", value=normalized['event.type'], inline=True)
            embed.add_field(name="Category", value=normalized['event.category'], inline=True)
            embed.add_field(name="Severity", value=normalized['event.severity'].upper(), inline=True)
            embed.add_field(name="Timestamp", value=normalized['event.timestamp'], inline=False)
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Error normalizing event: {e}")
    
    @commands.command(name='query_logs')
    @commands.has_permissions(administrator=True)
    async def query_logs_cmd(self, ctx, *, query: str):
        """
        Query normalized logs with filters
        
        Usage: !query_logs event.type=security_alert event.severity=high
        """
        try:
            # Parse query (key=value pairs)
            filters = {}
            for pair in query.split():
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    filters[key] = value.strip('"')
            
            results = self.query_events(ctx.guild.id, filters)
            
            embed = discord.Embed(
                title=f"📊 Log Query Results",
                description=f"Found **{len(results)}** matching events",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Show first 10 results
            for i, event in enumerate(results[:10], 1):
                embed.add_field(
                    name=f"Event {i}",
                    value=f"**Type**: {event.get('event.type', 'N/A')}\n"
                          f"**Severity**: {event.get('event.severity', 'N/A').upper()}\n"
                          f"**Timestamp**: {event.get('event.timestamp', 'N/A')[:19]}",
                    inline=False
                )
            
            if len(results) > 10:
                embed.set_footer(text=f"Showing 10 of {len(results)} results")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Error querying logs: {e}")
    
    @commands.command(name='log_taxonomy')
    @commands.has_permissions(administrator=True)
    async def log_taxonomy_cmd(self, ctx):
        """Show the standard log field taxonomy"""
        embed = discord.Embed(
            title="📖 Log Normalization Taxonomy",
            description="Standard field schema for normalized events (ECS-inspired)",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Group fields by prefix
        groups = {}
        for field, desc in self.standard_fields.items():
            prefix = field.split('.')[0]
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(f"`{field}`: {desc}")
        
        for prefix, fields in groups.items():
            embed.add_field(
                name=f"📁 {prefix.capitalize()} Fields",
                value='\n'.join(fields[:5]),  # Show first 5
                inline=False
            )
        
        embed.set_footer(text="Use !normalize_event to normalize custom events")
        await ctx.send(embed=embed)
    
    @commands.command(name='log_stats')
    @commands.has_permissions(administrator=True)
    async def log_stats_cmd(self, ctx):
        """Show normalized log statistics for this guild"""
        if str(ctx.guild.id) not in self.normalized_logs:
            await ctx.send("📊 No normalized logs found for this guild.")
            return
        
        events = self.normalized_logs[str(ctx.guild.id)]
        
        # Calculate stats
        total = len(events)
        by_type = {}
        by_severity = {}
        
        for event in events:
            event_type = event.get('event.type', 'unknown')
            severity = event.get('event.severity', 'unknown')
            
            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        embed = discord.Embed(
            title="📊 Normalized Log Statistics",
            description=f"**Total Events**: {total}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # By type
        type_str = '\n'.join([f"**{t}**: {c}" for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]])
        embed.add_field(name="📂 Top Event Types", value=type_str or "None", inline=True)
        
        # By severity
        sev_str = '\n'.join([f"**{s.upper()}**: {c}" for s, c in sorted(by_severity.items(), key=lambda x: x[1], reverse=True)])
        embed.add_field(name="⚠️ By Severity", value=sev_str or "None", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LogNormalizationEngine(bot))
