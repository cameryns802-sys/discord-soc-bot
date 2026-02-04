"""
Vendor Risk Management System - Third-party security assessment for Sentinel
Assess and monitor vendor security posture, contracts, and compliance
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class VendorRiskManagement(commands.Cog):
    """Third-party vendor security assessment and management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.vendor_file = 'data/vendors.json'
        self.assessments_file = 'data/vendor_assessments.json'
        self.load_data()
    
    def load_data(self):
        """Load vendor data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.vendor_file):
            with open(self.vendor_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.assessments_file):
            with open(self.assessments_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_vendors(self, guild_id):
        """Get vendors for guild"""
        with open(self.vendor_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_vendors(self, guild_id, vendors):
        """Save vendors"""
        with open(self.vendor_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = vendors
        with open(self.vendor_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_assessments(self, guild_id):
        """Get vendor assessments"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_assessment(self, guild_id, assessment):
        """Save assessment"""
        with open(self.assessments_file, 'r') as f:
            data = json.load(f)
        
        assessments = data.get(str(guild_id), [])
        assessments.append(assessment)
        data[str(guild_id)] = assessments[-100:]
        
        with open(self.assessments_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_risk_score(self, vendor):
        """Calculate vendor risk score (0-100)"""
        score = 100
        
        # Security certifications
        certifications = vendor.get('certifications', [])
        if 'soc2' in certifications:
            score -= 10
        if 'iso27001' in certifications:
            score -= 10
        if 'gdpr_compliant' in certifications:
            score -= 5
        
        # Breach history
        if vendor.get('breach_history', False):
            score -= 30
        
        # Data access level
        data_access = vendor.get('data_access', 'minimal')
        if data_access == 'sensitive':
            score += 20
        elif data_access == 'moderate':
            score += 10
        
        # Last assessment
        if vendor.get('last_assessment'):
            last = datetime.fromisoformat(vendor['last_assessment'])
            days_since = (get_now_pst() - last).days
            if days_since > 365:
                score += 25
            elif days_since > 180:
                score += 15
        else:
            score += 30
        
        # Contract status
        if vendor.get('contract_status') == 'expired':
            score += 20
        elif vendor.get('contract_status') == 'expiring_soon':
            score += 10
        
        return max(0, min(100, score))
    
    async def _vendoradd_logic(self, ctx, name: str, category: str, *, details: str = None):
        """Add vendor"""
        vendors = self.get_guild_vendors(ctx.guild.id)
        
        vendor_id = f"VND-{str(uuid.uuid4())[:8].upper()}"
        
        vendor = {
            'id': vendor_id,
            'name': name,
            'category': category,
            'added_at': get_now_pst().isoformat(),
            'status': 'active',
            'data_access': 'minimal',
            'certifications': [],
            'breach_history': False,
            'last_assessment': None,
            'risk_score': 100,
            'contract_status': 'active',
            'contract_expiry': None,
            'notes': details or ''
        }
        
        vendors[vendor_id] = vendor
        self.save_vendors(ctx.guild.id, vendors)
        
        embed = discord.Embed(
            title="🏢 Vendor Added",
            description=f"**{name}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Vendor ID", value=f"`{vendor_id}`", inline=True)
        embed.add_field(name="Category", value=category, inline=True)
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Risk Score", value="100/100 (Unassessed)", inline=True)
        embed.add_field(name="Data Access", value="Minimal", inline=True)
        embed.add_field(name="Certifications", value="None", inline=True)
        
        if details:
            embed.add_field(name="Notes", value=details, inline=False)
        
        embed.set_footer(text="Use !vendorassess to evaluate vendor security")
        
        await ctx.send(embed=embed)
    
    async def _vendorlist_logic(self, ctx):
        """List vendors"""
        vendors = self.get_guild_vendors(ctx.guild.id)
        
        if not vendors:
            await ctx.send("📋 No vendors registered yet.")
            return
        
        # Sort by risk score (highest first)
        sorted_vendors = sorted(vendors.values(), key=lambda v: v['risk_score'], reverse=True)
        
        embed = discord.Embed(
            title="🏢 Vendor Registry",
            description=f"{len(sorted_vendors)} vendor(s) tracked",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for vendor in sorted_vendors[:10]:
            risk_score = vendor['risk_score']
            risk_emoji = '🔴' if risk_score >= 75 else '🟠' if risk_score >= 50 else '🟡' if risk_score >= 25 else '🟢'
            status_emoji = '🟢' if vendor['status'] == 'active' else '🟠' if vendor['status'] == 'dormant' else '❌'
            
            embed.add_field(
                name=f"{risk_emoji} {vendor['name']} ({vendor['id']})",
                value=f"{status_emoji} {vendor['status'].title()} | Risk: {risk_score}/100 | {vendor['category']}",
                inline=False
            )
        
        if len(sorted_vendors) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_vendors) - 10} additional vendors", inline=False)
        
        embed.set_footer(text="Use !vendordetail <id> for full profile")
        
        await ctx.send(embed=embed)
    
    async def _vendordetail_logic(self, ctx, vendor_id: str):
        """Show vendor details"""
        vendors = self.get_guild_vendors(ctx.guild.id)
        
        vendor_id = vendor_id.upper()
        if not vendor_id.startswith('VND-'):
            vendor_id = f"VND-{vendor_id}"
        
        vendor = vendors.get(vendor_id)
        if not vendor:
            await ctx.send(f"❌ Vendor not found: {vendor_id}")
            return
        
        risk_score = vendor['risk_score']
        risk_emoji = '🔴' if risk_score >= 75 else '🟠' if risk_score >= 50 else '🟡' if risk_score >= 25 else '🟢'
        color = discord.Color.red() if risk_score >= 75 else discord.Color.orange() if risk_score >= 50 else discord.Color.gold() if risk_score >= 25 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"{risk_emoji} {vendor['name']}",
            description=vendor['notes'] if vendor['notes'] else "No notes",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Vendor ID", value=f"`{vendor['id']}`", inline=True)
        embed.add_field(name="Category", value=vendor['category'], inline=True)
        embed.add_field(name="Risk Score", value=f"{vendor['risk_score']}/100", inline=True)
        
        embed.add_field(name="Status", value=vendor['status'].title(), inline=True)
        embed.add_field(name="Data Access", value=vendor['data_access'].title(), inline=True)
        embed.add_field(name="Breach History", value="⚠️ Yes" if vendor['breach_history'] else "✅ No", inline=True)
        
        if vendor['certifications']:
            certs = ", ".join([c.upper() for c in vendor['certifications']])
            embed.add_field(name="Certifications", value=certs, inline=False)
        else:
            embed.add_field(name="Certifications", value="None", inline=False)
        
        if vendor['last_assessment']:
            last = datetime.fromisoformat(vendor['last_assessment']).strftime('%Y-%m-%d')
            embed.add_field(name="Last Assessment", value=last, inline=True)
        
        if vendor['contract_expiry']:
            embed.add_field(name="Contract Expires", value=vendor['contract_expiry'], inline=True)
        
        embed.set_footer(text="Sentinel Vendor Risk Management")
        
        await ctx.send(embed=embed)
    
    async def _vendorrisks_logic(self, ctx):
        """Show high-risk vendors"""
        vendors = self.get_guild_vendors(ctx.guild.id)
        
        if not vendors:
            await ctx.send("✅ No vendors to assess.")
            return
        
        # Filter high-risk
        high_risk = [v for v in vendors.values() if v['risk_score'] >= 75]
        
        embed = discord.Embed(
            title="⚠️ High-Risk Vendors",
            description=f"{len(high_risk)} vendor(s) require attention",
            color=discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        if not high_risk:
            embed.description = "✅ No high-risk vendors detected"
            embed.color = discord.Color.green()
        else:
            for vendor in high_risk[:5]:
                risks = []
                if vendor['breach_history']:
                    risks.append("🔴 Prior breach")
                if vendor['risk_score'] > 90:
                    risks.append("⚠️ Unassessed")
                if not vendor['certifications']:
                    risks.append("🟡 No certifications")
                if vendor['data_access'] == 'sensitive':
                    risks.append("🔴 Sensitive access")
                
                risk_str = " | ".join(risks) if risks else "⚠️ High risk score"
                
                embed.add_field(
                    name=f"🔴 {vendor['name']} ({vendor['id']})",
                    value=f"Risk: {vendor['risk_score']}/100\n{risk_str}",
                    inline=False
                )
        
        embed.set_footer(text="Use !vendorassess <id> to improve vendor security")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='vendoradd')
    async def vendoradd_prefix(self, ctx, name: str, category: str, *, details: str = None):
        """Add vendor - Prefix command"""
        await self._vendoradd_logic(ctx, name, category, details=details)
    
    @commands.command(name='vendorlist')
    async def vendorlist_prefix(self, ctx):
        """List vendors - Prefix command"""
        await self._vendorlist_logic(ctx)
    
    @commands.command(name='vendordetail')
    async def vendordetail_prefix(self, ctx, vendor_id: str):
        """Show vendor details - Prefix command"""
        await self._vendordetail_logic(ctx, vendor_id)
    
    @commands.command(name='vendorrisks')
    async def vendorrisks_prefix(self, ctx):
        """Show high-risk vendors - Prefix command"""
        await self._vendorrisks_logic(ctx)

async def setup(bot):
    await bot.add_cog(VendorRiskManagement(bot))
