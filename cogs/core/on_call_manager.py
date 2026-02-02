"""
ON-CALL MANAGER
Intelligent escalation and on-call workforce management.

Architecture:
- Manages on-call schedules and rotations
- Escalates critical threats to appropriate personnel
- Tracks acknowledgment and resolution times
- Integrates with signal bus for automated escalation
- Provides on-call analytics and rotation metrics
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from cogs.core.signal_bus import signal_bus, Signal, SignalType

class EscalationLevel(Enum):
    """Escalation severity levels"""
    P4 = "P4"  # Low priority
    P3 = "P3"  # Medium priority
    P2 = "P2"  # High priority
    P1 = "P1"  # Critical priority

class OnCallManager(commands.Cog):
    """Intelligent on-call and escalation management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/on_call_schedule.json'
        self.escalations_file = 'data/escalations.json'
        self.on_call_schedule = {}
        self.escalations = []
        self.load_on_call_data()
        self.setup_signal_listeners()
    
    def load_on_call_data(self):
        """Load on-call schedule and escalation history"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.on_call_schedule = json.load(f)
            except:
                self.on_call_schedule = self.init_default_schedule()
        else:
            self.on_call_schedule = self.init_default_schedule()
        
        if os.path.exists(self.escalations_file):
            try:
                with open(self.escalations_file, 'r') as f:
                    self.escalations = json.load(f)
            except:
                self.escalations = []
        else:
            self.escalations = []
    
    def init_default_schedule(self) -> Dict:
        """Initialize default on-call schedule"""
        return {
            'team_lead': {
                'name': 'Team Lead',
                'escalation_level': 'P1',
                'user_ids': [],
                'rotation_minutes': 120
            },
            'security_lead': {
                'name': 'Security Lead',
                'escalation_level': 'P2',
                'user_ids': [],
                'rotation_minutes': 120
            },
            'incident_commander': {
                'name': 'Incident Commander',
                'escalation_level': 'P3',
                'user_ids': [],
                'rotation_minutes': 120
            }
        }
    
    def save_on_call_data(self):
        """Save on-call data to disk"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.on_call_schedule, f, indent=2)
        
        with open(self.escalations_file, 'w') as f:
            json.dump(self.escalations, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus"""
        signal_bus.subscribe('on_call_manager', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Escalate based on signal severity"""
        # Only escalate critical or escalation-required signals
        if signal.severity != 'CRITICAL' and signal.signal_type != SignalType.ESCALATION_REQUIRED:
            return
        
        # Determine escalation level
        level = self.determine_escalation_level(signal)
        
        # Create escalation record
        escalation = {
            'id': f"ESC-{len(self.escalations) + 1:04d}",
            'timestamp': datetime.utcnow().isoformat(),
            'signal_type': str(signal.signal_type),
            'severity': signal.severity,
            'escalation_level': level,
            'source': signal.source,
            'details': signal.details,
            'status': 'PENDING',
            'acknowledged_by': None,
            'acknowledged_at': None,
            'resolved_at': None
        }
        
        self.escalations.append(escalation)
        
        # Notify on-call personnel
        await self.escalate_to_oncall(escalation, signal)
        
        self.save_on_call_data()
    
    def determine_escalation_level(self, signal: Signal) -> str:
        """Determine escalation level based on signal"""
        if signal.severity == 'CRITICAL':
            return 'P1'
        elif signal.severity == 'HIGH':
            return 'P2'
        elif signal.severity == 'MEDIUM':
            return 'P3'
        else:
            return 'P4'
    
    async def escalate_to_oncall(self, escalation: Dict, signal: Signal):
        """Notify on-call personnel"""
        level = escalation['escalation_level']
        
        # Find on-call rotation for this level
        on_call_role = None
        if level == 'P1':
            on_call_role = self.on_call_schedule.get('team_lead')
        elif level == 'P2':
            on_call_role = self.on_call_schedule.get('security_lead')
        else:
            on_call_role = self.on_call_schedule.get('incident_commander')
        
        if not on_call_role or not on_call_role.get('user_ids'):
            print(f"[OnCallManager] No on-call personnel for level {level}")
            return
        
        # Get current on-call person (simple round-robin)
        user_ids = on_call_role['user_ids']
        current_index = len(self.escalations) % len(user_ids)
        user_id = user_ids[current_index]
        
        try:
            user = await self.bot.fetch_user(user_id)
            
            # Create escalation embed
            embed = discord.Embed(
                title=f"🚨 {level} Escalation - {escalation['id']}",
                description=f"Signal: {escalation['signal_type']}\nSeverity: {escalation['severity']}",
                color=self.get_severity_color(escalation['severity']),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Source",
                value=escalation['source'],
                inline=True
            )
            
            embed.add_field(
                name="Escalation Level",
                value=escalation['escalation_level'],
                inline=True
            )
            
            if escalation['details']:
                details_text = "\n".join([
                    f"• {k}: {v}" for k, v in escalation['details'].items()
                ])
                embed.add_field(
                    name="Details",
                    value=details_text[:1024],
                    inline=False
                )
            
            embed.set_footer(text="React to acknowledge receipt")
            
            await user.send(embed=embed)
            
            # Log escalation
            print(f"[OnCallManager] Escalated {escalation['id']} to {user}")
            
        except Exception as e:
            print(f"[OnCallManager] Failed to notify on-call: {e}")
    
    def get_severity_color(self, severity: str) -> discord.Color:
        """Get color for severity level"""
        colors = {
            'CRITICAL': discord.Color.red(),
            'HIGH': discord.Color.orange(),
            'MEDIUM': discord.Color.yellow(),
            'LOW': discord.Color.blue()
        }
        return colors.get(severity, discord.Color.gray())
    
    def add_oncall_member(self, role: str, user_id: int):
        """Add user to on-call rotation"""
        if role not in self.on_call_schedule:
            return False
        
        if user_id not in self.on_call_schedule[role]['user_ids']:
            self.on_call_schedule[role]['user_ids'].append(user_id)
            self.save_on_call_data()
            return True
        
        return False
    
    def remove_oncall_member(self, role: str, user_id: int):
        """Remove user from on-call rotation"""
        if role not in self.on_call_schedule:
            return False
        
        if user_id in self.on_call_schedule[role]['user_ids']:
            self.on_call_schedule[role]['user_ids'].remove(user_id)
            self.save_on_call_data()
            return True
        
        return False
    
    def get_current_oncall(self) -> Dict:
        """Get current on-call personnel"""
        current = {}
        
        for role, role_data in self.on_call_schedule.items():
            if role_data['user_ids']:
                # Simple round-robin based on timestamp
                index = int(datetime.utcnow().timestamp() / (role_data['rotation_minutes'] * 60)) % len(role_data['user_ids'])
                current[role] = {
                    'user_id': role_data['user_ids'][index],
                    'rotation_name': role_data['name'],
                    'escalation_level': role_data['escalation_level']
                }
        
        return current
    
    def get_escalation_stats(self, hours: int = 24) -> Dict:
        """Get escalation statistics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent = []
        for esc in self.escalations:
            ts = datetime.fromisoformat(esc['timestamp'])
            if ts > cutoff:
                recent.append(esc)
        
        # Categorize by level
        by_level = {}
        by_status = {}
        
        for esc in recent:
            level = esc['escalation_level']
            status = esc['status']
            
            if level not in by_level:
                by_level[level] = 0
            by_level[level] += 1
            
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1
        
        # Calculate MTTK (Mean Time To Acknowledge)
        acknowledged = [e for e in recent if e['acknowledged_at']]
        mttk = 0
        if acknowledged:
            total_time = 0
            for esc in acknowledged:
                ts = datetime.fromisoformat(esc['timestamp'])
                ack_ts = datetime.fromisoformat(esc['acknowledged_at'])
                total_time += (ack_ts - ts).total_seconds()
            mttk = total_time / len(acknowledged)
        
        return {
            'period_hours': hours,
            'total_escalations': len(recent),
            'by_level': by_level,
            'by_status': by_status,
            'acknowledged_count': len(acknowledged),
            'mttk_seconds': mttk
        }
    
    @commands.command(name='oncallstatus')
    async def oncall_status_cmd(self, ctx):
        """View current on-call roster (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        current = self.get_current_oncall()
        
        embed = discord.Embed(
            title="👥 Current On-Call Roster",
            description="Active on-call personnel by escalation level",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for role, data in current.items():
            try:
                user = await self.bot.fetch_user(data['user_id'])
                embed.add_field(
                    name=f"{data['rotation_name']} ({data['escalation_level']})",
                    value=f"{user.mention}",
                    inline=False
                )
            except:
                embed.add_field(
                    name=f"{data['rotation_name']} ({data['escalation_level']})",
                    value=f"User ID: {data['user_id']}",
                    inline=False
                )
        
        embed.set_footer(text="Rotations update every 2 hours")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='escalationhistory')
    async def escalation_history_cmd(self, ctx, hours: int = 24):
        """View escalation history (owner only)"""
        
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        stats = self.get_escalation_stats(hours)
        
        embed = discord.Embed(
            title="📊 Escalation History",
            description=f"Analysis over last {hours} hours",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Total Escalations",
            value=str(stats['total_escalations']),
            inline=True
        )
        
        embed.add_field(
            name="Acknowledged",
            value=str(stats['acknowledged_count']),
            inline=True
        )
        
        # MTTK
        mttk_minutes = int(stats['mttk_seconds'] / 60) if stats['mttk_seconds'] > 0 else 0
        embed.add_field(
            name="Avg Time To Acknowledge",
            value=f"`{mttk_minutes} minutes`",
            inline=True
        )
        
        # By level
        if stats['by_level']:
            level_text = ""
            for level, count in sorted(stats['by_level'].items()):
                level_emoji = {
                    'P1': '🔴',
                    'P2': '🟠',
                    'P3': '🟡',
                    'P4': '🔵'
                }.get(level, '❓')
                level_text += f"{level_emoji} {level}: {count}\n"
            
            embed.add_field(
                name="By Escalation Level",
                value=level_text,
                inline=False
            )
        
        # By status
        if stats['by_status']:
            status_text = ""
            for status, count in sorted(stats['by_status'].items()):
                status_emoji = {
                    'PENDING': '⏳',
                    'ACKNOWLEDGED': '✅',
                    'RESOLVED': '✔️'
                }.get(status, '❓')
                status_text += f"{status_emoji} {status}: {count}\n"
            
            embed.add_field(
                name="By Status",
                value=status_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnCallManager(bot))
