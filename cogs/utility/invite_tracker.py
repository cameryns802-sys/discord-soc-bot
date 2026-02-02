"""
Invite Tracker System - Track invite usage and links
Monitor who invited whom
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from collections import defaultdict

class InviteTracker(commands.Cog):
    """Track and monitor invite usage"""
    
    def __init__(self, bot):
        self.bot = bot
        self.invite_file = 'data/invite_tracking.json'
        self.previous_invites = {}
        self.load_invite_data()
    
    def load_invite_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.invite_file):
            with open(self.invite_file, 'w') as f:
                json.dump({}, f)
    
    def get_invite_data(self, guild_id):
        try:
            with open(self.invite_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_invite_data(self, guild_id, data):
        try:
            with open(self.invite_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        
        all_data[str(guild_id)] = data
        with open(self.invite_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track which invite was used"""
        guild = member.guild
        
        try:
            invites = await guild.invites()
            
            data = self.get_invite_data(guild.id)
            if "invites" not in data:
                data["invites"] = {}
            
            # Check which invite was used
            used_invite = None
            for invite in invites:
                old_uses = self.previous_invites.get(f"{guild.id}_{invite.code}", 0)
                if invite.uses > old_uses:
                    used_invite = invite
                    break
            
            # Log the join
            if "joins" not in data:
                data["joins"] = []
            
            join_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "member": str(member),
                "member_id": member.id,
                "invite": used_invite.code if used_invite else "Unknown",
                "inviter": str(used_invite.inviter) if used_invite else "Unknown"
            }
            
            data["joins"].append(join_log)
            self.save_invite_data(guild.id, data)
            
            # Update previous invites
            for invite in invites:
                self.previous_invites[f"{guild.id}_{invite.code}"] = invite.uses
        
        except Exception as e:
            print(f"Error tracking invite: {e}")
    
    @commands.command(name='invite_stats')
    @commands.has_permissions(administrator=True)
    async def invite_stats(self, ctx):
        """Show invite statistics"""
        guild = ctx.guild
        data = self.get_invite_data(guild.id)
        
        embed = discord.Embed(
            title="📊 Invite Statistics",
            description=f"{guild.name} - Invite tracking",
            color=discord.Color.blue()
        )
        
        joins = data.get("joins", [])
        embed.add_field(name="Total Joins Tracked", value=str(len(joins)), inline=True)
        
        # Get list of all invites
        try:
            invites = await guild.invites()
            embed.add_field(name="Active Invites", value=str(len(invites)), inline=True)
            
            # Show top invite
            if invites:
                top_invite = max(invites, key=lambda i: i.uses)
                embed.add_field(
                    name="🔝 Top Invite",
                    value=f"Code: {top_invite.code}\nUses: {top_invite.uses}",
                    inline=False
                )
        except:
            pass
        
        # Show recent joins
        if joins:
            embed.add_field(name="Recent Joins", value="━" * 20, inline=False)
            for join in joins[-5:]:
                embed.add_field(
                    name=f"{join['member']}",
                    value=f"Inviter: {join['inviter']}\nCode: {join['invite']}",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='invite_info')
    @commands.has_permissions(administrator=True)
    async def invite_info(self, ctx, invite_code: str = None):
        """Show info about an invite"""
        try:
            if invite_code:
                invite = await self.bot.fetch_invite(invite_code)
            else:
                # Get invites from current guild
                invites = await ctx.guild.invites()
                if not invites:
                    await ctx.send("❌ No invites found")
                    return
                invite = invites[0]
            
            embed = discord.Embed(
                title="🔗 Invite Information",
                description=f"Invite details",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Code", value=invite.code, inline=True)
            embed.add_field(name="Uses", value=str(invite.uses), inline=True)
            embed.add_field(name="Max Uses", value=str(invite.max_uses) if invite.max_uses else "Unlimited", inline=True)
            embed.add_field(name="Inviter", value=str(invite.inviter) if invite.inviter else "Unknown", inline=True)
            embed.add_field(name="Created", value=invite.created_at.strftime('%Y-%m-%d %H:%M'), inline=True)
            embed.add_field(name="Expires", value="Never" if not invite.expires_at else invite.expires_at.strftime('%Y-%m-%d'), inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
