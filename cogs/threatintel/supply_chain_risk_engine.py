"""
Supply Chain Risk Engine
Monitors supply chain threats with third-party compromise alerts and dependency trust scoring
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class SupplyChainRiskEngineCog(commands.Cog):
    """Supply Chain Risk Engine - Tracks third-party and dependency security risks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/supply_chain"
        os.makedirs(self.data_dir, exist_ok=True)
        self.vendors_file = os.path.join(self.data_dir, "vendors.json")
        self.alerts_file = os.path.join(self.data_dir, "supply_chain_alerts.json")
        self.vendors = self.load_vendors()
        self.alerts = self.load_alerts()
        
    def load_vendors(self):
        if os.path.exists(self.vendors_file):
            with open(self.vendors_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_vendors(self):
        with open(self.vendors_file, 'w') as f:
            json.dump(self.vendors, f, indent=4)
    
    def load_alerts(self):
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_alerts(self):
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=4)
    
    @commands.command(name="supply_add_vendor")
    @commands.has_permissions(administrator=True)
    async def add_vendor(self, ctx, vendor_name: str, trust_score: int, *, description: str):
        """Add vendor to supply chain tracking\nUsage: !supply_add_vendor <name> <trust_0-100> <description>"""
        vendor = {
            "id": len(self.vendors) + 1,
            "name": vendor_name,
            "trust_score": max(0, min(100, trust_score)),
            "description": description,
            "added_at": datetime.utcnow().isoformat(),
            "added_by": str(ctx.author.id),
            "status": "active"
        }
        
        self.vendors.append(vendor)
        self.save_vendors()
        
        color = discord.Color.green() if trust_score >= 70 else discord.Color.gold() if trust_score >= 50 else discord.Color.red()
        embed = discord.Embed(title="✅ Vendor Added", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Vendor ID", value=f"#{vendor['id']}", inline=True)
        embed.add_field(name="Name", value=vendor_name, inline=True)
        embed.add_field(name="Trust Score", value=f"{trust_score}/100", inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="supply_alert")
    @commands.has_permissions(administrator=True)
    async def create_alert(self, ctx, vendor_id: int, severity: str, *, description: str):
        """Create supply chain security alert\nUsage: !supply_alert <vendor_id> <critical|high|medium|low> <description>"""
        vendor = next((v for v in self.vendors if v["id"] == vendor_id), None)
        if not vendor:
            await ctx.send(f"❌ Vendor #{vendor_id} not found")
            return
        
        alert = {
            "id": len(self.alerts) + 1,
            "vendor_id": vendor_id,
            "vendor_name": vendor["name"],
            "severity": severity.lower(),
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": str(ctx.author.id),
            "status": "open"
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        
        color_map = {"critical": discord.Color.dark_red(), "high": discord.Color.red(), "medium": discord.Color.gold(), "low": discord.Color.green()}
        embed = discord.Embed(title="⚠️ Supply Chain Alert", color=color_map.get(severity.lower(), discord.Color.blue()), timestamp=datetime.utcnow())
        embed.add_field(name="Alert ID", value=f"#{alert['id']}", inline=True)
        embed.add_field(name="Vendor", value=vendor["name"], inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="supply_risk_report")
    @commands.has_permissions(administrator=True)
    async def risk_report(self, ctx):
        """Generate supply chain risk report\nUsage: !supply_risk_report"""
        if not self.vendors:
            await ctx.send("📊 No vendors tracked")
            return
        
        high_risk = [v for v in self.vendors if v["trust_score"] < 50]
        medium_risk = [v for v in self.vendors if 50 <= v["trust_score"] < 70]
        low_risk = [v for v in self.vendors if v["trust_score"] >= 70]
        
        open_alerts = [a for a in self.alerts if a.get("status") == "open"]
        critical_alerts = [a for a in open_alerts if a.get("severity") == "critical"]
        
        embed = discord.Embed(title="📊 Supply Chain Risk Report", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="🔴 High Risk Vendors", value=len(high_risk), inline=True)
        embed.add_field(name="🟡 Medium Risk Vendors", value=len(medium_risk), inline=True)
        embed.add_field(name="🟢 Low Risk Vendors", value=len(low_risk), inline=True)
        embed.add_field(name="⚠️ Open Alerts", value=len(open_alerts), inline=True)
        embed.add_field(name="🚨 Critical Alerts", value=len(critical_alerts), inline=True)
        
        if high_risk:
            high_risk_text = "\n".join([f"• {v['name']} (Trust: {v['trust_score']})" for v in high_risk[:5]])
            embed.add_field(name="High Risk Vendors", value=high_risk_text, inline=False)
        
        if critical_alerts:
            embed.add_field(name="⚠️ Action Required", value=f"{len(critical_alerts)} critical alerts need immediate attention", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="supply_vendors")
    @commands.has_permissions(administrator=True)
    async def list_vendors(self, ctx):
        """List all tracked vendors\nUsage: !supply_vendors"""
        if not self.vendors:
            await ctx.send("📋 No vendors tracked")
            return
        
        sorted_vendors = sorted(self.vendors, key=lambda x: x["trust_score"])
        embed = discord.Embed(title="📋 Supply Chain Vendors", color=discord.Color.blue(), timestamp=datetime.utcnow())
        
        for vendor in sorted_vendors[:10]:
            trust = vendor["trust_score"]
            indicator = "🔴" if trust < 50 else "🟡" if trust < 70 else "🟢"
            embed.add_field(name=f"{indicator} {vendor['name']}", value=f"Trust: {trust}/100 | ID: #{vendor['id']}", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="supply_dashboard")
    @commands.has_permissions(administrator=True)
    async def dashboard(self, ctx):
        """View supply chain risk dashboard\nUsage: !supply_dashboard"""
        total_vendors = len(self.vendors)
        total_alerts = len(self.alerts)
        open_alerts = len([a for a in self.alerts if a.get("status") == "open"])
        high_risk_vendors = len([v for v in self.vendors if v["trust_score"] < 50])
        
        embed = discord.Embed(title="🔗 Supply Chain Risk Dashboard", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="📊 Total Vendors", value=total_vendors, inline=True)
        embed.add_field(name="⚠️ Total Alerts", value=total_alerts, inline=True)
        embed.add_field(name="🔴 Open Alerts", value=open_alerts, inline=True)
        embed.add_field(name="🚨 High Risk Vendors", value=high_risk_vendors, inline=True)
        
        status = "🟢 SECURE" if high_risk_vendors == 0 and open_alerts == 0 else "🟡 MONITOR" if high_risk_vendors < 3 else "🔴 ELEVATED"
        embed.add_field(name="Risk Status", value=status, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SupplyChainRiskEngineCog(bot))
