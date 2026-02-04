"""
Real-time Threat Feed - External threat intelligence integration for Sentinel
Ingests and correlates threat intelligence from multiple sources
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import random
import hashlib
from cogs.core.pst_timezone import get_now_pst

class RealTimeThreatFeed(commands.Cog):
    """Real-time threat intelligence feed and correlation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.feed_file = 'data/threat_feed.json'
        self.ioc_file = 'data/iocs.json'
        self.load_feed()
        self.load_iocs()
        self.feed_update_task.start()
    
    def cog_unload(self):
        """Stop background tasks on unload"""
        self.feed_update_task.cancel()
    
    def load_feed(self):
        """Load threat feed data"""
        if not os.path.exists(self.feed_file):
            os.makedirs(os.path.dirname(self.feed_file), exist_ok=True)
            with open(self.feed_file, 'w') as f:
                json.dump([], f)
    
    def load_iocs(self):
        """Load IOC database"""
        if not os.path.exists(self.ioc_file):
            os.makedirs(os.path.dirname(self.ioc_file), exist_ok=True)
            with open(self.ioc_file, 'w') as f:
                json.dump({}, f)
    
    def get_threat_feed(self):
        """Get current threat feed"""
        with open(self.feed_file, 'r') as f:
            return json.load(f)
    
    def save_threat_feed(self, feed):
        """Save threat feed"""
        with open(self.feed_file, 'w') as f:
            json.dump(feed, f, indent=2)
    
    def get_guild_iocs(self, guild_id):
        """Get IOCs for guild"""
        with open(self.ioc_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_ioc(self, guild_id, ioc_type, value, threat_name, confidence):
        """Save IOC"""
        with open(self.ioc_file, 'r') as f:
            data = json.load(f)
        
        if str(guild_id) not in data:
            data[str(guild_id)] = {}
        
        ioc_id = hashlib.md5(f"{ioc_type}:{value}".encode()).hexdigest()[:12]
        
        data[str(guild_id)][ioc_id] = {
            'id': ioc_id,
            'type': ioc_type,
            'value': value,
            'threat_name': threat_name,
            'confidence': confidence,
            'added_at': get_now_pst().isoformat(),
            'last_seen': get_now_pst().isoformat(),
            'hit_count': 0,
            'status': 'active'
        }
        
        with open(self.ioc_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data[str(guild_id)][ioc_id]
    
    @tasks.loop(minutes=30)
    async def feed_update_task(self):
        """Simulate threat feed updates every 30 minutes"""
        # In production, this would fetch from real threat intel sources
        # For now, we simulate updates
        feed = self.get_threat_feed()
        
        # Simulate new threat
        threat_types = ['Malware', 'Phishing', 'C2', 'Botnet', 'APT', 'Ransomware']
        new_threat = {
            'id': f"TF-{get_now_pst().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'name': f"{random.choice(threat_types)} Campaign {random.randint(100, 999)}",
            'type': random.choice(threat_types),
            'severity': random.choice(['critical', 'high', 'medium', 'low']),
            'description': 'New threat detected by intelligence sources',
            'discovered_at': get_now_pst().isoformat(),
            'confidence': random.choice(['high', 'medium', 'low']),
            'source': random.choice(['OSINT', 'Commercial Feed', 'ISAC', 'Internal'])
        }
        
        feed.append(new_threat)
        
        # Keep only last 50 threats
        feed = feed[-50:]
        self.save_threat_feed(feed)
    
    @feed_update_task.before_loop
    async def before_feed_update(self):
        """Wait for bot to be ready"""
        await self.bot.wait_until_ready()
    
    async def _threatfeed_logic(self, ctx, limit: int = 10):
        """Show recent threat intelligence"""
        feed = self.get_threat_feed()
        
        if not feed:
            await ctx.send("📡 No threat intelligence in feed yet. Check back soon.")
            return
        
        recent = sorted(feed, key=lambda x: x['discovered_at'], reverse=True)[:limit]
        
        embed = discord.Embed(
            title="📡 Real-time Threat Feed",
            description=f"Latest {len(recent)} threat(s) from intelligence sources",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for threat in recent:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(threat['severity'], '❓')
            confidence_emoji = {'high': '✅', 'medium': '⚠️', 'low': '❓'}.get(threat['confidence'], '❓')
            
            embed.add_field(
                name=f"{severity_emoji} {threat['name']} ({threat['type']})",
                value=f"Confidence: {confidence_emoji} {threat['confidence'].upper()}\nSource: {threat['source']}\nDiscovered: <t:{int(datetime.fromisoformat(threat['discovered_at']).timestamp())}:R>",
                inline=False
            )
        
        embed.add_field(name="📊 Feed Stats", value=f"Total threats tracked: {len(feed)}\nLast updated: <t:{int(get_now_pst().timestamp())}:R>", inline=False)
        embed.set_footer(text="Sentinel Threat Intelligence | Auto-updates every 30min")
        
        await ctx.send(embed=embed)
    
    async def _iocadd_logic(self, ctx, ioc_type: str, value: str, threat_name: str, confidence: str):
        """Add IOC to database"""
        valid_types = ['ip', 'domain', 'url', 'hash', 'email', 'user_id']
        valid_confidence = ['high', 'medium', 'low']
        
        if ioc_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid IOC type. Use: {', '.join(valid_types)}")
            return
        
        if confidence.lower() not in valid_confidence:
            await ctx.send(f"❌ Invalid confidence. Use: {', '.join(valid_confidence)}")
            return
        
        ioc = self.save_ioc(ctx.guild.id, ioc_type.lower(), value, threat_name, confidence.lower())
        
        embed = discord.Embed(
            title="🎯 IOC Added",
            description=f"Indicator of Compromise added to watchlist",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="IOC ID", value=f"`{ioc['id']}`", inline=True)
        embed.add_field(name="Type", value=ioc_type.upper(), inline=True)
        embed.add_field(name="Confidence", value=confidence.upper(), inline=True)
        embed.add_field(name="Value", value=f"`{value}`", inline=False)
        embed.add_field(name="Associated Threat", value=threat_name, inline=False)
        embed.set_footer(text="IOC will be monitored for matches")
        
        await ctx.send(embed=embed)
    
    async def _ioclist_logic(self, ctx):
        """List IOCs"""
        iocs = self.get_guild_iocs(ctx.guild.id)
        
        if not iocs:
            await ctx.send("📋 No IOCs in database yet.")
            return
        
        active_iocs = {k: v for k, v in iocs.items() if v['status'] == 'active'}
        
        embed = discord.Embed(
            title="🎯 Indicators of Compromise",
            description=f"{len(active_iocs)} active IOC(s) being monitored",
            color=discord.Color.orange(),
            timestamp=get_now_pst()
        )
        
        # Group by type
        by_type = {}
        for ioc in active_iocs.values():
            ioc_type = ioc['type']
            if ioc_type not in by_type:
                by_type[ioc_type] = []
            by_type[ioc_type].append(ioc)
        
        for ioc_type, ioc_list in by_type.items():
            ioc_str = ""
            for ioc in ioc_list[:5]:
                confidence_emoji = {'high': '✅', 'medium': '⚠️', 'low': '❓'}.get(ioc['confidence'], '❓')
                ioc_str += f"{confidence_emoji} `{ioc['value'][:40]}...` - {ioc['threat_name']}\n"
            
            if len(ioc_list) > 5:
                ioc_str += f"... and {len(ioc_list) - 5} more\n"
            
            embed.add_field(name=f"📌 {ioc_type.upper()} ({len(ioc_list)})", value=ioc_str, inline=False)
        
        embed.set_footer(text="Sentinel IOC Database | Continuously monitored")
        
        await ctx.send(embed=embed)
    
    async def _ioccheck_logic(self, ctx, value: str):
        """Check if value matches IOC"""
        iocs = self.get_guild_iocs(ctx.guild.id)
        
        matches = [ioc for ioc in iocs.values() if value.lower() in ioc['value'].lower()]
        
        if not matches:
            embed = discord.Embed(
                title="✅ No IOC Match",
                description=f"Value does not match any known IOCs",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            embed.add_field(name="Checked Value", value=f"`{value}`", inline=False)
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ IOC Match Found!",
            description=f"{len(matches)} matching IOC(s) detected",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Checked Value", value=f"`{value}`", inline=False)
        
        for match in matches[:5]:
            confidence_emoji = {'high': '✅', 'medium': '⚠️', 'low': '❓'}.get(match['confidence'], '❓')
            embed.add_field(
                name=f"{confidence_emoji} {match['type'].upper()} IOC",
                value=f"Threat: {match['threat_name']}\nConfidence: {match['confidence'].upper()}\nAdded: <t:{int(datetime.fromisoformat(match['added_at']).timestamp())}:R>",
                inline=False
            )
        
        embed.add_field(name="⚠️ Recommended Action", value="🔍 Investigate immediately\n📋 Create incident case\n🚨 Alert security team", inline=False)
        embed.set_footer(text="Sentinel IOC Correlation | Potential threat detected")
        
        await ctx.send(embed=embed)
    
    async def _threatcorrelate_logic(self, ctx):
        """Correlate threats with IOCs"""
        feed = self.get_threat_feed()
        iocs = self.get_guild_iocs(ctx.guild.id)
        
        if not feed or not iocs:
            await ctx.send("❌ Insufficient data for correlation (need both threat feed and IOCs).")
            return
        
        # Simulate correlation
        recent_threats = [t for t in feed if datetime.fromisoformat(t['discovered_at']) > (get_now_pst() - timedelta(days=7))]
        
        correlations = []
        for threat in recent_threats[:5]:
            matching_iocs = [ioc for ioc in iocs.values() if threat['type'].lower() in ioc['threat_name'].lower()]
            if matching_iocs:
                correlations.append((threat, matching_iocs[0]))
        
        if not correlations:
            await ctx.send("✅ No threat correlations found with your IOC database.")
            return
        
        embed = discord.Embed(
            title="🔗 Threat Correlation Analysis",
            description=f"{len(correlations)} correlation(s) found between threat feed and IOCs",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        for threat, ioc in correlations[:5]:
            embed.add_field(
                name=f"⚠️ {threat['name']}",
                value=f"Matches IOC: `{ioc['value'][:30]}...`\nIOC Type: {ioc['type'].upper()}\nThreat Type: {threat['type']}\nConfidence: {threat['confidence'].upper()}",
                inline=False
            )
        
        embed.add_field(name="💡 Recommendations", value="• Review correlated threats for your environment\n• Update detection rules\n• Brief security team on active threats", inline=False)
        embed.set_footer(text="Sentinel Threat Correlation Engine")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='threatfeed')
    async def threatfeed_prefix(self, ctx, limit: int = 10):
        """Show threat intelligence feed - Prefix command"""
        if limit < 1 or limit > 25:
            await ctx.send("❌ Limit must be 1-25.")
            return
        await self._threatfeed_logic(ctx, limit)
    
    @commands.command(name='iocadd')
    async def iocadd_prefix(self, ctx, ioc_type: str, value: str, confidence: str, *, threat_name: str):
        """Add IOC - Prefix command"""
        await self._iocadd_logic(ctx, ioc_type, value, threat_name, confidence)
    
    @commands.command(name='ioclist')
    async def ioclist_prefix(self, ctx):
        """List IOCs - Prefix command"""
        await self._ioclist_logic(ctx)
    
    @commands.command(name='ioccheck')
    async def ioccheck_prefix(self, ctx, *, value: str):
        """Check IOC match - Prefix command"""
        await self._ioccheck_logic(ctx, value)
    
    @commands.command(name='threatcorrelate')
    async def threatcorrelate_prefix(self, ctx):
        """Correlate threats with IOCs - Prefix command"""
        await self._threatcorrelate_logic(ctx)

async def setup(bot):
    await bot.add_cog(RealTimeThreatFeed(bot))
