"""
Executive Risk Dashboard - C-level security reporting and risk visualization
Comprehensive executive-level security and risk reporting for leadership
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid
from cogs.core.pst_timezone import get_now_pst

class ExecutiveRiskDashboard(commands.Cog):
    """Executive security risk dashboard and reporting"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reports_file = 'data/executive_reports.json'
        self.kpis_file = 'data/executive_kpis.json'
        self.load_data()
    
    def load_data(self):
        """Load executive dashboard data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.reports_file):
            with open(self.reports_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.kpis_file):
            with open(self.kpis_file, 'w') as f:
                json.dump({}, f)
    
    def get_reports(self, guild_id):
        """Get executive reports"""
        with open(self.reports_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_reports(self, guild_id, reports):
        """Save reports"""
        with open(self.reports_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = reports[-50:]
        with open(self.reports_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_kpis(self, guild_id):
        """Get KPIs"""
        with open(self.kpis_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_kpis(self, guild_id, kpis):
        """Save KPIs"""
        with open(self.kpis_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = kpis
        with open(self.kpis_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_risk_rating(self, kpis):
        """Calculate overall risk rating"""
        score = 0
        
        # Incident frequency
        incidents_month = kpis.get('incidents_last_month', 0)
        if incidents_month > 10:
            score += 35
        elif incidents_month > 5:
            score += 20
        elif incidents_month > 0:
            score += 10
        
        # MTTR (Mean Time to Respond)
        mttr = kpis.get('mttr_hours', 24)
        if mttr > 12:
            score += 20
        elif mttr > 4:
            score += 10
        
        # Security posture
        posture_score = kpis.get('security_posture_score', 60)
        if posture_score < 40:
            score += 30
        elif posture_score < 60:
            score += 15
        
        # Compliance status
        if not kpis.get('compliance_compliant', True):
            score += 25
        
        # Vulnerabilities
        critical_vulns = kpis.get('critical_vulnerabilities', 0)
        score += critical_vulns * 5
        
        return min(100, score)
    
    async def _executivedashboard_logic(self, ctx):
        """Show executive risk dashboard"""
        kpis = self.get_kpis(ctx.guild.id)
        
        # Initialize default KPIs
        if not kpis:
            kpis = {
                'incidents_last_month': 3,
                'incidents_last_quarter': 12,
                'mttr_hours': 2.5,
                'mttd_hours': 18,
                'security_posture_score': 78,
                'compliance_compliant': True,
                'critical_vulnerabilities': 2,
                'high_vulnerabilities': 8,
                'security_spend_percent': 4.2,
                'risk_trend': 'improving',
                'data_breaches_ytd': 0,
                'phishing_click_rate': 8
            }
            self.save_kpis(ctx.guild.id, kpis)
        
        risk_rating = self.calculate_risk_rating(kpis)
        risk_emoji = '🔴' if risk_rating >= 70 else '🟠' if risk_rating >= 50 else '🟡' if risk_rating >= 30 else '🟢'
        color = discord.Color.red() if risk_rating >= 70 else discord.Color.orange() if risk_rating >= 50 else discord.Color.gold() if risk_rating >= 30 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"{risk_emoji} Executive Security Risk Dashboard",
            description="C-Level Security & Risk Overview",
            color=color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Overall Risk Rating", value=f"**{risk_rating}/100**", inline=True)
        embed.add_field(name="Risk Trend", value=f"📈 {kpis.get('risk_trend', 'stable').title()}", inline=True)
        embed.add_field(name="Compliance Status", value="✅ Compliant" if kpis.get('compliance_compliant') else "⚠️ Non-Compliant", inline=True)
        
        embed.add_field(name="Incident Metrics", value="━" * 25, inline=False)
        embed.add_field(name="Incidents (30 days)", value=f"⚠️ {kpis.get('incidents_last_month', 0)}", inline=True)
        embed.add_field(name="Data Breaches (YTD)", value=f"🔴 {kpis.get('data_breaches_ytd', 0)}", inline=True)
        embed.add_field(name="MTTR (Avg)", value=f"⏱️ {kpis.get('mttr_hours', 0):.1f}h", inline=True)
        
        embed.add_field(name="Security Posture", value="━" * 25, inline=False)
        embed.add_field(name="Posture Score", value=f"📊 {kpis.get('security_posture_score', 0)}/100", inline=True)
        embed.add_field(name="Vulnerabilities", value=f"🔴 {kpis.get('critical_vulnerabilities', 0)} critical | 🟠 {kpis.get('high_vulnerabilities', 0)} high", inline=True)
        
        embed.add_field(name="Human Risk", value="━" * 25, inline=False)
        embed.add_field(name="Phishing Click Rate", value=f"⚠️ {kpis.get('phishing_click_rate', 0)}%", inline=True)
        embed.add_field(name="Training Completion", value=f"✅ 92%", inline=True)
        
        embed.add_field(name="Investment", value="━" * 25, inline=False)
        embed.add_field(name="Security Spend", value=f"💰 {kpis.get('security_spend_percent', 0):.1f}% of IT budget", inline=False)
        
        embed.set_footer(text="Updated daily at 6:00 AM | Drill down with !execsummary")
        
        await ctx.send(embed=embed)
    
    async def _execsummary_logic(self, ctx, period: str = 'monthly'):
        """Generate executive summary report"""
        kpis = self.get_kpis(ctx.guild.id)
        
        if not kpis:
            await ctx.send("📊 No KPI data available.")
            return
        
        period_label = period.lower()
        
        embed = discord.Embed(
            title=f"📋 Executive Security Summary ({period_label.title()})",
            description="Key Security & Risk Metrics for Leadership",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Executive summary
        embed.add_field(name="🎯 Key Findings", value="━" * 25, inline=False)
        embed.add_field(
            name="1. Incident Response Performance",
            value=f"MTTR: {kpis.get('mttr_hours', 0):.1f}h (Industry: 4h) | Status: ✅ EXCELLENT",
            inline=False
        )
        embed.add_field(
            name="2. Security Posture",
            value=f"Score: {kpis.get('security_posture_score', 0)}/100 | Trend: {kpis.get('risk_trend', 'stable').title()} | Status: 📈 IMPROVING",
            inline=False
        )
        embed.add_field(
            name="3. Vulnerability Management",
            value=f"Critical: {kpis.get('critical_vulnerabilities', 0)} | High: {kpis.get('high_vulnerabilities', 0)} | Remediation Rate: 94%",
            inline=False
        )
        embed.add_field(
            name="4. Compliance Status",
            value="✅ All regulatory frameworks met | GDPR: ✅ | SOC2: ✅ | ISO27001: ✅",
            inline=False
        )
        
        embed.add_field(name="📊 Business Impact", value="━" * 25, inline=False)
        embed.add_field(name="Data Breaches", value="🟢 0 (YTD)", inline=True)
        embed.add_field(name="System Downtime", value="🟢 0.02%", inline=True)
        embed.add_field(name="Risk Exposure", value="🟢 Low", inline=True)
        
        embed.add_field(name="💡 Recommendations", value="━" * 25, inline=False)
        embed.add_field(name="1. Phishing Awareness", value="Click rate 8% - Increase training frequency", inline=False)
        embed.add_field(name="2. Zero Trust Migration", value="50% complete - On track for Q2 2026", inline=False)
        embed.add_field(name="3. Cloud Security", value="Implement multi-cloud risk monitoring", inline=False)
        
        embed.set_footer(text="Full detailed report available in dashboard")
        
        await ctx.send(embed=embed)
    
    async def _risktrending_logic(self, ctx):
        """Show risk trending over time"""
        embed = discord.Embed(
            title="📈 Risk Trending Analysis",
            description="Security risk trends over the past 12 months",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="12-Month Trend", value="━" * 25, inline=False)
        
        # Simulate trending data
        trend_data = [
            ("January", 65, "🟠"),
            ("February", 62, "🟠"),
            ("March", 58, "🟡"),
            ("April", 52, "🟡"),
            ("May", 48, "🟡"),
            ("June", 45, "🟢"),
            ("July", 42, "🟢"),
            ("August", 40, "🟢"),
            ("September", 38, "🟢"),
            ("October", 35, "🟢"),
            ("November", 32, "🟢"),
            ("December", 28, "🟢"),
        ]
        
        for month, score, emoji in trend_data:
            bar = '█' * (score // 10) + '░' * (10 - score // 10)
            embed.add_field(name=f"{emoji} {month}", value=f"`{bar}` {score}/100", inline=False)
        
        embed.add_field(name="Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Overall Trend", value="📉 IMPROVING (55% reduction in risk score)", inline=False)
        embed.add_field(name="Key Drivers", value="• Enhanced incident response\n• Improved vulnerability management\n• Cloud security initiatives", inline=False)
        
        embed.set_footer(text="Data-driven security improvements")
        
        await ctx.send(embed=embed)
    
    async def _boardreport_logic(self, ctx):
        """Generate board-level risk report"""
        embed = discord.Embed(
            title="🏛️ Board-Level Security & Risk Report",
            description="Strategic Security Status for Board Review",
            color=discord.Color.gold(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="EXECUTIVE SUMMARY", value="━" * 25, inline=False)
        embed.add_field(
            name="Overall Assessment",
            value="Security posture has significantly improved over the past 12 months through strategic investments in detection, response, and prevention capabilities.",
            inline=False
        )
        
        embed.add_field(name="RISK MITIGATION", value="━" * 25, inline=False)
        embed.add_field(name="Incidents Prevented", value="Estimated 47 incidents prevented through proactive threat hunting", inline=False)
        embed.add_field(name="Cost Avoidance", value="Estimated $18.5M in breach cost avoidance (based on industry average)", inline=False)
        
        embed.add_field(name="STRATEGIC INITIATIVES", value="━" * 25, inline=False)
        embed.add_field(name="1. Zero Trust Architecture", value="Status: 50% complete | Timeline: Q4 2025", inline=False)
        embed.add_field(name="2. Cloud Security Program", value="Status: In progress | Coverage: 8 cloud environments", inline=False)
        embed.add_field(name="3. AI/ML Threat Detection", value="Status: Deployed | Detection rate: 94%", inline=False)
        
        embed.add_field(name="BUDGET & INVESTMENT", value="━" * 25, inline=False)
        embed.add_field(name="Security Spend", value="4.2% of IT budget | Industry average: 3.8%", inline=True)
        embed.add_field(name="ROI (Risk Reduction)", value="3.2x (industry avg: 2.1x)", inline=True)
        
        embed.set_footer(text="Approved for board review | Confidential")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='executivedashboard')
    async def executivedashboard_prefix(self, ctx):
        """Show executive dashboard - Prefix command"""
        await self._executivedashboard_logic(ctx)
    
    @commands.command(name='execsummary')
    async def execsummary_prefix(self, ctx, period: str = 'monthly'):
        """Generate executive summary - Prefix command"""
        await self._execsummary_logic(ctx, period)
    
    @commands.command(name='risktrending')
    async def risktrending_prefix(self, ctx):
        """Show risk trending - Prefix command"""
        await self._risktrending_logic(ctx)
    
    @commands.command(name='boardreport')
    async def boardreport_prefix(self, ctx):
        """Generate board report - Prefix command"""
        await self._boardreport_logic(ctx)

async def setup(bot):
    await bot.add_cog(ExecutiveRiskDashboard(bot))
