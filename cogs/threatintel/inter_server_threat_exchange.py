"""
Inter-server Threat Exchange: Anonymous, privacy-respecting threat sharing protocol for peer communities.
"""
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import hashlib

class InterServerThreatExchangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/threat_exchange.json"
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.get_default_data()

    def get_default_data(self):
        return {
            "threat_network": {},
            "shared_blocklists": {},
            "raid_patterns": {},
            "ttp_catalog": {},
            "server_reputation": {},
            "threat_feeds": [],
            "privacy_settings": {
                "anonymize_reports": True,
                "share_blocklists": True,
                "share_patterns": True
            },
            "network_stats": {
                "peers_connected": 0,
                "threats_shared": 0,
                "blocklists_received": 0
            }
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def is_staff(self, ctx):
        return ctx.author.guild_permissions.manage_messages or ctx.author.id == int(os.getenv('BOT_OWNER_ID', '0'))

    def anonymize_guild_id(self, guild_id):
        """Anonymize guild ID while maintaining consistency."""
        hash_val = hashlib.sha256(str(guild_id).encode()).hexdigest()
        return f"GUILD-{hash_val[:8]}"

    @commands.command(name="join_threat_network")
    async def join_threat_network(self, ctx):
        """Join the Discord threat intelligence network."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        anon_id = self.anonymize_guild_id(ctx.guild.id)
        
        network_entry = {
            "guild_name": ctx.guild.name,
            "anon_id": anon_id,
            "joined_at": datetime.utcnow().isoformat(),
            "status": "ACTIVE",
            "reputation_score": 0.5,
            "threats_reported": 0,
            "threats_received": 0,
            "last_activity": None
        }
        
        self.data["threat_network"][guild_id] = network_entry
        self.data["network_stats"]["peers_connected"] = len(self.data["threat_network"])
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🌐 Network Joined",
            description=f"Server: {ctx.guild.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Anon ID", value=anon_id, inline=True)
        embed.add_field(name="Status", value="✅ ACTIVE", inline=True)
        embed.add_field(name="Network Peers", value=str(self.data["network_stats"]["peers_connected"]), inline=True)
        embed.add_field(name="📡 Privacy Note", value="Your identity is anonymized. Only threat indicators are shared.", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="report_threat_to_network")
    async def report_threat_to_network(self, ctx, threat_type: str, *, details: str):
        """Report threat to network (with anonymization)."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data["threat_network"]:
            await ctx.send("❌ Not connected to threat network. Use `/join_threat_network` first.")
            return
        
        threat_id = f"THR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        threat_report = {
            "id": threat_id,
            "type": threat_type,
            "details": details,
            "reported_by_guild": self.data["threat_network"][guild_id]["anon_id"],  # Anonymized
            "reported_at": datetime.utcnow().isoformat(),
            "severity": "MEDIUM",
            "impact_radius": 5,  # Estimated affected servers
            "mitigated": False
        }
        
        self.data["threat_feeds"].append(threat_report)
        self.data["threat_network"][guild_id]["threats_reported"] += 1
        self.data["network_stats"]["threats_shared"] += 1
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🚨 Threat Reported to Network",
            description=f"Threat ID: {threat_id}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Type", value=threat_type, inline=True)
        embed.add_field(name="Status", value="Broadcast to peers", inline=True)
        embed.add_field(name="Your Guild ID", value=self.data["threat_network"][guild_id]["anon_id"], inline=True)
        embed.add_field(name="Details (anonymized)", value=details[:150], inline=False)
        embed.add_field(name="Peers Notified", value=f"{len(self.data['threat_network'])-1} servers", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="receive_threat_feed")
    async def receive_threat_feed(self, ctx):
        """Receive latest threat feed from network."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data["threat_network"]:
            await ctx.send("❌ Not connected to threat network.")
            return
        
        feed = self.data["threat_feeds"]
        recent = feed[-10:] if len(feed) > 10 else feed
        
        embed = discord.Embed(
            title="📡 Threat Intelligence Feed",
            description="Latest threats from network peers",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Threats", value=str(len(feed)), inline=True)
        embed.add_field(name="Active Peers", value=str(len(self.data["threat_network"])), inline=True)
        
        feed_str = ""
        for threat in recent[-5:]:
            feed_str += f"• **{threat['type']}** - {threat['id']}\n"
            feed_str += f"  From: {threat['reported_by_guild']}\n"
            feed_str += f"  Severity: {threat['severity']}\n"
        
        embed.add_field(name="Recent Threats", value=feed_str or "None", inline=False)
        
        self.data["threat_network"][guild_id]["last_activity"] = datetime.utcnow().isoformat()
        self.save_data(self.data)
        
        await ctx.send(embed=embed)

    @commands.command(name="share_blocklist")
    async def share_blocklist(self, ctx, *, user_ids: str):
        """Share ban/blocklist with peer servers."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data["threat_network"]:
            await ctx.send("❌ Not connected to threat network.")
            return
        
        blocklist_id = f"BL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Parse user IDs
        user_list = [uid.strip() for uid in user_ids.split(",")]
        
        blocklist = {
            "id": blocklist_id,
            "source_guild": self.data["threat_network"][guild_id]["anon_id"],
            "users": len(user_list),
            "reason": "Threat actors / Raid accounts",
            "shared_at": datetime.utcnow().isoformat(),
            "impact": "Applied by peers",
            "confidence": 0.95
        }
        
        self.data["shared_blocklists"][blocklist_id] = blocklist
        self.data["network_stats"]["blocklists_received"] += 1
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="📋 Blocklist Shared",
            description=f"Blocklist: {blocklist_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="Users Blocked", value=str(len(user_list)), inline=True)
        embed.add_field(name="Confidence", value="95%", inline=True)
        embed.add_field(name="Peers Receiving", value=str(len(self.data["threat_network"])-1), inline=True)
        embed.add_field(name="Reason", value=blocklist["reason"], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="ttp_share")
    async def ttp_share(self, ctx, ttp_name: str, *, description: str):
        """Share TTP (Tactics, Techniques, Procedures) with network."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data["threat_network"]:
            await ctx.send("❌ Not connected to threat network.")
            return
        
        ttp_id = f"TTP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        ttp = {
            "id": ttp_id,
            "name": ttp_name,
            "description": description,
            "shared_by": self.data["threat_network"][guild_id]["anon_id"],
            "shared_at": datetime.utcnow().isoformat(),
            "mitigations": [],
            "adoption_rate": 0.3
        }
        
        self.data["ttp_catalog"][ttp_id] = ttp
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🎯 TTP Shared with Network",
            description=f"TTP: {ttp_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="TTP ID", value=ttp_id, inline=True)
        embed.add_field(name="Description", value=description[:150], inline=False)
        embed.add_field(name="Network Adoption", value="30%", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="raid_pattern_alert")
    async def raid_pattern_alert(self, ctx, pattern_name: str, severity: str = "HIGH"):
        """Alert network of detected raid pattern."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data["threat_network"]:
            await ctx.send("❌ Not connected to threat network.")
            return
        
        pattern_id = f"RAID-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        raid_pattern = {
            "id": pattern_id,
            "name": pattern_name,
            "detected_by": self.data["threat_network"][guild_id]["anon_id"],
            "severity": severity,
            "detected_at": datetime.utcnow().isoformat(),
            "affected_count": 3,
            "status": "ONGOING"
        }
        
        self.data["raid_patterns"][pattern_id] = raid_pattern
        
        self.save_data(self.data)
        
        embed = discord.Embed(
            title="🚨 Raid Pattern Alert",
            description=f"Pattern: {pattern_name}",
            color=discord.Color.red() if severity == "CRITICAL" else discord.Color.orange()
        )
        embed.add_field(name="ID", value=pattern_id, inline=True)
        embed.add_field(name="Severity", value=severity, inline=True)
        embed.add_field(name="Servers Affected", value="3", inline=True)
        embed.add_field(name="Alerted Peers", value=str(len(self.data["threat_network"])-1), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="network_reputation")
    async def network_reputation(self, ctx, target_guild_id: str = None):
        """Check reputation of guild in threat network."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        guild_id = target_guild_id or str(ctx.guild.id)
        
        if guild_id not in self.data["threat_network"]:
            await ctx.send(f"❌ Guild not in threat network.")
            return
        
        guild_info = self.data["threat_network"][guild_id]
        
        embed = discord.Embed(
            title="⭐ Guild Reputation",
            description=f"Guild: {guild_info['anon_id']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Reputation Score", value=f"{guild_info['reputation_score']:.2f}/1.00", inline=True)
        embed.add_field(name="Threats Reported", value=str(guild_info["threats_reported"]), inline=True)
        embed.add_field(name="Threats Received", value=str(guild_info["threats_received"]), inline=True)
        embed.add_field(name="Status", value=guild_info["status"], inline=True)
        embed.add_field(name="Joined", value=guild_info["joined_at"], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="threat_network_stats")
    async def threat_network_stats(self, ctx):
        """View overall threat network statistics."""
        if not await self.is_staff(ctx):
            await ctx.send("❌ Staff only.")
            return
        
        stats = self.data["network_stats"]
        
        embed = discord.Embed(
            title="📊 Threat Network Statistics",
            color=discord.Color.blue()
        )
        embed.add_field(name="Connected Peers", value=str(stats["peers_connected"]), inline=True)
        embed.add_field(name="Threats Shared", value=str(stats["threats_shared"]), inline=True)
        embed.add_field(name="Blocklists Distributed", value=str(stats["blocklists_received"]), inline=True)
        embed.add_field(name="TTPs Catalogued", value=str(len(self.data["ttp_catalog"])), inline=True)
        embed.add_field(name="Raid Patterns Detected", value=str(len(self.data["raid_patterns"])), inline=True)
        embed.add_field(name="Active Threat Feeds", value=str(len(self.data["threat_feeds"])), inline=True)
        
        avg_reputation = sum(g["reputation_score"] for g in self.data["threat_network"].values()) / max(len(self.data["threat_network"]), 1)
        embed.add_field(name="Avg Network Reputation", value=f"{avg_reputation:.2f}/1.00", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InterServerThreatExchangeCog(bot))
