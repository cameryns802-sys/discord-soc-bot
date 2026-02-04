"""
Moderation Logging System - Track all moderation actions
Comprehensive audit trail for moderation
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class ModerationLogging(commands.Cog):
    """Log all moderation actions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_file = 'data/mod_logs.json'
        self.load_log_data()
    
    def load_log_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump({}, f)
    
    def log_action(self, guild_id, action_type, actor, target, reason=""):
        """Log a moderation action"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        guild_logs = data.get(str(guild_id), [])
        
        log_entry = {
            "timestamp": get_now_pst().isoformat(),
            "action": action_type,
            "actor": str(actor),
            "target": str(target),
            "reason": reason
        }
        
        guild_logs.append(log_entry)
        data[str(guild_id)] = guild_logs
        
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member ban"""
        self.log_action(guild.id, "BAN", "System", user, "Member banned")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log member kick"""
        guild = member.guild
        self.log_action(guild.id, "KICK", "System", member, "Member removed")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log role changes"""
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            if added:
                for role in added:
                    self.log_action(before.guild.id, "ROLE_ADD", "System", before, f"Added role: {role.name}")
            if removed:
                for role in removed:
                    self.log_action(before.guild.id, "ROLE_REMOVE", "System", before, f"Removed role: {role.name}")
    
    @commands.command(name='modlogs')
    @commands.has_permissions(administrator=True)
    async def modlogs(self, ctx):
        """View moderation logs"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        guild_logs = data.get(str(ctx.guild.id), [])
        
        embed = discord.Embed(
            title="📋 Moderation Logs",
            description=f"{ctx.guild.name} - Recent actions",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Actions", value=str(len(guild_logs)), inline=True)
        embed.add_field(name="Logging", value="✅ ACTIVE", inline=True)
        
        # Show last 5 actions
        for log in guild_logs[-5:]:
            embed.add_field(
                name=f"{log['action']} - {log['timestamp'][:10]}",
                value=f"Actor: {log['actor']}\nTarget: {log['target']}\nReason: {log.get('reason', 'N/A')}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='modstats')
    @commands.has_permissions(administrator=True)
    async def modstats(self, ctx):
        """Show moderation statistics"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        guild_logs = data.get(str(ctx.guild.id), [])
        
        # Count action types
        action_counts = {}
        for log in guild_logs:
            action = log['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        embed = discord.Embed(
            title="📊 Moderation Statistics",
            description="Action counts",
            color=discord.Color.blue()
        )
        
        for action, count in action_counts.items():
            embed.add_field(name=action, value=str(count), inline=True)
        
        embed.add_field(name="Total Actions Logged", value=str(len(guild_logs)), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationLogging(bot))
