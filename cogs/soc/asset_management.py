"""
Asset Management System - Comprehensive IT asset inventory and tracking
Track hardware, software, and cloud assets with security and compliance data
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import uuid

class AssetManagement(commands.Cog):
    """IT asset management and inventory tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.assets_file = 'data/asset_inventory.json'
        self.vulnerabilities_file = 'data/asset_vulnerabilities.json'
        self.load_data()
    
    def load_data(self):
        """Load asset data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.assets_file):
            with open(self.assets_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.vulnerabilities_file):
            with open(self.vulnerabilities_file, 'w') as f:
                json.dump({}, f)
    
    def get_assets(self, guild_id):
        """Get assets"""
        with open(self.assets_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_assets(self, guild_id, assets):
        """Save assets"""
        with open(self.assets_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = assets
        with open(self.assets_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_asset_risk(self, asset):
        """Calculate asset risk score (0-100)"""
        score = 20
        
        # Asset age
        deployed_date = asset.get('deployed_date')
        if deployed_date:
            days_old = (datetime.utcnow() - datetime.fromisoformat(deployed_date)).days
            if days_old > 1825:  # 5 years
                score += 30
            elif days_old > 1095:  # 3 years
                score += 15
        
        # Patch status
        if not asset.get('patched', False):
            score += 25
        
        # Criticality
        if asset.get('criticality') == 'critical':
            score += 15
        elif asset.get('criticality') == 'high':
            score += 10
        
        # Network exposure
        if asset.get('internet_facing', False):
            score += 20
        
        # Vulnerabilities
        vulns = asset.get('known_vulnerabilities', 0)
        score += vulns * 5
        
        # Last scan
        if asset.get('last_security_scan'):
            days_since = (datetime.utcnow() - datetime.fromisoformat(asset['last_security_scan'])).days
            if days_since > 30:
                score += 15
        else:
            score += 20
        
        return min(100, score)
    
    async def _registeredasset_logic(self, ctx, asset_name: str, asset_type: str, criticality: str = 'medium'):
        """Register new asset"""
        assets = self.get_assets(ctx.guild.id)
        
        asset_id = f"AST-{str(uuid.uuid4())[:8].upper()}"
        
        asset = {
            'id': asset_id,
            'name': asset_name,
            'type': asset_type.lower(),
            'criticality': criticality.lower(),
            'registered_at': datetime.utcnow().isoformat(),
            'deployed_date': datetime.utcnow().isoformat(),
            'status': 'active',
            'patched': True,
            'internet_facing': False,
            'owner': 'TBD',
            'location': 'Unknown',
            'last_security_scan': None,
            'known_vulnerabilities': 0,
            'risk_score': 0,
            'os': 'Unknown',
            'end_of_life': None,
            'inventory_notes': ''
        }
        
        asset['risk_score'] = self.calculate_asset_risk(asset)
        assets[asset_id] = asset
        self.save_assets(ctx.guild.id, assets)
        
        embed = discord.Embed(
            title="✅ Asset Registered",
            description=f"**{asset_name}**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Asset ID", value=f"`{asset_id}`", inline=True)
        embed.add_field(name="Type", value=asset_type.title(), inline=True)
        embed.add_field(name="Criticality", value=criticality.title(), inline=True)
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Risk Score", value=f"{asset['risk_score']}/100", inline=True)
        embed.add_field(name="Patched", value="✅ Yes", inline=True)
        
        embed.set_footer(text="Use !assetdetail to see full inventory record")
        
        await ctx.send(embed=embed)
    
    async def _assetinventory_logic(self, ctx):
        """Show asset inventory"""
        assets = self.get_assets(ctx.guild.id)
        
        if not assets:
            await ctx.send("📦 No assets registered.")
            return
        
        # Sort by risk
        sorted_assets = sorted(assets.values(), key=lambda a: a['risk_score'], reverse=True)
        
        embed = discord.Embed(
            title="📦 Asset Inventory",
            description=f"{len(sorted_assets)} asset(s) tracked",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Group by type
        by_type = {}
        for asset in assets.values():
            asset_type = asset['type']
            by_type[asset_type] = by_type.get(asset_type, 0) + 1
        
        embed.add_field(name="Asset Summary", value="━" * 25, inline=False)
        for asset_type, count in by_type.items():
            embed.add_field(name=asset_type.title(), value=f"📊 {count} asset(s)", inline=True)
        
        # High-risk assets
        high_risk = [a for a in sorted_assets if a['risk_score'] >= 70]
        if high_risk:
            embed.add_field(name="🔴 High-Risk Assets", value=f"{len(high_risk)} asset(s) require attention", inline=False)
        
        # Show top 8
        embed.add_field(name="Asset List", value="━" * 25, inline=False)
        for asset in sorted_assets[:8]:
            risk_emoji = '🔴' if asset['risk_score'] >= 70 else '🟠' if asset['risk_score'] >= 50 else '🟡' if asset['risk_score'] >= 30 else '🟢'
            
            embed.add_field(
                name=f"{risk_emoji} {asset['name']} ({asset['id']})",
                value=f"Type: {asset['type'].title()} | Criticality: {asset['criticality'].title()} | Risk: {asset['risk_score']}/100",
                inline=False
            )
        
        if len(sorted_assets) > 8:
            embed.add_field(name="... and more", value=f"+{len(sorted_assets) - 8} additional assets", inline=False)
        
        embed.set_footer(text="Use !assetdetail <id> for security details")
        
        await ctx.send(embed=embed)
    
    async def _assetdetail_logic(self, ctx, asset_id: str):
        """Show asset details"""
        assets = self.get_assets(ctx.guild.id)
        
        asset_id = asset_id.upper()
        if not asset_id.startswith('AST-'):
            asset_id = f"AST-{asset_id}"
        
        asset = assets.get(asset_id)
        if not asset:
            await ctx.send(f"❌ Asset not found: {asset_id}")
            return
        
        risk = asset['risk_score']
        color = discord.Color.red() if risk >= 70 else discord.Color.orange() if risk >= 50 else discord.Color.gold() if risk >= 30 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"📦 {asset['name']}",
            description=f"Type: {asset['type'].title()}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Asset ID", value=f"`{asset['id']}`", inline=True)
        embed.add_field(name="Status", value=asset['status'].title(), inline=True)
        embed.add_field(name="Risk Score", value=f"{risk}/100", inline=True)
        
        embed.add_field(name="Inventory Information", value="━" * 25, inline=False)
        embed.add_field(name="Criticality", value=asset['criticality'].title(), inline=True)
        embed.add_field(name="Owner", value=asset['owner'], inline=True)
        embed.add_field(name="Location", value=asset['location'], inline=True)
        embed.add_field(name="Operating System", value=asset['os'], inline=True)
        embed.add_field(name="Deployed", value=datetime.fromisoformat(asset['deployed_date']).strftime('%Y-%m-%d'), inline=True)
        
        embed.add_field(name="Security Status", value="━" * 25, inline=False)
        embed.add_field(name="Patched", value="✅ Yes" if asset['patched'] else "❌ No", inline=True)
        embed.add_field(name="Internet Facing", value="🌐 Yes" if asset['internet_facing'] else "🔒 No", inline=True)
        embed.add_field(name="Known Vulnerabilities", value=f"⚠️ {asset['known_vulnerabilities']}", inline=True)
        
        if asset['last_security_scan']:
            last_scan = datetime.fromisoformat(asset['last_security_scan']).strftime('%Y-%m-%d')
            embed.add_field(name="Last Security Scan", value=last_scan, inline=False)
        
        if asset['end_of_life']:
            embed.add_field(name="⚠️ End of Life Date", value=asset['end_of_life'], inline=False)
        
        embed.set_footer(text="Sentinel Asset Management System")
        
        await ctx.send(embed=embed)
    
    async def _assetrisk_logic(self, ctx):
        """Show high-risk assets"""
        assets = self.get_assets(ctx.guild.id)
        
        if not assets:
            await ctx.send("📦 No assets to analyze.")
            return
        
        # Identify risks
        unpatched = [a for a in assets.values() if not a['patched']]
        exposed = [a for a in assets.values() if a['internet_facing']]
        old = [a for a in assets.values() if (datetime.utcnow() - datetime.fromisoformat(a['deployed_date'])).days > 1825]
        vulns = [a for a in assets.values() if a['known_vulnerabilities'] > 0]
        unscan = [a for a in assets.values() if not a['last_security_scan']]
        
        embed = discord.Embed(
            title="⚠️ Asset Risk Analysis",
            description="Security risks identified in asset inventory",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk Summary", value="━" * 25, inline=False)
        
        if unpatched:
            embed.add_field(name="🔴 Unpatched Assets", value=f"{len(unpatched)} asset(s) need patches", inline=False)
        
        if exposed:
            embed.add_field(name="🌐 Internet-Exposed Assets", value=f"{len(exposed)} asset(s) directly accessible", inline=False)
        
        if old:
            embed.add_field(name="🔧 End-of-Life Assets", value=f"{len(old)} asset(s) > 5 years old", inline=False)
        
        if vulns:
            embed.add_field(name="⚠️ Assets with Vulnerabilities", value=f"{len(vulns)} asset(s) with known vulns", inline=False)
        
        if unscan:
            embed.add_field(name="🔍 Never Scanned", value=f"{len(unscan)} asset(s) lack security baseline", inline=False)
        
        embed.add_field(name="Remediation Actions", value="━" * 25, inline=False)
        embed.add_field(name="1. Apply Security Patches", value="Priority: CRITICAL - Complete within 7 days", inline=False)
        embed.add_field(name="2. Secure Exposed Assets", value="Implement WAF/network segmentation", inline=False)
        embed.add_field(name="3. Refresh Aging Assets", value="Plan replacement for >5 year assets", inline=False)
        
        embed.set_footer(text="Use !assetdetail <id> for specific remediation")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='registeredasset')
    async def registeredasset_prefix(self, ctx, asset_name: str, asset_type: str, criticality: str = 'medium'):
        """Register asset - Prefix command"""
        await self._registeredasset_logic(ctx, asset_name, asset_type, criticality)
    
    @commands.command(name='assetinventory')
    async def assetinventory_prefix(self, ctx):
        """Show asset inventory - Prefix command"""
        await self._assetinventory_logic(ctx)
    
    @commands.command(name='assetdetail')
    async def assetdetail_prefix(self, ctx, asset_id: str):
        """Show asset details - Prefix command"""
        await self._assetdetail_logic(ctx, asset_id)
    
    @commands.command(name='assetrisk')
    async def assetrisk_prefix(self, ctx):
        """Show asset risks - Prefix command"""
        await self._assetrisk_logic(ctx)

async def setup(bot):
    await bot.add_cog(AssetManagement(bot))
