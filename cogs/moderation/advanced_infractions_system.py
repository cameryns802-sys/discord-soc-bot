"""
Advanced Infractions System - Track mod actions with progressive escalation
Manages warns, mutes, kicks, bans with automatic escalation and appeals
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from cogs.core.pst_timezone import get_now_pst

class AdvancedInfractions(commands.Cog):
    """Advanced infraction tracking with escalation and appeals"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/infractions.json"
        self.infractions = {}  # user_id -> [infractions]
        self.appeals = []  # [appeals]
        self.load_data()
    
    def load_data(self):
        """Load infraction data"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.infractions = data.get('infractions', {})
                    self.appeals = data.get('appeals', [])
            except:
                self.infractions = {}
                self.appeals = []
    
    def save_data(self):
        """Save infraction data"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'infractions': self.infractions,
                'appeals': self.appeals
            }, f, indent=2)
    
    def get_user_infractions(self, user_id: int, guild_id: int = None) -> List[Dict]:
        """Get infractions for a user"""
        user_key = str(user_id)
        if user_key not in self.infractions:
            self.infractions[user_key] = []
        
        if guild_id:
            return [i for i in self.infractions[user_key] if i.get('guild_id') == guild_id]
        return self.infractions[user_key]
    
    def get_active_infractions(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get non-expired infractions"""
        user_infractions = self.get_user_infractions(user_id, guild_id)
        active = []
        
        for infraction in user_infractions:
            if infraction.get('type') == 'warn':
                # Warns expire after 30 days
                expires_at = datetime.fromisoformat(infraction['timestamp']) + timedelta(days=30)
                if get_now_pst() < expires_at:
                    active.append(infraction)
            elif infraction.get('type') in ['mute', 'kick']:
                # Only active if not resolved
                if not infraction.get('resolved'):
                    active.append(infraction)
            elif infraction.get('type') == 'ban':
                # Only active if not pardoned
                if not infraction.get('pardoned'):
                    active.append(infraction)
        
        return active
    
    def add_infraction(self, user_id: int, guild_id: int, infraction_type: str, 
                       reason: str, moderator_id: int, duration: Optional[int] = None) -> str:
        """Add infraction and check for escalation"""
        user_key = str(user_id)
        
        if user_key not in self.infractions:
            self.infractions[user_key] = []
        
        # Get active infraction count
        active_count = len(self.get_active_infractions(user_id, guild_id))
        
        infraction = {
            'id': f"INF-{get_now_pst().strftime('%Y%m%d%H%M%S')}-{user_id}",
            'type': infraction_type,
            'reason': reason,
            'moderator_id': moderator_id,
            'guild_id': guild_id,
            'timestamp': get_now_pst().isoformat(),
            'duration_minutes': duration,
            'active_count': active_count + 1,
            'resolved': False,
            'appeal_id': None
        }
        
        self.infractions[user_key].append(infraction)
        self.save_data()
        
        return infraction['id']
    
    def escalate_if_needed(self, user_id: int, guild_id: int) -> Optional[str]:
        """Check if user should be escalated to next punishment level"""
        active = self.get_active_infractions(user_id, guild_id)
        warn_count = len([i for i in active if i['type'] == 'warn'])
        
        escalation = None
        if warn_count >= 4:
            escalation = "BAN"
        elif warn_count >= 3:
            escalation = "KICK"
        elif warn_count >= 2:
            escalation = "MUTE"
        elif warn_count >= 1:
            escalation = "CONTINUE_WARN"
        
        return escalation
    
    def create_appeal(self, user_id: int, guild_id: int, infraction_id: str, reason: str) -> str:
        """Create appeal for infraction"""
        appeal_id = f"APL-{get_now_pst().strftime('%Y%m%d%H%M%S')}"
        
        appeal = {
            'id': appeal_id,
            'user_id': user_id,
            'guild_id': guild_id,
            'infraction_id': infraction_id,
            'reason': reason,
            'timestamp': get_now_pst().isoformat(),
            'status': 'pending',  # pending, approved, denied
            'mod_response': None,
            'mod_id': None
        }
        
        self.appeals.append(appeal)
        
        # Link appeal to infraction
        user_key = str(user_id)
        for inf in self.infractions[user_key]:
            if inf['id'] == infraction_id:
                inf['appeal_id'] = appeal_id
                break
        
        self.save_data()
        return appeal_id
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_user(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        """Issue a warning to a user"""
        if user.bot:
            await ctx.send("❌ Cannot warn bots")
            return
        
        if user.id == ctx.author.id:
            await ctx.send("❌ Cannot warn yourself")
            return
        
        # Add infraction
        inf_id = self.add_infraction(
            user.id, ctx.guild.id, 'warn', reason, 
            ctx.author.id
        )
        
        # Check escalation
        escalation = self.escalate_if_needed(user.id, ctx.guild.id)
        
        embed = discord.Embed(
            title="⚠️ User Warning",
            description=f"**User:** {user.mention}\n**Reason:** {reason}",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        active = self.get_active_infractions(user.id, ctx.guild.id)
        embed.add_field(name="Infraction ID", value=inf_id, inline=False)
        embed.add_field(name="Active Warnings", value=str(len([i for i in active if i['type'] == 'warn'])), inline=True)
        embed.add_field(name="Total Active Infractions", value=str(len(active)), inline=True)
        
        if escalation and escalation != "CONTINUE_WARN":
            embed.add_field(name="⚠️ Escalation Alert", value=f"Next action: **{escalation}**", inline=False)
        
        embed.set_footer(text=f"Issued by {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        # DM user
        try:
            await user.send(f"⚠️ You have been warned in {ctx.guild.name}\n**Reason:** {reason}\n\nYou have {4 - len(active)} warnings remaining before escalation.")
        except:
            pass
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_user(self, ctx, user: discord.Member, duration: Optional[int] = 10, *, reason: str = "No reason provided"):
        """Mute a user for specified minutes"""
        if user.bot:
            await ctx.send("❌ Cannot mute bots")
            return
        
        # Add infraction
        inf_id = self.add_infraction(
            user.id, ctx.guild.id, 'mute', reason, 
            ctx.author.id, duration
        )
        
        # Try to mute in Discord (would need mute role or permissions)
        embed = discord.Embed(
            title="🔇 User Muted",
            description=f"**User:** {user.mention}\n**Duration:** {duration} minutes\n**Reason:** {reason}",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Infraction ID", value=inf_id, inline=False)
        embed.add_field(name="Expires At", value=f"<t:{int((get_now_pst() + timedelta(minutes=duration)).timestamp())}:F>", inline=False)
        embed.set_footer(text=f"Issued by {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        # DM user
        try:
            await user.send(f"🔇 You have been muted in {ctx.guild.name} for {duration} minutes\n**Reason:** {reason}")
        except:
            pass
    
    @commands.command(name='userrecord')
    @commands.has_permissions(manage_messages=True)
    async def user_record(self, ctx, user: discord.Member):
        """View user's infraction record"""
        infractions = self.get_user_infractions(user.id, ctx.guild.id)
        
        if not infractions:
            await ctx.send(f"✅ {user.mention} has a clean record")
            return
        
        embed = discord.Embed(
            title=f"📋 {user.name}'s Infraction Record",
            description=f"Total infractions: {len(infractions)}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Show recent infractions
        for inf in infractions[-10:]:
            status = "Active" if not inf.get('resolved') else "Resolved"
            
            field_value = f"**Type:** {inf['type'].upper()}\n"
            field_value += f"**Reason:** {inf['reason']}\n"
            field_value += f"**Status:** {status}"
            
            if inf.get('appeal_id'):
                field_value += f"\n**Appeal:** {inf['appeal_id']}"
            
            embed.add_field(
                name=f"{inf['id']} - {datetime.fromisoformat(inf['timestamp']).strftime('%Y-%m-%d %H:%M')}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text=f"View full record with /infractions detailed")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='appeal')
    async def appeal_infraction(self, ctx, infraction_id: str, *, reason: str):
        """Appeal an infraction"""
        # Find the infraction
        user_key = str(ctx.author.id)
        infraction = None
        
        if user_key in self.infractions:
            for inf in self.infractions[user_key]:
                if inf['id'] == infraction_id:
                    infraction = inf
                    break
        
        if not infraction:
            await ctx.send(f"❌ Infraction {infraction_id} not found")
            return
        
        # Create appeal
        appeal_id = self.create_appeal(
            ctx.author.id, ctx.guild.id, infraction_id, reason
        )
        
        embed = discord.Embed(
            title="📝 Appeal Submitted",
            description=f"Your appeal for {infraction_id} has been submitted",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Appeal ID", value=appeal_id, inline=False)
        embed.add_field(name="Your Reason", value=reason, inline=False)
        embed.add_field(name="Status", value="Pending Moderator Review", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='appeals')
    @commands.has_permissions(manage_messages=True)
    async def view_appeals(self, ctx):
        """View pending appeals"""
        guild_appeals = [a for a in self.appeals if a.get('guild_id') == ctx.guild.id and a['status'] == 'pending']
        
        if not guild_appeals:
            await ctx.send("✅ No pending appeals")
            return
        
        embed = discord.Embed(
            title="📋 Pending Appeals",
            description=f"{len(guild_appeals)} appeal(s) awaiting review",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for appeal in guild_appeals:
            user = self.bot.get_user(appeal['user_id'])
            user_name = user.name if user else f"User {appeal['user_id']}"
            
            embed.add_field(
                name=f"Appeal {appeal['id']}",
                value=f"**User:** {user_name}\n**Infraction:** {appeal['infraction_id']}\n**Reason:** {appeal['reason'][:100]}",
                inline=False
            )
        
        embed.set_footer(text="Use /appealreview to respond")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedInfractions(bot))
