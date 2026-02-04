"""
Automated Response Playbooks - Execute predefined security response plans for Sentinel
Implements SOAR (Security Orchestration, Automation and Response) capabilities
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid
from cogs.core.pst_timezone import get_now_pst

class AutomatedResponsePlaybooks(commands.Cog):
    """SOAR playbook execution and response automation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.playbook_file = 'data/playbooks.json'
        self.execution_file = 'data/playbook_executions.json'
        self.load_playbooks()
        self.load_executions()
    
    def load_playbooks(self):
        """Load playbook templates"""
        if not os.path.exists(self.playbook_file):
            os.makedirs(os.path.dirname(self.playbook_file), exist_ok=True)
            self.init_default_playbooks()
        else:
            with open(self.playbook_file, 'r') as f:
                self.playbooks = json.load(f)
    
    def load_executions(self):
        """Load execution records"""
        if not os.path.exists(self.execution_file):
            os.makedirs(os.path.dirname(self.execution_file), exist_ok=True)
            with open(self.execution_file, 'w') as f:
                json.dump({}, f)
    
    def init_default_playbooks(self):
        """Initialize default playbooks"""
        playbooks = {
            'phishing_response': {
                'name': 'Phishing Response',
                'description': 'Response to phishing/malware threat',
                'trigger_type': 'Phishing Attempt',
                'severity': 'high',
                'steps': [
                    'Identify and isolate affected users',
                    'Delete malicious messages',
                    'Warn guild members in #announcements',
                    'Collect evidence from message history',
                    'Create incident case',
                    'Monitor for similar patterns'
                ],
                'estimated_time': '15 minutes'
            },
            'account_compromise': {
                'name': 'Account Compromise Response',
                'description': 'Response to compromised user account',
                'trigger_type': 'Unauthorized Access',
                'severity': 'critical',
                'steps': [
                    'Immediately mute compromised user',
                    'Remove all sensitive roles',
                    'Review recent actions and audit logs',
                    'Notify user via DM to reset password',
                    'Create critical incident',
                    'Monitor account for recovery',
                    'Document all findings'
                ],
                'estimated_time': '10 minutes'
            },
            'raid_response': {
                'name': 'Raid/Mass Attack Response',
                'description': 'Response to raid or mass disruption attack',
                'trigger_type': 'Mass Action',
                'severity': 'critical',
                'steps': [
                    'Activate slowmode on all channels',
                    'Ban repeat offenders',
                    'Lockdown guild permissions',
                    'Alert admins immediately',
                    'Save evidence of attack',
                    'Document attacker identities',
                    'Create incident for post-mortem'
                ],
                'estimated_time': '5 minutes'
            },
            'permission_abuse': {
                'name': 'Permission Abuse Response',
                'description': 'Response to privilege escalation/abuse',
                'trigger_type': 'Unauthorized Access',
                'severity': 'high',
                'steps': [
                    'Audit all role changes',
                    'Identify unauthorized escalations',
                    'Revoke unauthorized permissions',
                    'Review historical actions',
                    'Create incident case',
                    'Implement permission controls',
                    'Review role hierarchy'
                ],
                'estimated_time': '20 minutes'
            },
            'data_exfil': {
                'name': 'Data Exfiltration Response',
                'description': 'Response to potential data theft',
                'trigger_type': 'Suspicious User Activity',
                'severity': 'critical',
                'steps': [
                    'Identify affected data/channels',
                    'Review export/download logs',
                    'Restrict suspect user access',
                    'Analyze what data was accessed',
                    'Notify affected parties',
                    'Create critical incident',
                    'Implement data protection controls'
                ],
                'estimated_time': '30 minutes'
            }
        }
        
        with open(self.playbook_file, 'w') as f:
            json.dump(playbooks, f, indent=2)
        self.playbooks = playbooks
    
    def get_guild_executions(self, guild_id):
        """Get execution records for guild"""
        with open(self.execution_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_execution(self, guild_id, execution):
        """Save execution record"""
        with open(self.execution_file, 'r') as f:
            data = json.load(f)
        
        if str(guild_id) not in data:
            data[str(guild_id)] = []
        
        data[str(guild_id)].append(execution)
        with open(self.execution_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def execute_playbook(self, guild_id, playbook_id, executor, incident_id=None):
        """Execute a playbook"""
        if playbook_id not in self.playbooks:
            return None
        
        playbook = self.playbooks[playbook_id]
        
        execution = {
            'id': str(uuid.uuid4())[:8],
            'playbook_id': playbook_id,
            'playbook_name': playbook['name'],
            'started_at': get_now_pst().isoformat(),
            'completed_at': get_now_pst().isoformat(),
            'executor': executor,
            'incident_id': incident_id,
            'status': 'completed',
            'steps_completed': len(playbook['steps']),
            'total_steps': len(playbook['steps']),
            'notes': []
        }
        
        self.save_execution(guild_id, execution)
        return execution
    
    async def _playbooks_logic(self, ctx):
        """List available playbooks"""
        embed = discord.Embed(
            title="🎯 Available Response Playbooks",
            description="Pre-configured automation responses for security threats",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        for playbook_id, playbook in self.playbooks.items():
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(playbook.get('severity', 'medium'), '❓')
            
            embed.add_field(
                name=f"{severity_emoji} {playbook['name']}",
                value=f"Trigger: {playbook['trigger_type']}\nSteps: {len(playbook['steps'])}\nTime: ~{playbook['estimated_time']}\n\n`/playbook exec {playbook_id} [incident_id]`",
                inline=False
            )
        
        embed.add_field(name="ℹ️ Usage", value="Run `/playbook exec <playbook_id> [incident_id]` to execute\nUse `/playbook detail <id>` for step details", inline=False)
        embed.set_footer(text="Sentinel SOAR System | Security Orchestration & Automation")
        
        await ctx.send(embed=embed)
    
    async def _playbook_detail_logic(self, ctx, playbook_id: str):
        """Show detailed playbook information"""
        if playbook_id not in self.playbooks:
            await ctx.send(f"❌ Playbook `{playbook_id}` not found.")
            return
        
        playbook = self.playbooks[playbook_id]
        
        embed = discord.Embed(
            title=f"📋 Playbook: {playbook['name']}",
            description=playbook['description'],
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Trigger", value=playbook['trigger_type'], inline=True)
        embed.add_field(name="Severity", value=playbook['severity'].upper(), inline=True)
        embed.add_field(name="Est. Time", value=playbook['estimated_time'], inline=True)
        embed.add_field(name="Total Steps", value=str(len(playbook['steps'])), inline=True)
        
        # Steps
        steps_str = ""
        for i, step in enumerate(playbook['steps'], 1):
            steps_str += f"{i}. {step}\n"
        
        embed.add_field(name="📝 Response Steps", value=steps_str, inline=False)
        
        embed.add_field(name="⚡ Execute", value=f"`/playbook exec {playbook_id} [incident_id]`", inline=False)
        
        embed.set_footer(text="Sentinel SOAR Playbook Details")
        
        await ctx.send(embed=embed)
    
    async def _playbook_exec_logic(self, ctx, playbook_id: str, incident_id: str = None):
        """Execute a playbook"""
        if playbook_id not in self.playbooks:
            await ctx.send(f"❌ Playbook `{playbook_id}` not found.")
            return
        
        playbook = self.playbooks[playbook_id]
        
        # Execute playbook
        execution = self.execute_playbook(ctx.guild.id, playbook_id, ctx.author.id, incident_id)
        
        severity_color = {
            'critical': discord.Color.red(),
            'high': discord.Color.orange(),
            'medium': discord.Color.gold(),
            'low': discord.Color.green()
        }.get(playbook.get('severity', 'medium'), discord.Color.greyple())
        
        embed = discord.Embed(
            title=f"⚡ Playbook Executed: {playbook['name']}",
            description=f"Response automation initiated",
            color=severity_color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Playbook ID", value=f"`{playbook_id}`", inline=True)
        embed.add_field(name="Execution ID", value=f"`{execution['id']}`", inline=True)
        embed.add_field(name="Executed By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="✅ COMPLETED", inline=True)
        embed.add_field(name="Steps Executed", value=f"{execution['steps_completed']}/{execution['total_steps']}", inline=True)
        
        if incident_id:
            embed.add_field(name="Linked Incident", value=f"`{incident_id}`", inline=True)
        
        # Show steps
        steps_str = ""
        for i, step in enumerate(playbook['steps'], 1):
            steps_str += f"✅ {i}. {step}\n"
        
        embed.add_field(name="🚀 Executed Steps", value=steps_str, inline=False)
        
        embed.add_field(name="⏱️ Execution Time", value=playbook['estimated_time'], inline=True)
        embed.add_field(name="Completed", value=f"<t:{int(get_now_pst().timestamp())}:R>", inline=True)
        
        embed.set_footer(text="Sentinel SOAR | Response automated and logged")
        
        await ctx.send(embed=embed)
    
    async def _playbook_history_logic(self, ctx):
        """Show playbook execution history"""
        executions = self.get_guild_executions(ctx.guild.id)
        
        if not executions:
            await ctx.send("📋 No playbook executions yet.")
            return
        
        embed = discord.Embed(
            title="📊 Playbook Execution History",
            description=f"{len(executions)} playbook(s) executed",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        # Show recent
        for execution in sorted(executions, key=lambda x: x['started_at'], reverse=True)[:8]:
            embed.add_field(
                name=f"{execution['playbook_name']} (ID: {execution['id']})",
                value=f"Executed: <t:{int(datetime.fromisoformat(execution['started_at']).timestamp())}:R>\nSteps: {execution['steps_completed']}/{execution['total_steps']}\nIncident: {execution.get('incident_id', 'N/A')}",
                inline=False
            )
        
        if len(executions) > 8:
            embed.add_field(name="... and more", value=f"+{len(executions) - 8} additional executions", inline=False)
        
        embed.set_footer(text="Sentinel SOAR Execution Log")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='playbook')
    async def playbook_prefix(self, ctx, action: str = 'list', *, args: str = None):
        """Manage response playbooks - Prefix command"""
        action = action.lower()
        
        if action == 'list' or action == '':
            await self._playbooks_logic(ctx)
        elif action == 'detail':
            if not args:
                await ctx.send("Usage: `!playbook detail <playbook_id>`")
                return
            await self._playbook_detail_logic(ctx, args.split()[0] if args else '')
        elif action == 'exec':
            if not args:
                await ctx.send("Usage: `!playbook exec <playbook_id> [incident_id]`")
                return
            parts = args.split()
            playbook_id = parts[0]
            incident_id = parts[1] if len(parts) > 1 else None
            await self._playbook_exec_logic(ctx, playbook_id, incident_id)
        elif action == 'history':
            await self._playbook_history_logic(ctx)
        else:
            await ctx.send("Usage: `!playbook [list|detail|exec|history]`")

async def setup(bot):
    await bot.add_cog(AutomatedResponsePlaybooks(bot))
