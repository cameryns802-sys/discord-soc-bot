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
from cogs.core.pst_timezone import get_now_pst

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
        self.playbooks_file = 'data/playbooks.json'
        self.executions = []
        self.default_playbooks = self._init_playbooks()
        self.custom_playbooks = self.load_custom_playbooks()
        self.playbooks = {**self.default_playbooks, **self.custom_playbooks}
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

    def _resolve_signal_type(self, value: str) -> Optional[SignalType]:
        """Resolve a string to a SignalType enum"""
        if not value:
            return None
        value_norm = value.strip().lower()
        for signal_type in SignalType:
            if value_norm == signal_type.value or value_norm == signal_type.name.lower():
                return signal_type
        return None

    def _get_signal_type(self, signal: Signal) -> Optional[SignalType]:
        """Get signal type with backward compatibility"""
        signal_type = getattr(signal, "signal_type", None)
        if isinstance(signal_type, SignalType):
            return signal_type
        if signal_type is None:
            signal_type = getattr(signal, "type", None)
        if isinstance(signal_type, SignalType):
            return signal_type
        if isinstance(signal_type, str):
            return self._resolve_signal_type(signal_type)
        return None

    def _normalize_playbook(self, playbook_id: str, playbook: Dict) -> Optional[Dict]:
        """Normalize playbook data for runtime use"""
        signal_types = playbook.get("signal_types", [])
        normalized_types = []
        for item in signal_types:
            if isinstance(item, SignalType):
                normalized_types.append(item)
                continue
            if isinstance(item, str):
                resolved = self._resolve_signal_type(item)
                if resolved:
                    normalized_types.append(resolved)
        if not normalized_types:
            return None

        actions = playbook.get("actions", [])
        if not isinstance(actions, list) or not actions:
            actions = [{"type": "alert", "priority": "MEDIUM"}]

        threshold = playbook.get("confidence_threshold", 0.8)
        try:
            threshold = float(threshold)
        except (TypeError, ValueError):
            threshold = 0.8
        threshold = min(1.0, max(0.0, threshold))

        return {
            "name": playbook.get("name", playbook_id),
            "signal_types": normalized_types,
            "actions": actions,
            "confidence_threshold": threshold,
            "auto_approve": bool(playbook.get("auto_approve", False))
        }

    def _serialize_playbook(self, playbook: Dict) -> Dict:
        """Serialize playbook to JSON-safe format"""
        signal_types = [t.value if isinstance(t, SignalType) else str(t) for t in playbook.get("signal_types", [])]
        return {
            "name": playbook.get("name"),
            "signal_types": signal_types,
            "actions": playbook.get("actions", []),
            "confidence_threshold": playbook.get("confidence_threshold", 0.8),
            "auto_approve": playbook.get("auto_approve", False)
        }

    def load_custom_playbooks(self) -> Dict:
        """Load custom playbooks from disk"""
        if os.path.exists(self.playbooks_file):
            try:
                with open(self.playbooks_file, 'r') as f:
                    raw = json.load(f)
            except Exception:
                raw = {}
        else:
            raw = {}

        normalized = {}
        for playbook_id, playbook in raw.items():
            normalized_playbook = self._normalize_playbook(playbook_id, playbook)
            if normalized_playbook:
                normalized[playbook_id] = normalized_playbook
        return normalized

    def save_custom_playbooks(self) -> None:
        """Save custom playbooks to disk"""
        os.makedirs(os.path.dirname(self.playbooks_file), exist_ok=True)
        payload = {
            playbook_id: self._serialize_playbook(playbook)
            for playbook_id, playbook in self.custom_playbooks.items()
        }
        with open(self.playbooks_file, 'w') as f:
            json.dump(payload, f, indent=2)
    
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
        signal_type = self._get_signal_type(signal)
        if not signal_type:
            return
        # Find matching playbooks
        for playbook_id, playbook in self.playbooks.items():
            if signal_type in playbook['signal_types']:
                if signal.confidence >= playbook['confidence_threshold']:
                    await self.execute_playbook(playbook_id, signal)
    
    async def execute_playbook(self, playbook_id: str, signal: Signal):
        """Execute a playbook in response to a signal"""
        playbook = self.playbooks[playbook_id]
        signal_type = self._get_signal_type(signal)
        signal_type_value = signal_type.value if isinstance(signal_type, SignalType) else str(signal_type)
        
        execution = {
            'id': len(self.executions),
            'timestamp': get_now_pst().isoformat(),
            'playbook_id': playbook_id,
            'playbook_name': playbook['name'],
            'signal_type': signal_type_value,
            'signal_severity': signal.severity,
            'signal_confidence': signal.confidence,
            'status': PlaybookStatus.PENDING.value,
            'actions': [],
            'auto_approved': playbook.get('auto_approve', False),
            'executed_at': None,
            'executed_by': None
        }
        
        # Execute actions
        for action in playbook['actions']:
            action_result = await self.execute_action(action, signal)
            execution['actions'].append(action_result)
        
        if playbook.get('auto_approve', False):
            execution['status'] = PlaybookStatus.COMPLETED.value
            execution['executed_at'] = get_now_pst().isoformat()
        else:
            execution['status'] = PlaybookStatus.PENDING.value
            await self.send_approval_request(execution)
        
        self.executions.append(execution)
        self.save_executions()
    
    async def execute_action(self, action: Dict, signal: Signal) -> Dict:
        """Execute a single playbook action"""
        result = {
            'type': action['type'],
            'timestamp': get_now_pst().isoformat(),
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
                timestamp=get_now_pst()
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
        cutoff = get_now_pst() - timedelta(hours=hours)
        
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
            timestamp=get_now_pst()
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

    @commands.command(name='playbook_list')
    @commands.has_permissions(administrator=True)
    async def playbook_list_cmd(self, ctx):
        """List available playbooks"""
        embed = discord.Embed(
            title="📘 Playbooks",
            description=f"Total: {len(self.playbooks)} (Custom: {len(self.custom_playbooks)})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )

        for playbook_id, playbook in sorted(self.playbooks.items()):
            signal_types = ", ".join([t.value for t in playbook['signal_types']])
            auto_flag = "auto" if playbook.get("auto_approve", False) else "manual"
            source = "custom" if playbook_id in self.custom_playbooks else "default"
            value = (
                f"Name: {playbook['name']}\n"
                f"Signals: {signal_types}\n"
                f"Threshold: {playbook.get('confidence_threshold', 0.0):.2f} | {auto_flag} | {source}"
            )
            embed.add_field(name=playbook_id, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='playbook_show')
    @commands.has_permissions(administrator=True)
    async def playbook_show_cmd(self, ctx, playbook_id: str):
        """Show playbook details"""
        playbook = self.playbooks.get(playbook_id)
        if not playbook:
            await ctx.send(f"❌ Playbook `{playbook_id}` not found")
            return

        embed = discord.Embed(
            title=f"📖 Playbook: {playbook_id}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        embed.add_field(name="Name", value=playbook['name'], inline=False)
        embed.add_field(name="Signal Types", value=", ".join([t.value for t in playbook['signal_types']]), inline=False)
        embed.add_field(name="Confidence Threshold", value=f"{playbook.get('confidence_threshold', 0.0):.2f}", inline=True)
        embed.add_field(name="Auto Approve", value=str(playbook.get('auto_approve', False)), inline=True)

        actions_text = "\n".join([f"{idx}. {a['type']}" for idx, a in enumerate(playbook.get('actions', []))])
        embed.add_field(name="Actions", value=actions_text or "(none)", inline=False)
        embed.set_footer(text="Use !playbook_add_action or !playbook_remove_action")
        await ctx.send(embed=embed)

    @commands.command(name='playbook_create')
    @commands.is_owner()
    async def playbook_create_cmd(self, ctx, playbook_id: str, signal_type: str, confidence_threshold: float, auto_approve: str, *, name: str):
        """Create a custom playbook"""
        if playbook_id in self.default_playbooks:
            await ctx.send("❌ Playbook ID is reserved by default playbooks")
            return
        if playbook_id in self.custom_playbooks:
            await ctx.send("❌ Playbook already exists")
            return

        resolved = self._resolve_signal_type(signal_type)
        if not resolved:
            await ctx.send("❌ Invalid signal type")
            return

        auto_value = auto_approve.strip().lower() in {"true", "1", "yes", "y"}
        playbook = {
            "name": name,
            "signal_types": [resolved],
            "actions": [{"type": "alert", "priority": "MEDIUM"}],
            "confidence_threshold": min(1.0, max(0.0, float(confidence_threshold))),
            "auto_approve": auto_value
        }

        self.custom_playbooks[playbook_id] = playbook
        self.playbooks[playbook_id] = playbook
        self.save_custom_playbooks()
        await ctx.send(f"✅ Created playbook `{playbook_id}`")

    @commands.command(name='playbook_delete')
    @commands.is_owner()
    async def playbook_delete_cmd(self, ctx, playbook_id: str):
        """Delete a custom playbook"""
        if playbook_id not in self.custom_playbooks:
            await ctx.send("❌ Custom playbook not found")
            return

        del self.custom_playbooks[playbook_id]
        if playbook_id in self.playbooks:
            del self.playbooks[playbook_id]
        self.save_custom_playbooks()
        await ctx.send(f"✅ Deleted playbook `{playbook_id}`")

    @commands.command(name='playbook_set_threshold')
    @commands.is_owner()
    async def playbook_set_threshold_cmd(self, ctx, playbook_id: str, confidence_threshold: float):
        """Update playbook confidence threshold"""
        playbook = self.custom_playbooks.get(playbook_id)
        if not playbook:
            await ctx.send("❌ Custom playbook not found")
            return

        playbook['confidence_threshold'] = min(1.0, max(0.0, float(confidence_threshold)))
        self.save_custom_playbooks()
        await ctx.send(f"✅ Updated threshold for `{playbook_id}`")

    @commands.command(name='playbook_set_autoapprove')
    @commands.is_owner()
    async def playbook_set_autoapprove_cmd(self, ctx, playbook_id: str, auto_approve: str):
        """Update playbook auto-approve flag"""
        playbook = self.custom_playbooks.get(playbook_id)
        if not playbook:
            await ctx.send("❌ Custom playbook not found")
            return

        playbook['auto_approve'] = auto_approve.strip().lower() in {"true", "1", "yes", "y"}
        self.save_custom_playbooks()
        await ctx.send(f"✅ Updated auto-approve for `{playbook_id}`")

    @commands.command(name='playbook_add_action')
    @commands.is_owner()
    async def playbook_add_action_cmd(self, ctx, playbook_id: str, action_type: str, *params: str):
        """Add an action to a custom playbook"""
        playbook = self.custom_playbooks.get(playbook_id)
        if not playbook:
            await ctx.send("❌ Custom playbook not found")
            return

        action = {"type": action_type}
        for param in params:
            if "=" not in param:
                continue
            key, value = param.split("=", 1)
            value_lower = value.lower()
            if value_lower in {"true", "false"}:
                parsed = value_lower == "true"
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    try:
                        parsed = float(value)
                    except ValueError:
                        parsed = value
            action[key] = parsed

        playbook['actions'].append(action)
        self.save_custom_playbooks()
        await ctx.send(f"✅ Added action to `{playbook_id}`")

    @commands.command(name='playbook_remove_action')
    @commands.is_owner()
    async def playbook_remove_action_cmd(self, ctx, playbook_id: str, index: int):
        """Remove an action from a custom playbook"""
        playbook = self.custom_playbooks.get(playbook_id)
        if not playbook:
            await ctx.send("❌ Custom playbook not found")
            return

        if index < 0 or index >= len(playbook.get('actions', [])):
            await ctx.send("❌ Invalid action index")
            return

        playbook['actions'].pop(index)
        self.save_custom_playbooks()
        await ctx.send(f"✅ Removed action {index} from `{playbook_id}`")
    
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
            timestamp=get_now_pst()
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
            self.executions[execution_id]['executed_at'] = get_now_pst().isoformat()
            self.executions[execution_id]['executed_by'] = str(ctx.author)
            self.save_executions()
            
            await ctx.send(f"✅ Execution {execution_id} approved and completed")
        else:
            await ctx.send(f"❌ Execution {execution_id} not found")

async def setup(bot):
    await bot.add_cog(AutomatedPlaybookExecutor(bot))
