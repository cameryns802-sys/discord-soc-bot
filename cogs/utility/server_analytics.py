"""
Server Analytics System - Track server metrics and statistics
Monitor server growth, activity, and health
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class ServerAnalytics(commands.Cog):
    """Track and analyze server metrics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.analytics_file = 'data/server_analytics.json'
        self.load_analytics_data()
        self.collect_metrics.start()
    
    def load_analytics_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.analytics_file):
            with open(self.analytics_file, 'w') as f:
                json.dump({}, f)
    
    def get_analytics(self, guild_id):
        try:
            with open(self.analytics_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_analytics(self, guild_id, data):
        try:
            with open(self.analytics_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        
        all_data[str(guild_id)] = data
        with open(self.analytics_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    @tasks.loop(hours=1)
    async def collect_metrics(self):
        """Collect server metrics every hour"""
        for guild in self.bot.guilds:
            analytics = self.get_analytics(guild.id)
            
            if "metrics" not in analytics:
                analytics["metrics"] = []
            
            metric = {
                "timestamp": datetime.utcnow().isoformat(),
                "members": len(guild.members),
                "bots": sum(1 for m in guild.members if m.bot),
                "channels": len(guild.channels),
                "roles": len(guild.roles)
            }
            
            analytics["metrics"].append(metric)
            
            # Keep only last 30 days
            if len(analytics["metrics"]) > 720:  # 30 days * 24 hours
                analytics["metrics"] = analytics["metrics"][-720:]
            
            self.save_analytics(guild.id, analytics)
    
    @commands.command(name='server_analytics')
    async def server_analytics(self, ctx):
        """Show server analytics"""
        guild = ctx.guild
        analytics = self.get_analytics(guild.id)
        
        embed = discord.Embed(
            title="📊 Server Analytics",
            description=f"{guild.name} - Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="👥 Members", value=str(len(guild.members)), inline=True)
        embed.add_field(name="🤖 Bots", value=str(sum(1 for m in guild.members if m.bot)), inline=True)
        embed.add_field(name="📊 Humans", value=str(len(guild.members) - sum(1 for m in guild.members if m.bot)), inline=True)
        
        embed.add_field(name="📡 Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="🏷️ Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
        
        # Growth metrics
        if analytics.get("metrics") and len(analytics["metrics"]) > 1:
            current = len(guild.members)
            previous = analytics["metrics"][-24]["members"] if len(analytics["metrics"]) > 24 else analytics["metrics"][0]["members"]
            growth = current - previous
            trend = "📈 Growing" if growth > 0 else "📉 Declining" if growth < 0 else "➡️ Stable"
            
            embed.add_field(name="Growth (24h)", value=f"{growth:+d} {trend}", inline=False)
        
        embed.add_field(name="🔐 Verification", value=guild.verification_level.name.title(), inline=True)
        embed.add_field(name="🎭 Content Filter", value=guild.explicit_content_filter.name.replace('_', ' ').title(), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='growth_stats')
    @commands.has_permissions(administrator=True)
    async def growth_stats(self, ctx):
        """Show growth statistics"""
        guild = ctx.guild
        analytics = self.get_analytics(guild.id)
        
        embed = discord.Embed(
            title="📈 Growth Statistics",
            description="Server growth over time",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if analytics.get("metrics"):
            metrics = analytics["metrics"]
            
            # 24 hour growth
            if len(metrics) > 24:
                growth_24h = metrics[-1]["members"] - metrics[-24]["members"]
            else:
                growth_24h = 0
            
            # 7 day growth
            if len(metrics) > 168:
                growth_7d = metrics[-1]["members"] - metrics[-168]["members"]
            else:
                growth_7d = 0
            
            # Current stats
            embed.add_field(name="24 Hour", value=f"{growth_24h:+d} members", inline=True)
            embed.add_field(name="7 Day", value=f"{growth_7d:+d} members", inline=True)
            embed.add_field(name="Current", value=f"{metrics[-1]['members']} members", inline=True)
        
        embed.add_field(name="Trend", value="📊 Data collection in progress", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerAnalytics(bot))
