"""
Enhanced AutoMod System - Syncs with Discord native automod
Coordinates between bot automod and Discord's native automod rules
Centralized violation tracking and enforcement
"""
import discord
from discord.ext import commands
from cogs.core.signal_bus import signal_bus, Signal, SignalType
import json
import os
from datetime import datetime, timedelta
import re

CAPS_THRESHOLD = 0.7  # 70% caps
EMOJI_SPAM_THRESHOLD = 5
MENTION_SPAM_THRESHOLD = 5
LINK_REGEX = r"https?://\S+"

class AutoModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.violations_file = 'data/automod_violations.json'
        self.rules_file = 'data/automod_rules.json'
        self.discord_automod_cache = {}
        self.load_data()
    
    def load_data(self):
        """Load violation and rule data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.violations_file):
            with open(self.violations_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.rules_file):
            with open(self.rules_file, 'w') as f:
                json.dump({}, f)
    
    def get_violations(self, guild_id):
        """Get violations for guild"""
        with open(self.violations_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_violations(self, guild_id, violations):
        """Save violations"""
        with open(self.violations_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = violations
        with open(self.violations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_rules(self, guild_id):
        """Get automod rules for guild"""
        with open(self.rules_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_rules(self, guild_id, rules):
        """Save rules"""
        with open(self.rules_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = rules
        with open(self.rules_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def sync_discord_automod(self, guild):
        """Sync with Discord's native automod rules"""
        try:
            # Fetch all automod rules from guild
            automod_rules = await guild.fetch_automod_rules()
            
            synced_count = 0
            for rule in automod_rules:
                self.discord_automod_cache[f"{guild.id}:{rule.id}"] = {
                    'id': rule.id,
                    'name': rule.name,
                    'type': str(rule.trigger_type),
                    'enabled': rule.enabled,
                    'actions': [str(a) for a in rule.actions],
                    'synced_at': datetime.utcnow().isoformat()
                }
                synced_count += 1
            
            return synced_count
        except Exception as e:
            print(f"[AutoMod] Error syncing Discord automod: {e}")
            return 0
    
    async def emit_violation(self, msg: str, severity: str = "medium", author=None, channel=None):
        """Emit policy violation signal"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.POLICY_VIOLATION,
            severity=severity,
            source='automod',
            data={'violation': msg, 'author': str(author), 'channel': str(channel)},
            confidence=0.90,
            dedup_key=f'automod:{msg}:{author}'
        ))
    
    def log_violation(self, guild_id, user_id, violation_type, severity, details):
        """Log violation for tracking"""
        violations = self.get_violations(guild_id)
        
        violation = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'type': violation_type,
            'severity': severity,
            'details': details
        }
        
        violations.append(violation)
        
        # Keep only last 500 per guild
        violations = violations[-500:]
        self.save_violations(guild_id, violations)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Sync Discord automod when bot is ready"""
        for guild in self.bot.guilds:
            synced = await self.sync_discord_automod(guild)
            if synced > 0:
                print(f"[AutoMod] Synced {synced} automod rules from {guild.name}")
    
    @commands.Cog.listener()
    async def on_automod_action_execution(self, execution: discord.AutoModAction):
        """Handle Discord automod action execution"""
        guild = execution.guild
        
        violation_data = {
            'action': str(execution.action.type),
            'rule_id': execution.rule_id,
            'rule_name': execution.rule.name if execution.rule else 'Unknown',
            'user': str(execution.user),
            'user_id': execution.user.id,
            'channel': str(execution.channel) if execution.channel else 'Unknown',
            'message_id': execution.message_id
        }
        
        # Determine severity
        severity = "high" if execution.action.type in [discord.AutoModActionType.block_member_interaction, discord.AutoModActionType.send_alert_message] else "medium"
        
        # Log violation
        self.log_violation(
            guild.id,
            execution.user.id,
            f"discord_automod:{execution.rule.name}",
            severity,
            violation_data
        )
        
        # Emit signal
        await self.emit_violation(
            f"discord_automod_triggered: {execution.rule.name}",
            severity,
            execution.user,
            execution.channel
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        guild = message.guild
        if not guild:
            return
        
        # Check caps lock spam
        if len(message.content) > 10:
            caps_count = sum(1 for c in message.content if c.isupper())
            caps_ratio = caps_count / len(message.content)
            if caps_ratio > CAPS_THRESHOLD:
                self.log_violation(
                    guild.id,
                    message.author.id,
                    'excessive_caps_lock',
                    'low',
                    {'message': message.content[:100]}
                )
                await self.emit_violation("excessive_caps_lock", "low", message.author, message.channel)
        
        # Check emoji spam
        emoji_count = sum(message.content.count(e) for e in ["🔥", "⚠️", "❌", "💀", "😂"])
        if emoji_count > EMOJI_SPAM_THRESHOLD:
            self.log_violation(
                guild.id,
                message.author.id,
                'emoji_spam',
                'low',
                {'emoji_count': emoji_count}
            )
            await self.emit_violation("emoji_spam", "low", message.author, message.channel)
        
        # Check mention spam
        mention_count = len(message.mentions)
        if mention_count > MENTION_SPAM_THRESHOLD:
            self.log_violation(
                guild.id,
                message.author.id,
                'mention_spam',
                'medium',
                {'mention_count': mention_count}
            )
            await self.emit_violation("mention_spam", "medium", message.author, message.channel)
        
        # Check for excessive links
        link_count = len(re.findall(LINK_REGEX, message.content))
        if link_count > 3:
            self.log_violation(
                guild.id,
                message.author.id,
                'link_spam',
                'medium',
                {'link_count': link_count}
            )
            await self.emit_violation("link_spam", "medium", message.author, message.channel)
    
    @commands.command(name='automodrules')
    async def show_automod_rules_cmd(self, ctx):
        """Show synced Discord automod rules"""
        guild = ctx.guild
        
        # Sync latest rules
        synced = await self.sync_discord_automod(guild)
        
        # Get all rules for this guild
        rules = [r for k, r in self.discord_automod_cache.items() if k.startswith(f"{guild.id}:")]
        
        if not rules:
            await ctx.send("❌ No automod rules configured.")
            return
        
        embed = discord.Embed(
            title="🤖 Discord AutoMod Rules",
            description=f"{len(rules)} rule(s) active",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for rule in rules[:10]:
            status = "🟢 Active" if rule['enabled'] else "🔴 Inactive"
            embed.add_field(
                name=f"{rule['name']} ({rule['type']})",
                value=f"{status} | ID: {rule['id']}",
                inline=False
            )
        
        embed.set_footer(text=f"Last synced: {rules[0]['synced_at'] if rules else 'Never'}")
        await ctx.send(embed=embed)
    
    @commands.command(name='automodviolations')
    async def show_violations_cmd(self, ctx, days: int = 7):
        """Show recent automod violations"""
        guild = ctx.guild
        violations = self.get_violations(guild.id)
        
        if not violations:
            await ctx.send("✅ No violations recorded.")
            return
        
        # Filter by date
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [v for v in violations if v['timestamp'] > cutoff]
        
        # Group by type
        by_type = {}
        for v in recent:
            vtype = v['type']
            by_type[vtype] = by_type.get(vtype, 0) + 1
        
        embed = discord.Embed(
            title=f"⚠️ Violations (Last {days} Days)",
            description=f"{len(recent)} violation(s)",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Summary", value="━" * 25, inline=False)
        for vtype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=vtype.title(), value=f"📊 {count}", inline=True)
        
        # Top violators
        user_counts = {}
        for v in recent:
            uid = v['user_id']
            user_counts[uid] = user_counts.get(uid, 0) + 1
        
        embed.add_field(name="Top Violators", value="━" * 25, inline=False)
        for uid, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            try:
                user = await self.bot.fetch_user(uid)
                embed.add_field(name=f"{user}", value=f"⚠️ {count} violations", inline=False)
            except:
                pass
        
        await ctx.send(embed=embed)
    
    @commands.command(name='automodsync')
    async def sync_automod_cmd(self, ctx):
        """Manually sync Discord automod rules"""
        guild = ctx.guild
        
        synced = await self.sync_discord_automod(guild)
        
        embed = discord.Embed(
            title="✅ AutoMod Rules Synced",
            description=f"Synchronized {synced} rule(s)",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Status", value="🔄 Bot and Discord automod are in sync", inline=False)
        embed.add_field(name="Rules Cached", value=f"📋 {synced}", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoModCog(bot))
