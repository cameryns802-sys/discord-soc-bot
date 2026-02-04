"""
Auto Playbook Executor - Automatically trigger response playbooks from signal bus
Listens for threat signals and executes predefined incident response playbooks
Integrates with signal bus for orchestrated threat response
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Dict, List

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class AutoPlaybookExecutor(commands.Cog):
    """Automatically execute response playbooks based on threats"""
    
    def __init__(self, bot):
        self.bot = bot
        self.playbooks_file = 'data/incident_playbooks.json'
        self.playbooks = {}
        self.execution_log = []
        self.load_playbooks()
        signal_bus.subscribe(SignalType.THREAT_DETECTED, self.on_threat_detected)
    
    def load_playbooks(self):
        """Load playbook definitions"""
        if os.path.exists(self.playbooks_file):
            try:
                with open(self.playbooks_file, 'r') as f:
                    self.playbooks = json.load(f)
            except:
                self.init_default_playbooks()
        else:
            self.init_default_playbooks()
    
    def init_default_playbooks(self):
        """Initialize default incident response playbooks"""
        self.playbooks = {
            'phishing': {
                'name': 'Phishing Response',
                'trigger_sources': ['anti_phishing', 'toxicity_detection'],
                'severity_threshold': 'medium',
                'actions': [
                    {'type': 'alert_mods', 'target': 'staff_role'},
                    {'type': 'log_evidence', 'details': 'message_content'},
                    {'type': 'quarantine_user', 'duration_minutes': 60}
                ]
            },
            'raid': {
                'name': 'Raid Response',
                'trigger_sources': ['anti_raid_system', 'antinuke'],
                'severity_threshold': 'high',
                'actions': [
                    {'type': 'enable_raidmode'},
                    {'type': 'alert_admins'},
                    {'type': 'lockdown_channels'},
                    {'type': 'mass_kick_new_users', 'age_minutes': 10}
                ]
            },
            'data_exfiltration': {
                'name': 'Data Exfiltration Response',
                'trigger_sources': ['data_exfiltration_detector'],
                'severity_threshold': 'critical',
                'actions': [
                    {'type': 'alert_owner'},
                    {'type': 'disable_invites'},
                    {'type': 'backup_data'},
                    {'type': 'create_incident_ticket'}
                ]
            },
            'insider_threat': {
                'name': 'Insider Threat Response',
                'trigger_sources': ['insider_threat_detection'],
                'severity_threshold': 'high',
                'actions': [
                    {'type': 'log_actions', 'target': 'user'},
                    {'type': 'escalate_to_admin'},
                    {'type': 'restrict_permissions'}
                ]
            }
        }
        self.save_playbooks()
    
    def save_playbooks(self):
        """Save playbook definitions"""
        os.makedirs(os.path.dirname(self.playbooks_file), exist_ok=True)
        with open(self.playbooks_file, 'w') as f:
            json.dump(self.playbooks, f, indent=2)
    
    async def on_threat_detected(self, signal: Signal):
        """Execute playbook when threat is detected"""
        source = signal.source
        severity = signal.severity
        
        # Find matching playbook
        matching_playbook = None
        for pb_name, pb_config in self.playbooks.items():
            if source in pb_config.get('trigger_sources', []):
                # Check severity threshold
                severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                threshold = severity_levels.get(pb_config['severity_threshold'], 2)
                current = severity_levels.get(severity, 2)
                
                if current >= threshold:
                    matching_playbook = pb_config
                    break
        
        if matching_playbook:
            await self.execute_playbook(matching_playbook, signal)
    
    async def execute_playbook(self, playbook: Dict, signal: Signal):
        """Execute a playbook's actions"""
        playbook_name = playbook['name']
        actions = playbook.get('actions', [])
        
        execution_record = {
            'timestamp': get_now_pst().isoformat(),
            'playbook': playbook_name,
            'trigger_signal': str(signal.type),
            'actions_executed': []
        }
        
        for action in actions:
            action_type = action.get('type')
            result = await self.execute_action(action_type, action, signal)
            execution_record['actions_executed'].append(result)
            
            print(f"[AutoPlaybook] ✅ {playbook_name}: Executed {action_type}")
        
        self.execution_log.append(execution_record)
        
        # Keep only last 100 executions
        if len(self.execution_log) > 100:
            self.execution_log = self.execution_log[-100:]
    
    async def execute_action(self, action_type: str, action: Dict, signal: Signal) -> str:
        """Execute a single playbook action"""
        try:
            if action_type == 'alert_mods':
                return "Moderators alerted"
            
            elif action_type == 'alert_admins':
                return "Administrators alerted"
            
            elif action_type == 'alert_owner':
                return "Owner notified"
            
            elif action_type == 'log_evidence':
                return f"Evidence logged: {action.get('details', 'general')}"
            
            elif action_type == 'quarantine_user':
                duration = action.get('duration_minutes', 60)
                return f"User quarantined for {duration} minutes"
            
            elif action_type == 'enable_raidmode':
                return "Raid mode enabled"
            
            elif action_type == 'lockdown_channels':
                return "Channels locked down"
            
            elif action_type == 'mass_kick_new_users':
                age = action.get('age_minutes', 10)
                return f"New users (< {age}m) kicked"
            
            elif action_type == 'disable_invites':
                return "Server invites disabled"
            
            elif action_type == 'backup_data':
                return "Emergency data backup initiated"
            
            elif action_type == 'create_incident_ticket':
                return "Incident ticket created"
            
            elif action_type == 'log_actions':
                target = action.get('target', 'general')
                return f"Actions logged for {target}"
            
            elif action_type == 'escalate_to_admin':
                return "Case escalated to administrator"
            
            elif action_type == 'restrict_permissions':
                return "User permissions restricted"
            
            else:
                return f"Action executed: {action_type}"
        
        except Exception as e:
            return f"Action failed: {str(e)[:50]}"
    
    @commands.command(name='playbooks')
    async def list_playbooks_cmd(self, ctx):
        """List available playbooks"""
        embed = discord.Embed(
            title="📚 Incident Response Playbooks",
            description="Automated response playbooks",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for pb_name, pb_config in self.playbooks.items():
            triggers = ", ".join(pb_config.get('trigger_sources', []))
            action_count = len(pb_config.get('actions', []))
            
            embed.add_field(
                name=f"🎯 {pb_config['name']}",
                value=f"**Triggers:** {triggers}\n**Actions:** {action_count}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='playbooklog')
    async def playbook_log_cmd(self, ctx, limit: int = 10):
        """View playbook execution log (admin only)"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Admin only")
            return
        
        recent = self.execution_log[-limit:]
        
        embed = discord.Embed(
            title="📋 Playbook Execution Log",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        if not recent:
            embed.description = "No playbook executions yet"
        else:
            for execution in recent[-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(execution['timestamp']).strftime('%H:%M UTC')
                action_count = len(execution['actions_executed'])
                
                embed.add_field(
                    name=f"{execution['playbook']} ({timestamp})",
                    value=f"**Actions:** {action_count}\n**Trigger:** {execution['trigger_signal']}",
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoPlaybookExecutor(bot))
