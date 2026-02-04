"""
IOC MANAGER
Advanced IOC management with bulk operations, expiration, and feed integration.

Features:
- Bulk IOC import/export
- IOC expiration and aging
- Confidence scoring
- False positive tracking
- Feed integration capabilities
- IOC relationship mapping
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import csv
import io

from cogs.core.signal_bus import signal_bus, Signal, SignalType
from cogs.core.pst_timezone import get_now_pst

class IOCManager(commands.Cog):
    """Advanced IOC lifecycle management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/ioc_manager.json'
        self.ioc_metadata = {}  # IOC ID -> metadata
        self.false_positives = []  # False positive tracking
        self.ioc_relationships = {}  # IOC -> related IOCs
        self.feeds = {}  # Feed name -> feed config
        self.load_manager_data()
        self.cleanup_expired_iocs.start()
    
    def load_manager_data(self):
        """Load IOC manager data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.ioc_metadata = data.get('metadata', {})
                    self.false_positives = data.get('false_positives', [])
                    self.ioc_relationships = data.get('relationships', {})
                    self.feeds = data.get('feeds', {})
            except:
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        """Initialize default data"""
        self.ioc_metadata = {}
        self.false_positives = []
        self.ioc_relationships = {}
        self.feeds = {
            'internal': {
                'name': 'Internal IOCs',
                'enabled': True,
                'last_update': get_now_pst().isoformat()
            }
        }
        self.save_manager_data()
    
    def save_manager_data(self):
        """Save manager data"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'metadata': self.ioc_metadata,
                'false_positives': self.false_positives,
                'relationships': self.ioc_relationships,
                'feeds': self.feeds
            }, f, indent=2)
    
    @tasks.loop(hours=24)
    async def cleanup_expired_iocs(self):
        """Clean up expired IOCs"""
        # Get threat intel hub
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        if not threat_intel:
            return
        
        expired_count = 0
        for ioc_value, metadata in list(self.ioc_metadata.items()):
            expiry = metadata.get('expires_at')
            if expiry and datetime.fromisoformat(expiry) < get_now_pst():
                # Mark as expired
                if ioc_value in threat_intel.iocs:
                    del threat_intel.iocs[ioc_value]
                    expired_count += 1
        
        if expired_count > 0:
            threat_intel.save_threat_data()
            print(f"[IOC Manager] Cleaned up {expired_count} expired IOCs")
    
    def add_metadata(self, ioc_value: str, ttl_days: int = None, 
                    confidence: float = 1.0, tags: List[str] = None,
                    source_feed: str = 'internal'):
        """Add metadata to IOC"""
        expires_at = None
        if ttl_days:
            expires_at = (get_now_pst() + timedelta(days=ttl_days)).isoformat()
        
        self.ioc_metadata[ioc_value] = {
            'added_at': get_now_pst().isoformat(),
            'expires_at': expires_at,
            'confidence': confidence,
            'tags': tags or [],
            'source_feed': source_feed,
            'last_updated': get_now_pst().isoformat()
        }
        
        self.save_manager_data()
    
    def mark_false_positive(self, ioc_value: str, reason: str, reporter: str):
        """Mark IOC as false positive"""
        fp = {
            'ioc_value': ioc_value,
            'reason': reason,
            'reporter': reporter,
            'timestamp': get_now_pst().isoformat()
        }
        
        self.false_positives.append(fp)
        self.save_manager_data()
    
    def add_relationship(self, ioc_value: str, related_ioc: str, 
                        relationship_type: str = 'related'):
        """Link related IOCs"""
        if ioc_value not in self.ioc_relationships:
            self.ioc_relationships[ioc_value] = []
        
        self.ioc_relationships[ioc_value].append({
            'related_ioc': related_ioc,
            'type': relationship_type,
            'timestamp': get_now_pst().isoformat()
        })
        
        self.save_manager_data()
    
    def bulk_import_iocs(self, csv_content: str) -> Dict:
        """Import IOCs from CSV"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        if not threat_intel:
            return {'error': 'Threat intel hub not available'}
        
        reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0
        failed = 0
        
        for row in reader:
            try:
                ioc_type = row.get('type')
                value = row.get('value')
                category = row.get('category', 'unknown')
                severity = row.get('severity', 'MEDIUM')
                attributed_to = row.get('attributed_to')
                
                if not ioc_type or not value:
                    failed += 1
                    continue
                
                threat_intel.add_ioc(
                    ioc_type, value, category, 
                    severity, attributed_to
                )
                
                # Add metadata
                ttl_days = int(row.get('ttl_days', 0)) if row.get('ttl_days') else None
                confidence = float(row.get('confidence', 1.0))
                tags = row.get('tags', '').split(',') if row.get('tags') else None
                
                self.add_metadata(value, ttl_days, confidence, tags)
                
                imported += 1
                
            except Exception as e:
                print(f"[IOC Manager] Failed to import IOC: {e}")
                failed += 1
        
        return {
            'imported': imported,
            'failed': failed
        }
    
    def export_iocs_csv(self) -> str:
        """Export IOCs to CSV"""
        threat_intel = self.bot.get_cog('ThreatIntelHub')
        if not threat_intel:
            return "error,Threat intel hub not available"
        
        output = io.StringIO()
        fieldnames = ['type', 'value', 'category', 'severity', 'attributed_to', 
                     'confidence', 'ttl_days', 'tags', 'added_date']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for ioc in threat_intel.iocs.values():
            metadata = self.ioc_metadata.get(ioc['value'], {})
            
            writer.writerow({
                'type': ioc.get('type'),
                'value': ioc.get('value'),
                'category': ioc.get('category'),
                'severity': ioc.get('severity'),
                'attributed_to': ioc.get('attributed_to', ''),
                'confidence': metadata.get('confidence', 1.0),
                'ttl_days': '',
                'tags': ','.join(metadata.get('tags', [])),
                'added_date': ioc.get('added_date')
            })
        
        return output.getvalue()
    
    def get_aging_report(self) -> Dict:
        """Get IOC aging report"""
        now = get_now_pst()
        
        aging_buckets = {
            'fresh': 0,      # < 7 days
            'active': 0,     # 7-30 days
            'aging': 0,      # 30-90 days
            'stale': 0,      # 90+ days
            'expired': 0
        }
        
        for ioc_value, metadata in self.ioc_metadata.items():
            added_at = datetime.fromisoformat(metadata['added_at'])
            expires_at = metadata.get('expires_at')
            
            # Check expiration
            if expires_at and datetime.fromisoformat(expires_at) < now:
                aging_buckets['expired'] += 1
                continue
            
            # Check age
            age_days = (now - added_at).days
            
            if age_days < 7:
                aging_buckets['fresh'] += 1
            elif age_days < 30:
                aging_buckets['active'] += 1
            elif age_days < 90:
                aging_buckets['aging'] += 1
            else:
                aging_buckets['stale'] += 1
        
        return aging_buckets
    
    @commands.command(name='importiocs')
    async def import_iocs_cmd(self, ctx):
        """Import IOCs from CSV attachment (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        if not ctx.message.attachments:
            await ctx.send("❌ Please attach a CSV file\n"
                          "Format: type,value,category,severity,attributed_to,confidence,ttl_days,tags")
            return
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            await ctx.send("❌ File must be a CSV")
            return
        
        try:
            content = await attachment.read()
            csv_content = content.decode('utf-8')
            
            result = self.bulk_import_iocs(csv_content)
            
            embed = discord.Embed(
                title="📥 IOC Import Complete",
                color=discord.Color.green(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Imported", value=str(result['imported']), inline=True)
            embed.add_field(name="Failed", value=str(result['failed']), inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Import failed: {e}")
    
    @commands.command(name='exportiocs')
    async def export_iocs_cmd(self, ctx):
        """Export IOCs to CSV (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        try:
            csv_content = self.export_iocs_csv()
            
            file = discord.File(
                io.BytesIO(csv_content.encode('utf-8')),
                filename=f'iocs_export_{get_now_pst().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
            await ctx.send("📤 IOC Export", file=file)
            
        except Exception as e:
            await ctx.send(f"❌ Export failed: {e}")
    
    @commands.command(name='markfalsepositive')
    async def mark_fp_cmd(self, ctx, ioc_value: str, *, reason: str):
        """Mark IOC as false positive (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        self.mark_false_positive(ioc_value, reason, str(ctx.author))
        
        await ctx.send(f"✅ Marked `{ioc_value}` as false positive")
    
    @commands.command(name='iocaging')
    async def ioc_aging_cmd(self, ctx):
        """View IOC aging report (owner only)"""
        owner_id = int(os.getenv('BOT_OWNER_ID', '0'))
        if ctx.author.id != owner_id:
            await ctx.send("❌ Owner only command")
            return
        
        report = self.get_aging_report()
        
        embed = discord.Embed(
            title="📅 IOC Aging Report",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🟢 Fresh (<7 days)", value=str(report['fresh']), inline=True)
        embed.add_field(name="🔵 Active (7-30 days)", value=str(report['active']), inline=True)
        embed.add_field(name="🟡 Aging (30-90 days)", value=str(report['aging']), inline=True)
        embed.add_field(name="🟠 Stale (90+ days)", value=str(report['stale']), inline=True)
        embed.add_field(name="🔴 Expired", value=str(report['expired']), inline=True)
        
        total = sum(report.values())
        embed.add_field(name="Total IOCs", value=str(total), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(IOCManager(bot))
