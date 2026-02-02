"""
Board Risk Summary
Board-level risk summaries with business impact translation, SLA metrics, quarterly trends
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class BoardRiskSummaryCog(commands.Cog):
    """
    Board Risk Summary Generator
    
    Creates executive-level risk summaries for board meetings with business
    impact analysis and strategic recommendations.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/board_reports"
        os.makedirs(self.data_dir, exist_ok=True)
        self.summaries_file = os.path.join(self.data_dir, "risk_summaries.json")
        self.metrics_file = os.path.join(self.data_dir, "sla_metrics.json")
        self.trends_file = os.path.join(self.data_dir, "quarterly_trends.json")
        self.summaries = self.load_summaries()
        self.metrics = self.load_metrics()
        self.trends = self.load_trends()
        
    def load_summaries(self) -> List[Dict]:
        """Load risk summaries from JSON storage"""
        if os.path.exists(self.summaries_file):
            with open(self.summaries_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_summaries(self):
        """Save risk summaries to JSON storage"""
        with open(self.summaries_file, 'w') as f:
            json.dump(self.summaries, f, indent=4)
    
    def load_metrics(self) -> Dict:
        """Load SLA metrics from JSON storage"""
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            "mttr": [],  # Mean Time To Respond
            "mttd": [],  # Mean Time To Detect
            "mttr_target": 240,  # 4 hours in minutes
            "mttd_target": 60    # 1 hour in minutes
        }
    
    def save_metrics(self):
        """Save SLA metrics to JSON storage"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=4)
    
    def load_trends(self) -> Dict:
        """Load quarterly trends from JSON storage"""
        if os.path.exists(self.trends_file):
            with open(self.trends_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_trends(self):
        """Save quarterly trends to JSON storage"""
        with open(self.trends_file, 'w') as f:
            json.dump(self.trends, f, indent=4)
    
    @commands.command(name="board_risk_summary")
    @commands.has_permissions(administrator=True)
    async def generate_risk_summary(self, ctx):
        """
        Generate board-level risk summary
        
        Usage: !board_risk_summary
        """
        await ctx.send("⏳ Generating board risk summary...")
        
        # Collect risk data from various systems
        risk_data = {
            "critical_risks": 0,
            "high_risks": 0,
            "medium_risks": 0,
            "financial_impact": 0,
            "active_incidents": 0,
            "sla_compliance": 0
        }
        
        # Check trust scoring system
        trust_cog = self.bot.get_cog('DynamicTrustScoringCog')
        if trust_cog and hasattr(trust_cog, 'scores'):
            for user_id, user_data in trust_cog.scores.items():
                for guild_id, score_data in user_data.items():
                    score = score_data.get("score", 50)
                    if score < 30:
                        risk_data["critical_risks"] += 1
                    elif score < 50:
                        risk_data["high_risks"] += 1
                    elif score < 70:
                        risk_data["medium_risks"] += 1
        
        # Check incident data
        incident_cog = self.bot.get_cog('IncidentManagerCog')
        if incident_cog and hasattr(incident_cog, 'incidents'):
            active_incidents = [
                i for i in incident_cog.incidents
                if i.get("status") == "active"
            ]
            risk_data["active_incidents"] = len(active_incidents)
        
        # Calculate SLA compliance
        if self.metrics["mttr"] and self.metrics["mttd"]:
            avg_mttr = sum(self.metrics["mttr"]) / len(self.metrics["mttr"])
            avg_mttd = sum(self.metrics["mttd"]) / len(self.metrics["mttd"])
            
            mttr_compliance = (avg_mttr <= self.metrics["mttr_target"])
            mttd_compliance = (avg_mttd <= self.metrics["mttd_target"])
            
            risk_data["sla_compliance"] = (mttr_compliance + mttd_compliance) / 2 * 100
        else:
            risk_data["sla_compliance"] = 100
        
        # Estimate financial impact (placeholder formula)
        risk_data["financial_impact"] = (
            risk_data["critical_risks"] * 100000 +
            risk_data["high_risks"] * 25000 +
            risk_data["medium_risks"] * 5000
        )
        
        # Generate summary
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "quarter": f"Q{(datetime.utcnow().month - 1) // 3 + 1} {datetime.utcnow().year}",
            "risk_data": risk_data,
            "generated_by": str(ctx.author.id)
        }
        
        self.summaries.append(summary)
        self.save_summaries()
        
        # Create rich embed for board presentation
        embed = discord.Embed(
            title="📊 Board Risk Summary",
            description=f"Executive Risk Assessment - {summary['quarter']}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Risk Overview
        embed.add_field(
            name="🚨 Critical Risks",
            value=f"**{risk_data['critical_risks']}** items requiring immediate attention",
            inline=False
        )
        embed.add_field(
            name="⚠️ High Priority Risks",
            value=f"**{risk_data['high_risks']}** items requiring mitigation",
            inline=True
        )
        embed.add_field(
            name="🟡 Medium Priority Risks",
            value=f"**{risk_data['medium_risks']}** items under monitoring",
            inline=True
        )
        
        # Business Impact
        embed.add_field(
            name="💰 Estimated Financial Impact",
            value=f"**${risk_data['financial_impact']:,}** potential exposure",
            inline=False
        )
        
        # Operational Metrics
        embed.add_field(
            name="🔥 Active Incidents",
            value=risk_data['active_incidents'],
            inline=True
        )
        embed.add_field(
            name="📈 SLA Compliance",
            value=f"{risk_data['sla_compliance']:.1f}%",
            inline=True
        )
        
        # Recommendations
        recommendations = []
        if risk_data["critical_risks"] > 5:
            recommendations.append("• Immediate executive review required for critical risks")
        if risk_data["sla_compliance"] < 90:
            recommendations.append("• Consider additional SOC resources to meet SLA targets")
        if risk_data["financial_impact"] > 500000:
            recommendations.append("• Recommend increased cybersecurity insurance coverage")
        
        if recommendations:
            embed.add_field(
                name="💡 Strategic Recommendations",
                value="\n".join(recommendations),
                inline=False
            )
        
        embed.set_footer(text=f"Generated by {ctx.author} | Confidential - Board Use Only")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="board_sla_metrics")
    @commands.has_permissions(administrator=True)
    async def sla_metrics_report(self, ctx):
        """
        Generate SLA metrics report for board
        
        Usage: !board_sla_metrics
        """
        if not self.metrics["mttr"] or not self.metrics["mttd"]:
            embed = discord.Embed(
                title="📊 SLA Metrics Report",
                description="Insufficient data for SLA analysis",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate metrics
        avg_mttr = sum(self.metrics["mttr"]) / len(self.metrics["mttr"])
        avg_mttd = sum(self.metrics["mttd"]) / len(self.metrics["mttd"])
        
        mttr_compliance = (avg_mttr <= self.metrics["mttr_target"])
        mttd_compliance = (avg_mttd <= self.metrics["mttd_target"])
        
        embed = discord.Embed(
            title="📊 SLA Performance Metrics",
            description="Incident Response Service Level Agreements",
            color=discord.Color.green() if mttr_compliance and mttd_compliance else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⏱️ Mean Time To Detect (MTTD)",
            value=f"**{avg_mttd:.1f} min** (Target: {self.metrics['mttd_target']} min)\n{'✅ Meeting SLA' if mttd_compliance else '❌ Below SLA'}",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Mean Time To Respond (MTTR)",
            value=f"**{avg_mttr:.1f} min** (Target: {self.metrics['mttr_target']} min)\n{'✅ Meeting SLA' if mttr_compliance else '❌ Below SLA'}",
            inline=True
        )
        
        overall_compliance = ((mttr_compliance + mttd_compliance) / 2) * 100
        embed.add_field(
            name="📈 Overall SLA Compliance",
            value=f"**{overall_compliance:.0f}%**",
            inline=False
        )
        
        embed.add_field(
            name="📊 Data Points",
            value=f"MTTR: {len(self.metrics['mttr'])} incidents\nMTTD: {len(self.metrics['mttd'])} detections",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="board_trends")
    @commands.has_permissions(administrator=True)
    async def quarterly_trends(self, ctx):
        """
        Display quarterly security trends for board
        
        Usage: !board_trends
        """
        current_quarter = f"Q{(datetime.utcnow().month - 1) // 3 + 1} {datetime.utcnow().year}"
        
        # Calculate trends from historical data
        if not self.summaries:
            embed = discord.Embed(
                title="📈 Quarterly Trends",
                description="Insufficient historical data",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Get last 4 quarters
        recent_summaries = sorted(self.summaries, key=lambda x: x["timestamp"], reverse=True)[:4]
        
        embed = discord.Embed(
            title="📈 Quarterly Security Trends",
            description=f"Risk trend analysis through {current_quarter}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if recent_summaries:
            # Show trend for each quarter
            for summary in recent_summaries:
                quarter = summary["quarter"]
                risk_data = summary["risk_data"]
                
                trend_text = (
                    f"Critical: {risk_data['critical_risks']} | "
                    f"High: {risk_data['high_risks']} | "
                    f"Incidents: {risk_data['active_incidents']}\n"
                    f"Financial Impact: ${risk_data['financial_impact']:,}"
                )
                
                embed.add_field(
                    name=f"📅 {quarter}",
                    value=trend_text,
                    inline=False
                )
        
        # Calculate trend direction
        if len(recent_summaries) >= 2:
            current = recent_summaries[0]["risk_data"]["critical_risks"]
            previous = recent_summaries[1]["risk_data"]["critical_risks"]
            
            if current < previous:
                trend = "📉 Improving (Lower Critical Risks)"
                color = discord.Color.green()
            elif current > previous:
                trend = "📈 Deteriorating (Higher Critical Risks)"
                color = discord.Color.red()
            else:
                trend = "➡️ Stable (No Change)"
                color = discord.Color.gold()
            
            embed.add_field(name="Trend Analysis", value=trend, inline=False)
            embed.color = color
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="board_record_metric")
    @commands.has_permissions(administrator=True)
    async def record_sla_metric(self, ctx, metric_type: str, value: float):
        """
        Record SLA metric (MTTR or MTTD)
        
        Usage: !board_record_metric <mttr|mttd> <value_in_minutes>
        
        Example: !board_record_metric mttr 180
        """
        if metric_type.lower() not in ["mttr", "mttd"]:
            await ctx.send("❌ Invalid metric type. Use 'mttr' or 'mttd'")
            return
        
        self.metrics[metric_type.lower()].append(value)
        self.save_metrics()
        
        embed = discord.Embed(
            title="✅ SLA Metric Recorded",
            description=f"Recorded {metric_type.upper()} metric",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Metric Type", value=metric_type.upper(), inline=True)
        embed.add_field(name="Value", value=f"{value} minutes", inline=True)
        embed.add_field(name="Total Data Points", value=len(self.metrics[metric_type.lower()]), inline=True)
        
        embed.set_footer(text=f"Recorded by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="board_export")
    @commands.has_permissions(administrator=True)
    async def export_board_report(self, ctx):
        """
        Export comprehensive board report
        
        Usage: !board_export
        """
        await ctx.send("⏳ Generating comprehensive board report...")
        
        # Generate complete report
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "quarter": f"Q{(datetime.utcnow().month - 1) // 3 + 1} {datetime.utcnow().year}",
            "risk_summaries": self.summaries[-4:] if len(self.summaries) >= 4 else self.summaries,
            "sla_metrics": {
                "mttr_avg": sum(self.metrics["mttr"]) / len(self.metrics["mttr"]) if self.metrics["mttr"] else 0,
                "mttd_avg": sum(self.metrics["mttd"]) / len(self.metrics["mttd"]) if self.metrics["mttd"] else 0,
                "mttr_target": self.metrics["mttr_target"],
                "mttd_target": self.metrics["mttd_target"]
            },
            "quarterly_trends": self.trends
        }
        
        # Save to file
        report_file = os.path.join(self.data_dir, f"board_report_{datetime.utcnow().strftime('%Y%m%d')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
        
        embed = discord.Embed(
            title="✅ Board Report Exported",
            description="Comprehensive report generated",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Report File", value=os.path.basename(report_file), inline=False)
        embed.add_field(name="Report Period", value=report["quarter"], inline=True)
        embed.add_field(name="Risk Summaries", value=len(report["risk_summaries"]), inline=True)
        
        embed.set_footer(text=f"Generated by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(BoardRiskSummaryCog(bot))
