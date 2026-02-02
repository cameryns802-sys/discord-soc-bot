# Observability: Real-time event streaming, correlation, and trend analysis
import discord
from discord.ext import commands
import datetime

class ObservabilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_stream = []
        self.correlations = []
        self.trends = {}
        self.event_types = {}

    @commands.command()
    async def obs_stream(self, ctx, limit: int = 10):
        """View real-time event stream."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.event_stream:
            await ctx.send("No events recorded.")
            return
        recent = self.event_stream[-limit:]
        desc = "\n".join([f"**{e['type'].upper()}** - {e['description']} ({e['time'].strftime('%H:%M:%S')})" for e in recent])
        embed = discord.Embed(title="Event Stream", description=desc, color=discord.Color.blue())
        embed.set_footer(text=f"Total Events: {len(self.event_stream)}")
        await ctx.send(embed=embed)

    @commands.command()
    async def obs_inject_event(self, ctx, event_type: str, *, description: str):
        """Inject test event into stream (admin)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        self.event_stream.append({
            "type": event_type.lower(),
            "description": description,
            "time": datetime.datetime.utcnow(),
            "source": ctx.author.mention
        })
        self.event_types[event_type.lower()] = self.event_types.get(event_type.lower(), 0) + 1
        embed = discord.Embed(title="Event Injected", description=description, color=discord.Color.green())
        embed.add_field(name="Type", value=event_type.upper(), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def obs_correlation(self, ctx):
        """View correlated events (attack patterns)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if len(self.event_stream) < 3:
            await ctx.send("Not enough events for correlation analysis.")
            return
        # Simple correlation: multiple events of same type in short window
        from collections import Counter
        recent_types = [e['type'] for e in self.event_stream[-20:]]
        event_counts = Counter(recent_types)
        
        desc = "\n".join([f"**{etype.upper()}**: {count} events" for etype, count in event_counts.most_common(5)])
        embed = discord.Embed(title="Event Correlations (Last 20)", description=desc, color=discord.Color.orange())
        embed.add_field(name="Analysis", value="Pattern detected: Multiple events suggest coordinated activity", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def obs_trends(self, ctx):
        """View event trends over time."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.event_stream:
            await ctx.send("No event data.")
            return
        total = len(self.event_stream)
        last_10_min = len([e for e in self.event_stream if (datetime.datetime.utcnow() - e['time']).seconds < 600])
        from collections import Counter
        top_events = Counter([e['type'] for e in self.event_stream]).most_common(5)
        desc = "\n".join([f"**{t[0].upper()}**: {t[1]} occurrences" for t in top_events])
        embed = discord.Embed(title="Event Trends", description=desc, color=discord.Color.blue())
        embed.add_field(name="Total Events", value=str(total), inline=True)
        embed.add_field(name="Last 10 min", value=str(last_10_min), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def obs_timeline(self, ctx):
        """View incident timeline with correlated events."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.event_stream:
            await ctx.send("No timeline data.")
            return
        # Group by minute
        from collections import defaultdict
        timeline = defaultdict(int)
        for event in self.event_stream[-60:]:  # Last 60 events
            minute = event['time'].strftime("%H:%M")
            timeline[minute] += 1
        desc = "\n".join([f"{time}: {count} events" for time, count in sorted(timeline.items())[-10:]])
        embed = discord.Embed(title="Activity Timeline (Last 60 Events)", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def obs_anomaly_score(self, ctx):
        """Calculate current anomaly score."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return
        if not self.event_stream:
            score = 0
        else:
            # Simple anomaly: rapid events = higher score
            recent = [e for e in self.event_stream if (datetime.datetime.utcnow() - e['time']).seconds < 300]
            score = min(100, len(recent) * 5)
        color = discord.Color.red() if score > 70 else discord.Color.orange() if score > 40 else discord.Color.green()
        embed = discord.Embed(title="Anomaly Score", color=color)
        embed.add_field(name="Score", value=f"{score}/100", inline=True)
        embed.add_field(name="Status", value="🔴 HIGH" if score > 70 else "🟡 MEDIUM" if score > 40 else "🟢 LOW", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ObservabilityCog(bot))
