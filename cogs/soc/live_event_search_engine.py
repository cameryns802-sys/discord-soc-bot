"""
Live Event Search Engine - Full-text search across all security events for Sentinel
Enables rapid incident investigation and threat hunting with comprehensive search
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import re
from cogs.core.pst_timezone import get_now_pst

class LiveEventSearchEngine(commands.Cog):
    """Full-text search across security events and incident data"""
    
    def __init__(self, bot):
        self.bot = bot
        self.threat_file = 'data/threat_responses.json'
        self.incident_file = 'data/incidents.json'
        self.alert_file = 'data/alerts.json'
        self.checklist_file = 'data/security_checklist.json'
    
    def search_threats(self, guild_id, query):
        """Search threat data"""
        if not os.path.exists(self.threat_file):
            return []
        
        with open(self.threat_file, 'r') as f:
            all_threats = json.load(f)
        
        guild_threats = all_threats.get(str(guild_id), [])
        query_lower = query.lower()
        
        results = []
        for threat in guild_threats:
            searchable = f"{threat.get('threat_type', '')} {threat.get('description', '')} {threat.get('details', '')}".lower()
            if query_lower in searchable:
                results.append(threat)
        
        return results
    
    def search_incidents(self, guild_id, query):
        """Search incident data"""
        if not os.path.exists(self.incident_file):
            return []
        
        with open(self.incident_file, 'r') as f:
            all_incidents = json.load(f)
        
        guild_incidents = all_incidents.get(str(guild_id), {})
        query_lower = query.lower()
        
        results = []
        for incident_id, incident in guild_incidents.items():
            searchable = f"{incident.get('title', '')} {incident.get('description', '')}".lower()
            for note in incident.get('notes', []):
                searchable += f" {note.get('text', '')}".lower()
            
            if query_lower in searchable:
                results.append(incident)
        
        return results
    
    def search_alerts(self, guild_id, query):
        """Search alert data"""
        if not os.path.exists(self.alert_file):
            return []
        
        with open(self.alert_file, 'r') as f:
            all_alerts = json.load(f)
        
        guild_alerts = all_alerts.get(str(guild_id), {})
        query_lower = query.lower()
        
        results = []
        for alert_id, alert in guild_alerts.items():
            searchable = f"{alert.get('title', '')} {alert.get('description', '')} {alert.get('source', '')}".lower()
            
            if query_lower in searchable:
                results.append(alert)
        
        return results
    
    def search_all(self, guild_id, query):
        """Search all event sources"""
        threats = self.search_threats(guild_id, query)
        incidents = self.search_incidents(guild_id, query)
        alerts = self.search_alerts(guild_id, query)
        
        return {
            'threats': threats,
            'incidents': incidents,
            'alerts': alerts,
            'total': len(threats) + len(incidents) + len(alerts)
        }
    
    def search_by_date(self, guild_id, days_back=7):
        """Search events from past N days"""
        cutoff = get_now_pst() - timedelta(days=days_back)
        
        results = {
            'threats': [],
            'incidents': [],
            'alerts': []
        }
        
        # Recent threats
        if os.path.exists(self.threat_file):
            with open(self.threat_file, 'r') as f:
                all_threats = json.load(f)
            guild_threats = all_threats.get(str(guild_id), [])
            for threat in guild_threats:
                try:
                    t_time = datetime.fromisoformat(threat.get('timestamp', ''))
                    if t_time > cutoff:
                        results['threats'].append(threat)
                except:
                    pass
        
        # Recent incidents
        if os.path.exists(self.incident_file):
            with open(self.incident_file, 'r') as f:
                all_incidents = json.load(f)
            guild_incidents = all_incidents.get(str(guild_id), {})
            for incident in guild_incidents.values():
                try:
                    i_time = datetime.fromisoformat(incident.get('created_at', ''))
                    if i_time > cutoff:
                        results['incidents'].append(incident)
                except:
                    pass
        
        # Recent alerts
        if os.path.exists(self.alert_file):
            with open(self.alert_file, 'r') as f:
                all_alerts = json.load(f)
            guild_alerts = all_alerts.get(str(guild_id), {})
            for alert in guild_alerts.values():
                try:
                    a_time = datetime.fromisoformat(alert.get('created_at', ''))
                    if a_time > cutoff:
                        results['alerts'].append(alert)
                except:
                    pass
        
        return results
    
    async def _search_logic(self, ctx, *, query: str):
        """Full-text search across all events"""
        results = self.search_all(ctx.guild.id, query)
        
        if results['total'] == 0:
            await ctx.send(f"❌ No results found for: `{query}`")
            return
        
        embed = discord.Embed(
            title=f"🔍 Search Results",
            description=f"Query: `{query}` | Found: {results['total']} result(s)",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        # Threats
        if results['threats']:
            threat_summary = f"{len(results['threats'])} threat(s) found\n"
            for threat in results['threats'][:3]:
                threat_summary += f"• {threat.get('threat_type', 'Unknown')} ({threat.get('severity', 'low')})\n"
            if len(results['threats']) > 3:
                threat_summary += f"... and {len(results['threats']) - 3} more"
            embed.add_field(name="🎯 Threats", value=threat_summary, inline=False)
        
        # Incidents
        if results['incidents']:
            incident_summary = f"{len(results['incidents'])} incident(s) found\n"
            for incident in results['incidents'][:3]:
                incident_summary += f"• {incident.get('title', 'Unknown')} (ID: {incident.get('id', 'N/A')})\n"
            if len(results['incidents']) > 3:
                incident_summary += f"... and {len(results['incidents']) - 3} more"
            embed.add_field(name="📋 Incidents", value=incident_summary, inline=False)
        
        # Alerts
        if results['alerts']:
            alert_summary = f"{len(results['alerts'])} alert(s) found\n"
            for alert in results['alerts'][:3]:
                alert_summary += f"• {alert.get('title', 'Unknown')} ({alert.get('severity', 'low')})\n"
            if len(results['alerts']) > 3:
                alert_summary += f"... and {len(results['alerts']) - 3} more"
            embed.add_field(name="🚨 Alerts", value=alert_summary, inline=False)
        
        embed.set_footer(text="Sentinel Event Search Engine")
        
        await ctx.send(embed=embed)
    
    async def _recentevents_logic(self, ctx, days: int = 7):
        """Show recent events from past N days"""
        if days < 1 or days > 90:
            await ctx.send("❌ Days must be between 1-90.")
            return
        
        results = self.search_by_date(ctx.guild.id, days)
        total = len(results['threats']) + len(results['incidents']) + len(results['alerts'])
        
        if total == 0:
            await ctx.send(f"✅ No events in the past {days} day(s).")
            return
        
        embed = discord.Embed(
            title=f"📅 Recent Events (Past {days} Days)",
            description=f"Total: {total} event(s)",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        if results['threats']:
            embed.add_field(name=f"🎯 Threats ({len(results['threats'])})", value=f"Recent threat activity detected", inline=True)
        
        if results['incidents']:
            embed.add_field(name=f"📋 Incidents ({len(results['incidents'])})", value=f"Recent security incidents", inline=True)
        
        if results['alerts']:
            embed.add_field(name=f"🚨 Alerts ({len(results['alerts'])})", value=f"Recent alert activity", inline=True)
        
        # Timeline
        timeline_str = ""
        all_events = []
        
        for threat in results['threats']:
            try:
                t_time = datetime.fromisoformat(threat.get('timestamp', ''))
                all_events.append((t_time, f"🎯 {threat.get('threat_type', 'Threat')}", threat.get('severity')))
            except:
                pass
        
        for incident in results['incidents']:
            try:
                i_time = datetime.fromisoformat(incident.get('created_at', ''))
                all_events.append((i_time, f"📋 {incident.get('title', 'Incident')}", incident.get('severity')))
            except:
                pass
        
        for alert in results['alerts']:
            try:
                a_time = datetime.fromisoformat(alert.get('created_at', ''))
                all_events.append((a_time, f"🚨 {alert.get('title', 'Alert')}", alert.get('severity')))
            except:
                pass
        
        # Sort by time (newest first)
        all_events.sort(key=lambda x: x[0], reverse=True)
        
        for event_time, event_name, severity in all_events[:8]:
            timeline_str += f"\n<t:{int(event_time.timestamp())}:R> - {event_name}"
        
        if timeline_str:
            embed.add_field(name="📊 Timeline (Last 8 Events)", value=timeline_str, inline=False)
        
        embed.set_footer(text="Sentinel Event Search Engine")
        
        await ctx.send(embed=embed)
    
    async def _searchstats_logic(self, ctx):
        """Show search statistics and event summary"""
        results = self.search_by_date(ctx.guild.id, 30)  # Last 30 days
        
        embed = discord.Embed(
            title="📊 Security Event Statistics",
            description="Summary of all recorded events (30-day window)",
            color=discord.Color.greyple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🎯 Threats", value=f"`{len(results['threats'])}`", inline=True)
        embed.add_field(name="📋 Incidents", value=f"`{len(results['incidents'])}`", inline=True)
        embed.add_field(name="🚨 Alerts", value=f"`{len(results['alerts'])}`", inline=True)
        embed.add_field(name="Total Events", value=f"`{len(results['threats']) + len(results['incidents']) + len(results['alerts'])}`", inline=True)
        
        embed.add_field(name="ℹ️ Info", value="Use `/search <query>` to find specific events\nUse `/recentevents <days>` for timeline view", inline=False)
        
        embed.set_footer(text="Sentinel Event Search Engine")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='search')
    async def search_prefix(self, ctx, *, query: str):
        """Full-text search across all events - Prefix command"""
        await self._search_logic(ctx, query=query)
    
    @commands.command(name='recentevents')
    async def recentevents_prefix(self, ctx, days: int = 7):
        """Show recent events timeline - Prefix command"""
        await self._recentevents_logic(ctx, days)
    
    @commands.command(name='searchstats')
    async def searchstats_prefix(self, ctx):
        """Show event statistics - Prefix command"""
        await self._searchstats_logic(ctx)

async def setup(bot):
    await bot.add_cog(LiveEventSearchEngine(bot))
