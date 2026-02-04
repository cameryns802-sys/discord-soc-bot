"""
Auto-Escalation System - Automatically escalate security threats based on severity,
confidence, and patterns. Routes to on-call responders and triggers auto-reactions.
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class AutoEscalationSystem(commands.Cog):
    """Automatic threat escalation with intelligent routing"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/auto_escalation.json'
        
        # Escalation rules
        self.escalation_rules = {}  # Threat type -> escalation config
        self.escalation_history = []
        self.on_call_responders = []
        
        self.load_escalation_data()
        self.check_escalations.start()
    
    def load_escalation_data(self):
        """Load escalation configuration"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.escalation_rules = data.get('rules', self._default_rules())
                    self.escalation_history = data.get('history', [])
                    self.on_call_responders = data.get('on_call', [])
            except:
                self.init_default_data()
        else:
            self.init_default_data()
    
    def _default_rules(self) -> Dict:
        """Define default escalation rules"""
        return {
            'threat_detected': {
                'low_confidence': {'threshold': 0.4, 'action': 'log', 'escalate_after': 5},
                'medium_confidence': {'threshold': 0.6, 'action': 'alert_mods', 'escalate_after': 3},
                'high_confidence': {'threshold': 0.8, 'action': 'timeout', 'escalate_after': 1},
                'critical_confidence': {'threshold': 0.95, 'action': 'ban', 'escalate_after': 0}
            },
            'raid_detected': {
                'users_per_minute': {'threshold': 10, 'action': 'enable_raidmode', 'escalate_after': 0},
                'spam_volume': {'threshold': 50, 'action': 'lockdown', 'escalate_after': 0}
            },
            'phishing_detected': {
                'urls': {'threshold': 3, 'action': 'alert_community', 'escalate_after': 1},
                'confidence': {'threshold': 0.9, 'action': 'ban_user', 'escalate_after': 0}
            },
            'malware_detected': {
                'file_indicators': {'threshold': 1, 'action': 'ban_user', 'escalate_after': 0},
                'confidence': {'threshold': 0.85, 'action': 'purge_messages', 'escalate_after': 0}
            }
        }
    
    def init_default_data(self):
        """Initialize escalation data"""
        self.escalation_rules = self._default_rules()
        self.escalation_history = []
        self.on_call_responders = []
        self.save_escalation_data()
    
    def save_escalation_data(self):
        """Save escalation data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'rules': self.escalation_rules,
                'history': self.escalation_history[-500:],
                'on_call': self.on_call_responders
            }, f, indent=2)
    
    async def evaluate_threat(self, signal: Signal) -> tuple[str, int]:
        """
        Evaluate threat severity and determine escalation level
        Returns: (action, escalation_level)
        escalation_level: 0=none, 1=log, 2=alert, 3=timeout, 4=ban, 5=lockdown
        """
        
        severity_map = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
        confidence_boost = signal.confidence * 10
        
        base_level = severity_map.get(signal.severity, 2)
        final_level = min(5, base_level + int(confidence_boost / 20))
        
        # Map level to action
        action_map = {
            1: 'log',
            2: 'log_and_watch',
            3: 'alert_moderators',
            4: 'timeout_user',
            5: 'ban_and_lockdown'
        }
        
        action = action_map.get(final_level, 'log')
        
        return action, final_level
    
    async def execute_escalation_action(self, guild: discord.Guild, action: str, 
                                       signal: Signal, member: discord.Member = None):
        """Execute escalation action"""
        
        escalation = {
            'timestamp': get_now_pst().isoformat(),
            'guild': str(guild),
            'guild_id': guild.id,
            'signal_type': str(signal.type),
            'severity': signal.severity,
            'confidence': signal.confidence,
            'action': action,
            'source': signal.source
        }
        
        try:
            if action == 'log':
                # Just log, no action
                print(f"[AutoEscalation] Logged: {signal.type} - Confidence: {signal.confidence:.0%}")
                escalation['status'] = 'logged'
                
            elif action == 'log_and_watch':
                # Log and add to watch list
                escalation['status'] = 'watching'
                print(f"[AutoEscalation] Watching: {signal.type}")
                
            elif action == 'alert_moderators':
                # Alert mod channel
                mod_channel = discord.utils.get(guild.text_channels, name="mod-logs")
                if mod_channel and member:
                    embed = discord.Embed(
                        title=f"⚠️ Auto-Escalation Alert: {signal.source}",
                        description=f"Potential threat from {member.mention}",
                        color=discord.Color.orange(),
                        timestamp=get_now_pst()
                    )
                    embed.add_field(name="Severity", value=signal.severity.upper(), inline=True)
                    embed.add_field(name="Confidence", value=f"{signal.confidence:.0%}", inline=True)
                    embed.add_field(name="Reason", value=signal.data.get('reason', 'Unknown'), inline=False)
                    
                    await mod_channel.send(embed=embed)
                    escalation['status'] = 'alert_sent'
                
            elif action == 'timeout_user':
                # Timeout user
                if member:
                    until = discord.utils.utcnow() + timedelta(hours=1)
                    await member.timeout(until, reason=f"Auto-escalation: {signal.source}")
                    escalation['status'] = 'user_timed_out'
                    escalation['target_user'] = str(member)
                
            elif action == 'ban_and_lockdown':
                # Ban user + lockdown
                if member:
                    try:
                        await member.ban(reason=f"Auto-escalation: {signal.source}", delete_message_days=7)
                        escalation['status'] = 'user_banned'
                        escalation['target_user'] = str(member)
                    except:
                        escalation['status'] = 'ban_failed'
                
                # Lockdown channels
                for channel in guild.text_channels[:5]:  # First 5 channels
                    try:
                        overwrite = channel.overwrites_for(guild.default_role)
                        overwrite.send_messages = False
                        await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    except:
                        pass
                
                escalation['status'] = 'lockdown_initiated'
                
                # Notify admins
                for admin in guild.members:
                    if admin.guild_permissions.administrator:
                        try:
                            await admin.send(f"🚨 **Server Lockdown Initiated** in {guild.name}\n"
                                           f"Reason: {signal.source}\n"
                                           f"Severity: {signal.severity}")
                        except:
                            pass
            
            # Route to on-call responder
            if signal.confidence > 0.8 and self.on_call_responders:
                responder_id = self.on_call_responders[0]
                try:
                    responder = await self.bot.fetch_user(responder_id)
                    await responder.send(
                        f"🚨 **Auto-Escalation Notification**\n"
                        f"Guild: {guild.name}\n"
                        f"Threat: {signal.source}\n"
                        f"Severity: {signal.severity}\n"
                        f"Confidence: {signal.confidence:.0%}\n"
                        f"Action: {action}"
                    )
                    escalation['notified_responder'] = str(responder)
                except:
                    pass
        
        except Exception as e:
            escalation['status'] = f'error: {str(e)}'
        
        # Record escalation
        self.escalation_history.append(escalation)
        self.save_escalation_data()
    
    @tasks.loop(seconds=30)
    async def check_escalations(self):
        """Periodically check for escalation triggers"""
        # Subscribe to signal bus
        signal_bus.subscribe('auto_escalation', self.on_threat_signal)
    
    async def on_threat_signal(self, signal: Signal):
        """Handle incoming threat signals"""
        
        # Evaluate threat
        action, level = await self.evaluate_threat(signal)
        
        # Find guild from signal data
        guild_id = signal.data.get('guild_id')
        user_id = signal.data.get('user_id')
        
        if guild_id:
            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                
                member = None
                if user_id:
                    try:
                        member = await guild.fetch_member(user_id)
                    except:
                        pass
                
                # Execute escalation
                await self.execute_escalation_action(guild, action, signal, member)
                
                # Emit escalation signal
                await signal_bus.emit(Signal(
                    signal_type=SignalType.ESCALATION_REQUIRED,
                    severity=signal.severity,
                    source='auto_escalation',
                    data={
                        'original_signal': str(signal.type),
                        'escalation_action': action,
                        'escalation_level': level,
                        'guild_id': guild_id
                    },
                    confidence=signal.confidence,
                    dedup_key=f'escalation:{guild_id}:{signal.source}'
                ))
            
            except Exception as e:
                print(f"[AutoEscalation] Error: {e}")
    
    @check_escalations.before_loop
    async def before_check_escalations(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='setescalationrule')
    @commands.is_owner()
    async def set_escalation_rule(self, ctx, threat_type: str, confidence_level: str, action: str):
        """Configure escalation rule (owner only)"""
        
        valid_actions = ['log', 'alert_mods', 'timeout', 'ban', 'lockdown']
        
        if action not in valid_actions:
            await ctx.send(f"❌ Invalid action. Choose from: {', '.join(valid_actions)}")
            return
        
        if threat_type not in self.escalation_rules:
            self.escalation_rules[threat_type] = {}
        
        self.escalation_rules[threat_type][confidence_level] = {
            'action': action,
            'configured_at': get_now_pst().isoformat()
        }
        
        self.save_escalation_data()
        
        await ctx.send(f"✅ Updated escalation rule: {threat_type} @ {confidence_level} → {action}")
    
    @commands.command(name='escalationhistory')
    @commands.has_permissions(manage_guild=True)
    async def escalation_history(self, ctx, limit: int = 10):
        """View escalation history"""
        
        recent = self.escalation_history[-limit:]
        
        if not recent:
            await ctx.send("✅ No escalations recorded")
            return
        
        embed = discord.Embed(
            title=f"📊 Escalation History (Last {len(recent)})",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for esc in reversed(recent[:5]):
            embed.add_field(
                name=f"{esc['source']} → {esc['action']}",
                value=f"**Severity:** {esc['severity']}\n**Confidence:** {esc['confidence']:.0%}\n**Status:** {esc.get('status', 'unknown')}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='setonc')
    @commands.is_owner()
    async def set_on_call(self, ctx, member: discord.Member):
        """Set on-call responder (owner only)"""
        
        if member.id not in self.on_call_responders:
            self.on_call_responders.append(member.id)
            self.save_escalation_data()
            
            await ctx.send(f"✅ {member.mention} is now on-call for escalations")
        else:
            await ctx.send(f"⚠️ {member.mention} is already on-call")
    
    @commands.command(name='escalationstats')
    @commands.has_permissions(manage_guild=True)
    async def escalation_stats(self, ctx):
        """View escalation statistics"""
        
        actions_taken = {}
        severities = {}
        
        for esc in self.escalation_history:
            action = esc.get('action', 'unknown')
            severity = esc.get('severity', 'unknown')
            
            actions_taken[action] = actions_taken.get(action, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        embed = discord.Embed(
            title="📊 Escalation Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Escalations", value=len(self.escalation_history), inline=True)
        embed.add_field(name="On-Call Responders", value=len(self.on_call_responders), inline=True)
        
        if actions_taken:
            actions_text = "\n".join([f"• {a}: {c}" for a, c in sorted(actions_taken.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(name="Actions Taken", value=actions_text, inline=False)
        
        if severities:
            sev_text = "\n".join([f"• {s}: {c}" for s, c in severities.items()])
            embed.add_field(name="By Severity", value=sev_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoEscalationSystem(bot))
