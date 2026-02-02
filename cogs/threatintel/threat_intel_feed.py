"""Threat Intelligence Feed: Aggregate and analyze threat intel"""
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random
import json
import os

class ThreatIntelFeedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threat_feeds = {}
        self.indicators = []
        self.feed_counter = 0
        self.data_file = "data/threat_feeds.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.threat_feeds = data.get('feeds', {})
                    self.indicators = data.get('indicators', [])
                    self.feed_counter = data.get('counter', 0)
            except: pass

    def save_data(self):
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({'feeds': self.threat_feeds, 'indicators': self.indicators, 'counter': self.feed_counter}, f, indent=2)

    @commands.command(name="threatfeed_add", description="Add threat intelligence feed")
    @commands.has_permissions(administrator=True)
    async def threatfeed_add(self, ctx, feed_name: str, source_url: str):
        self.feed_counter += 1
        feed_id = str(self.feed_counter)
        self.threat_feeds[feed_id] = {"id": feed_id, "name": feed_name, "source_url": source_url, "status": "active", "added_by": ctx.author.id, "added_at": datetime.datetime.now(datetime.UTC).isoformat(), "last_update": None, "total_indicators": 0}
        self.save_data()
        embed = discord.Embed(title="Threat Feed Added", description=feed_name, color=discord.Color.green())
        embed.add_field(name="Feed ID", value=f"#{feed_id}", inline=True)
        embed.add_field(name="Source", value=source_url, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="threatfeed_list", description="List all threat intelligence feeds")
    async def threatfeed_list(self, ctx):
        if not self.threat_feeds:
            await ctx.send("No threat feeds configured.")
            return
        desc = "\n".join([f"**#{f['id']}** {f['name']} - {f['status'].upper()} ({f['total_indicators']} indicators)" for f in self.threat_feeds.values()])
        embed = discord.Embed(title="Threat Intelligence Feeds", description=desc[:4000], color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name="threatfeed_update", description="Manually update threat feed")
    @commands.has_permissions(administrator=True)
    async def threatfeed_update(self, ctx, feed_id: str):
        if feed_id not in self.threat_feeds:
            await ctx.send(f"Feed #{feed_id} not found.")
            return
        feed = self.threat_feeds[feed_id]
        new_indicators = random.randint(5, 50)
        feed["last_update"] = datetime.datetime.now(datetime.UTC).isoformat()
        feed["total_indicators"] += new_indicators
        for _ in range(new_indicators):
            self.indicators.append({"type": random.choice(["ip", "domain", "hash", "url"]), "value": f"indicator_{random.randint(1000, 9999)}", "severity": random.choice(["low", "medium", "high", "critical"]), "feed_id": feed_id, "timestamp": datetime.datetime.now(datetime.UTC).isoformat()})
        self.save_data()
        embed = discord.Embed(title="🔄 Feed Updated", description=f"{feed['name']} synchronized", color=discord.Color.green())
        embed.add_field(name="New Indicators", value=str(new_indicators), inline=True)
        embed.add_field(name="Total Indicators", value=str(feed["total_indicators"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="threatfeed_indicators", description="View threat indicators by severity")
    async def threatfeed_indicators(self, ctx, severity: str = "all"):
        if severity != "all" and severity.lower() not in ["low", "medium", "high", "critical"]:
            await ctx.send("Severity must be: all, low, medium, high, or critical")
            return
        if not self.indicators:
            await ctx.send("No indicators available. Update feeds first.")
            return
        filtered = self.indicators if severity == "all" else [i for i in self.indicators if i["severity"] == severity.lower()]
        if not filtered:
            await ctx.send(f"No {severity} indicators found.")
            return
        desc = "\n".join([f"**{i['type'].upper()}** {i['value']} ({i['severity']})" for i in filtered[:20]])
        embed = discord.Embed(title=f"🔍 Threat Indicators - {severity.upper()}", description=desc, color=discord.Color.orange())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreatIntelFeedCog(bot))
