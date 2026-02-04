"""
Enhanced Blacklist System - Comprehensive user, guild, IP, and domain blacklisting
with severity tiers, auto-actions, whitelist exceptions, and appeals system.
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class BlacklistTier(Enum):
    """Blacklist severity tiers"""
    CRITICAL = "critical"    # Instant ban, all platforms
    HIGH = "high"             # Timeout 24h, monitor closely
    MEDIUM = "medium"         # Warn, timeout 1h, escalate on repeat
    LOW = "low"               # Log, monitor, no immediate action
    SUSPICIOUS = "suspicious" # Watch list

class BlacklistItemType(Enum):
    """Types of items that can be blacklisted"""
    USER = "user"
    GUILD = "guild"
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    EMAIL = "email"
    WALLET_ADDRESS = "wallet_address"  # Crypto wallet
    PHONE = "phone"

class EnhancedBlacklistSystem(commands.Cog):
    """Advanced blacklist management with tiers and auto-actions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/blacklist_system.json'
        self.appeals_file = 'data/blacklist_appeals.json'
        
        # Blacklist storage
        self.blacklist = {}  # Item value -> blacklist data
        self.whitelist = {}  # Exceptions to blacklist
        self.appeals = []     # Appeal requests
        
        # Metrics
        self.blocked_actions = []
        self.false_positives = []
        
        self.load_blacklist_data()
    
    def load_blacklist_data(self):
        """Load blacklist and appeals from disk"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.blacklist = data.get('blacklist', {})
                    self.whitelist = data.get('whitelist', {})
                    self.blocked_actions = data.get('blocked_actions', [])
            except:
                self.init_default_data()
        else:
            self.init_default_data()
        
        if os.path.exists(self.appeals_file):
            try:
                with open(self.appeals_file, 'r') as f:
                    self.appeals = json.load(f)
            except:
                self.appeals = []
    
    def init_default_data(self):
        """Initialize default blacklist data"""
        self.blacklist = {}
        self.whitelist = {}
        self.blocked_actions = []
        self.save_blacklist_data()
    
    def save_blacklist_data(self):
        """Save blacklist to disk"""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'blacklist': self.blacklist,
                'whitelist': self.whitelist,
                'blocked_actions': self.blocked_actions[-500:]  # Keep last 500
            }, f, indent=2)
    
    def save_appeals(self):
        """Save appeals to disk"""
        with open(self.appeals_file, 'w') as f:
            json.dump(self.appeals, f, indent=2)
    
    async def add_to_blacklist(self, item_value: str, item_type: str, tier: str,
                               reason: str, added_by: str, duration_days: int = None) -> str:
        """Add item to blacklist"""
        
        bl_id = f"BL-{len(self.blacklist)}-{int(get_now_pst().timestamp())}"
        
        expires_at = None
        if duration_days:
            expires_at = (get_now_pst() + timedelta(days=duration_days)).isoformat()
        
        self.blacklist[item_value] = {
            'id': bl_id,
            'type': item_type,
            'value': item_value,
            'tier': tier,
            'reason': reason,
            'added_by': added_by,
            'added_at': get_now_pst().isoformat(),
            'expires_at': expires_at,
            'times_triggered': 0,
            'last_triggered': None,
            'actions_taken': [],
            'appeals': []
        }
        
        self.save_blacklist_data()
        
        # Emit signal
        await self.emit_blacklist_signal(item_value, item_type, tier, reason)
        
        return bl_id
    
    async def emit_blacklist_signal(self, item: str, item_type: str, tier: str, reason: str):
        """Emit signal when item is blacklisted"""
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity=tier.upper(),
            source='blacklist_system',
            data={
                'item': item,
                'item_type': item_type,
                'tier': tier,
                'reason': reason,
                'action': 'added_to_blacklist'
            },
            confidence=0.99,
            dedup_key=f'blacklist:{item}'
        ))
    
    async def check_blacklist(self, item_value: str) -> tuple[bool, Optional[Dict]]:
        """Check if item is blacklisted"""
        if item_value in self.whitelist:
            return False, None
        
        if item_value in self.blacklist:
            bl_data = self.blacklist[item_value]
            
            # Check expiration
            if bl_data.get('expires_at'):
                if datetime.fromisoformat(bl_data['expires_at']) < get_now_pst():
                    del self.blacklist[item_value]
                    self.save_blacklist_data()
                    return False, None
            
            # Update metrics
            bl_data['times_triggered'] += 1
            bl_data['last_triggered'] = get_now_pst().isoformat()
            self.save_blacklist_data()
            
            return True, bl_data
        
        return False, None
    
    async def execute_blacklist_action(self, member: discord.Member, bl_data: Dict):
        """Execute automatic action based on blacklist tier"""
        tier = bl_data.get('tier', 'medium')
        reason = f"Blacklist ({tier}): {bl_data['reason']}"
        
        try:
            if tier == BlacklistTier.CRITICAL.value:
                # Instant ban
                await member.guild.ban(member, reason=reason, delete_message_days=7)
                action = "banned"
                
            elif tier == BlacklistTier.HIGH.value:
                # Timeout 24 hours
                until = discord.utils.utcnow() + timedelta(hours=24)
                await member.timeout(until, reason=reason)
                action = "timeout_24h"
                
            elif tier == BlacklistTier.MEDIUM.value:
                # Timeout 1 hour
                until = discord.utils.utcnow() + timedelta(hours=1)
                await member.timeout(until, reason=reason)
                action = "timeout_1h"
                
            elif tier == BlacklistTier.LOW.value:
                # Send warning DM
                try:
                    await member.send(f"⚠️ **Warning**: Your activity matches our blacklist criteria. ({bl_data['reason']})")
                except:
                    pass
                action = "warned"
                
            elif tier == BlacklistTier.SUSPICIOUS.value:
                # Log only
                action = "logged"
            
            # Track action
            bl_data['actions_taken'].append({
                'timestamp': get_now_pst().isoformat(),
                'member': str(member),
                'guild': str(member.guild),
                'action': action
            })
            
            self.blocked_actions.append({
                'timestamp': get_now_pst().isoformat(),
                'user': str(member),
                'user_id': member.id,
                'action': action,
                'reason': reason
            })
            
            self.save_blacklist_data()
            
        except Exception as e:
            print(f"[Blacklist] Error executing action: {e}")
    
    def add_to_whitelist(self, item_value: str, reason: str) -> bool:
        """Add item to whitelist (exception to blacklist)"""
        self.whitelist[item_value] = {
            'value': item_value,
            'reason': reason,
            'added_at': get_now_pst().isoformat()
        }
        self.save_blacklist_data()
        return True
    
    async def request_appeal(self, user_id: int, item_value: str, reason: str) -> str:
        """Submit appeal for blacklist removal"""
        appeal_id = f"APPEAL-{len(self.appeals)}-{int(get_now_pst().timestamp())}"
        
        appeal = {
            'id': appeal_id,
            'user_id': user_id,
            'blacklist_item': item_value,
            'reason': reason,
            'submitted_at': get_now_pst().isoformat(),
            'status': 'pending',
            'response': None,
            'decided_by': None,
            'decided_at': None
        }
        
        self.appeals.append(appeal)
        self.save_appeals()
        
        return appeal_id
    
    def get_blacklist_stats(self) -> Dict:
        """Get blacklist statistics"""
        by_tier = {}
        by_type = {}
        
        for bl in self.blacklist.values():
            tier = bl.get('tier', 'unknown')
            item_type = bl.get('type', 'unknown')
            
            by_tier[tier] = by_tier.get(tier, 0) + 1
            by_type[item_type] = by_type.get(item_type, 0) + 1
        
        return {
            'total_blacklisted': len(self.blacklist),
            'total_whitelisted': len(self.whitelist),
            'by_tier': by_tier,
            'by_type': by_type,
            'total_actions_taken': len(self.blocked_actions),
            'pending_appeals': len([a for a in self.appeals if a['status'] == 'pending'])
        }
    
    @commands.command(name='addblacklist')
    @commands.has_permissions(ban_members=True)
    async def add_blacklist_cmd(self, ctx, item: str, item_type: str, tier: str, *, reason: str):
        """Add item to blacklist (admin only)"""
        
        valid_types = [t.value for t in BlacklistItemType]
        valid_tiers = [t.value for t in BlacklistTier]
        
        if item_type not in valid_types:
            await ctx.send(f"❌ Invalid type. Choose from: {', '.join(valid_types)}")
            return
        
        if tier not in valid_tiers:
            await ctx.send(f"❌ Invalid tier. Choose from: {', '.join(valid_tiers)}")
            return
        
        bl_id = await self.add_to_blacklist(item, item_type, tier, reason, str(ctx.author))
        
        embed = discord.Embed(
            title="✅ Added to Blacklist",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="ID", value=bl_id, inline=True)
        embed.add_field(name="Type", value=item_type, inline=True)
        embed.add_field(name="Tier", value=f"🔴 {tier.upper()}", inline=True)
        embed.add_field(name="Item", value=f"`{item}`", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Added By", value=ctx.author.mention, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='removeblacklist')
    @commands.has_permissions(ban_members=True)
    async def remove_blacklist_cmd(self, ctx, item: str):
        """Remove item from blacklist (admin only)"""
        
        if item in self.blacklist:
            del self.blacklist[item]
            self.save_blacklist_data()
            
            await ctx.send(f"✅ Removed `{item}` from blacklist")
        else:
            await ctx.send(f"❌ Item `{item}` not found in blacklist")
    
    @commands.command(name='whitelistitem')
    @commands.has_permissions(ban_members=True)
    async def whitelist_cmd(self, ctx, item: str, *, reason: str):
        """Add item to whitelist (exception to blacklist)"""
        
        self.add_to_whitelist(item, reason)
        
        await ctx.send(f"✅ Added `{item}` to whitelist\n**Reason:** {reason}")
    
    @commands.command(name='blackliststats')
    @commands.has_permissions(manage_guild=True)
    async def blacklist_stats_cmd(self, ctx):
        """View blacklist statistics"""
        
        stats = self.get_blacklist_stats()
        
        embed = discord.Embed(
            title="📊 Blacklist Statistics",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🔴 Total Blacklisted", value=stats['total_blacklisted'], inline=True)
        embed.add_field(name="✅ Total Whitelisted", value=stats['total_whitelisted'], inline=True)
        embed.add_field(name="⚠️ Actions Taken", value=stats['total_actions_taken'], inline=True)
        
        # By tier
        if stats['by_tier']:
            tier_text = "\n".join([f"• {t}: {c}" for t, c in stats['by_tier'].items()])
            embed.add_field(name="By Tier", value=tier_text, inline=False)
        
        # By type
        if stats['by_type']:
            type_text = "\n".join([f"• {t}: {c}" for t, c in stats['by_type'].items()])
            embed.add_field(name="By Type", value=type_text, inline=False)
        
        embed.add_field(name="⏳ Pending Appeals", value=stats['pending_appeals'], inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='searchblacklist')
    @commands.has_permissions(manage_guild=True)
    async def search_blacklist_cmd(self, ctx, query: str):
        """Search blacklist"""
        
        matches = [bl for bl in self.blacklist.values() if query.lower() in bl['value'].lower()]
        
        if not matches:
            await ctx.send("❌ No matches found")
            return
        
        embed = discord.Embed(
            title=f"🔍 Blacklist Search Results ({len(matches)})",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for bl in matches[:10]:
            embed.add_field(
                name=f"`{bl['value']}`",
                value=f"**Type:** {bl['type']}\n**Tier:** {bl['tier']}\n**Hits:** {bl['times_triggered']}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Check new member against blacklist"""
        user_id_str = str(member.id)
        
        is_blacklisted, bl_data = await self.check_blacklist(user_id_str)
        
        if is_blacklisted:
            await self.execute_blacklist_action(member, bl_data)
            
            embed = discord.Embed(
                title="🔴 Blacklisted Member Detected",
                description=f"{member.mention} matched blacklist criteria",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Member", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="Tier", value=bl_data['tier'].upper(), inline=True)
            embed.add_field(name="Reason", value=bl_data['reason'], inline=False)
            embed.add_field(name="Action", value=bl_data['actions_taken'][-1]['action'] if bl_data['actions_taken'] else "Logged", inline=False)
            
            # Try to send to mod-logs
            mod_channel = discord.utils.get(member.guild.text_channels, name="mod-logs")
            if mod_channel:
                try:
                    await mod_channel.send(embed=embed)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(EnhancedBlacklistSystem(bot))
