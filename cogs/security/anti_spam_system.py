"""
Anti-Spam System - Detect and prevent spam messages
Protects server from spam attacks
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from cogs.core.pst_timezone import get_now_pst

class AntiSpamSystem(commands.Cog):
    """Detect and prevent spam messages"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_file = 'data/anti_spam.json'
        self.message_cache = defaultdict(list)
        self.load_spam_data()
    
    def load_spam_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.spam_file):
            with open(self.spam_file, 'w') as f:
                json.dump({}, f)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor for spam"""
        if message.author.bot or not message.guild:
            return
        
        # Track messages per user
        user_key = f"{message.guild.id}_{message.author.id}"
        now = get_now_pst()
        
        self.message_cache[user_key].append(now)
        
        # Clean old messages (older than 1 minute)
        self.message_cache[user_key] = [
            msg_time for msg_time in self.message_cache[user_key]
            if (now - msg_time).total_seconds() < 60
        ]
        
        # Check for spam (more than 10 messages in 10 seconds)
        recent = [
            msg_time for msg_time in self.message_cache[user_key]
            if (now - msg_time).total_seconds() < 10
        ]
        
        if len(recent) > 10:
            # Spam detected
            try:
                await message.delete()
                embed = discord.Embed(
                    title="🚫 Spam Detected",
                    description=f"User: {message.author.mention}\nReason: Sending messages too fast",
                    color=discord.Color.red()
                )
                embed.add_field(name="Messages in 10s", value=str(len(recent)), inline=True)
                embed.add_field(name="Action", value="Message deleted", inline=True)
                
                if message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send(embed=embed, delete_after=5)
            except:
                pass
    
    @commands.command(name='spam_check')
    @commands.has_permissions(administrator=True)
    async def spam_check(self, ctx):
        """Check spam statistics"""
        embed = discord.Embed(
            title="📊 Anti-Spam Status",
            description="Spam detection system active",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        embed.add_field(name="Threshold", value="10 messages/10 seconds", inline=True)
        embed.add_field(name="Action", value="Auto-delete + warn", inline=True)
        embed.add_field(name="Coverage", value=f"Monitoring {len(self.message_cache)} users", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiSpamSystem(bot))
