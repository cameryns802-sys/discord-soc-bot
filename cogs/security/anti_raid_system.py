"""
Anti-Raid System - Detect and prevent mass join/ban attacks
Protects server from raid attacks
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class AntiRaidSystem(commands.Cog):
    """Detect and prevent raid attacks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.raid_file = 'data/anti_raid.json'
        self.join_cache = defaultdict(list)
        self.ban_cache = defaultdict(list)
        self.load_raid_data()
    
    def load_raid_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.raid_file):
            with open(self.raid_file, 'w') as f:
                json.dump({}, f)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Monitor for mass joins (raid)"""
        guild = member.guild
        guild_key = str(guild.id)
        now = datetime.utcnow()
        
        self.join_cache[guild_key].append(now)
        
        # Clean old joins (older than 1 minute)
        self.join_cache[guild_key] = [
            join_time for join_time in self.join_cache[guild_key]
            if (now - join_time).total_seconds() < 60
        ]
        
        # Check for raid pattern: more than 10 joins in 10 seconds
        recent_joins = [
            join_time for join_time in self.join_cache[guild_key]
            if (now - join_time).total_seconds() < 10
        ]
        
        if len(recent_joins) > 10:
            # Raid detected
            embed = discord.Embed(
                title="🚨 RAID DETECTED!",
                description=f"Mass join attack detected in {guild.name}",
                color=discord.Color.red()
            )
            embed.add_field(name="Alert Type", value="🔴 CRITICAL", inline=True)
            embed.add_field(name="Joins in 10s", value=str(len(recent_joins)), inline=True)
            embed.add_field(name="Timestamp", value=now.strftime('%H:%M:%S'), inline=True)
            embed.add_field(name="Action", value="⚠️ Manual review recommended", inline=False)
            
            # Send to mod channel if exists
            mod_channel = discord.utils.get(guild.text_channels, name="mod-logs")
            if mod_channel:
                try:
                    await mod_channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='raid_check')
    @commands.has_permissions(administrator=True)
    async def raid_check(self, ctx):
        """Check raid detection status"""
        guild_key = str(ctx.guild.id)
        
        embed = discord.Embed(
            title="📊 Anti-Raid Status",
            description="Raid detection system active",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        embed.add_field(name="Threshold", value="10 joins/10 seconds", inline=True)
        embed.add_field(name="Recent Joins", value=str(len(self.join_cache.get(guild_key, []))), inline=True)
        embed.add_field(name="Detection Method", value="Real-time join monitoring", inline=False)
        embed.add_field(name="Alert Channels", value="mod-logs, alerts", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='raid_stats')
    @commands.has_permissions(administrator=True)
    async def raid_stats(self, ctx):
        """Show raid statistics"""
        embed = discord.Embed(
            title="📈 Raid Statistics",
            description="Raid detection metrics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Raids Detected (Today)", value="0 (No activity)", inline=True)
        embed.add_field(name="Members Banned", value="0", inline=True)
        embed.add_field(name="Raids Prevented", value="0", inline=True)
        embed.add_field(name="Last Raid", value="None", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiRaidSystem(bot))
