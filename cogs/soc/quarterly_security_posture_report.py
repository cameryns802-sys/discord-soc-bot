"""
Quarterly Security Posture Report
Quarterly security reports with compliance status, incident trends, investment recommendations
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class QuarterlySecurityPostureReportCog(commands.Cog):
    """
    Quarterly Security Posture Report Generator
    
    Generates comprehensive quarterly security reports with compliance
    status, incident trends, and investment recommendations.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/quarterly_reports"
        os.makedirs(self.data_dir, exist_ok=True)
        self.reports_file = os.path.join(self.data_dir, "security_posture_reports.json")
        self.compliance_file = os.path.join(self.data_dir, "compliance_status.json")
        self.investments_file = os.path.join(self.data_dir, "investment_recommendations.json")
        self.reports = self.load_reports()
        self.compliance = self.load_compliance()
        self.investments = self.load_investments()
        
    def load_reports(self) -> List[Dict]:
        """Load quarterly reports from JSON storage"""
        if os.path.exists(self.reports_file):
            with open(self.reports_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_reports(self):
        """Save quarterly reports to JSON storage"""
        with open(self.reports_file, 'w') as f:
            json.dump(self.reports, f, indent=4)
    
    def load_compliance(self) -> Dict:
        """Load compliance status from JSON storage"""
        if os.path.exists(self.compliance_file):
            with open(self.compliance_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_compliance(self):
        """Save compliance status to JSON storage"""
        with open(self.compliance_file, 'w') as f:
            json.dump(self.compliance, f, indent=4)
    
    def load_investments(self) -> List[Dict]:
        """Load investment recommendations from JSON storage"""
        if os.path.exists(self.investments_file):
            with open(self.investments_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_investments(self):
        """Save investment recommendations to JSON storage"""
        with open(self.investments_file, 'w') as f:
            json.dump(self.investments, f, indent=4)
    
    def get_current_quarter(self) -> str:
        """Get current quarter in format Q1 2026"""
        now = get_now_pst()
        quarter = (now.month - 1) // 3 + 1
        return f"Q{quarter} {now.year}"
    
    @commands.command(name="quarterly_report")
    @commands.has_permissions(administrator=True)
    async def generate_quarterly_report(self, ctx):
        """
        Generate comprehensive quarterly security posture report
        
        Usage: !quarterly_report
        """
        await ctx.send("⏳ Generating quarterly security posture report...")
        
        quarter = self.get_current_quarter()
        
        # Collect incident data
        incident_cog = self.bot.get_cog('IncidentManagerCog')
        incident_stats = {
            "total_incidents": 0,
            "critical_incidents": 0,
            "resolved_incidents": 0,
            "avg_resolution_time": 0
        }
        
        if incident_cog and hasattr(incident_cog, 'incidents'):
            # Filter incidents for this quarter
            start_of_quarter = get_now_pst() - timedelta(days=90)
            quarter_incidents = [
                i for i in incident_cog.incidents
                if datetime.fromisoformat(i.get("timestamp", "2020-01-01")) >= start_of_quarter
            ]
            
            incident_stats["total_incidents"] = len(quarter_incidents)
            incident_stats["critical_incidents"] = len([i for i in quarter_incidents if i.get("severity") == "critical"])
            incident_stats["resolved_incidents"] = len([i for i in quarter_incidents if i.get("status") == "resolved"])
        
        # Collect compliance data
        compliance_status = {
            "gdpr_compliant": self.compliance.get("gdpr", False),
            "hipaa_compliant": self.compliance.get("hipaa", False),
            "pci_compliant": self.compliance.get("pci", False),
            "soc2_compliant": self.compliance.get("soc2", False),
            "overall_compliance": 0
        }
        
        compliant_count = sum([
            compliance_status["gdpr_compliant"],
            compliance_status["hipaa_compliant"],
            compliance_status["pci_compliant"],
            compliance_status["soc2_compliant"]
        ])
        compliance_status["overall_compliance"] = (compliant_count / 4) * 100
        
        # Collect threat intelligence
        threat_cog = self.bot.get_cog('ExecutiveThreatBriefingCog')
        threat_stats = {
            "active_threats": 0,
            "resolved_threats": 0,
            "critical_threats": 0
        }
        
        if threat_cog and hasattr(threat_cog, 'threats'):
            threat_stats["active_threats"] = len([t for t in threat_cog.threats if t.get("status") == "active"])
            threat_stats["resolved_threats"] = len([t for t in threat_cog.threats if t.get("status") == "resolved"])
            threat_stats["critical_threats"] = len([t for t in threat_cog.threats if t.get("severity") == "critical" and t.get("status") == "active"])
        
        # Generate report
        report = {
            "quarter": quarter,
            "generated_at": get_now_pst().isoformat(),
            "incident_stats": incident_stats,
            "compliance_status": compliance_status,
            "threat_stats": threat_stats,
            "generated_by": str(ctx.author.id)
        }
        
        self.reports.append(report)
        self.save_reports()
        
        # Create comprehensive embed
        embed = discord.Embed(
            title="📊 Quarterly Security Posture Report",
            description=f"Comprehensive Security Assessment - {quarter}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Executive Summary
        summary = f"This quarter saw **{incident_stats['total_incidents']}** security incidents with **{incident_stats['critical_incidents']}** critical events. "
        summary += f"Compliance rate stands at **{compliance_status['overall_compliance']:.0f}%** across key frameworks."
        embed.add_field(name="📋 Executive Summary", value=summary, inline=False)
        
        # Incident Trends
        embed.add_field(name="🔥 Total Incidents", value=incident_stats["total_incidents"], inline=True)
        embed.add_field(name="🚨 Critical", value=incident_stats["critical_incidents"], inline=True)
        embed.add_field(name="✅ Resolved", value=incident_stats["resolved_incidents"], inline=True)
        
        # Compliance Status
        compliance_text = ""
        compliance_text += f"GDPR: {'✅' if compliance_status['gdpr_compliant'] else '❌'}\n"
        compliance_text += f"HIPAA: {'✅' if compliance_status['hipaa_compliant'] else '❌'}\n"
        compliance_text += f"PCI-DSS: {'✅' if compliance_status['pci_compliant'] else '❌'}\n"
        compliance_text += f"SOC 2: {'✅' if compliance_status['soc2_compliant'] else '❌'}"
        embed.add_field(name="📜 Compliance Status", value=compliance_text, inline=True)
        
        # Threat Landscape
        threat_text = f"Active: {threat_stats['active_threats']}\n"
        threat_text += f"Critical: {threat_stats['critical_threats']}\n"
        threat_text += f"Resolved: {threat_stats['resolved_threats']}"
        embed.add_field(name="⚠️ Threat Landscape", value=threat_text, inline=True)
        
        # Investment Recommendations
        recommendations = self.generate_investment_recommendations(report)
        if recommendations:
            rec_text = "\n".join([f"• {r}" for r in recommendations[:5]])
            embed.add_field(name="💰 Investment Recommendations", value=rec_text, inline=False)
        
        # Trend Analysis
        if len(self.reports) >= 2:
            prev_report = self.reports[-2]
            current_incidents = incident_stats["total_incidents"]
            prev_incidents = prev_report["incident_stats"]["total_incidents"]
            
            if current_incidents < prev_incidents:
                trend = f"📉 Improving: {abs(current_incidents - prev_incidents)} fewer incidents"
                color = discord.Color.green()
            elif current_incidents > prev_incidents:
                trend = f"📈 Escalating: {abs(current_incidents - prev_incidents)} more incidents"
                color = discord.Color.orange()
            else:
                trend = "➡️ Stable: No change in incident volume"
                color = discord.Color.blue()
            
            embed.add_field(name="📈 Quarter-over-Quarter Trend", value=trend, inline=False)
            embed.color = color
        
        embed.set_footer(text=f"Generated by {ctx.author} | Report ID: {len(self.reports)}")
        
        await ctx.send(embed=embed)
    
    def generate_investment_recommendations(self, report: Dict) -> List[str]:
        """Generate investment recommendations based on report data"""
        recommendations = []
        
        incident_stats = report["incident_stats"]
        compliance_status = report["compliance_status"]
        threat_stats = report["threat_stats"]
        
        # High incident rate
        if incident_stats["total_incidents"] > 20:
            recommendations.append("Enhanced threat detection capabilities (SIEM upgrade)")
        
        # Critical incidents
        if incident_stats["critical_incidents"] > 5:
            recommendations.append("24/7 SOC staffing or managed security service")
        
        # Compliance gaps
        if compliance_status["overall_compliance"] < 75:
            recommendations.append("Compliance automation tools and consulting")
        
        # Active threats
        if threat_stats["critical_threats"] > 3:
            recommendations.append("Advanced threat intelligence platform")
        
        # Resolution efficiency
        if incident_stats["resolved_incidents"] < incident_stats["total_incidents"] * 0.8:
            recommendations.append("Incident response automation (SOAR platform)")
        
        if not recommendations:
            recommendations.append("Maintain current security investments")
        
        return recommendations
    
    @commands.command(name="quarterly_compliance")
    @commands.has_permissions(administrator=True)
    async def update_compliance(self, ctx, framework: str, status: str):
        """
        Update compliance framework status
        
        Usage: !quarterly_compliance <gdpr|hipaa|pci|soc2> <compliant|non_compliant>
        
        Example: !quarterly_compliance gdpr compliant
        """
        framework = framework.lower()
        is_compliant = status.lower() == "compliant"
        
        if framework not in ["gdpr", "hipaa", "pci", "soc2"]:
            await ctx.send("❌ Invalid framework. Use: gdpr, hipaa, pci, or soc2")
            return
        
        self.compliance[framework] = is_compliant
        self.compliance[f"{framework}_updated_at"] = get_now_pst().isoformat()
        self.compliance[f"{framework}_updated_by"] = str(ctx.author.id)
        self.save_compliance()
        
        embed = discord.Embed(
            title="✅ Compliance Status Updated",
            description=f"{framework.upper()} compliance status updated",
            color=discord.Color.green() if is_compliant else discord.Color.red(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Framework", value=framework.upper(), inline=True)
        embed.add_field(name="Status", value="✅ Compliant" if is_compliant else "❌ Non-Compliant", inline=True)
        embed.set_footer(text=f"Updated by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="quarterly_investment")
    @commands.has_permissions(administrator=True)
    async def add_investment(self, ctx, priority: str, amount: int, *, justification: str):
        """
        Add investment recommendation
        
        Usage: !quarterly_investment <critical|high|medium|low> <amount> <justification>
        
        Example: !quarterly_investment high 50000 SIEM platform upgrade for improved threat detection
        """
        investment = {
            "id": len(self.investments) + 1,
            "quarter": self.get_current_quarter(),
            "priority": priority.lower(),
            "amount": amount,
            "justification": justification,
            "added_at": get_now_pst().isoformat(),
            "added_by": str(ctx.author.id),
            "status": "proposed"
        }
        
        self.investments.append(investment)
        self.save_investments()
        
        color_map = {
            "critical": discord.Color.dark_red(),
            "high": discord.Color.red(),
            "medium": discord.Color.gold(),
            "low": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="✅ Investment Recommendation Added",
            description=f"New {priority.upper()} priority investment",
            color=color_map.get(priority.lower(), discord.Color.blue()),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Investment ID", value=f"#{investment['id']}", inline=True)
        embed.add_field(name="Priority", value=priority.upper(), inline=True)
        embed.add_field(name="Amount", value=f"${amount:,}", inline=True)
        embed.add_field(name="Justification", value=justification, inline=False)
        embed.add_field(name="Quarter", value=investment["quarter"], inline=True)
        
        embed.set_footer(text=f"Added by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="quarterly_compare")
    @commands.has_permissions(administrator=True)
    async def compare_quarters(self, ctx):
        """
        Compare last two quarters
        
        Usage: !quarterly_compare
        """
        if len(self.reports) < 2:
            await ctx.send("❌ Insufficient data. Need at least 2 quarterly reports.")
            return
        
        current = self.reports[-1]
        previous = self.reports[-2]
        
        embed = discord.Embed(
            title="📊 Quarter-over-Quarter Comparison",
            description=f"{previous['quarter']} vs {current['quarter']}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Incident comparison
        curr_incidents = current["incident_stats"]["total_incidents"]
        prev_incidents = previous["incident_stats"]["total_incidents"]
        incident_change = curr_incidents - prev_incidents
        incident_pct = (incident_change / prev_incidents * 100) if prev_incidents > 0 else 0
        
        embed.add_field(
            name="🔥 Incident Trend",
            value=f"Previous: {prev_incidents}\nCurrent: {curr_incidents}\nChange: {incident_change:+d} ({incident_pct:+.1f}%)",
            inline=True
        )
        
        # Critical incidents
        curr_critical = current["incident_stats"]["critical_incidents"]
        prev_critical = previous["incident_stats"]["critical_incidents"]
        critical_change = curr_critical - prev_critical
        
        embed.add_field(
            name="🚨 Critical Incidents",
            value=f"Previous: {prev_critical}\nCurrent: {curr_critical}\nChange: {critical_change:+d}",
            inline=True
        )
        
        # Compliance
        curr_compliance = current["compliance_status"]["overall_compliance"]
        prev_compliance = previous["compliance_status"]["overall_compliance"]
        compliance_change = curr_compliance - prev_compliance
        
        embed.add_field(
            name="📜 Compliance",
            value=f"Previous: {prev_compliance:.0f}%\nCurrent: {curr_compliance:.0f}%\nChange: {compliance_change:+.0f}%",
            inline=True
        )
        
        # Overall assessment
        if incident_change < 0 and compliance_change > 0:
            assessment = "🟢 Improving - Fewer incidents, better compliance"
            color = discord.Color.green()
        elif incident_change > 0 or compliance_change < 0:
            assessment = "🔴 Declining - Increased incidents or compliance gaps"
            color = discord.Color.red()
        else:
            assessment = "🟡 Stable - No significant changes"
            color = discord.Color.gold()
        
        embed.add_field(name="Overall Assessment", value=assessment, inline=False)
        embed.color = color
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="quarterly_dashboard")
    @commands.has_permissions(administrator=True)
    async def quarterly_dashboard(self, ctx):
        """
        Display quarterly reporting dashboard
        
        Usage: !quarterly_dashboard
        """
        current_quarter = self.get_current_quarter()
        
        # Get current quarter report if exists
        current_report = next((r for r in self.reports if r["quarter"] == current_quarter), None)
        
        embed = discord.Embed(
            title="📊 Quarterly Reporting Dashboard",
            description=f"Current Period: {current_quarter}",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        # Report statistics
        embed.add_field(name="📋 Total Reports", value=len(self.reports), inline=True)
        embed.add_field(name="💰 Investment Recommendations", value=len(self.investments), inline=True)
        
        # Compliance overview
        compliant_count = sum([
            self.compliance.get("gdpr", False),
            self.compliance.get("hipaa", False),
            self.compliance.get("pci", False),
            self.compliance.get("soc2", False)
        ])
        embed.add_field(name="✅ Compliant Frameworks", value=f"{compliant_count}/4", inline=True)
        
        # Current quarter status
        if current_report:
            incidents = current_report["incident_stats"]["total_incidents"]
            critical = current_report["incident_stats"]["critical_incidents"]
            
            embed.add_field(
                name=f"📈 {current_quarter} Incidents",
                value=f"Total: {incidents}\nCritical: {critical}",
                inline=True
            )
        else:
            embed.add_field(
                name=f"📈 {current_quarter} Status",
                value="No report generated yet",
                inline=True
            )
        
        # Investment summary
        proposed_investments = [i for i in self.investments if i.get("status") == "proposed"]
        if proposed_investments:
            total_proposed = sum(i["amount"] for i in proposed_investments)
            embed.add_field(
                name="💵 Proposed Investments",
                value=f"{len(proposed_investments)} items\nTotal: ${total_proposed:,}",
                inline=True
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(QuarterlySecurityPostureReportCog(bot))
