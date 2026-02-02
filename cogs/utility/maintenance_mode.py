"""
Maintenance Mode System - Toggle maintenance and service status
Temporarily disable bot features for maintenance
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

class MaintenanceMode(commands.Cog):
    """Manage maintenance mode and service status"""
    
    def __init__(self, bot):
        self.bot = bot
        self.maintenance_file = 'data/maintenance_mode.json'
        self.maintenance_active = False
        self.load_maintenance_data()
    
    def load_maintenance_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.maintenance_file):
            with open(self.maintenance_file, 'w') as f:
                json.dump({"active": False}, f)
    
    def get_maintenance_status(self):
        try:
            with open(self.maintenance_file, 'r') as f:
                data = json.load(f)
            return data.get("active", False)
        except:
            return False
    
    def save_maintenance_status(self, active, reason=""):
        try:
            with open(self.maintenance_file, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        
        data["active"] = active
        data["reason"] = reason
        data["timestamp"] = datetime.utcnow().isoformat()
        
        with open(self.maintenance_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @commands.command(name='maintenance_on')
    @commands.has_permissions(administrator=True)
    async def maintenance_on(self, ctx, *, reason: str = "Scheduled maintenance"):
        """Enable maintenance mode"""
        self.maintenance_active = True
        self.save_maintenance_status(True, reason)
        
        embed = discord.Embed(
            title="🔧 Maintenance Mode: ON",
            description="Bot entering maintenance mode",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="Status", value="🟠 MAINTENANCE", inline=True)
        embed.add_field(name="Enabled By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime('%H:%M:%S'), inline=True)
        
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Impact", value="━" * 25, inline=False)
        embed.add_field(name="→", value="Security commands disabled", inline=False)
        embed.add_field(name="→", value="Automated responses paused", inline=False)
        embed.add_field(name="→", value="Admin commands available", inline=False)
        
        embed.add_field(name="To Resume", value="Use `!maintenance_off`", inline=False)
        
        # Notify all guilds
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass
    
    @commands.command(name='maintenance_off')
    @commands.has_permissions(administrator=True)
    async def maintenance_off(self, ctx):
        """Disable maintenance mode"""
        self.maintenance_active = False
        self.save_maintenance_status(False)
        
        embed = discord.Embed(
            title="✅ Maintenance Mode: OFF",
            description="Bot resuming normal operations",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Status", value="🟢 ONLINE", inline=True)
        embed.add_field(name="Resumed By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime('%H:%M:%S'), inline=True)
        
        embed.add_field(name="Services", value="━" * 25, inline=False)
        embed.add_field(name="→", value="✅ Security systems active", inline=False)
        embed.add_field(name="→", value="✅ Automated responses enabled", inline=False)
        embed.add_field(name="→", value="✅ All commands available", inline=False)
        
        # Notify all guilds
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass
    
    @commands.command(name='maintenance_status')
    async def maintenance_status(self, ctx):
        """Check maintenance status"""
        try:
            with open(self.maintenance_file, 'r') as f:
                data = json.load(f)
        except:
            data = {"active": False}
        
        status = data.get("active", False)
        reason = data.get("reason", "N/A")
        
        embed = discord.Embed(
            title="🔧 Maintenance Status",
            description="Current maintenance mode status",
            color=discord.Color.orange() if status else discord.Color.green()
        )
        
        embed.add_field(
            name="Status",
            value="🟠 MAINTENANCE" if status else "🟢 NORMAL OPERATIONS",
            inline=True
        )
        
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Last Updated", value=data.get("timestamp", "N/A"), inline=False)
        
        if status:
            embed.add_field(name="Services Disabled", value="━" * 25, inline=False)
            embed.add_field(name="→", value="Security commands", inline=False)
            embed.add_field(name="→", value="Automated responses", inline=False)
            embed.add_field(name="→", value="Drill systems", inline=False)
        else:
            embed.add_field(name="All Services", value="✅ OPERATIONAL", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='scheduled_maintenance')
    @commands.has_permissions(administrator=True)
    async def scheduled_maintenance(self, ctx, hours_from_now: int = 1, *, reason: str = "Scheduled maintenance"):
        """Schedule maintenance for later"""
        scheduled_time = datetime.utcnow() + timedelta(hours=hours_from_now)
        
        embed = discord.Embed(
            title="📅 Maintenance Scheduled",
            description="Maintenance window scheduled",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Scheduled Time", value=scheduled_time.strftime('%H:%M:%S'), inline=True)
        embed.add_field(name="Hours from Now", value=str(hours_from_now), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        embed.add_field(name="Action", value="Scheduled by " + ctx.author.mention, inline=False)
        
        # Notify all guilds
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass

async def setup(bot):
    await bot.add_cog(MaintenanceMode(bot))
