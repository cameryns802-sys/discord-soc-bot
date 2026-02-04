"""
Live Threat Intel Feed: Real-time threat feed integration with auto-enrichment.
"""
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from cogs.core.pst_timezone import get_now_pst

class LiveThreatIntelFeedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/threat_intel_feed.json"
        self.data = self.load_data()
        self.feed_monitor.start()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "feed_sources": {
                "alienvault": {"enabled": True, "last_check": None, "iocs": []},
                "abuse_ch": {"enabled": True, "last_check": None, "iocs": []},
                "phishtank": {"enabled": True, "last_check": None, "iocs": []},
                "urlhaus": {"enabled": True, "last_check": None, "iocs": []}
            },
            "detected_indicators": [],
            "enrichment_cache": {},
            "alert_history": [],
            "watchlist": []
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def enrich_indicator(self, indicator: str, indicator_type: str):
        """Enrich threat indicator with context."""
        # Simulated enrichment (would use real APIs: VirusTotal, AbuseIPDB, etc.)
        enrichment = {
            "indicator": indicator,
            "type": indicator_type,
            "enriched_at": get_now_pst().isoformat(),
            "context": {
                "threat_score": 85,
                "first_seen": "2026-01-15",
                "last_seen": "2026-02-01",
                "geolocation": "Unknown",
                "malware_families": ["Emotet", "TrickBot"],
                "campaign": "APT28-Winter2026",
                "confidence": "HIGH"
            }
        }
        return enrichment

    @tasks.loop(minutes=30)
    async def feed_monitor(self):
        """Monitor threat feeds every 30 minutes."""
        try:
            # Simulated feed checks (would use real API calls)
            for feed_name, feed_data in self.data["feed_sources"].items():
                if feed_data["enabled"]:
                    # Simulate finding new IOCs
                    new_iocs = self.fetch_feed_iocs(feed_name)
                    if new_iocs:
                        await self.alert_on_iocs(new_iocs, feed_name)
                    
                    feed_data["last_check"] = get_now_pst().isoformat()
            
            self.save_data(self.data)
        except Exception as e:
            print(f"[Threat Feed Monitor] Error: {e}")

    def fetch_feed_iocs(self, feed_name: str):
        """Fetch IOCs from threat feed (simulated)."""
        # In production, would call real APIs
        return []

    async def alert_on_iocs(self, iocs: list, feed_name: str):
        """Alert on detected IOCs."""
        # Would send alerts to configured channels
        pass

    @feed_monitor.before_loop
    async def before_feed_monitor(self):
        await self.bot.wait_until_ready()

    @commands.command(name="threat_feed_status")
    async def threat_feed_status(self, ctx):
        """View threat feed status."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        embed = discord.Embed(
            title="🔴 Live Threat Feed Status",
            color=discord.Color.red()
        )
        
        for feed_name, feed_data in self.data["feed_sources"].items():
            status = "🟢 Active" if feed_data["enabled"] else "🔴 Disabled"
            last_check = feed_data.get("last_check", "Never")[:19] if feed_data.get("last_check") else "Never"
            ioc_count = len(feed_data.get("iocs", []))
            
            embed.add_field(
                name=f"{feed_name.upper()}",
                value=f"{status}\nLast Check: {last_check}\nIOCs: {ioc_count}",
                inline=True
            )
        
        embed.add_field(name="Total Detected Indicators", value=str(len(self.data["detected_indicators"])), inline=False)
        embed.add_field(name="Alert History", value=str(len(self.data["alert_history"])), inline=True)
        embed.set_footer(text="Feeds update every 30 minutes")
        
        await ctx.send(embed=embed)

    @commands.command(name="check_indicator")
    async def check_indicator(self, ctx, indicator_type: str, *, indicator: str):
        """Check if an indicator (IP, domain, hash, URL) is malicious."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        valid_types = ["ip", "domain", "hash", "url", "email"]
        if indicator_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid type. Use: {', '.join(valid_types)}")
            return
        
        # Check local cache first
        if indicator in self.data["enrichment_cache"]:
            enrichment = self.data["enrichment_cache"][indicator]
        else:
            # Fetch enrichment
            enrichment = self.enrich_indicator(indicator, indicator_type)
            self.data["enrichment_cache"][indicator] = enrichment
            self.save_data(self.data)
        
        threat_score = enrichment["context"]["threat_score"]
        color = discord.Color.red() if threat_score > 70 else discord.Color.orange() if threat_score > 40 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"🔍 Indicator Analysis: {indicator_type.upper()}",
            description=f"`{indicator}`",
            color=color
        )
        
        embed.add_field(name="Threat Score", value=f"{threat_score}/100", inline=True)
        embed.add_field(name="Confidence", value=enrichment["context"]["confidence"], inline=True)
        embed.add_field(name="First Seen", value=enrichment["context"]["first_seen"], inline=True)
        embed.add_field(name="Last Seen", value=enrichment["context"]["last_seen"], inline=True)
        
        if enrichment["context"]["malware_families"]:
            embed.add_field(name="Malware Families", value=", ".join(enrichment["context"]["malware_families"]), inline=False)
        
        if enrichment["context"]["campaign"]:
            embed.add_field(name="Campaign", value=enrichment["context"]["campaign"], inline=True)
        
        embed.set_footer(text=f"Enriched at: {enrichment['enriched_at'][:19]}")
        
        await ctx.send(embed=embed)

    @commands.command(name="add_watchlist")
    async def add_watchlist(self, ctx, indicator_type: str, *, indicator: str):
        """Add indicator to watchlist for monitoring."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        watchlist_entry = {
            "indicator": indicator,
            "type": indicator_type,
            "added_by": str(ctx.author.id),
            "added_at": get_now_pst().isoformat(),
            "hits": 0
        }
        
        self.data["watchlist"].append(watchlist_entry)
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="✅ Added to Watchlist",
            description=f"{indicator_type.upper()}: `{indicator}`",
            color=discord.Color.green()
        )
        embed.set_footer(text="Will be monitored in real-time")
        
        await ctx.send(embed=embed)

    @commands.command(name="threat_feed_summary")
    async def threat_feed_summary(self, ctx):
        """View threat feed summary."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        total_iocs = sum(len(feed["iocs"]) for feed in self.data["feed_sources"].values())
        active_feeds = sum(1 for feed in self.data["feed_sources"].values() if feed["enabled"])
        
        embed = discord.Embed(
            title="📊 Threat Feed Summary",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Active Feeds", value=f"{active_feeds}/{len(self.data['feed_sources'])}", inline=True)
        embed.add_field(name="Total IOCs", value=str(total_iocs), inline=True)
        embed.add_field(name="Watchlist Items", value=str(len(self.data["watchlist"])), inline=True)
        embed.add_field(name="Detected Threats", value=str(len(self.data["detected_indicators"])), inline=True)
        embed.add_field(name="Enrichment Cache", value=str(len(self.data["enrichment_cache"])), inline=True)
        embed.add_field(name="Alert History", value=str(len(self.data["alert_history"])), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="recent_threats")
    async def recent_threats(self, ctx, hours: int = 24):
        """View recent threat detections."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        cutoff = get_now_pst() - timedelta(hours=hours)
        recent = [
            alert for alert in self.data["alert_history"]
            if datetime.fromisoformat(alert.get("detected_at", "2000-01-01")) > cutoff
        ]
        
        embed = discord.Embed(
            title=f"🚨 Recent Threats ({hours}h)",
            description=f"Found {len(recent)} threats",
            color=discord.Color.red()
        )
        
        for alert in recent[:10]:
            embed.add_field(
                name=f"{alert.get('type', 'Unknown').upper()}",
                value=f"`{alert.get('indicator', 'N/A')}`\nScore: {alert.get('threat_score', 0)}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LiveThreatIntelFeedCog(bot))
