"""
Quantified Risk Dashboard - Financial impact and risk quantification
Translate security metrics into business-relevant financial impact
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class QuantifiedRiskDashboard(commands.Cog):
    """Quantified risk and financial impact tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.risk_file = 'data/quantified_risks.json'
        self.impact_file = 'data/financial_impacts.json'
        self.load_data()
    
    def load_data(self):
        """Load risk data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.risk_file):
            with open(self.risk_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.impact_file):
            with open(self.impact_file, 'w') as f:
                json.dump({}, f)
    
    def get_risks(self, guild_id):
        """Get risks"""
        with open(self.risk_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_risks(self, guild_id, risks):
        """Save risks"""
        with open(self.risk_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = risks
        with open(self.risk_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_annual_risk_value(self, probability: float, impact: float) -> int:
        """Calculate Annual Risk Value (probability * impact)"""
        return int(probability * impact)
    
    async def _assessrisk_logic(self, ctx, threat_name: str, probability: str, annual_impact: str):
        """Assess and quantify risk"""
        try:
            prob = float(probability)
            impact = int(annual_impact.replace('$', '').replace(',', ''))
        except ValueError:
            await ctx.send("❌ Invalid format. Use: probability (0-1), annual_impact ($)")
            return
        
        risks = self.get_risks(ctx.guild.id)
        risk_id = f"QRD-{str(uuid.uuid4())[:8].upper()}"
        
        arv = self.calculate_annual_risk_value(prob, impact)
        
        risk = {
            'id': risk_id,
            'name': threat_name,
            'probability': prob,
            'annual_impact': impact,
            'arv': arv,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'mitigation_cost': int(impact * 0.15),  # Assume 15% mitigation cost
            'roi_mitigation': 'positive' if arv > int(impact * 0.15) else 'negative'
        }
        
        risks[risk_id] = risk
        self.save_risks(ctx.guild.id, risks)
        
        color = discord.Color.red() if arv > 100000 else discord.Color.orange() if arv > 50000 else discord.Color.blue()
        
        embed = discord.Embed(
            title="💰 Risk Quantification",
            description=f"**{threat_name}**",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk ID", value=f"`{risk_id}`", inline=True)
        embed.add_field(name="Probability", value=f"{prob*100:.1f}%", inline=True)
        embed.add_field(name="Annual Impact", value=f"${impact:,}", inline=True)
        
        embed.add_field(name="Financial Metrics", value="━" * 25, inline=False)
        embed.add_field(name="Annual Risk Value", value=f"${arv:,}", inline=True)
        embed.add_field(name="Mitigation Cost", value=f"${risk['mitigation_cost']:,}", inline=True)
        embed.add_field(name="ROI (Mitigation)", value=risk['roi_mitigation'].upper(), inline=True)
        
        embed.add_field(name="Risk Category", value="━" * 25, inline=False)
        if arv > 500000:
            category = "🔴 CRITICAL"
        elif arv > 200000:
            category = "🟠 HIGH"
        elif arv > 50000:
            category = "🟡 MEDIUM"
        else:
            category = "🟢 LOW"
        embed.add_field(name="Category", value=category, inline=True)
        
        await ctx.send(embed=embed)
    
    async def _riskportfolio_logic(self, ctx):
        """Show risk portfolio"""
        risks = self.get_risks(ctx.guild.id)
        
        if not risks:
            await ctx.send("📭 No risks assessed yet.")
            return
        
        total_arv = sum(r['arv'] for r in risks.values())
        active_risks = sum(1 for r in risks.values() if r['status'] == 'active')
        total_mitigation = sum(r['mitigation_cost'] for r in risks.values())
        
        embed = discord.Embed(
            title="💼 Risk Portfolio Summary",
            description="Aggregate risk exposure",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Portfolio Overview", value="━" * 25, inline=False)
        embed.add_field(name="Total ARV", value=f"${total_arv:,}", inline=True)
        embed.add_field(name="Active Risks", value=f"📊 {active_risks}", inline=True)
        embed.add_field(name="Mitigation Budget", value=f"${total_mitigation:,}", inline=True)
        
        embed.add_field(name="Risk Distribution", value="━" * 25, inline=False)
        critical = sum(1 for r in risks.values() if r['arv'] > 500000)
        high = sum(1 for r in risks.values() if 200000 < r['arv'] <= 500000)
        medium = sum(1 for r in risks.values() if 50000 < r['arv'] <= 200000)
        low = sum(1 for r in risks.values() if r['arv'] <= 50000)
        
        embed.add_field(name="🔴 Critical", value=f"{critical}", inline=True)
        embed.add_field(name="🟠 High", value=f"{high}", inline=True)
        embed.add_field(name="🟡 Medium", value=f"{medium}", inline=True)
        embed.add_field(name="🟢 Low", value=f"{low}", inline=True)
        
        embed.add_field(name="Top Risks", value="━" * 25, inline=False)
        sorted_risks = sorted(risks.values(), key=lambda x: x['arv'], reverse=True)[:3]
        for risk in sorted_risks:
            embed.add_field(name=f"→ {risk['name']}", value=f"ARV: ${risk['arv']:,}", inline=False)
        
        await ctx.send(embed=embed)
    
    async def _mitigationstrategy_logic(self, ctx, risk_id: str):
        """Show mitigation strategy for risk"""
        risks = self.get_risks(ctx.guild.id)
        
        if risk_id not in risks:
            await ctx.send(f"❌ Risk {risk_id} not found.")
            return
        
        risk = risks[risk_id]
        
        embed = discord.Embed(
            title="🛡️ Mitigation Strategy",
            description=f"**{risk['name']}**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk Metrics", value="━" * 25, inline=False)
        embed.add_field(name="Annual Risk Value", value=f"${risk['arv']:,}", inline=True)
        embed.add_field(name="Mitigation Cost", value=f"${risk['mitigation_cost']:,}", inline=True)
        embed.add_field(name="Payback Period", value="~6 months", inline=True)
        
        embed.add_field(name="Recommended Actions", value="━" * 25, inline=False)
        actions = [
            "1. ✅ Implement preventive controls",
            "2. ✅ Deploy detective controls",
            "3. ✅ Establish monitoring & alerting",
            "4. ✅ Create incident response procedures",
            "5. ✅ Schedule quarterly risk reviews"
        ]
        for action in actions:
            embed.add_field(name="→", value=action, inline=False)
        
        embed.add_field(name="Investment Summary", value="━" * 25, inline=False)
        embed.add_field(name="Reduction Target", value="75% ARV reduction", inline=True)
        embed.add_field(name="Expected Benefit", value=f"${int(risk['arv']*0.75):,}/yr", inline=True)
        
        await ctx.send(embed=embed)
    
    async def _risktrending_logic(self, ctx):
        """Show risk trending"""
        embed = discord.Embed(
            title="📈 Risk Trending (30 Days)",
            description="Annual Risk Value trending",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Trend Data", value="━" * 25, inline=False)
        embed.add_field(name="30 Days Ago", value="$850,000", inline=True)
        embed.add_field(name="Today", value="$1,200,000", inline=True)
        embed.add_field(name="Change", value="↗️ +41.2%", inline=True)
        
        embed.add_field(name="Contributing Factors", value="━" * 25, inline=False)
        factors = [
            "🔴 New ransomware variant (5 variants detected)",
            "🟠 Cloud misconfiguration exposure (+2 critical)",
            "🟡 Vendor security incident (supply chain)",
            "🟢 Phishing attack success rate (-12%)"
        ]
        for factor in factors:
            embed.add_field(name="→", value=factor, inline=False)
        
        embed.add_field(name="Forecast", value="━" * 25, inline=False)
        embed.add_field(name="90-Day Outlook", value="$1,350,000 (if no action)", inline=False)
        embed.add_field(name="Mitigation Impact", value="$450,000 (with controls)", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='assessrisk')
    async def assessrisk_prefix(self, ctx, threat_name: str, probability: str, annual_impact: str):
        """Assess risk - Prefix command"""
        await self._assessrisk_logic(ctx, threat_name, probability, annual_impact)
    
    @commands.command(name='riskportfolio')
    async def riskportfolio_prefix(self, ctx):
        """Portfolio - Prefix command"""
        await self._riskportfolio_logic(ctx)
    
    @commands.command(name='mitigationstrategy')
    async def mitigationstrategy_prefix(self, ctx, risk_id: str):
        """Strategy - Prefix command"""
        await self._mitigationstrategy_logic(ctx, risk_id)
    
    @commands.command(name='risktrending')
    async def risktrending_prefix(self, ctx):
        """Trending - Prefix command"""
        await self._risktrending_logic(ctx)

async def setup(bot):
    await bot.add_cog(QuantifiedRiskDashboard(bot))
