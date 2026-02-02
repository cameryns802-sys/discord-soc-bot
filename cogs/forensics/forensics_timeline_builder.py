"""
Forensics Timeline Builder: Interactive visual timeline of all events for investigations.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class ForensicsTimelineBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/forensics_timeline.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "timelines": {},
            "timeline_counter": 1,
            "event_types": ["MESSAGE", "EDIT", "DELETE", "JOIN", "LEAVE", "ROLE_CHANGE", "PERMISSION_CHANGE", "BAN", "KICK", "WARNING"]
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    @commands.command(name="create_timeline")
    async def create_timeline(self, ctx, *, investigation_name: str):
        """Create a new forensic timeline."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        timeline_id = f"TL-{self.data['timeline_counter']:04d}"
        self.data['timeline_counter'] += 1
        
        timeline = {
            "timeline_id": timeline_id,
            "investigation_name": investigation_name,
            "created_by": str(ctx.author.id),
            "created_at": datetime.utcnow().isoformat(),
            "events": [],
            "subjects": [],
            "status": "ACTIVE"
        }
        
        self.data["timelines"][timeline_id] = timeline
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Forensic Timeline Created",
            description=investigation_name,
            color=discord.Color.green()
        )
        embed.add_field(name="Timeline ID", value=timeline_id, inline=True)
        embed.add_field(name="Status", value="ACTIVE", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="add_event")
    async def add_event(self, ctx, timeline_id: str, event_type: str, *, event_description: str):
        """Add an event to forensic timeline."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if timeline_id not in self.data["timelines"]:
            await ctx.send("❌ Timeline not found.")
            return
        
        if event_type.upper() not in self.data["event_types"]:
            await ctx.send(f"❌ Invalid event type. Use: {', '.join(self.data['event_types'])}")
            return
        
        timeline = self.data["timelines"][timeline_id]
        
        event = {
            "event_id": f"EVT-{len(timeline['events']) + 1:05d}",
            "type": event_type.upper(),
            "description": event_description,
            "timestamp": datetime.utcnow().isoformat(),
            "recorded_by": str(ctx.author.id),
            "metadata": {}
        }
        
        timeline["events"].append(event)
        self.save_data(self.data)
        
        embed = discord.Embed(
            title=f"✅ Event Added to {timeline_id}",
            description=event_description,
            color=discord.Color.green()
        )
        embed.add_field(name="Event ID", value=event["event_id"], inline=True)
        embed.add_field(name="Type", value=event_type.upper(), inline=True)
        embed.add_field(name="Total Events", value=str(len(timeline["events"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="view_timeline")
    async def view_timeline(self, ctx, timeline_id: str, event_type: str = "ALL"):
        """View forensic timeline."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if timeline_id not in self.data["timelines"]:
            await ctx.send("❌ Timeline not found.")
            return
        
        timeline = self.data["timelines"][timeline_id]
        
        # Filter events
        events = timeline["events"]
        if event_type != "ALL" and event_type.upper() in self.data["event_types"]:
            events = [e for e in events if e["type"] == event_type.upper()]
        
        embed = discord.Embed(
            title=f"📊 Forensic Timeline: {timeline_id}",
            description=timeline["investigation_name"],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Status", value=timeline["status"], inline=True)
        embed.add_field(name="Total Events", value=str(len(timeline["events"])), inline=True)
        embed.add_field(name="Filtered Events", value=str(len(events)), inline=True)
        
        # Show last 10 events
        for event in events[-10:]:
            embed.add_field(
                name=f"{event['type']}: {event['event_id']}",
                value=f"{event['description'][:100]}\n{event['timestamp'][:19]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="export_timeline")
    async def export_timeline(self, ctx, timeline_id: str):
        """Export timeline as JSON."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if timeline_id not in self.data["timelines"]:
            await ctx.send("❌ Timeline not found.")
            return
        
        timeline = self.data["timelines"][timeline_id]
        
        # Create export file
        export_filename = f"timeline_{timeline_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = os.path.join("data", "exports", export_filename)
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        with open(export_path, 'w') as f:
            json.dump(timeline, f, indent=2, default=str)
        
        embed = discord.Embed(
            title="✅ Timeline Exported",
            description=f"Exported to: `{export_path}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Timeline", value=timeline_id, inline=True)
        embed.add_field(name="Events", value=str(len(timeline["events"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="list_timelines")
    async def list_timelines(self, ctx):
        """List all forensic timelines."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        embed = discord.Embed(
            title="📊 Forensic Timelines",
            description=f"Total: {len(self.data['timelines'])} timelines",
            color=discord.Color.blue()
        )
        
        for timeline_id, timeline in self.data["timelines"].items():
            status_emoji = "🟢" if timeline["status"] == "ACTIVE" else "⚫"
            embed.add_field(
                name=f"{status_emoji} {timeline_id}",
                value=f"{timeline['investigation_name'][:50]}\nEvents: {len(timeline['events'])}\nCreated: {timeline['created_at'][:19]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="timeline_stats")
    async def timeline_stats(self, ctx, timeline_id: str):
        """View timeline statistics."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        if timeline_id not in self.data["timelines"]:
            await ctx.send("❌ Timeline not found.")
            return
        
        timeline = self.data["timelines"][timeline_id]
        
        # Calculate stats
        event_type_counts = {}
        for event in timeline["events"]:
            event_type = event["type"]
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        embed = discord.Embed(
            title=f"📊 Timeline Statistics: {timeline_id}",
            description=timeline["investigation_name"],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Events", value=str(len(timeline["events"])), inline=True)
        embed.add_field(name="Status", value=timeline["status"], inline=True)
        
        for event_type, count in sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=event_type, value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ForensicsTimelineBuilderCog(bot))
