"""
Third-Party Risk Intelligence - Continuous vendor and supplier risk monitoring
Unified vendor risk monitoring with supply chain intelligence and continuous assessment
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class ThirdPartyRiskIntelligence(commands.Cog):
    """Third-party risk intelligence and supply chain monitoring"""
    
    def __init__(self, bot):
        self.bot = bot
        self.suppliers_file = 'data/third_party_suppliers.json'
        self.incidents_file = 'data/third_party_incidents.json'
        self.load_data()
    
    def load_data(self):
        """Load third-party risk data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.suppliers_file):
            with open(self.suppliers_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.incidents_file):
            with open(self.incidents_file, 'w') as f:
                json.dump({}, f)
    
    def get_suppliers(self, guild_id):
        """Get third-party suppliers"""
        with open(self.suppliers_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_suppliers(self, guild_id, suppliers):
        """Save suppliers"""
        with open(self.suppliers_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = suppliers
        with open(self.suppliers_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_incidents(self, guild_id):
        """Get third-party incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_incidents(self, guild_id, incidents):
        """Save incidents"""
        with open(self.incidents_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = incidents[-150:]
        with open(self.incidents_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_supply_chain_risk(self, supplier):
        """Calculate supply chain risk score (0-100)"""
        score = 30
        
        # Direct security incidents
        incidents = supplier.get('security_incidents', 0)
        score += incidents * 8
        
        # Industry reputation
        reputation = supplier.get('industry_reputation', 'good')
        if reputation == 'poor':
            score += 30
        elif reputation == 'fair':
            score += 15
        
        # Criticality to operations
        if supplier.get('critical_operations', False):
            score += 20
        
        # Data handling
        if supplier.get('handles_sensitive_data', False):
            score += 25
        
        # Geopolitical risk
        high_risk_countries = ['high_risk']
        if supplier.get('location') in high_risk_countries:
            score += 20
        
        # Subcontractor chain depth
        subcontractors = supplier.get('subcontractor_count', 0)
        if subcontractors > 10:
            score += 15
        
        # Last security audit
        if supplier.get('last_security_audit'):
            last = datetime.fromisoformat(supplier['last_security_audit'])
            days_since = (get_now_pst() - last).days
            if days_since > 365:
                score += 20
        else:
            score += 25
        
        # Contractual security requirements
        if not supplier.get('has_security_requirements', False):
            score += 15
        
        return min(100, score)
    
    async def _addsupplier_logic(self, ctx, supplier_name: str, supplier_type: str, criticality: str = 'medium'):
        """Add third-party supplier"""
        suppliers = self.get_suppliers(ctx.guild.id)
        
        supplier_id = f"3PTY-{str(uuid.uuid4())[:8].upper()}"
        
        supplier = {
            'id': supplier_id,
            'name': supplier_name,
            'type': supplier_type.lower(),
            'criticality': criticality.lower(),
            'added_at': get_now_pst().isoformat(),
            'status': 'active',
            'security_incidents': 0,
            'industry_reputation': 'good',
            'critical_operations': criticality == 'critical',
            'handles_sensitive_data': False,
            'location': 'USA',
            'subcontractor_count': 0,
            'last_security_audit': None,
            'has_security_requirements': True,
            'risk_score': 0,
            'contract_end_date': (get_now_pst() + timedelta(days=365)).isoformat(),
            'incident_history': []
        }
        
        supplier['risk_score'] = self.calculate_supply_chain_risk(supplier)
        suppliers[supplier_id] = supplier
        self.save_suppliers(ctx.guild.id, suppliers)
        
        embed = discord.Embed(
            title="🏭 Third-Party Supplier Added",
            description=f"**{supplier_name}**",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Supplier ID", value=f"`{supplier_id}`", inline=True)
        embed.add_field(name="Type", value=supplier_type.title(), inline=True)
        embed.add_field(name="Criticality", value=criticality.title(), inline=True)
        embed.add_field(name="Risk Score", value=f"{supplier['risk_score']}/100", inline=True)
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Reputation", value="Good", inline=True)
        
        embed.set_footer(text="Use !supplierfull to see complete profile")
        
        await ctx.send(embed=embed)
    
    async def _supplierindex_logic(self, ctx):
        """List all third-party suppliers"""
        suppliers = self.get_suppliers(ctx.guild.id)
        
        if not suppliers:
            await ctx.send("🏭 No third-party suppliers registered.")
            return
        
        # Sort by risk score
        sorted_suppliers = sorted(suppliers.values(), key=lambda s: s['risk_score'], reverse=True)
        
        embed = discord.Embed(
            title="🏭 Third-Party Supplier Index",
            description=f"{len(sorted_suppliers)} supplier(s) tracked",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Risk distribution
        critical = sum(1 for s in suppliers.values() if s['risk_score'] >= 70)
        high = sum(1 for s in suppliers.values() if 50 <= s['risk_score'] < 70)
        
        embed.add_field(name="Risk Distribution", value=f"🔴 {critical} critical | 🟠 {high} high | 🟢 {len(suppliers) - critical - high} acceptable", inline=False)
        
        for supplier in sorted_suppliers[:10]:
            risk_emoji = '🔴' if supplier['risk_score'] >= 70 else '🟠' if supplier['risk_score'] >= 50 else '🟡' if supplier['risk_score'] >= 30 else '🟢'
            
            embed.add_field(
                name=f"{risk_emoji} {supplier['name']} ({supplier['id']})",
                value=f"Type: {supplier['type'].title()} | Criticality: {supplier['criticality'].title()} | Risk: {supplier['risk_score']}/100",
                inline=False
            )
        
        if len(sorted_suppliers) > 10:
            embed.add_field(name="... and more", value=f"+{len(sorted_suppliers) - 10} additional suppliers", inline=False)
        
        embed.set_footer(text="Use !supplierfull <id> for detailed risk analysis")
        
        await ctx.send(embed=embed)
    
    async def _supplierfull_logic(self, ctx, supplier_id: str):
        """Show detailed supplier risk profile"""
        suppliers = self.get_suppliers(ctx.guild.id)
        
        supplier_id = supplier_id.upper()
        if not supplier_id.startswith('3PTY-'):
            supplier_id = f"3PTY-{supplier_id}"
        
        supplier = suppliers.get(supplier_id)
        if not supplier:
            await ctx.send(f"❌ Supplier not found: {supplier_id}")
            return
        
        risk_score = supplier['risk_score']
        color = discord.Color.red() if risk_score >= 70 else discord.Color.orange() if risk_score >= 50 else discord.Color.gold() if risk_score >= 30 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"🏭 {supplier['name']} - Supply Chain Risk Profile",
            description=f"Risk Score: **{risk_score}/100**",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Supplier ID", value=f"`{supplier['id']}`", inline=True)
        embed.add_field(name="Type", value=supplier['type'].title(), inline=True)
        embed.add_field(name="Criticality", value=supplier['criticality'].title(), inline=True)
        
        embed.add_field(name="Risk Factors", value="━" * 25, inline=False)
        embed.add_field(name="Security Incidents", value=f"⚠️ {supplier['security_incidents']}", inline=True)
        embed.add_field(name="Reputation", value=supplier['industry_reputation'].title(), inline=True)
        embed.add_field(name="Location", value=supplier['location'], inline=True)
        
        embed.add_field(name="Operational Context", value="━" * 25, inline=False)
        embed.add_field(name="Critical Operations", value="✅ Yes" if supplier['critical_operations'] else "❌ No", inline=True)
        embed.add_field(name="Handles Sensitive Data", value="✅ Yes" if supplier['handles_sensitive_data'] else "❌ No", inline=True)
        embed.add_field(name="Subcontractors", value=f"{supplier['subcontractor_count']}", inline=True)
        
        embed.add_field(name="Contract Management", value="━" * 25, inline=False)
        embed.add_field(name="Status", value=supplier['status'].title(), inline=True)
        embed.add_field(name="Contract Expires", value=datetime.fromisoformat(supplier['contract_end_date']).strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Security Requirements", value="✅ Yes" if supplier['has_security_requirements'] else "⚠️ No", inline=True)
        
        if supplier['last_security_audit']:
            last_audit = datetime.fromisoformat(supplier['last_security_audit']).strftime('%Y-%m-%d')
            embed.add_field(name="Last Security Audit", value=last_audit, inline=False)
        
        if supplier['incident_history']:
            incidents = "\n".join([f"• {i}" for i in supplier['incident_history'][:3]])
            embed.add_field(name="Incident History", value=incidents, inline=False)
        
        embed.set_footer(text="Sentinel Third-Party Risk Intelligence")
        
        await ctx.send(embed=embed)
    
    async def _supplychainmonitor_logic(self, ctx):
        """Monitor supply chain risks"""
        suppliers = self.get_suppliers(ctx.guild.id)
        incidents = self.get_incidents(ctx.guild.id)
        
        if not suppliers:
            await ctx.send("🏭 No suppliers to monitor.")
            return
        
        # Identify risk areas
        critical_suppliers = [s for s in suppliers.values() if s['criticality'] == 'critical' and s['risk_score'] >= 50]
        suppliers_with_incidents = [s for s in suppliers.values() if s['security_incidents'] > 0]
        expiring_contracts = [s for s in suppliers.values() if datetime.fromisoformat(s['contract_end_date']) < get_now_pst() + timedelta(days=90)]
        
        embed = discord.Embed(
            title="🔍 Supply Chain Risk Monitoring",
            description="Real-time supply chain threat assessment",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Total Suppliers", value=f"🏭 {len(suppliers)}", inline=True)
        embed.add_field(name="Recent Incidents", value=f"⚠️ {len(incidents)}", inline=True)
        embed.add_field(name="Contract Status", value="📋 View expiring contracts", inline=True)
        
        if critical_suppliers:
            embed.add_field(name="🔴 Critical Risk Suppliers", value=f"{len(critical_suppliers)} supplier(s) require attention", inline=False)
            for sup in critical_suppliers[:3]:
                embed.add_field(name=f"  • {sup['name']}", value=f"Risk: {sup['risk_score']}/100 | Incidents: {sup['security_incidents']}", inline=False)
        
        if suppliers_with_incidents:
            embed.add_field(name="⚠️ Suppliers With Incidents", value=f"{len(suppliers_with_incidents)} supplier(s) with incident history", inline=False)
        
        if expiring_contracts:
            embed.add_field(name="📋 Expiring Contracts", value=f"{len(expiring_contracts)} contract(s) expiring within 90 days", inline=False)
        
        embed.set_footer(text="Use !supplierfull <id> to investigate specific suppliers")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='addsupplier')
    async def addsupplier_prefix(self, ctx, supplier_name: str, supplier_type: str, criticality: str = 'medium'):
        """Add third-party supplier - Prefix command"""
        await self._addsupplier_logic(ctx, supplier_name, supplier_type, criticality)
    
    @commands.command(name='supplierindex')
    async def supplierindex_prefix(self, ctx):
        """List suppliers - Prefix command"""
        await self._supplierindex_logic(ctx)
    
    @commands.command(name='supplierfull')
    async def supplierfull_prefix(self, ctx, supplier_id: str):
        """Show supplier profile - Prefix command"""
        await self._supplierfull_logic(ctx, supplier_id)
    
    @commands.command(name='supplychainmonitor')
    async def supplychainmonitor_prefix(self, ctx):
        """Monitor supply chain - Prefix command"""
        await self._supplychainmonitor_logic(ctx)

async def setup(bot):
    await bot.add_cog(ThirdPartyRiskIntelligence(bot))
