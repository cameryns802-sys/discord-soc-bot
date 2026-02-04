"""
Custom Automod Rules - Create custom mod rules beyond Discord's built-in
Supports keywords, regex patterns, users, domains with custom actions
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from cogs.core.pst_timezone import get_now_pst

class CustomAutomod(commands.Cog):
    """Create and manage custom automod rules"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/custom_automod_rules.json"
        self.rules = {}  # guild_id -> [rules]
        self.violations = []  # Track violations
        self.load_data()
    
    def load_data(self):
        """Load custom rules"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.rules = data.get('rules', {})
                    self.violations = data.get('violations', [])
            except:
                self.rules = {}
                self.violations = []
    
    def save_data(self):
        """Save custom rules"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'rules': self.rules,
                'violations': self.violations[-10000:]  # Keep last 10k
            }, f, indent=2)
    
    def add_rule(self, guild_id: int, rule_type: str, pattern: str, 
                 action: str, duration_minutes: Optional[int] = None) -> str:
        """Add custom rule"""
        guild_key = str(guild_id)
        
        if guild_key not in self.rules:
            self.rules[guild_key] = []
        
        rule_id = f"RULE-{get_now_pst().strftime('%Y%m%d%H%M%S')}"
        
        rule = {
            'id': rule_id,
            'type': rule_type,  # keyword, regex, domain, user
            'pattern': pattern,
            'action': action,  # warn, mute, kick, ban, delete
            'duration_minutes': duration_minutes,
            'enabled': True,
            'created_at': get_now_pst().isoformat(),
            'violations_count': 0
        }
        
        self.rules[guild_key].append(rule)
        self.save_data()
        return rule_id
    
    def check_message(self, guild_id: int, message: discord.Message) -> Optional[Dict]:
        """Check if message violates any rules"""
        guild_key = str(guild_id)
        
        if guild_key not in self.rules:
            return None
        
        for rule in self.rules[guild_key]:
            if not rule['enabled']:
                continue
            
            triggered = False
            
            if rule['type'] == 'keyword':
                # Case-insensitive keyword match
                if rule['pattern'].lower() in message.content.lower():
                    triggered = True
            
            elif rule['type'] == 'regex':
                # Regex pattern match
                try:
                    if re.search(rule['pattern'], message.content, re.IGNORECASE):
                        triggered = True
                except:
                    pass
            
            elif rule['type'] == 'domain':
                # Check if domain is in message
                if rule['pattern'] in message.content:
                    triggered = True
            
            elif rule['type'] == 'user':
                # Check if user is mentioned
                if int(rule['pattern']) in [m.id for m in message.mentions]:
                    triggered = True
            
            if triggered:
                rule['violations_count'] += 1
                return rule
        
        return None
    
    def log_violation(self, guild_id: int, rule_id: str, user_id: int, 
                      message_id: int, action_taken: str):
        """Log rule violation"""
        violation = {
            'timestamp': get_now_pst().isoformat(),
            'guild_id': guild_id,
            'rule_id': rule_id,
            'user_id': user_id,
            'message_id': message_id,
            'action_taken': action_taken
        }
        
        self.violations.append(violation)
        self.save_data()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check messages against custom rules"""
        if message.author.bot or not message.guild:
            return
        
        # Check rules
        rule = self.check_message(message.guild.id, message)
        
        if not rule:
            return
        
        # Take action based on rule
        action = rule['action']
        
        if action == 'delete':
            try:
                await message.delete()
                self.log_violation(message.guild.id, rule['id'], message.author.id, 
                                  message.id, 'deleted')
                
                # Notify mods
                embed = discord.Embed(
                    title="🚫 Custom Automod Triggered",
                    description=f"Rule: {rule['pattern']}\nAction: Deleted",
                    color=discord.Color.red()
                )
                embed.add_field(name="User", value=message.author.mention, inline=True)
                embed.add_field(name="Message", value=message.content[:100], inline=True)
                
                # Send to mod channel if exists
                mod_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if mod_channel:
                    await mod_channel.send(embed=embed, delete_after=60)
            except:
                pass
        
        elif action == 'warn':
            # Would integrate with infraction system
            self.log_violation(message.guild.id, rule['id'], message.author.id, 
                              message.id, 'warned')
        
        elif action == 'mute':
            self.log_violation(message.guild.id, rule['id'], message.author.id, 
                              message.id, 'muted')
    
    @commands.command(name='addrule')
    @commands.has_permissions(manage_guild=True)
    async def add_custom_rule(self, ctx, rule_type: str, pattern: str, 
                             action: str, duration: Optional[int] = None):
        """Add custom automod rule
        
        Types: keyword, regex, domain, user
        Actions: warn, mute, kick, ban, delete
        """
        if rule_type not in ['keyword', 'regex', 'domain', 'user']:
            await ctx.send("❌ Invalid rule type. Use: keyword, regex, domain, user")
            return
        
        if action not in ['warn', 'mute', 'kick', 'ban', 'delete']:
            await ctx.send("❌ Invalid action. Use: warn, mute, kick, ban, delete")
            return
        
        rule_id = self.add_rule(ctx.guild.id, rule_type, pattern, action, duration)
        
        embed = discord.Embed(
            title="✅ Custom Rule Added",
            description=f"Rule ID: {rule_id}",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Type", value=rule_type.upper(), inline=True)
        embed.add_field(name="Pattern", value=f"`{pattern}`", inline=True)
        embed.add_field(name="Action", value=action.upper(), inline=True)
        
        if duration:
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rules')
    @commands.has_permissions(manage_guild=True)
    async def list_rules(self, ctx):
        """List all custom rules"""
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.rules or not self.rules[guild_key]:
            await ctx.send("No custom rules configured")
            return
        
        embed = discord.Embed(
            title="📋 Custom Automod Rules",
            description=f"{len(self.rules[guild_key])} rule(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for rule in self.rules[guild_key]:
            status = "✅ Active" if rule['enabled'] else "❌ Disabled"
            
            field_value = f"**Type:** {rule['type'].upper()}\n"
            field_value += f"**Pattern:** `{rule['pattern']}`\n"
            field_value += f"**Action:** {rule['action'].upper()}\n"
            field_value += f"**Status:** {status}\n"
            field_value += f"**Violations:** {rule['violations_count']}"
            
            embed.add_field(
                name=rule['id'],
                value=field_value,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='deleterule')
    @commands.has_permissions(manage_guild=True)
    async def delete_rule(self, ctx, rule_id: str):
        """Delete a custom rule"""
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.rules:
            await ctx.send("No rules to delete")
            return
        
        for i, rule in enumerate(self.rules[guild_key]):
            if rule['id'] == rule_id:
                deleted_rule = self.rules[guild_key].pop(i)
                self.save_data()
                
                embed = discord.Embed(
                    title="🗑️ Rule Deleted",
                    description=f"Rule {rule_id} has been removed",
                    color=discord.Color.orange()
                )
                
                await ctx.send(embed=embed)
                return
        
        await ctx.send(f"❌ Rule {rule_id} not found")
    
    @commands.command(name='ruleviolations')
    @commands.has_permissions(manage_guild=True)
    async def rule_violations(self, ctx, rule_id: Optional[str] = None, hours: int = 24):
        """View rule violations"""
        cutoff = get_now_pst() - timedelta(hours=hours)
        
        violations = [
            v for v in self.violations 
            if v['guild_id'] == ctx.guild.id and 
            datetime.fromisoformat(v['timestamp']) > cutoff
        ]
        
        if rule_id:
            violations = [v for v in violations if v['rule_id'] == rule_id]
        
        if not violations:
            await ctx.send(f"No violations in the last {hours} hours")
            return
        
        embed = discord.Embed(
            title="📊 Rule Violations",
            description=f"{len(violations)} violation(s) in last {hours}h",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Group by rule
        by_rule = {}
        for v in violations:
            rule_id = v['rule_id']
            by_rule[rule_id] = by_rule.get(rule_id, 0) + 1
        
        for rule_id, count in sorted(by_rule.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=rule_id, value=f"{count} violation(s)", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomAutomod(bot))
