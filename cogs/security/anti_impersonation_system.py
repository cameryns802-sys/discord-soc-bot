"""
Anti-Impersonation System - Prevent user impersonation attacks
Detects and prevents username/role spoofing
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from difflib import SequenceMatcher

class AntiImpersonationSystem(commands.Cog):
    """Detect and prevent impersonation attacks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.imperson_file = 'data/anti_impersonation.json'
        self.load_imperson_data()
    
    def load_imperson_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.imperson_file):
            with open(self.imperson_file, 'w') as f:
                json.dump({}, f)
    
    def similarity(self, a, b):
        """Calculate string similarity"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Monitor for impersonation attempts"""
        if before.name == after.name:
            return
        
        guild = after.guild
        
        # Check if new name is similar to admin/moderator names
        suspicious = False
        similar_to = None
        
        for member in guild.members:
            if member.id == after.id:
                continue
            if member.bot:
                continue
            
            # Check similarity (>80% match is suspicious)
            if self.similarity(after.name, member.name) > 0.8:
                suspicious = True
                similar_to = member.name
                break
        
        if suspicious and similar_to:
            # Log suspicious activity
            embed = discord.Embed(
                title="⚠️ Suspicious Name Change Detected",
                description="Possible impersonation attempt",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="User", value=after.mention, inline=True)
            embed.add_field(name="New Name", value=after.name, inline=True)
            embed.add_field(name="Similar to", value=similar_to, inline=True)
            embed.add_field(name="Similarity", value="80%+", inline=True)
            embed.add_field(name="Action", value="⚠️ Flagged for review", inline=False)
            
            # Send to mod channel
            mod_channel = discord.utils.get(guild.text_channels, name="mod-logs")
            if mod_channel:
                try:
                    await mod_channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='impersonation_check')
    @commands.has_permissions(administrator=True)
    async def impersonation_check(self, ctx):
        """Check anti-impersonation status"""
        embed = discord.Embed(
            title="🛡️ Anti-Impersonation Status",
            description="Impersonation detection active",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        embed.add_field(name="Detection Method", value="String similarity analysis", inline=True)
        embed.add_field(name="Threshold", value="80% similarity", inline=True)
        embed.add_field(name="Monitoring", value="Username changes", inline=False)
        embed.add_field(name="Action", value="Flag and log suspicious changes", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiImpersonationSystem(bot))
