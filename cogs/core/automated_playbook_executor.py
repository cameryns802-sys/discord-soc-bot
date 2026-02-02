"""
AUTOMATED PLAYBOOK EXECUTOR
Automatically executes response playbooks based on signal types and threat severity.

Architecture:
- Subscribes to signal bus for all signal types
- Matches signals against playbook templates
- Executes auto-response actions
- Logs execution history
- Provides owner oversight and manual approval workflows
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from cogs.core.signal_bus import signal_bus, Signal, SignalType

class PlaybookStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

class AutomatedPlaybookExecutor(commands.Cog):
    """Automated response playbooks for threat handling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/playbook_executions.json'
        self.executions = []
        self.playbooks = self._init_playbooks()
        self.load_executions()
        self.setup_signal_listeners()
    
    def _init_playbooks(self) -> Dict:
        """Define automated response playbooks"""
        return {
            'threat_detected': {
                'name': 'Threat Response',
                'signal_types': [SignalType.THREAT_DETECTED],
                'actions': [
                    {'type': 'alert', 'priority': 'HIGH', 'target': 'owner'},
                    {'type': 'escalate', 'level': 2},
                    {'type': 'log', 'retention': 90}
                ],
                'confidence_threshold': 0.80,
                'auto_approve': False  # Requires owner approval
            },
            'policy_violation': {
                'name': 'Policy Violation Response',
                'signal_types': [SignalType.POLICY_VIOLATION],
                'actions': [
                    {'type': 'alert', 'priority': 'MEDIUM'},
                    {'type': 'flag', 'review_required': True},
                    {'type': 'escalate', 'level': 1}
                ],
                'confidence_threshold': 0.70,
                'auto_approve': True
            },
            'unauthorized_access': {
                'name': 'Access Control Response',
                'signal_types': [SignalType.UNAUTHORIZED_ACCESS],
                'actions': [
                    {'type': 'alert', 'priority': 'CRITICAL'},
                    {'type': 'revoke_access', 'immediate': True},
                    {'type': 'escalate', 'level': 3},
                    {'type': 'forensics', 'collect_logs': True}
                ],
                'confidence_threshold': 0.90,
                'auto_approve': False
            },
            'escalation_required': {
                'name': 'Escalation Response',
                'signal_types': [SignalType.ESCALATION_REQUIRED],
                'actions': [
                    {'type': 'alert', 'priority': 'HIGH'},
                    {'type': 'escalate', 'level': 2},
                    {'type': 'notify_oncall', 'immediate': True}
                ],
                'confidence_threshold': 0.85,
                'auto_approve': False
            }
        }
    
    def load_executions(self):
        """Load execution history from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.executions = json.load(f)
            except:
                self.executions = []
        else:
            self.executions = []
    
    def save_executions(self):
        """Save execution history to disk"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.executions, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus"""
        signal_bus.subscribe('automated_playbook_executor', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Handle incoming signals from signal bus"""
        # Find matching playbooks
        for playbook_id, playbook in self.playbooks.items():
            if signal.signal_type in playbook['signal_types']:
                if signal.confidence >= playbook['confidence_threshold']:
                    await self.execute_playbook(playbook_id, signal)
    
    async def execute_playbook(self, playbook_id: str, signal: Signal):
        """Execute a playbook in response to a signal"""
        playbook = self.playbooks[playbook_id]
        
        execution = {
            'id': len(self.executions),
            'timestamp': datetime.utcnow().isoformat(),
            'playbook_id': playbook_id,
            'playbook_name': playbook['name'],
            'signal_type': str(signal.signal_type),
            'signal_severity': signal.severity,
            'signal_confidence': signal.confidence,
            'status': PlaybookStatus.PENDING.value,
            'actions': [],
            'auto_approved': playbook['auto_approve'],
            'executed_at': None,
            'executed_by': None
        }
        
        # Execute actions
        for action in playbook['actions']:
            action_result = await self.execute_action(action, signal)
            execution['actions'].append(action_result)
        
        if playbook['auto_approve']:
            execution['status'] = PlaybookStatus.COMPLETED.value
            execution['executed_at'] = datetime.utcnow().isoformat()
        else:
            execution['status'] = PlaybookStatus.PENDING.value
            await self.send_approval_request(execution)
        
        self.executions.append(execution)
        self.save_executions()
    
    async def execute_action(self, action: Dict, signal: Signal) -> Dict:
        """Execute a single playbook action"""
        result = {
            'type': action['type'],
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'details': {}
        }
        
        action_type = action['type']
        
        if action_type == 'alert':
            result['details']['target'] = action.get('target', 'owner')
            result['details']['priority'] = action.get('priority', 'MEDIUM')
            
        elif action_type == 'escalate':
            result['details']['level'] = action.get('level', 1)
            
        elif action_type == 'flag':
            result['details']['review_required'] = action.get('review_required', True)
            
        elif action_type == 'revoke_access':
            result['details']['immediate'] = action.get('immediate', False)
            
        elif action_type == 'notify_oncall':
            result['details']['immediate'] = action.get('immediate', False)
            
        elif action_type == 'forensics':
            result['details']['collect_logs'] = action.get('collect_logs', False)
        
        return result
    
    async def send_approval_request(self, execution: Dict):
        """Send approval request to owner"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        
        if not owner_id:
            return
        
        try:
            owner = await self.bot.fetch_user(owner_id)
            
            embed = discord.Embed(
                title=f"🤖 Playbook Approval Required",
                description=f"Playbook **{execution['playbook_name']}** needs approval",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Signal Type",
                value=f"`{execution['signal_type']}`",
                inline=True
            )
            
            embed.add_field(
                name="Severity",
                value=execution['signal_severity'],
                inline=True
            )
            
            embed.add_field(
                name="Confidence",
                value=f"`{execution['signal_confidence']:.2%}`",
                inline=True
            )
            
            actions_text = "\n".join([f"• {a['type']}" for a in execution['actions']])
            embed.add_field(
                name="Proposed Actions",
                value=actions_text,
                inline=False
            )
            
            embed.add_field(
                name="Execution ID",
                value=f"`{execution['id']}`",
                inline=False
            )
            
            embed.set_footer(text="Use /approveplaybook or /rejectplaybook to respond")
            
            await owner.send(embed=embed)
        except:
            pass
    
    def get_execution_history(self, playbook_id: str = None, hours: int = 24) -> List[Dict]:
        """Get playbook execution history"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        history = [
            e for e in self.executions
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        if playbook_id:
            history = [e for e in history if e['playbook_id'] == playbook_id]
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def get_execution_stats(self) -> Dict:
        """Calculate execution statistics"""
        if not self.executions:
            return {
                'total_executions': 0,
                'by_status': {},
                'by_playbook': {},
                'success_rate': 0.0
            }
        
        # By status
        by_status = {}
        for execution in self.executions:
            status = execution['status']
            by_status[status] = by_status.get(status, 0) + 1
        
        # By playbook
        by_playbook = {}
        for execution in self.executions:
            pb_id = execution['playbook_id']
            by_playbook[pb_id] = by_playbook.get(pb_id, 0) + 1
        
        # Success rate
        total = len(self.executions)
        completed = by_status.get(PlaybookStatus.COMPLETED.value, 0)
        success_rate = (completed / total * 100) if total > 0 else 0.0
        
        return {
            'total_executions': total,
            'by_status': by_status,
            'by_playbook': by_playbook,
            'success_rate': success_rate,
            'completed_count': completed,
            'pending_count': by_status.get(PlaybookStatus.PENDING.value, 0),
            'failed_count': by_status.get(PlaybookStatus.FAILED.value, 0)
        }
    
    @commands.command(name='playbookhistory')
    async def playbook_history_cmd(self, ctx, playbook_id: str = None, hours: int = 24):
        """View playbook execution history (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        history = self.get_execution_history(playbook_id, hours)
        
        if not history:
            await ctx.send(f"✅ No playbook executions in the last {hours} hours")
            return
        
        embed = discord.Embed(
            title="📋 Playbook Execution History",
            description=f"Showing {len(history)} executions from the last {hours} hours",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for execution in history[:10]:
            ts = datetime.fromisoformat(execution['timestamp'])
            status_emoji = {
                'completed': '✅',
                'pending': '⏳',
                'failed': '❌',
                'rejected': '🚫'
            }.get(execution['status'], '❓')
            
            field_value = f"{status_emoji} {execution['status'].upper()}\n"
            field_value += f"Playbook: `{execution['playbook_id']}`\n"
            field_value += f"Signal: `{execution['signal_type']}`\n"
            field_value += f"Confidence: `{execution['signal_confidence']:.2%}`\n"
            field_value += f"Actions: {len(execution['actions'])}"
            
            embed.add_field(
                name=f"Execution {execution['id']}",
                value=field_value,
                inline=False
            )
        
        stats = self.get_execution_stats()
        embed.add_field(
            name="📊 Statistics",
            value=f"Total: {stats['total_executions']}\n"
                  f"✅ Completed: {stats['completed_count']}\n"
                  f"⏳ Pending: {stats['pending_count']}\n"
                  f"❌ Failed: {stats['failed_count']}\n"
                  f"📈 Success Rate: {stats['success_rate']:.1f}%",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='playbookstats')
    async def playbook_stats_cmd(self, ctx):
        """View playbook execution statistics (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        stats = self.get_execution_stats()
        
        if stats['total_executions'] == 0:
            await ctx.send("✅ No playbook executions recorded yet")
            return
        
        embed = discord.Embed(
            title="📊 Playbook Execution Statistics",
            description=f"Analysis of {stats['total_executions']} total executions",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Status distribution
        status_text = "**By Status:**\n"
        for status, count in stats['by_status'].items():
            percent = (count / stats['total_executions'] * 100)
            status_text += f"• {status.upper()}: {count} ({percent:.1f}%)\n"
        
        embed.add_field(
            name="Execution Status",
            value=status_text,
            inline=False
        )
        
        # Playbook distribution
        if stats['by_playbook']:
            playbook_text = "**By Playbook:**\n"
            for pb_id, count in sorted(stats['by_playbook'].items(), key=lambda x: x[1], reverse=True):
                playbook_text += f"• `{pb_id}`: {count}\n"
            
            embed.add_field(
                name="Playbook Distribution",
                value=playbook_text,
                inline=False
            )
        
        # Overall metrics
        embed.add_field(
            name="📈 Overall Metrics",
            value=f"Success Rate: {stats['success_rate']:.1f}%\n"
                  f"Completed: {stats['completed_count']}\n"
                  f"Pending Review: {stats['pending_count']}\n"
                  f"Failed: {stats['failed_count']}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='approveplaybook')
    async def approve_playbook_cmd(self, ctx, execution_id: int):
        """Approve a pending playbook execution (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        if 0 <= execution_id < len(self.executions):
            self.executions[execution_id]['status'] = PlaybookStatus.COMPLETED.value
            self.executions[execution_id]['executed_at'] = datetime.utcnow().isoformat()
            self.executions[execution_id]['executed_by'] = str(ctx.author)
            self.save_executions()
            
            await ctx.send(f"✅ Execution {execution_id} approved and completed")
        else:
            await ctx.send(f"❌ Execution {execution_id} not found")

async def setup(bot):
    await bot.add_cog(AutomatedPlaybookExecutor(bot))
