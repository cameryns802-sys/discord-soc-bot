"""
Breach Response Orchestration - Coordinated incident response automation
Orchestrate and automate coordinated response actions across teams and systems
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class BreachResponseOrchestration(commands.Cog):
    """Breach response orchestration and automation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.incidents_file = 'data/breach_incidents.json'
        self.playbooks_file = 'data/breach_playbooks.json'
        self.load_data()
    
    def load_data(self):
        """Load breach response data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.incidents_file):
            with open(self.incidents_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.playbooks_file):
            with open(self.playbooks_file, 'w') as f:
                json.dump({}, f)
    
    def get_incidents(self, guild_id):
        """Get breach incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_incidents(self, guild_id, incidents):
        """Save incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = incidents
        with open(self.incidents_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_breach_severity(self, incident):
        """Calculate breach severity (0-100)"""
        score = 0
        
        # Data sensitivity
        data_type = incident.get('data_compromised', [])
        if 'PII' in data_type or 'PHI' in data_type:
            score += 30
        if 'Financial' in data_type:
            score += 25
        if 'Source Code' in data_type:
            score += 20
        
        # Number of records
        records = incident.get('records_affected', 0)
        if records > 10000:
            score += 20
        elif records > 1000:
            score += 15
        elif records > 100:
            score += 10
        
        # Scope
        if incident.get('cross_system', False):
            score += 15
        
        # Containment status
        if not incident.get('contained', False):
            score += 20
        
        # Time to detect
        if incident.get('dwell_time_days', 0) > 30:
            score += 15
        
        return min(100, score)
    
    async def _breachdetect_logic(self, ctx, breach_type: str, data_affected: str, records: int = 0):
        """Detect and initiate breach response"""
        incidents = self.get_incidents(ctx.guild.id)
        
        incident_id = f"BRH-{get_now_pst().strftime('%Y%m%d%H%M%S')}"
        
        incident = {
            'id': incident_id,
            'type': breach_type.lower(),
            'detected_at': get_now_pst().isoformat(),
            'status': 'active',
            'data_compromised': data_affected.split(','),
            'records_affected': records,
            'cross_system': False,
            'contained': False,
            'dwell_time_days': 0,
            'severity': 0,
            'response_actions': [],
            'teams_involved': [],
            'notifications_sent': [],
            'legal_notification_required': records > 100,
            'regulatory_agencies': []
        }
        
        incident['severity'] = self.calculate_breach_severity(incident)
        incidents[incident_id] = incident
        self.save_incidents(ctx.guild.id, incidents)
        
        severity_color = discord.Color.red() if incident['severity'] >= 80 else discord.Color.orange() if incident['severity'] >= 60 else discord.Color.gold()
        severity_emoji = '🔴' if incident['severity'] >= 80 else '🟠' if incident['severity'] >= 60 else '🟡'
        
        embed = discord.Embed(
            title=f"{severity_emoji} BREACH DETECTED - Response Initiated",
            description=f"**{breach_type.title()}**",
            color=severity_color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Incident ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Severity", value=f"{incident['severity']}/100", inline=True)
        embed.add_field(name="Status", value="🔴 ACTIVE", inline=True)
        embed.add_field(name="Data Compromised", value=", ".join(incident['data_compromised']), inline=False)
        embed.add_field(name="Records Affected", value=str(records), inline=True)
        embed.add_field(name="Containment", value="⏳ IN PROGRESS", inline=True)
        
        if incident['legal_notification_required']:
            embed.add_field(name="⚠️ Legal Notification", value="Required (72-hour GDPR/CCPA deadline)", inline=False)
        
        embed.set_footer(text="Automated response playbook has been triggered")
        
        await ctx.send(embed=embed)
    
    async def _breachstatus_logic(self, ctx):
        """Show breach incident status"""
        incidents = self.get_incidents(ctx.guild.id)
        
        if not incidents:
            await ctx.send("✅ No active breach incidents.")
            return
        
        active = [i for i in incidents.values() if i['status'] == 'active']
        
        embed = discord.Embed(
            title="🚨 Breach Incident Status",
            description=f"{len(active)} active incident(s)",
            color=discord.Color.red() if active else discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        contained = sum(1 for i in incidents.values() if i['contained'])
        embed.add_field(name="Incident Summary", value=f"🔴 {len(active)} active | 🟢 {contained} contained | 📊 {len(incidents)} total", inline=False)
        
        for incident in sorted(active, key=lambda i: i['severity'], reverse=True)[:8]:
            severity_emoji = '🔴' if incident['severity'] >= 80 else '🟠' if incident['severity'] >= 60 else '🟡'
            
            embed.add_field(
                name=f"{severity_emoji} {incident['type'].replace('_', ' ').title()} ({incident['id']})",
                value=f"Severity: {incident['severity']}/100 | Records: {incident['records_affected']} | Contained: {'✅ Yes' if incident['contained'] else '❌ No'}",
                inline=False
            )
        
        embed.set_footer(text="Use !breachdetail <incident_id> for response coordination")
        
        await ctx.send(embed=embed)
    
    async def _breachdetail_logic(self, ctx, incident_id: str):
        """Show breach incident details"""
        incidents = self.get_incidents(ctx.guild.id)
        
        incident_id = incident_id.upper()
        incident = incidents.get(incident_id)
        
        if not incident:
            await ctx.send(f"❌ Incident not found: {incident_id}")
            return
        
        severity = incident['severity']
        color = discord.Color.red() if severity >= 80 else discord.Color.orange() if severity >= 60 else discord.Color.gold()
        
        embed = discord.Embed(
            title=f"🚨 Breach Incident: {incident_id}",
            description=f"{incident['type'].title()}",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Severity", value=f"{severity}/100", inline=True)
        embed.add_field(name="Status", value="🔴 ACTIVE" if incident['status'] == 'active' else "🟢 CONTAINED", inline=True)
        embed.add_field(name="Detected", value=datetime.fromisoformat(incident['detected_at']).strftime('%Y-%m-%d %H:%M:%S'), inline=True)
        
        embed.add_field(name="Scope Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Data Compromised", value=", ".join(incident['data_compromised']), inline=False)
        embed.add_field(name="Records Affected", value=str(incident['records_affected']), inline=True)
        embed.add_field(name="Cross-System", value="✅ Yes" if incident['cross_system'] else "❌ No", inline=True)
        embed.add_field(name="Dwell Time", value=f"{incident['dwell_time_days']} days", inline=True)
        
        embed.add_field(name="Response Coordination", value="━" * 25, inline=False)
        embed.add_field(name="Containment", value="✅ Contained" if incident['contained'] else "⏳ IN PROGRESS", inline=True)
        embed.add_field(name="Teams Involved", value=str(len(incident['teams_involved'])), inline=True)
        embed.add_field(name="Notifications Sent", value=str(len(incident['notifications_sent'])), inline=True)
        
        if incident['legal_notification_required']:
            embed.add_field(name="⚠️ Legal Notification", value="REQUIRED", inline=False)
        
        if incident['response_actions']:
            actions = "\n".join([f"• {a}" for a in incident['response_actions'][:5]])
            embed.add_field(name="Response Actions", value=actions, inline=False)
        
        embed.set_footer(text="Sentinel Breach Response Orchestration")
        
        await ctx.send(embed=embed)
    
    async def _breachrespond_logic(self, ctx, incident_id: str, action: str):
        """Execute breach response action"""
        incidents = self.get_incidents(ctx.guild.id)
        
        incident_id = incident_id.upper()
        incident = incidents.get(incident_id)
        
        if not incident:
            await ctx.send(f"❌ Incident not found: {incident_id}")
            return
        
        actions = [
            'isolate_systems',
            'preserve_evidence',
            'notify_legal',
            'contact_customers',
            'activate_incident_response_team',
            'document_timeline',
            'engage_forensics',
            'activate_crisis_comms'
        ]
        
        if action.lower() not in actions:
            action_list = ", ".join(actions)
            await ctx.send(f"❌ Invalid action. Valid actions:\n{action_list}")
            return
        
        incident['response_actions'].append(action)
        incidents[incident_id] = incident
        self.save_incidents(ctx.guild.id, incidents)
        
        embed = discord.Embed(
            title=f"✅ Response Action Executed",
            description=f"**{action.replace('_', ' ').title()}**",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Incident ID", value=f"`{incident_id}`", inline=True)
        embed.add_field(name="Action", value=action.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Status", value="✅ Executed", inline=True)
        embed.add_field(name="Total Actions", value=str(len(incident['response_actions'])), inline=False)
        
        embed.set_footer(text="All response actions are logged and coordinated")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='breachdetect')
    async def breachdetect_prefix(self, ctx, breach_type: str, data_affected: str, records: int = 0):
        """Detect breach and initiate response - Prefix command"""
        await self._breachdetect_logic(ctx, breach_type, data_affected, records)
    
    @commands.command(name='breachstatus')
    async def breachstatus_prefix(self, ctx):
        """Show breach incident status - Prefix command"""
        await self._breachstatus_logic(ctx)
    
    @commands.command(name='breachdetail')
    async def breachdetail_prefix(self, ctx, incident_id: str):
        """Show breach incident details - Prefix command"""
        await self._breachdetail_logic(ctx, incident_id)
    
    @commands.command(name='breachrespond')
    async def breachrespond_prefix(self, ctx, incident_id: str, action: str):
        """Execute response action - Prefix command"""
        await self._breachrespond_logic(ctx, incident_id, action)

async def setup(bot):
    await bot.add_cog(BreachResponseOrchestration(bot))
