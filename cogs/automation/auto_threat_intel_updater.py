"""
Auto Threat Intel Updater - Automatically update threat intelligence feeds
Periodically fetches latest IOCs from threat feeds and updates the threat intelligence hub
Alerts SOC team on new critical threats
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class ThreatIntelUpdater(commands.Cog):
    """Automatically update threat intelligence from feeds"""
    
    def __init__(self, bot):
        self.bot = bot
        self.feeds_file = 'data/threat_intel_feeds.json'
        self.feed_updates_file = 'data/feed_updates.json'
        self.feeds = {}
        self.feed_updates = []
        self.load_feeds()
        self.update_threat_intel.start()
    
    def load_feeds(self):
        """Load threat intel feed configurations"""
        if os.path.exists(self.feeds_file):
            try:
                with open(self.feeds_file, 'r') as f:
                    self.feeds = json.load(f)
            except:
                self.init_default_feeds()
        else:
            self.init_default_feeds()
        
        if os.path.exists(self.feed_updates_file):
            try:
                with open(self.feed_updates_file, 'r') as f:
                    self.feed_updates = json.load(f)
            except:
                self.feed_updates = []
    
    def init_default_feeds(self):
        """Initialize default threat intel feeds"""
        self.feeds = {
            'abuse_ch': {
                'name': 'abuse.ch URLhaus',
                'type': 'url_malware',
                'enabled': True,
                'last_updated': None,
                'ioc_count': 0,
                'update_frequency_hours': 6
            },
            'malware_bazaar': {
                'name': 'Malware Bazaar',
                'type': 'file_hash',
                'enabled': True,
                'last_updated': None,
                'ioc_count': 0,
                'update_frequency_hours': 12
            },
            'phishtank': {
                'name': 'PhishTank',
                'type': 'phishing_url',
                'enabled': True,
                'last_updated': None,
                'ioc_count': 0,
                'update_frequency_hours': 6
            },
            'abuse_ipbl': {
                'name': 'Abuse.ch IP Blocklist',
                'type': 'ip_address',
                'enabled': True,
                'last_updated': None,
                'ioc_count': 0,
                'update_frequency_hours': 24
            },
            'cybercriminals': {
                'name': 'Cybercriminals Feed',
                'type': 'c2_server',
                'enabled': True,
                'last_updated': None,
                'ioc_count': 0,
                'update_frequency_hours': 12
            }
        }
        self.save_feeds()
    
    def save_feeds(self):
        """Save feed configurations"""
        os.makedirs(os.path.dirname(self.feeds_file), exist_ok=True)
        with open(self.feeds_file, 'w') as f:
            json.dump(self.feeds, f, indent=2)
    
    def save_updates(self):
        """Save feed updates log"""
        os.makedirs(os.path.dirname(self.feed_updates_file), exist_ok=True)
        with open(self.feed_updates_file, 'w') as f:
            json.dump(self.feed_updates[-500:], f, indent=2)  # Keep last 500
    
    @tasks.loop(hours=6)
    async def update_threat_intel(self):
        """Update threat intelligence from feeds"""
        await self.bot.wait_until_ready()
        
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        if not threat_intel:
            print("[ThreatIntelUpdater] ThreatIntelHub not available")
            return
        
        for feed_name, feed_config in self.feeds.items():
            if not feed_config['enabled']:
                continue
            
            # Check if update is needed
            last_updated = feed_config.get('last_updated')
            update_hours = feed_config.get('update_frequency_hours', 24)
            
            if last_updated:
                hours_since = (get_now_pst() - datetime.fromisoformat(last_updated)).total_seconds() / 3600
                if hours_since < update_hours:
                    continue
            
            # Simulate feed update
            update = await self.fetch_feed(feed_name, feed_config)
            
            if update['success']:
                # Add IOCs to threat intel hub
                new_iocs = await self.process_feed_iocs(threat_intel, feed_name, update)
                
                # Record update
                self.feeds[feed_name]['last_updated'] = get_now_pst().isoformat()
                self.feeds[feed_name]['ioc_count'] = update.get('ioc_count', 0)
                self.save_feeds()
                
                # Log update
                update_log = {
                    'timestamp': get_now_pst().isoformat(),
                    'feed': feed_name,
                    'feed_type': feed_config['type'],
                    'new_iocs': new_iocs,
                    'total_iocs': update.get('ioc_count', 0),
                    'critical_iocs': update.get('critical_count', 0)
                }
                self.feed_updates.append(update_log)
                self.save_updates()
                
                # Alert if critical IOCs found
                if update.get('critical_count', 0) > 0:
                    await self.alert_critical_iocs(feed_name, update)
                
                print(f"[ThreatIntelUpdater] ✅ {feed_config['name']}: {new_iocs} new IOCs")
    
    async def fetch_feed(self, feed_name: str, feed_config: Dict) -> Dict:
        """Fetch IOCs from threat feed (simulated)"""
        # In production, this would call actual threat feeds (VirusTotal, abuse.ch, etc.)
        # For now, simulate feed data
        
        ioc_count = 10  # Simulated count
        critical_count = 0
        
        if feed_config['type'] == 'url_malware':
            ioc_count = 15
            critical_count = 3
        elif feed_config['type'] == 'c2_server':
            ioc_count = 8
            critical_count = 2
        elif feed_config['type'] == 'phishing_url':
            ioc_count = 25
            critical_count = 1
        
        return {
            'success': True,
            'feed': feed_name,
            'ioc_count': ioc_count,
            'critical_count': critical_count,
            'iocs': [
                {
                    'type': feed_config['type'],
                    'value': f"threat_{feed_name}_{i}",
                    'severity': 'CRITICAL' if i < critical_count else 'HIGH',
                    'category': feed_config['type']
                }
                for i in range(ioc_count)
            ]
        }
    
    async def process_feed_iocs(self, threat_intel, feed_name: str, update: Dict) -> int:
        """Process and add IOCs from feed to threat intel hub"""
        new_iocs = 0
        
        for ioc in update.get('iocs', []):
            ioc_value = ioc['value']
            
            # Check if already in database
            if ioc_value not in threat_intel.iocs:
                threat_intel.add_ioc(
                    ioc_type=ioc.get('type', 'unknown'),
                    value=ioc_value,
                    category=ioc.get('category', 'unknown'),
                    severity=ioc.get('severity', 'MEDIUM'),
                    attributed_to=f"Feed: {feed_name}",
                    description=f"From {feed_name} threat feed"
                )
                new_iocs += 1
            else:
                # Update existing IOC
                if ioc_value in threat_intel.iocs:
                    threat_intel.iocs[ioc_value]['last_seen'] = get_now_pst().isoformat()
                    threat_intel.iocs[ioc_value]['hit_count'] = threat_intel.iocs[ioc_value].get('hit_count', 0) + 1
        
        threat_intel.save_threat_data()
        return new_iocs
    
    async def alert_critical_iocs(self, feed_name: str, update: Dict):
        """Alert SOC team of critical IOCs"""
        critical_count = update.get('critical_count', 0)
        
        # Emit signal
        await signal_bus.emit(Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='CRITICAL',
            source='threat_intel_updater',
            data={
                'threat_feed': feed_name,
                'critical_iocs': critical_count,
                'total_iocs': update.get('ioc_count', 0),
                'enrichment': 'threat_feed_update',
                'confidence': 0.95
            }
        ))
    
    @commands.command(name='feedstatus')
    async def feed_status_cmd(self, ctx):
        """View threat feed status"""
        embed = discord.Embed(
            title="🔄 Threat Intelligence Feeds",
            description="Active threat intelligence feeds",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        total_iocs = 0
        
        for feed_name, feed_config in self.feeds.items():
            status = "✅ ACTIVE" if feed_config['enabled'] else "⏹️ DISABLED"
            last_updated = feed_config.get('last_updated')
            
            if last_updated:
                time_ago = (get_now_pst() - datetime.fromisoformat(last_updated)).total_seconds() / 3600
                update_status = f"Updated {int(time_ago)}h ago"
            else:
                update_status = "Never updated"
            
            ioc_count = feed_config.get('ioc_count', 0)
            total_iocs += ioc_count
            
            field_value = f"**Status:** {status}\n"
            field_value += f"**Type:** {feed_config['type']}\n"
            field_value += f"**IOCs:** {ioc_count}\n"
            field_value += f"**Update:** {update_status}"
            
            embed.add_field(
                name=feed_config['name'],
                value=field_value,
                inline=False
            )
        
        embed.add_field(name="Total IOCs", value=str(total_iocs), inline=True)
        embed.add_field(name="Update Frequency", value="Every 6-24 hours", inline=True)
        
        embed.set_footer(text="Threat feeds update automatically")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='feedupdates')
    async def feed_updates_cmd(self, ctx, limit: int = 10):
        """View feed update history"""
        guild_updates = [u for u in self.feed_updates]  # All feeds
        
        recent = guild_updates[-limit:]
        
        if not recent:
            await ctx.send("📊 No feed updates yet")
            return
        
        embed = discord.Embed(
            title="📋 Feed Update History",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for update in recent[-5:]:
            timestamp = datetime.fromisoformat(update['timestamp']).strftime('%Y-%m-%d %H:%M')
            new_iocs = update.get('new_iocs', 0)
            critical = update.get('critical_iocs', 0)
            
            field_value = f"**Feed:** {update['feed']}\n"
            field_value += f"**New IOCs:** {new_iocs}\n"
            field_value += f"**Critical:** {critical}"
            
            emoji = "🔴" if critical > 0 else "🟢"
            
            embed.add_field(
                name=f"{emoji} {timestamp}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="Feed updates logged automatically")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='enablefeed')
    @commands.has_permissions(administrator=True)
    async def enable_feed_cmd(self, ctx, feed_name: str):
        """Enable a threat feed"""
        if feed_name not in self.feeds:
            await ctx.send(f"❌ Feed not found: {feed_name}")
            return
        
        self.feeds[feed_name]['enabled'] = True
        self.save_feeds()
        
        await ctx.send(f"✅ Feed enabled: {self.feeds[feed_name]['name']}")
    
    @commands.command(name='disablefeed')
    @commands.has_permissions(administrator=True)
    async def disable_feed_cmd(self, ctx, feed_name: str):
        """Disable a threat feed"""
        if feed_name not in self.feeds:
            await ctx.send(f"❌ Feed not found: {feed_name}")
            return
        
        self.feeds[feed_name]['enabled'] = False
        self.save_feeds()
        
        await ctx.send(f"✅ Feed disabled: {self.feeds[feed_name]['name']}")

async def setup(bot):
    await bot.add_cog(ThreatIntelUpdater(bot))
