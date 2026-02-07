"""
Mod Audit Log - Track all moderator actions to prevent abuse
Logs who did what, when, and allows mod action reversals
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from cogs.core.pst_timezone import get_now_pst

class ModAuditLog(commands.Cog):
    """Track and audit all moderator actions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/mod_audit.json"
        self.audit_log = []  # All mod actions
        self.mod_stats = {}  # Moderator statistics
        self.load_data()
    
    def load_data(self):
        """Load audit log data"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.audit_log = data.get('audit_log', [])
                    self.mod_stats = data.get('mod_stats', {})
            except:
                self.audit_log = []
                self.mod_stats = {}
    
    def save_data(self):
        """Save audit log data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'audit_log': self.audit_log[-5000:],  # Keep last 5000 actions
                'mod_stats': self.mod_stats
            }, f, indent=2)
    
    def log_action(self, action_type: str, moderator_id: int, target_user_id: int, 
                   guild_id: int, reason: str, details: Dict = None) -> str:
        """Log a moderator action"""
        action_id = f"ACT-{get_now_pst().strftime('%Y%m%d%H%M%S')}-{moderator_id}"
        
        action = {
            'id': action_id,
            'type': action_type,  # warn, mute, kick, ban, delete, etc.
            'moderator_id': moderator_id,
            'target_user_id': target_user_id,
            'guild_id': guild_id,
            'reason': reason,
            'timestamp': get_now_pst().isoformat(),
            'details': details or {},
            'reversed': False,
            'reversal_reason': None
        }
        
        self.audit_log.append(action)
        
        # Update mod stats
        mod_key = str(moderator_id)
        if mod_key not in self.mod_stats:
            self.mod_stats[mod_key] = {
                'total_actions': 0,
                'by_type': {},
                'reversals': 0,
                'first_action': get_now_pst().isoformat(),
                'last_action': None
            }
        
        self.mod_stats[mod_key]['total_actions'] += 1
        self.mod_stats[mod_key]['by_type'][action_type] = self.mod_stats[mod_key]['by_type'].get(action_type, 0) + 1
        self.mod_stats[mod_key]['last_action'] = get_now_pst().isoformat()
        
        self.save_data()
        return action_id
    
    def get_mod_actions(self, moderator_id: int, guild_id: int, 
                        limit: int = 50, action_type: str = None) -> List[Dict]:
        """Get all actions by a moderator"""
        actions = [
            a for a in self.audit_log 
            if a['moderator_id'] == moderator_id and a['guild_id'] == guild_id
        ]
        
        if action_type:
            actions = [a for a in actions if a['type'] == action_type]
        
        return actions[-limit:]
    
    def get_user_actions(self, target_user_id: int, guild_id: int, limit: int = 50) -> List[Dict]:
        """Get all actions taken against a user"""
        return [
            a for a in self.audit_log 
            if a['target_user_id'] == target_user_id and a['guild_id'] == guild_id
        ][-limit:]
    
    def reverse_action(self, action_id: str, reversal_reason: str) -> bool:
        """Mark an action as reversed"""
        for action in self.audit_log:
            if action['id'] == action_id:
                action['reversed'] = True
                action['reversal_reason'] = reversal_reason
                
                # Update mod stats
                mod_key = str(action['moderator_id'])
                if mod_key in self.mod_stats:
                    self.mod_stats[mod_key]['reversals'] += 1
                
                self.save_data()
                return True
        
        return False
    
    def check_mod_abuse(self, moderator_id: int, guild_id: int) -> Dict:
        """Check for potential mod abuse patterns"""
        actions = self.get_mod_actions(moderator_id, guild_id, limit=100)
        
        abuse_indicators = {
            'excessive_bans': 0,
            'excessive_kicks': 0,
            'high_reversal_rate': 0,
            'self_targeting': 0,
            'warnings': []
        }
        
        if len(actions) < 10:
            return abuse_indicators
        
        # Check ban rate
        bans = [a for a in actions if a['type'] == 'ban']
        if len(bans) / len(actions) > 0.5:
            abuse_indicators['warnings'].append("High ban rate (50%+ of actions)")
            abuse_indicators['excessive_bans'] = len(bans)
        
        # Check kick rate
        kicks = [a for a in actions if a['type'] == 'kick']
        if len(kicks) / len(actions) > 0.4:
            abuse_indicators['warnings'].append("High kick rate (40%+ of actions)")
            abuse_indicators['excessive_kicks'] = len(kicks)
        
        # Check reversal rate
        reversals = [a for a in actions if a.get('reversed')]
        if reversals and len(reversals) / len(actions) > 0.2:
            abuse_indicators['warnings'].append("High reversal rate (20%+) - actions often overturned")
            abuse_indicators['high_reversal_rate'] = len(reversals)
        
        return abuse_indicators
    
    @commands.command(name='modactions')
    @commands.has_permissions(manage_messages=True)
    async def view_mod_actions(self, ctx, moderator: Optional[discord.Member] = None):
        """View a moderator's action history"""
        target_mod = moderator or ctx.author
        
        actions = self.get_mod_actions(target_mod.id, ctx.guild.id, limit=20)
        
        if not actions:
            await ctx.send(f"No audit log entries for {target_mod.mention}")
            return
        
        embed = discord.Embed(
            title=f"🔍 Mod Actions - {target_mod.name}",
            description=f"Recent {len(actions)} actions",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for action in actions[-10:]:
            status = "✅" if not action.get('reversed') else "⚠️ Reversed"
            
            field_value = f"**Type:** {action['type'].upper()}\n"
            field_value += f"**Target:** <@{action['target_user_id']}>\n"
            field_value += f"**Reason:** {action['reason']}\n"
            field_value += f"**Status:** {status}"
            
            embed.add_field(
                name=f"{action['id']}",
                value=field_value,
                inline=False
            )
        
        # Check for abuse
        abuse = self.check_mod_abuse(target_mod.id, ctx.guild.id)
        if abuse['warnings']:
            embed.add_field(
                name="⚠️ Potential Issues",
                value="\n".join(abuse['warnings']),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='useractions')
    @commands.has_permissions(manage_messages=True)
    async def view_user_actions(self, ctx, user: discord.Member):
        """View all actions taken against a user"""
        actions = self.get_user_actions(user.id, ctx.guild.id)
        
        if not actions:
            await ctx.send(f"✅ No actions against {user.mention}")
            return
        
        embed = discord.Embed(
            title=f"📋 Actions Against {user.name}",
            description=f"{len(actions)} total action(s)",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        for action in actions[-10:]:
            mod = self.bot.get_user(action['moderator_id'])
            mod_name = mod.name if mod else f"User {action['moderator_id']}"
            
            status = "✅ Active" if not action.get('reversed') else "⚠️ Reversed"
            
            field_value = f"**Mod:** {mod_name}\n"
            field_value += f"**Type:** {action['type'].upper()}\n"
            field_value += f"**Reason:** {action['reason']}\n"
            field_value += f"**Status:** {status}"
            
            embed.add_field(
                name=f"{datetime.fromisoformat(action['timestamp']).strftime('%Y-%m-%d %H:%M')}",
                value=field_value,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='audit_modstats')
    @commands.has_permissions(manage_guild=True)
    async def mod_statistics(self, ctx):
        """View moderation team statistics"""
        embed = discord.Embed(
            title="📊 Moderation Team Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        if not self.mod_stats:
            await ctx.send("No moderation statistics yet")
            return
        
        # Sort by actions
        sorted_mods = sorted(
            self.mod_stats.items(),
            key=lambda x: x[1]['total_actions'],
            reverse=True
        )
        
        for mod_id_str, stats in sorted_mods[:10]:
            mod = self.bot.get_user(int(mod_id_str))
            mod_name = mod.name if mod else f"User {mod_id_str}"
            
            action_breakdown = " | ".join([
                f"{k}: {v}" for k, v in stats['by_type'].items()
            ])
            
            field_value = f"**Total Actions:** {stats['total_actions']}\n"
            field_value += f"**Reversals:** {stats['reversals']}\n"
            field_value += f"**Actions by Type:** {action_breakdown}"
            
            embed.add_field(
                name=f"👮 {mod_name}",
                value=field_value,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='auditlog')
    @commands.has_permissions(manage_guild=True)
    async def full_audit_log(self, ctx, hours: int = 24):
        """View full audit log for time period"""
        cutoff = get_now_pst() - timedelta(hours=hours)
        
        recent = [
            a for a in self.audit_log 
            if a['guild_id'] == ctx.guild.id and 
            datetime.fromisoformat(a['timestamp']) > cutoff
        ]
        
        if not recent:
            await ctx.send(f"No audit log entries in the last {hours} hours")
            return
        
        embed = discord.Embed(
            title=f"📋 Audit Log (Last {hours}h)",
            description=f"{len(recent)} action(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for action in recent[-20:]:
            mod = self.bot.get_user(action['moderator_id'])
            mod_name = mod.name if mod else f"Mod {action['moderator_id']}"
            
            status = "✅" if not action.get('reversed') else "⚠️ Reversed"
            
            field_value = f"**Mod:** {mod_name}\n**Type:** {action['type'].upper()}\n**Status:** {status}"
            
            embed.add_field(
                name=f"{datetime.fromisoformat(action['timestamp']).strftime('%m-%d %H:%M')}",
                value=field_value,
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModAuditLog(bot))
