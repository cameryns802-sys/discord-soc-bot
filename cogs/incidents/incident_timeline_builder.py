import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from cogs.core.pst_timezone import get_now_pst

class IncidentTimelineBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timelines_file = "data/incident_timelines.json"
        self.load_timelines()

    def load_timelines(self):
        if os.path.exists(self.timelines_file):
            with open(self.timelines_file) as f:
                self.timelines = json.load(f)
        else:
            self.timelines = {}

    def save_timelines(self):
        os.makedirs("data", exist_ok=True)
        with open(self.timelines_file, 'w') as f:
            json.dump(self.timelines, f, indent=2)

    @commands.command()
    async def newtimeline(self, ctx, incident_id: int, title: str = None):
        """Create a new incident timeline"""
        if str(incident_id) in self.timelines:
            await ctx.send("❌ Timeline already exists for this incident")
            return
        
        self.timelines[str(incident_id)] = {
            "title": title or f"Incident #{incident_id}",
            "events": [],
            "created": get_now_pst().isoformat()
        }
        self.save_timelines()
        
        embed = discord.Embed(
            title="✅ Timeline Created",
            description=f"Incident #{incident_id}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def addevent(self, ctx, incident_id: int, timestamp: str, event: str):
        """Add an event to incident timeline (format: HH:MM:SS)"""
        if str(incident_id) not in self.timelines:
            await ctx.send("❌ Timeline not found. Create one first with `!newtimeline`")
            return
        
        self.timelines[str(incident_id)]["events"].append({
            "timestamp": timestamp,
            "event": event,
            "added": get_now_pst().isoformat()
        })
        self.save_timelines()
        
        embed = discord.Embed(
            title="✅ Event Added",
            description=f"[{timestamp}] {event}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def showtimeline(self, ctx, incident_id: int):
        """Display incident timeline"""
        if str(incident_id) not in self.timelines:
            await ctx.send("❌ Timeline not found")
            return
        
        timeline = self.timelines[str(incident_id)]
        embed = discord.Embed(
            title=f"📅 {timeline['title']}",
            color=discord.Color.blue()
        )
        
        if timeline["events"]:
            events_text = "\n".join([f"`{e['timestamp']}` - {e['event']}" for e in timeline["events"][:20]])
            embed.add_field(name="Timeline Events", value=events_text, inline=False)
        else:
            embed.add_field(name="Timeline Events", value="No events recorded yet", inline=False)
        
        embed.add_field(name="Total Events", value=str(len(timeline["events"])), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def timelinereport(self, ctx, incident_id: int):
        """Generate incident timeline report"""
        if str(incident_id) not in self.timelines:
            await ctx.send("❌ Timeline not found")
            return
        
        timeline = self.timelines[str(incident_id)]
        embed = discord.Embed(
            title=f"📊 Timeline Report - {timeline['title']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Event Count", value=str(len(timeline["events"])), inline=True)
        embed.add_field(name="Created", value=timeline["created"][:10], inline=True)
        embed.add_field(
            name="Incident Span",
            value=f"From `{timeline['events'][0]['timestamp']}` to `{timeline['events'][-1]['timestamp']}`" if timeline["events"] else "N/A",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IncidentTimelineBuilderCog(bot))
