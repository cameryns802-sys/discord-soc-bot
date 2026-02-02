"""
Security Drill System - Advanced incident response drills
Run security drills to test team readiness and procedures
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from enum import Enum

class DrillType(Enum):
    BREACH = "Data Breach"
    PHISHING = "Phishing Campaign"
    RANSOMWARE = "Ransomware Attack"
    DDoS = "DDoS Attack"
    INSIDER = "Insider Threat"
    MALWARE = "Malware Infection"
    COMPROMISED = "Account Compromise"
    SUPPLY_CHAIN = "Supply Chain Attack"

class DrillProtocol(Enum):
    BLACK = "🔴 CRITICAL SHUTDOWN"
    RED = "🔴 RED ALERT - Maximum Response"
    YELLOW = "🟡 YELLOW ALERT - Elevated Response"
    GREEN = "🟢 GREEN LIGHT - Normal Operations"
    BLUE = "🔵 BLUE PROTOCOL - Containment"
    AMBER = "🟠 AMBER ALERT - Moderate Response"

class SecurityDrill(commands.Cog):
    """Advanced security drill and exercise system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.drill_file = 'data/security_drills.json'
        self.active_drill = {}
        self.load_drill_data()
    
    def load_drill_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.drill_file):
            with open(self.drill_file, 'w') as f:
                json.dump({}, f)
    
    def get_drill_data(self, guild_id):
        try:
            with open(self.drill_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_drill_data(self, guild_id, data):
        try:
            with open(self.drill_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        all_data[str(guild_id)] = data
        with open(self.drill_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    @commands.command(name='activate_drill')
    @commands.has_permissions(administrator=True)
    async def activate_drill(self, ctx, drill_type: str = "BREACH", protocol: str = "BLACK"):
        """Activate a security drill"""
        guild = ctx.guild
        
        try:
            drill_type = DrillType[drill_type.upper()]
        except:
            drill_type = DrillType.BREACH
        
        try:
            protocol = DrillProtocol[protocol.upper()]
        except:
            protocol = DrillProtocol.BLACK
        
        # Create drill record
        drill_data = self.get_drill_data(guild.id)
        if "drills" not in drill_data:
            drill_data["drills"] = []
        
        drill_id = f"DRILL-{len(drill_data['drills']) + 1:04d}"
        
        drill_info = {
            "drill_id": drill_id,
            "type": drill_type.value,
            "protocol": protocol.name,
            "protocol_description": protocol.value,
            "level": "CRITICAL",
            "activated_by": str(ctx.author),
            "activated_at": datetime.utcnow().isoformat(),
            "status": "ACTIVE",
            "team_responses": [],
            "timeline": []
        }
        
        drill_data["drills"].append(drill_info)
        self.active_drill[guild.id] = drill_info
        self.save_drill_data(guild.id, drill_data)
        
        # Update bot status to drill mode
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status:
            await dynamic_status.activate_drill_status(drill_type.value, protocol.name)
        
        # Create activation embed
        embed = discord.Embed(
            title="🛡️ Security Drill Activated",
            description="⚠️ THIS IS A DRILL - THIS IS A DRILL",
            color=discord.Color.red()
        )
        
        embed.add_field(name="🎯 Drill ID", value=drill_id, inline=True)
        embed.add_field(name="📋 Type", value=f"🔴 {drill_type.value}", inline=True)
        embed.add_field(name="⏰ Activated", value=datetime.utcnow().strftime('%H:%M:%S'), inline=True)
        
        embed.add_field(name="📌 Protocol", value=protocol.value, inline=False)
        embed.add_field(name="🔴 Level", value="CRITICAL", inline=True)
        embed.add_field(name="👤 By", value=ctx.author.mention, inline=True)
        
        embed.add_field(name="📢 Action Required", value="━" * 30, inline=False)
        embed.add_field(name="→", value="Incident Commander take command", inline=False)
        embed.add_field(name="→", value="Security team to #incident-response", inline=False)
        embed.add_field(name="→", value="Execute response procedures", inline=False)
        embed.add_field(name="→", value="Report status with !drill_respond", inline=False)
        
        embed.set_footer(text=f"Guild: {guild.name} ({guild.id})")
        
        # Send to all channels
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
        
        await ctx.send(embed=embed)
    
    @commands.command(name='drill_reset')
    @commands.has_permissions(administrator=True)
    async def drill_reset(self, ctx):
        """Reset current drill"""
        guild = ctx.guild
        
        if guild.id not in self.active_drill:
            await ctx.send("❌ No active drill")
            return
        
        drill_info = self.active_drill[guild.id]
        drill_info["status"] = "COMPLETED"
        drill_info["completed_at"] = datetime.utcnow().isoformat()
        
        # Deactivate drill status
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status:
            await dynamic_status.deactivate_drill_status()
        
        # Save
        drill_data = self.get_drill_data(guild.id)
        for drill in drill_data.get("drills", []):
            if drill["drill_id"] == drill_info["drill_id"]:
                drill["status"] = "COMPLETED"
                drill["completed_at"] = datetime.utcnow().isoformat()
        
        self.save_drill_data(guild.id, drill_data)
        
        embed = discord.Embed(
            title="✅ Drill Reset",
            description="Security drill completed and reset",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Drill ID", value=drill_info["drill_id"], inline=True)
        embed.add_field(name="Duration", value="Calculated from timestamps", inline=True)
        embed.add_field(name="Reset By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value="ℹ️ DRILL COMPLETED", inline=False)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='protocol_change')
    @commands.has_permissions(administrator=True)
    async def protocol_change(self, ctx, new_protocol: str):
        """Change drill protocol"""
        guild = ctx.guild
        
        if guild.id not in self.active_drill:
            await ctx.send("❌ No active drill")
            return
        
        try:
            protocol = DrillProtocol[new_protocol.upper()]
        except:
            await ctx.send("❌ Invalid protocol")
            return
        
        drill_info = self.active_drill[guild.id]
        old_protocol = drill_info["protocol"]
        drill_info["protocol"] = protocol.name
        drill_info["protocol_description"] = protocol.value
        
        embed = discord.Embed(
            title="📢 Protocol Changed",
            description=f"Escalation in effect",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="Previous", value=old_protocol, inline=True)
        embed.add_field(name="Current", value=protocol.value, inline=True)
        embed.add_field(name="Changed By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime('%H:%M:%S'), inline=False)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='drill_respond')
    async def drill_respond(self, ctx, status: str = "ACKNOWLEDGED"):
        """Log team response to drill"""
        guild = ctx.guild
        
        if guild.id not in self.active_drill:
            await ctx.send("❌ No active drill")
            return
        
        drill_info = self.active_drill[guild.id]
        
        response = {
            "responder": str(ctx.author),
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if "team_responses" not in drill_info:
            drill_info["team_responses"] = []
        
        drill_info["team_responses"].append(response)
        
        embed = discord.Embed(
            title="✅ Response Logged",
            description=f"Team member acknowledged drill",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Responder", value=ctx.author.mention, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime('%H:%M:%S'), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='drill_stats')
    @commands.has_permissions(administrator=True)
    async def drill_stats(self, ctx):
        """Show drill statistics"""
        guild = ctx.guild
        drill_data = self.get_drill_data(guild.id)
        
        drills = drill_data.get("drills", [])
        
        embed = discord.Embed(
            title="📊 Security Drill Statistics",
            description=f"{guild.name} - All drills",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Drills", value=str(len(drills)), inline=True)
        completed = len([d for d in drills if d.get("status") == "COMPLETED"])
        embed.add_field(name="Completed", value=str(completed), inline=True)
        active = len([d for d in drills if d.get("status") == "ACTIVE"])
        embed.add_field(name="Active", value=str(active), inline=True)
        
        if drills:
            embed.add_field(name="Recent Drills", value="━" * 25, inline=False)
            for drill in drills[-5:]:
                embed.add_field(
                    name=f"{drill['drill_id']} - {drill['type']}",
                    value=f"Protocol: {drill['protocol']}\nStatus: {drill['status']}",
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityDrill(bot))
