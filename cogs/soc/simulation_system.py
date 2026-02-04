"""
Simulation System - Advanced security simulation and exercise platform
Tabletop exercises, scenarios, and team training
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from cogs.core.pst_timezone import get_now_pst

class SimulationType(Enum):
    TABLETOP = "Tabletop Exercise"
    INCIDENT = "Incident Simulation"
    PHISHING = "Phishing Exercise"
    RANSOMWARE = "Ransomware Scenario"
    APT = "APT Campaign"
    SUPPLY_CHAIN = "Supply Chain Attack"
    INSIDER = "Insider Threat"
    DISASTER = "Disaster Recovery"

class SimulationLevel(Enum):
    BEGINNER = "Training Level"
    INTERMEDIATE = "Professional Level"
    ADVANCED = "Expert Level"
    EXTREME = "Maximum Stress"

class SimulationSystem(commands.Cog):
    """Advanced security simulation and exercise system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.simulation_file = 'data/simulations.json'
        self.active_simulations = {}
        self.load_simulation_data()
        self.run_simulations.start()
    
    def load_simulation_data(self):
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.simulation_file):
            with open(self.simulation_file, 'w') as f:
                json.dump({}, f)
    
    def get_simulation_data(self, guild_id):
        try:
            with open(self.simulation_file, 'r') as f:
                data = json.load(f)
            return data.get(str(guild_id), {})
        except:
            return {}
    
    def save_simulation_data(self, guild_id, data):
        try:
            with open(self.simulation_file, 'r') as f:
                all_data = json.load(f)
        except:
            all_data = {}
        all_data[str(guild_id)] = data
        with open(self.simulation_file, 'w') as f:
            json.dump(all_data, f, indent=2)
    
    @tasks.loop(minutes=5)
    async def run_simulations(self):
        """Background simulation engine"""
        for guild_id, sim in self.active_simulations.items():
            if sim.get("status") == "RUNNING":
                # Simulate events
                pass
    
    @commands.command(name='start_simulation')
    @commands.has_permissions(administrator=True)
    async def start_simulation(self, ctx, sim_type: str = "INCIDENT", level: str = "INTERMEDIATE"):
        """Start a security simulation"""
        guild = ctx.guild
        
        try:
            sim_type = SimulationType[sim_type.upper()]
        except:
            sim_type = SimulationType.INCIDENT
        
        try:
            level = SimulationLevel[level.upper()]
        except:
            level = SimulationLevel.INTERMEDIATE
        
        # Create simulation record
        sim_data = self.get_simulation_data(guild.id)
        if "simulations" not in sim_data:
            sim_data["simulations"] = []
        
        sim_id = f"SIM-{len(sim_data['simulations']) + 1:05d}"
        
        simulation_info = {
            "sim_id": sim_id,
            "type": sim_type.value,
            "level": level.value,
            "status": "RUNNING",
            "started_by": str(ctx.author),
            "started_at": get_now_pst().isoformat(),
            "events": [],
            "participant_count": 0,
            "score": 0,
            "metrics": {
                "detection_time": None,
                "response_time": None,
                "containment_time": None,
                "recovery_time": None
            }
        }
        
        sim_data["simulations"].append(simulation_info)
        self.active_simulations[guild.id] = simulation_info
        self.save_simulation_data(guild.id, sim_data)
        
        embed = discord.Embed(
            title="✅ SIMULATION",
            description="Security simulation exercise started",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🆔 Simulation ID", value=sim_id, inline=True)
        embed.add_field(name="📋 Type", value=sim_type.value, inline=True)
        embed.add_field(name="📊 Difficulty", value=level.value, inline=True)
        
        embed.add_field(name="⏰ Started", value=get_now_pst().strftime('%H:%M:%S'), inline=True)
        embed.add_field(name="👤 Started By", value=ctx.author.mention, inline=True)
        embed.add_field(name="📍 Status", value="✅ RUNNING", inline=True)
        
        embed.add_field(name="🎯 Objectives", value="━" * 25, inline=False)
        embed.add_field(name="→", value="Detect simulated threat", inline=False)
        embed.add_field(name="→", value="Initiate response procedures", inline=False)
        embed.add_field(name="→", value="Document timeline", inline=False)
        embed.add_field(name="→", value="Achieve containment", inline=False)
        
        embed.add_field(name="📢 Commands", value="━" * 25, inline=False)
        embed.add_field(name="→", value="`!sim_join` - Join simulation", inline=False)
        embed.add_field(name="→", value="`!sim_event` - Report simulation events", inline=False)
        embed.add_field(name="→", value="`!sim_status` - Check current status", inline=False)
        embed.add_field(name="→", value="`!stop_simulation` - End simulation", inline=False)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='sim_join')
    async def sim_join(self, ctx):
        """Join active simulation"""
        guild = ctx.guild
        
        if guild.id not in self.active_simulations:
            await ctx.send("❌ No active simulation")
            return
        
        sim = self.active_simulations[guild.id]
        sim["participant_count"] = sim.get("participant_count", 0) + 1
        
        embed = discord.Embed(
            title="✅ Joined Simulation",
            description=f"You are now part of {sim['sim_id']}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Simulation", value=sim['type'], inline=True)
        embed.add_field(name="Level", value=sim['level'], inline=True)
        embed.add_field(name="Participants", value=str(sim['participant_count']), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sim_event')
    async def sim_event(self, ctx, *, event: str):
        """Report simulation event"""
        guild = ctx.guild
        
        if guild.id not in self.active_simulations:
            await ctx.send("❌ No active simulation")
            return
        
        sim = self.active_simulations[guild.id]
        
        event_log = {
            "reporter": str(ctx.author),
            "event": event,
            "timestamp": get_now_pst().isoformat()
        }
        
        if "events" not in sim:
            sim["events"] = []
        
        sim["events"].append(event_log)
        
        embed = discord.Embed(
            title="📝 Simulation Event Logged",
            description="Event recorded in simulation timeline",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Reporter", value=ctx.author.mention, inline=True)
        embed.add_field(name="Event", value=event, inline=False)
        embed.add_field(name="Time", value=get_now_pst().strftime('%H:%M:%S'), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sim_status')
    async def sim_status(self, ctx):
        """Check simulation status"""
        guild = ctx.guild
        
        if guild.id not in self.active_simulations:
            await ctx.send("❌ No active simulation")
            return
        
        sim = self.active_simulations[guild.id]
        
        embed = discord.Embed(
            title="📊 Simulation Status",
            description=f"{sim['sim_id']} - Current metrics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Type", value=sim['type'], inline=True)
        embed.add_field(name="Level", value=sim['level'], inline=True)
        embed.add_field(name="Status", value="✅ " + sim['status'], inline=True)
        
        embed.add_field(name="👥 Participants", value=str(sim.get('participant_count', 0)), inline=True)
        embed.add_field(name="📅 Duration", value="Calculating...", inline=True)
        embed.add_field(name="📈 Score", value=f"{sim.get('score', 0)}/100", inline=True)
        
        embed.add_field(name="⏱️ Metrics", value="━" * 20, inline=False)
        embed.add_field(
            name="Detection Time",
            value=sim['metrics'].get('detection_time') or "Pending",
            inline=True
        )
        embed.add_field(
            name="Response Time",
            value=sim['metrics'].get('response_time') or "Pending",
            inline=True
        )
        embed.add_field(
            name="Containment Time",
            value=sim['metrics'].get('containment_time') or "Pending",
            inline=True
        )
        
        embed.add_field(name="📋 Events Logged", value=str(len(sim.get('events', []))), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='stop_simulation')
    @commands.has_permissions(administrator=True)
    async def stop_simulation(self, ctx):
        """End active simulation"""
        guild = ctx.guild
        
        if guild.id not in self.active_simulations:
            await ctx.send("❌ No active simulation")
            return
        
        sim = self.active_simulations[guild.id]
        sim["status"] = "COMPLETED"
        sim["ended_at"] = get_now_pst().isoformat()
        sim["ended_by"] = str(ctx.author)
        
        # Calculate duration
        started = datetime.fromisoformat(sim["started_at"])
        ended = datetime.fromisoformat(sim["ended_at"])
        duration = ended - started
        
        embed = discord.Embed(
            title="✅ Simulation Completed",
            description="Security simulation exercise concluded",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Simulation ID", value=sim['sim_id'], inline=True)
        embed.add_field(name="Type", value=sim['type'], inline=True)
        embed.add_field(name="Level", value=sim['level'], inline=True)
        
        embed.add_field(name="Duration", value=str(duration).split('.')[0], inline=True)
        embed.add_field(name="Participants", value=str(sim.get('participant_count', 0)), inline=True)
        embed.add_field(name="Final Score", value=f"{sim.get('score', 0)}/100", inline=True)
        
        embed.add_field(name="📊 Summary", value="━" * 20, inline=False)
        embed.add_field(name="Events Logged", value=str(len(sim.get('events', []))), inline=True)
        embed.add_field(name="Ended By", value=ctx.author.mention, inline=True)
        
        embed.add_field(name="Next Steps", value="Review After Action Report (AAR)", inline=False)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except:
                    pass
        
        del self.active_simulations[guild.id]

async def setup(bot):
    await bot.add_cog(SimulationSystem(bot))
