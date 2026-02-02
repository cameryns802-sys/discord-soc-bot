"""
THREAT INTELLIGENCE HUB
Central hub for threat intelligence, IOC tracking, and correlation.

Architecture:
- IOC (Indicator of Compromise) tracking and management
- Threat actor profiling and attribution
- Correlation with incoming security signals
- Threat enrichment and context
- Integration with external threat feeds (optional)
- Historical threat pattern analysis
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import hashlib

from cogs.core.signal_bus import signal_bus, Signal, SignalType

class IOCType(Enum):
    """Types of Indicators of Compromise"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    USER_AGENT = "user_agent"
    REGISTRY_KEY = "registry_key"
    MUTEX = "mutex"

class ThreatCategory(Enum):
    """Threat categorization"""
    MALWARE = "malware"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    APT = "apt"
    BOTNET = "botnet"
    C2_SERVER = "c2_server"
    CRYPTOMINING = "cryptomining"
    DATA_EXFILTRATION = "data_exfiltration"
    INSIDER_THREAT = "insider_threat"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"

class ThreatIntelHub(commands.Cog):
    """Advanced threat intelligence and IOC management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/threat_intel.json'
        self.iocs = {}  # IOC value -> IOC data
        self.threat_actors = {}  # Actor name -> Actor data
        self.campaigns = {}  # Campaign ID -> Campaign data
        self.correlations = []  # Signal correlations
        self.load_threat_data()
        self.setup_signal_listeners()
    
    def load_threat_data(self):
        """Load threat intelligence data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.iocs = data.get('iocs', {})
                    self.threat_actors = data.get('threat_actors', {})
                    self.campaigns = data.get('campaigns', {})
                    self.correlations = data.get('correlations', [])
            except:
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        """Initialize with sample threat intelligence"""
        self.iocs = {}
        self.threat_actors = {}
        self.campaigns = {}
        self.correlations = []
        self.save_threat_data()
    
    def save_threat_data(self):
        """Save threat data to disk"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'iocs': self.iocs,
                'threat_actors': self.threat_actors,
                'campaigns': self.campaigns,
                'correlations': self.correlations
            }, f, indent=2)
    
    def setup_signal_listeners(self):
        """Subscribe to signal bus for correlation"""
        signal_bus.subscribe('threat_intel_hub', self.on_signal)
    
    async def on_signal(self, signal: Signal):
        """Correlate incoming signals with threat intelligence"""
        # Extract IOCs from signal data
        iocs_found = self.extract_iocs_from_signal(signal)
        
        if iocs_found:
            # Check against known IOCs
            matches = []
            for ioc_value in iocs_found:
                if ioc_value in self.iocs:
                    matches.append(self.iocs[ioc_value])
            
            if matches:
                # Emit enriched threat signal
                await self.emit_enriched_threat(signal, matches)
                
                # Record correlation
                self.record_correlation(signal, matches)
    
    def extract_iocs_from_signal(self, signal: Signal) -> List[str]:
        """Extract potential IOCs from signal data"""
        iocs = []
        
        if not signal.data:
            return iocs
        
        # Extract from various fields
        for key, value in signal.data.items():
            if isinstance(value, str):
                # Check for IP addresses
                if self.is_ip_address(value):
                    iocs.append(value)
                # Check for domains
                elif self.is_domain(value):
                    iocs.append(value)
                # Check for URLs
                elif self.is_url(value):
                    iocs.append(value)
                # Check for file hashes
                elif self.is_file_hash(value):
                    iocs.append(value)
        
        return iocs
    
    def is_ip_address(self, value: str) -> bool:
        """Check if value is an IP address"""
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(pattern, value))
    
    def is_domain(self, value: str) -> bool:
        """Check if value is a domain"""
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
        return bool(re.match(pattern, value))
    
    def is_url(self, value: str) -> bool:
        """Check if value is a URL"""
        return value.startswith(('http://', 'https://'))
    
    def is_file_hash(self, value: str) -> bool:
        """Check if value is a file hash"""
        # MD5 (32), SHA1 (40), SHA256 (64)
        return len(value) in [32, 40, 64] and value.isalnum()
    
    async def emit_enriched_threat(self, signal: Signal, matches: List[Dict]):
        """Emit enriched threat signal with IOC context"""
        enriched_signal = Signal(
            signal_type=SignalType.THREAT_DETECTED,
            severity='HIGH',
            source='threat_intel_hub',
            data={
                'original_signal': str(signal.type),
                'original_source': signal.source,
                'ioc_matches': len(matches),
                'threat_categories': list(set([m.get('category', 'unknown') for m in matches])),
                'threat_actors': list(set([m.get('attributed_to', 'unknown') for m in matches if m.get('attributed_to')])),
                'confidence': 0.95,
                'enrichment': 'threat_intel_correlation'
            }
        )
        
        await signal_bus.emit(enriched_signal)
    
    def record_correlation(self, signal: Signal, matches: List[Dict]):
        """Record correlation for analytics"""
        correlation = {
            'timestamp': datetime.utcnow().isoformat(),
            'signal_type': str(signal.type),
            'signal_source': signal.source,
            'ioc_count': len(matches),
            'threat_categories': list(set([m.get('category', 'unknown') for m in matches])),
            'severity': signal.severity
        }
        
        self.correlations.append(correlation)
        
        # Keep last 1000 correlations
        if len(self.correlations) > 1000:
            self.correlations = self.correlations[-1000:]
        
        self.save_threat_data()
    
    def add_ioc(self, ioc_type: str, value: str, category: str, 
                severity: str = 'MEDIUM', attributed_to: str = None,
                description: str = None, source: str = None) -> str:
        """Add IOC to threat intelligence database"""
        ioc_id = hashlib.md5(f"{ioc_type}:{value}".encode()).hexdigest()[:12]
        
        self.iocs[value] = {
            'id': ioc_id,
            'type': ioc_type,
            'value': value,
            'category': category,
            'severity': severity,
            'attributed_to': attributed_to,
            'description': description,
            'source': source,
            'added_date': datetime.utcnow().isoformat(),
            'last_seen': None,
            'hit_count': 0
        }
        
        self.save_threat_data()
        return ioc_id
    
    def add_threat_actor(self, name: str, aliases: List[str] = None,
                        origin: str = None, motivation: str = None,
                        techniques: List[str] = None) -> str:
        """Add threat actor profile"""
        actor_id = hashlib.md5(name.encode()).hexdigest()[:12]
        
        self.threat_actors[name] = {
            'id': actor_id,
            'name': name,
            'aliases': aliases or [],
            'origin': origin,
            'motivation': motivation,
            'techniques': techniques or [],
            'first_seen': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'associated_iocs': [],
            'campaigns': []
        }
        
        self.save_threat_data()
        return actor_id
    
    def add_campaign(self, name: str, threat_actor: str = None,
                    category: str = None, start_date: str = None,
                    targets: List[str] = None, description: str = None) -> str:
        """Add threat campaign"""
        campaign_id = hashlib.md5(f"{name}:{start_date}".encode()).hexdigest()[:12]
        
        self.campaigns[campaign_id] = {
            'id': campaign_id,
            'name': name,
            'threat_actor': threat_actor,
            'category': category,
            'start_date': start_date or datetime.utcnow().isoformat(),
            'end_date': None,
            'targets': targets or [],
            'description': description,
            'associated_iocs': [],
            'signals_detected': 0
        }
        
        self.save_threat_data()
        return campaign_id
    
    def get_ioc_stats(self) -> Dict:
        """Get IOC statistics"""
        by_type = {}
        by_category = {}
        by_severity = {}
        
        for ioc in self.iocs.values():
            # By type
            ioc_type = ioc.get('type', 'unknown')
            by_type[ioc_type] = by_type.get(ioc_type, 0) + 1
            
            # By category
            category = ioc.get('category', 'unknown')
            by_category[category] = by_category.get(category, 0) + 1
            
            # By severity
            severity = ioc.get('severity', 'MEDIUM')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_iocs': len(self.iocs),
            'by_type': by_type,
            'by_category': by_category,
            'by_severity': by_severity,
            'threat_actors': len(self.threat_actors),
            'campaigns': len(self.campaigns),
            'correlations': len(self.correlations)
        }
    
    def get_correlation_report(self, hours: int = 24) -> Dict:
        """Get correlation report"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent = [
            c for c in self.correlations
            if datetime.fromisoformat(c['timestamp']) > cutoff
        ]
        
        by_category = {}
        by_signal = {}
        
        for corr in recent:
            # By category
            for cat in corr.get('threat_categories', []):
                by_category[cat] = by_category.get(cat, 0) + 1
            
            # By signal type
            sig_type = corr.get('signal_type', 'unknown')
            by_signal[sig_type] = by_signal.get(sig_type, 0) + 1
        
        return {
            'period_hours': hours,
            'total_correlations': len(recent),
            'by_threat_category': by_category,
            'by_signal_type': by_signal,
            'unique_iocs_detected': len(set([c.get('ioc_count', 0) for c in recent]))
        }
    
    def search_iocs(self, query: str = None, ioc_type: str = None, 
                   category: str = None, limit: int = 10) -> List[Dict]:
        """Search IOCs"""
        results = []
        
        for ioc in self.iocs.values():
            # Filter by query
            if query and query.lower() not in ioc.get('value', '').lower():
                continue
            
            # Filter by type
            if ioc_type and ioc.get('type') != ioc_type:
                continue
            
            # Filter by category
            if category and ioc.get('category') != category:
                continue
            
            results.append(ioc)
            
            if len(results) >= limit:
                break
        
        return results
    
    @commands.command(name='addioc')
    async def add_ioc_cmd(self, ctx, ioc_type: str, value: str, category: str, 
                          severity: str = 'MEDIUM', attributed_to: str = None):
        """Add IOC to threat intelligence database (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        try:
            ioc_id = self.add_ioc(ioc_type, value, category, severity, attributed_to)
            
            embed = discord.Embed(
                title="✅ IOC Added",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="IOC ID", value=ioc_id, inline=True)
            embed.add_field(name="Type", value=ioc_type, inline=True)
            embed.add_field(name="Value", value=f"`{value}`", inline=False)
            embed.add_field(name="Category", value=category, inline=True)
            embed.add_field(name="Severity", value=severity, inline=True)
            
            if attributed_to:
                embed.add_field(name="Attributed To", value=attributed_to, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to add IOC: {e}")
    
    @commands.command(name='searchioc')
    async def search_ioc_cmd(self, ctx, query: str = None):
        """Search IOCs (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        results = self.search_iocs(query=query, limit=10)
        
        if not results:
            await ctx.send("❌ No IOCs found")
            return
        
        embed = discord.Embed(
            title=f"🔍 IOC Search Results",
            description=f"Query: `{query or 'all'}`",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for ioc in results[:5]:
            ioc_info = f"**Type:** {ioc.get('type')}\n"
            ioc_info += f"**Category:** {ioc.get('category')}\n"
            ioc_info += f"**Severity:** {ioc.get('severity')}\n"
            ioc_info += f"**Hits:** {ioc.get('hit_count', 0)}"
            
            embed.add_field(
                name=f"`{ioc.get('value')[:50]}`",
                value=ioc_info,
                inline=False
            )
        
        embed.set_footer(text=f"Showing {len(results[:5])}/{len(results)} results")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='iocstats')
    async def ioc_stats_cmd(self, ctx):
        """View IOC statistics (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        stats = self.get_ioc_stats()
        
        embed = discord.Embed(
            title="📊 Threat Intelligence Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Total IOCs",
            value=str(stats['total_iocs']),
            inline=True
        )
        
        embed.add_field(
            name="Threat Actors",
            value=str(stats['threat_actors']),
            inline=True
        )
        
        embed.add_field(
            name="Campaigns",
            value=str(stats['campaigns']),
            inline=True
        )
        
        # By type
        if stats['by_type']:
            type_text = "\n".join([f"• {t}: {c}" for t, c in stats['by_type'].items()])
            embed.add_field(name="IOCs by Type", value=type_text, inline=False)
        
        # By category
        if stats['by_category']:
            cat_text = "\n".join([f"• {c}: {count}" for c, count in stats['by_category'].items()])
            embed.add_field(name="IOCs by Category", value=cat_text, inline=False)
        
        # By severity
        if stats['by_severity']:
            sev_text = "\n".join([
                f"{'🔴' if s == 'CRITICAL' else '🟠' if s == 'HIGH' else '🟡'} {s}: {c}" 
                for s, c in stats['by_severity'].items()
            ])
            embed.add_field(name="IOCs by Severity", value=sev_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='correlationreport')
    async def correlation_report_cmd(self, ctx, hours: int = 24):
        """View IOC correlation report (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        report = self.get_correlation_report(hours)
        
        embed = discord.Embed(
            title="🔗 IOC Correlation Report",
            description=f"Analysis over last {hours} hours",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Total Correlations",
            value=str(report['total_correlations']),
            inline=True
        )
        
        embed.add_field(
            name="Unique IOCs",
            value=str(report['unique_iocs_detected']),
            inline=True
        )
        
        # By threat category
        if report['by_threat_category']:
            cat_text = "\n".join([
                f"• {cat}: {count}" 
                for cat, count in sorted(report['by_threat_category'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]
            ])
            embed.add_field(name="Top Threat Categories", value=cat_text, inline=False)
        
        # By signal type
        if report['by_signal_type']:
            sig_text = "\n".join([
                f"• {sig}: {count}" 
                for sig, count in sorted(report['by_signal_type'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]
            ])
            embed.add_field(name="Top Signal Types", value=sig_text, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreatIntelHub(bot))
