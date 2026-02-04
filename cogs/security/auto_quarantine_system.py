"""
Auto-Quarantine System - Automatically isolate threats, malicious users, and content
in designated quarantine areas with evidence preservation and forensic analysis.
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class QuarantineReason:
    MALWARE = "malware"
    PHISHING = "phishing"
    HARASSMENT = "harassment"
    SPAM = "spam"
    RAID = "raid"
    EXPLOIT = "exploit"
    MANUAL = "manual_quarantine"

class AutoQuarantineSystem(commands.Cog):
    """Automatic threat quarantine with forensic preservation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/auto_quarantine.json'
        
        self.quarantine_entries = {}  # User/guild ID -> quarantine data
        self.quarantine_channels = {}  # Guild ID -> quarantine channel ID
        self.evidence_vault = {}  # Evidence ID -> evidence data
        
        self.load_quarantine_data()
        self.setup_signal_listeners()
    
    def load_quarantine_data(self):
        """Load quarantine configuration"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.quarantine_entries = data.get('entries', {})
                    self.quarantine_channels = data.get('channels', {})
                    self.evidence_vault = data.get('evidence', {})
            except:
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        """Initialize quarantine data"""
        self.quarantine_entries = {}
        self.quarantine_channels = {}
        self.evidence_vault = {}
        self.save_quarantine_data()
    
    def save_quarantine_data(self):
        """Save quarantine data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'entries': self.quarantine_entries,
                'channels': self.quarantine_channels,
                'evidence': self.evidence_vault
            }, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus for auto-quarantine triggers"""
        signal_bus.subscribe(SignalType.THREAT_DETECTED, self.on_threat_signal)
    
    async def on_threat_signal(self, signal: Signal):
        """Auto-quarantine on high-confidence threats"""
        
        # Only auto-quarantine critical threats
        if signal.confidence < 0.85 or signal.severity not in ['critical', 'high']:
            return
        
        # Get threat info
        data = signal.data or {}
        user_id = data.get('user_id')
        guild_id = data.get('guild_id')
        
        if user_id and guild_id:
            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                
                member = await guild.fetch_member(user_id)
                if member:
                    await self.quarantine_user(guild, member, 
                                             QuarantineReason.MALWARE, 
                                             signal.source, signal)
            except:
                pass
    
    async def quarantine_user(self, guild: discord.Guild, member: discord.Member, 
                             reason: str, threat_source: str, signal: Signal = None,
                             auto: bool = True) -> bool:
        """Quarantine a user by moving them to isolation role"""
        
        entry_id = f"{guild.id}:{member.id}"
        
        # Create quarantine entry
        quarantine = {
            'id': entry_id,
            'guild_id': guild.id,
            'user_id': member.id,
            'username': str(member),
            'reason': reason,
            'threat_source': threat_source,
            'quarantined_at': get_now_pst().isoformat(),
            'auto_quarantine': auto,
            'status': 'active',
            'evidence': [],
            'notes': []
        }
        
        try:
            # Get or create quarantine role
            quarantine_role = discord.utils.get(guild.roles, name="Quarantine")
            if not quarantine_role:
                quarantine_role = await guild.create_role(
                    name="Quarantine",
                    color=discord.Color.red(),
                    reason="Auto-created for threat quarantine"
                )
            
            # Create quarantine channel if needed
            if guild.id not in self.quarantine_channels:
                # Create private quarantine channel
                overwrite = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    quarantine_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)
                }
                
                quar_channel = await guild.create_text_channel(
                    name="quarantine-isolation",
                    overwrites=overwrite,
                    reason="Quarantine evidence channel"
                )
                
                self.quarantine_channels[guild.id] = quar_channel.id
            
            # Remove all roles and add quarantine role
            try:
                await member.edit(roles=[quarantine_role], reason=f"Quarantine: {reason}")
            except discord.Forbidden:
                return False
            
            # Store entry
            self.quarantine_entries[entry_id] = quarantine
            
            # Preserve evidence
            if signal:
                evidence_id = await self.preserve_evidence(entry_id, signal)
                quarantine['evidence'].append(evidence_id)
            
            self.save_quarantine_data()
            
            # Log to quarantine channel
            quar_channel_id = self.quarantine_channels.get(guild.id)
            if quar_channel_id:
                quar_channel = guild.get_channel(quar_channel_id)
                if quar_channel:
                    embed = discord.Embed(
                        title="🚫 User Quarantined",
                        description=f"User {member.mention} has been quarantined",
                        color=discord.Color.red(),
                        timestamp=get_now_pst()
                    )
                    
                    embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
                    embed.add_field(name="Reason", value=reason, inline=True)
                    embed.add_field(name="Threat Source", value=threat_source, inline=True)
                    embed.add_field(name="Auto-Quarantine", value="✅ Yes" if auto else "❌ Manual", inline=True)
                    
                    if signal:
                        embed.add_field(name="Threat Confidence", value=f"{signal.confidence:.0%}", inline=True)
                    
                    await quar_channel.send(embed=embed)
            
            # Notify member
            try:
                notify_embed = discord.Embed(
                    title="⚠️ Account Quarantined",
                    description="Your account has been quarantined due to detected threats",
                    color=discord.Color.red(),
                    timestamp=get_now_pst()
                )
                
                notify_embed.add_field(name="Reason", value=reason, inline=False)
                notify_embed.add_field(name="Server", value=guild.name, inline=True)
                notify_embed.add_field(name="Status", value="Under Review", inline=True)
                notify_embed.add_field(name="Appeal", value="Contact server administrators", inline=False)
                
                await member.send(embed=notify_embed)
            except:
                pass
            
            # Emit signal
            await signal_bus.emit(Signal(
                signal_type=SignalType.POLICY_VIOLATION,
                severity='high',
                source='auto_quarantine',
                data={
                    'action': 'user_quarantined',
                    'guild_id': guild.id,
                    'user_id': member.id,
                    'reason': reason,
                    'auto': auto
                },
                confidence=0.95,
                dedup_key=f'quarantine:{entry_id}'
            ))
            
            return True
            
        except Exception as e:
            print(f"[AutoQuarantine] Error quarantining user: {e}")
            return False
    
    async def preserve_evidence(self, entry_id: str, signal: Signal) -> str:
        """Preserve threat evidence for forensic analysis"""
        
        evidence_id = f"EVD-{get_now_pst().strftime('%Y%m%d%H%M%S')}"
        
        evidence = {
            'id': evidence_id,
            'quarantine_id': entry_id,
            'preserved_at': get_now_pst().isoformat(),
            'signal_type': str(signal.type),
            'signal_source': signal.source,
            'severity': signal.severity,
            'confidence': signal.confidence,
            'data': signal.data,
            'chain_of_custody': []
        }
        
        self.evidence_vault[evidence_id] = evidence
        self.save_quarantine_data()
        
        return evidence_id
    
    async def unquarantine_user(self, guild: discord.Guild, member: discord.Member,
                               reason: str = "Appeal approved"):
        """Release user from quarantine"""
        
        entry_id = f"{guild.id}:{member.id}"
        
        if entry_id not in self.quarantine_entries:
            return False
        
        try:
            quarantine = self.quarantine_entries[entry_id]
            quarantine['status'] = 'released'
            quarantine['released_at'] = get_now_pst().isoformat()
            quarantine['release_reason'] = reason
            
            # Restore member
            await member.edit(roles=[], reason=f"Quarantine lifted: {reason}")
            
            # Restore some default roles if needed
            default_role = discord.utils.get(guild.roles, name="Member")
            if default_role:
                await member.add_roles(default_role)
            
            self.save_quarantine_data()
            
            # Notify member
            try:
                await member.send(
                    f"✅ Your quarantine in **{guild.name}** has been lifted.\n"
                    f"Reason: {reason}"
                )
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"[AutoQuarantine] Error unquarantining user: {e}")
            return False
    
    @commands.command(name='quarantineuser')
    @commands.has_permissions(manage_members=True)
    async def quarantine_user_cmd(self, ctx, member: discord.Member, *, reason: str = "Policy violation"):
        """Manually quarantine a user"""
        
        success = await self.quarantine_user(ctx.guild, member, reason, ctx.command.name, auto=False)
        
        if success:
            embed = discord.Embed(
                title="✅ User Quarantined",
                description=f"{member.mention} has been quarantined",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="User", value=str(member), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Status", value="🚫 Quarantined", inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to quarantine user")
    
    @commands.command(name='unquarantineuser')
    @commands.has_permissions(manage_members=True)
    async def unquarantine_user_cmd(self, ctx, member: discord.Member, *, reason: str = "Appeal approved"):
        """Release user from quarantine"""
        
        success = await self.unquarantine_user(ctx.guild, member, reason)
        
        if success:
            embed = discord.Embed(
                title="✅ Quarantine Lifted",
                description=f"{member.mention} has been released from quarantine",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="User", value=str(member), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Status", value="🟢 Released", inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ User not in quarantine or failed to release")
    
    @commands.command(name='quarantinestatus')
    @commands.has_permissions(manage_guild=True)
    async def quarantine_status(self, ctx, member: discord.Member = None):
        """View quarantine status"""
        
        if member:
            entry_id = f"{ctx.guild.id}:{member.id}"
            entry = self.quarantine_entries.get(entry_id)
            
            if not entry:
                await ctx.send(f"✅ {member.mention} is not quarantined")
                return
            
            embed = discord.Embed(
                title="🚫 Quarantine Details",
                description=f"User: {member.mention}",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Status", value=entry['status'].upper(), inline=True)
            embed.add_field(name="Reason", value=entry['reason'], inline=True)
            embed.add_field(name="Quarantined Since", value=entry['quarantined_at'], inline=False)
            embed.add_field(name="Evidence Count", value=len(entry['evidence']), inline=True)
            
            await ctx.send(embed=embed)
        
        else:
            # Show all quarantined users in guild
            guild_quarantines = [
                e for e in self.quarantine_entries.values()
                if e['guild_id'] == ctx.guild.id and e['status'] == 'active'
            ]
            
            if not guild_quarantines:
                await ctx.send("✅ No users currently quarantined")
                return
            
            embed = discord.Embed(
                title="🚫 Active Quarantines",
                description=f"{len(guild_quarantines)} user(s) quarantined",
                color=discord.Color.red(),
                timestamp=get_now_pst()
            )
            
            for entry in guild_quarantines[:10]:
                embed.add_field(
                    name=entry['username'],
                    value=f"**Reason:** {entry['reason']}\n**Since:** <t:{int(datetime.fromisoformat(entry['quarantined_at']).timestamp())}:R>",
                    inline=False
                )
            
            await ctx.send(embed=embed)
    
    @commands.command(name='quarantineevidence')
    @commands.has_permissions(manage_guild=True)
    async def view_evidence(self, ctx, member: discord.Member):
        """View evidence against quarantined user"""
        
        entry_id = f"{ctx.guild.id}:{member.id}"
        entry = self.quarantine_entries.get(entry_id)
        
        if not entry:
            await ctx.send("❌ User not quarantined")
            return
        
        embed = discord.Embed(
            title=f"🔍 Evidence for {member}",
            description=f"{len(entry['evidence'])} evidence item(s)",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for evidence_id in entry['evidence'][:5]:
            evidence = self.evidence_vault.get(evidence_id)
            if evidence:
                embed.add_field(
                    name=f"Evidence {evidence['id']}",
                    value=f"**Type:** {evidence['signal_type']}\n**Source:** {evidence['signal_source']}\n**Confidence:** {evidence['confidence']:.0%}",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='quarantinestats')
    @commands.has_permissions(manage_guild=True)
    async def quarantine_stats(self, ctx):
        """View quarantine statistics"""
        
        guild_entries = [
            e for e in self.quarantine_entries.values()
            if e['guild_id'] == ctx.guild.id
        ]
        
        active = sum(1 for e in guild_entries if e['status'] == 'active')
        released = sum(1 for e in guild_entries if e['status'] == 'released')
        
        embed = discord.Embed(
            title="📊 Quarantine Statistics",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Active Quarantines", value=active, inline=True)
        embed.add_field(name="Released Users", value=released, inline=True)
        embed.add_field(name="Total Evidence", value=len(self.evidence_vault), inline=True)
        
        # Group by reason
        by_reason = {}
        for entry in guild_entries:
            reason = entry['reason']
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        if by_reason:
            reason_text = "\n".join([f"• {r}: {c}" for r, c in sorted(by_reason.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(name="By Reason", value=reason_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoQuarantineSystem(bot))
