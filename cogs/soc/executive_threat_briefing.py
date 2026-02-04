"""
Executive Threat Briefing
Executive-level threat briefings with non-technical language and trend analysis
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cogs.core.pst_timezone import get_now_pst

class ExecutiveThreatBriefingCog(commands.Cog):
    """
    Executive Threat Briefing Generator
    
    Creates non-technical threat briefings for executives with business
    context and strategic implications.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/executive_briefings"
        os.makedirs(self.data_dir, exist_ok=True)
        self.briefings_file = os.path.join(self.data_dir, "threat_briefings.json")
        self.threats_file = os.path.join(self.data_dir, "tracked_threats.json")
        self.briefings = self.load_briefings()
        self.threats = self.load_threats()
        
    def load_briefings(self) -> List[Dict]:
        """Load threat briefings from JSON storage"""
        if os.path.exists(self.briefings_file):
            with open(self.briefings_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_briefings(self):
        """Save threat briefings to JSON storage"""
        with open(self.briefings_file, 'w') as f:
            json.dump(self.briefings, f, indent=4)
    
    def load_threats(self) -> List[Dict]:
        """Load tracked threats from JSON storage"""
        if os.path.exists(self.threats_file):
            with open(self.threats_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_threats(self):
        """Save tracked threats to JSON storage"""
        with open(self.threats_file, 'w') as f:
            json.dump(self.threats, f, indent=4)
    
    def translate_to_business_language(self, technical_term: str) -> str:
        """Translate technical security terms to business language"""
        translations = {
            "DDoS": "service disruption attack",
            "phishing": "fraudulent impersonation attempt",
            "ransomware": "data encryption extortion",
            "malware": "malicious software",
            "botnet": "network of compromised computers",
            "zero-day": "previously unknown vulnerability",
            "exploit": "security weakness being actively used",
            "APT": "sophisticated targeted attack",
            "SQL injection": "database manipulation attack",
            "XSS": "website trust exploitation"
        }
        return translations.get(technical_term, technical_term)
    
    @commands.command(name="exec_briefing")
    @commands.has_permissions(administrator=True)
    async def generate_executive_briefing(self, ctx):
        """
        Generate executive threat briefing
        
        Usage: !exec_briefing
        """
        await ctx.send("⏳ Generating executive threat briefing...")
        
        # Collect threat intelligence
        threat_summary = {
            "active_threats": 0,
            "critical_threats": 0,
            "threat_categories": {},
            "business_impact": "Low",
            "trending_threats": []
        }
        
        # Analyze recent threats (last 30 days)
        now = get_now_pst()
        recent_threats = [
            t for t in self.threats
            if (now - datetime.fromisoformat(t["detected_at"])).days <= 30
        ]
        
        threat_summary["active_threats"] = len(recent_threats)
        
        # Categorize threats
        for threat in recent_threats:
            category = threat.get("category", "Unknown")
            severity = threat.get("severity", "medium")
            
            if category not in threat_summary["threat_categories"]:
                threat_summary["threat_categories"][category] = 0
            threat_summary["threat_categories"][category] += 1
            
            if severity == "critical":
                threat_summary["critical_threats"] += 1
        
        # Determine business impact
        if threat_summary["critical_threats"] > 5:
            threat_summary["business_impact"] = "High - Immediate attention required"
        elif threat_summary["critical_threats"] > 2:
            threat_summary["business_impact"] = "Medium - Proactive monitoring needed"
        else:
            threat_summary["business_impact"] = "Low - Routine security operations"
        
        # Generate briefing
        briefing = {
            "timestamp": get_now_pst().isoformat(),
            "period": "Last 30 Days",
            "threat_summary": threat_summary,
            "generated_by": str(ctx.author.id)
        }
        
        self.briefings.append(briefing)
        self.save_briefings()
        
        # Create executive-friendly embed
        embed = discord.Embed(
            title="🎯 Executive Threat Briefing",
            description=f"Security Landscape Overview - {briefing['period']}",
            color=discord.Color.dark_blue(),
            timestamp=get_now_pst()
        )
        
        # Executive Summary
        embed.add_field(
            name="📋 Executive Summary",
            value=f"**{threat_summary['active_threats']}** security events detected in the past 30 days, with **{threat_summary['critical_threats']}** requiring immediate attention.",
            inline=False
        )
        
        # Business Impact
        embed.add_field(
            name="💼 Business Impact Assessment",
            value=threat_summary["business_impact"],
            inline=False
        )
        
        # Threat Landscape
        if threat_summary["threat_categories"]:
            landscape_text = "\n".join([
                f"• **{cat}**: {count} incidents"
                for cat, count in sorted(threat_summary["threat_categories"].items(), key=lambda x: x[1], reverse=True)[:5]
            ])
            embed.add_field(
                name="🌐 Current Threat Landscape",
                value=landscape_text or "No significant threats detected",
                inline=False
            )
        
        # What Keeps Us Up At Night
        concerns = []
        if threat_summary["critical_threats"] > 0:
            concerns.append(f"• {threat_summary['critical_threats']} critical security events requiring executive awareness")
        
        # Check for ransomware threats
        ransomware_threats = [t for t in recent_threats if "ransomware" in t.get("category", "").lower()]
        if ransomware_threats:
            concerns.append(f"• {len(ransomware_threats)} potential ransomware indicators detected")
        
        # Check for data exfiltration
        exfil_threats = [t for t in recent_threats if "exfil" in t.get("category", "").lower() or "data" in t.get("category", "").lower()]
        if exfil_threats:
            concerns.append(f"• {len(exfil_threats)} possible data access anomalies")
        
        if concerns:
            embed.add_field(
                name="🌙 What Keeps Us Up At Night",
                value="\n".join(concerns[:5]),
                inline=False
            )
        else:
            embed.add_field(
                name="🌙 What Keeps Us Up At Night",
                value="Security posture is stable with no critical concerns at this time.",
                inline=False
            )
        
        # Strategic Recommendations
        recommendations = []
        if threat_summary["critical_threats"] > 5:
            recommendations.append("• Consider additional security resources or third-party assessment")
        if threat_summary["active_threats"] > 50:
            recommendations.append("• Evaluate current security controls effectiveness")
        
        if not recommendations:
            recommendations.append("• Continue current security operations")
            recommendations.append("• Maintain regular security awareness training")
        
        embed.add_field(
            name="💡 Strategic Recommendations",
            value="\n".join(recommendations),
            inline=False
        )
        
        embed.set_footer(text=f"Generated by {ctx.author} | Confidential - Executive Use Only")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="exec_add_threat")
    @commands.has_permissions(administrator=True)
    async def add_threat(self, ctx, severity: str, category: str, *, description: str):
        """
        Add a threat to executive tracking
        
        Usage: !exec_add_threat <critical|high|medium|low> <category> <description>
        
        Example: !exec_add_threat critical phishing Targeted attack on finance team
        """
        threat = {
            "id": len(self.threats) + 1,
            "severity": severity.lower(),
            "category": category,
            "description": description,
            "detected_at": get_now_pst().isoformat(),
            "added_by": str(ctx.author.id),
            "status": "active"
        }
        
        self.threats.append(threat)
        self.save_threats()
        
        # Update bot status for critical/high threats
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status and severity.lower() in ['critical', 'high']:
            await dynamic_status.activate_threat_status(
                f"{category} threat",
                severity.upper()
            )
        
        # Translate to business language
        business_category = self.translate_to_business_language(category)
        
        color_map = {
            "critical": discord.Color.dark_red(),
            "high": discord.Color.red(),
            "medium": discord.Color.gold(),
            "low": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="✅ Threat Added to Executive Tracking",
            description=f"New {severity.upper()} threat logged",
            color=color_map.get(severity.lower(), discord.Color.blue()),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Threat ID", value=f"#{threat['id']}", inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        embed.add_field(name="Category", value=business_category, inline=True)
        embed.add_field(name="Description", value=description, inline=False)
        embed.set_footer(text=f"Added by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="exec_resolve_threat")
    @commands.has_permissions(administrator=True)
    async def resolve_threat(self, ctx, threat_id: int):
        """
        Resolve an active threat
        
        Usage: !exec_resolve_threat <threat_id>
        
        Example: !exec_resolve_threat 5
        """
        # Find threat
        threat = None
        for t in self.threats:
            if t['id'] == threat_id:
                threat = t
                break
        
        if not threat:
            await ctx.send(f"❌ Threat #{threat_id} not found")
            return
        
        if threat['status'] != 'active':
            await ctx.send(f"⚠️ Threat #{threat_id} is already resolved")
            return
        
        # Mark as resolved
        threat['status'] = 'resolved'
        threat['resolved_at'] = get_now_pst().isoformat()
        threat['resolved_by'] = str(ctx.author.id)
        self.save_threats()
        
        # Check if we should deactivate threat status
        # Only deactivate if no other critical/high threats are active
        active_critical = [
            t for t in self.threats 
            if t['status'] == 'active' and t['severity'] in ['critical', 'high']
        ]
        
        dynamic_status = self.bot.get_cog('DynamicStatus')
        if dynamic_status and not active_critical:
            await dynamic_status.deactivate_threat_status()
        
        embed = discord.Embed(
            title="✅ Threat Resolved",
            description=f"Threat #{threat_id} marked as resolved",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Category", value=threat['category'], inline=True)
        embed.add_field(name="Severity", value=threat['severity'].upper(), inline=True)
        embed.add_field(name="Description", value=threat['description'], inline=False)
        embed.set_footer(text=f"Resolved by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="exec_threat_trends")
    @commands.has_permissions(administrator=True)
    async def threat_trends(self, ctx, days: int = 30):
        """
        Display threat trends for executives
        
        Usage: !exec_threat_trends [days]
        
        Example: !exec_threat_trends 90
        """
        now = get_now_pst()
        period_threats = [
            t for t in self.threats
            if (now - datetime.fromisoformat(t["detected_at"])).days <= days
        ]
        
        embed = discord.Embed(
            title="📈 Threat Trend Analysis",
            description=f"Security trends over the past {days} days",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        if not period_threats:
            embed.add_field(
                name="No Threats",
                value=f"No threats recorded in the past {days} days",
                inline=False
            )
        else:
            # Trend by severity
            severity_counts = {}
            for threat in period_threats:
                sev = threat.get("severity", "unknown")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            severity_text = "\n".join([
                f"• **{sev.capitalize()}**: {count}"
                for sev, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True)
            ])
            
            embed.add_field(name="Threat Severity Distribution", value=severity_text, inline=False)
            
            # Trend by category
            category_counts = {}
            for threat in period_threats:
                cat = threat.get("category", "Unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            category_text = "\n".join([
                f"• **{self.translate_to_business_language(cat)}**: {count}"
                for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ])
            
            embed.add_field(name="Most Common Threat Types", value=category_text, inline=False)
            
            # Weekly breakdown
            weeks_ago = [7, 14, 21, 28]
            weekly_counts = []
            for week in weeks_ago:
                week_threats = [
                    t for t in period_threats
                    if (now - datetime.fromisoformat(t["detected_at"])).days <= week
                ]
                weekly_counts.append(len(week_threats))
            
            if len(weekly_counts) >= 2:
                if weekly_counts[0] < weekly_counts[1]:
                    trend = "📉 Improving - Threat volume decreasing"
                    color = discord.Color.green()
                elif weekly_counts[0] > weekly_counts[1]:
                    trend = "📈 Escalating - Threat volume increasing"
                    color = discord.Color.red()
                else:
                    trend = "➡️ Stable - No significant change"
                    color = discord.Color.gold()
                
                embed.add_field(name="Trend Direction", value=trend, inline=False)
                embed.color = color
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name="exec_resolve_threat")
    @commands.has_permissions(administrator=True)
    async def resolve_threat(self, ctx, threat_id: int, *, resolution: str):
        """
        Mark a threat as resolved
        
        Usage: !exec_resolve_threat <threat_id> <resolution>
        
        Example: !exec_resolve_threat 5 Attack mitigated, systems secured
        """
        threat = next((t for t in self.threats if t["id"] == threat_id), None)
        
        if not threat:
            await ctx.send(f"❌ Threat #{threat_id} not found")
            return
        
        threat["status"] = "resolved"
        threat["resolved_at"] = get_now_pst().isoformat()
        threat["resolution"] = resolution
        threat["resolved_by"] = str(ctx.author.id)
        
        self.save_threats()
        
        embed = discord.Embed(
            title="✅ Threat Resolved",
            description=f"Threat #{threat_id} has been marked as resolved",
            color=discord.Color.green(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Threat ID", value=f"#{threat_id}", inline=True)
        embed.add_field(name="Category", value=threat["category"], inline=True)
        embed.add_field(name="Resolution", value=resolution, inline=False)
        embed.set_footer(text=f"Resolved by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="exec_threat_dashboard")
    @commands.has_permissions(administrator=True)
    async def executive_dashboard(self, ctx):
        """
        Display executive threat dashboard
        
        Usage: !exec_threat_dashboard
        """
        # Calculate statistics
        active_threats = [t for t in self.threats if t.get("status") == "active"]
        critical_active = [t for t in active_threats if t.get("severity") == "critical"]
        
        # Recent threats (7 days)
        now = get_now_pst()
        recent = [
            t for t in active_threats
            if (now - datetime.fromisoformat(t["detected_at"])).days <= 7
        ]
        
        embed = discord.Embed(
            title="🎯 Executive Threat Dashboard",
            description="Real-time security posture overview",
            color=discord.Color.dark_blue(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="🚨 Active Threats", value=len(active_threats), inline=True)
        embed.add_field(name="🔴 Critical", value=len(critical_active), inline=True)
        embed.add_field(name="📅 New (7 days)", value=len(recent), inline=True)
        embed.add_field(name="📊 Total Tracked", value=len(self.threats), inline=True)
        embed.add_field(name="✅ Resolved", value=len([t for t in self.threats if t.get("status") == "resolved"]), inline=True)
        
        # Threat level indicator
        if len(critical_active) > 5:
            threat_level = "🔴 ELEVATED - Immediate action required"
            color = discord.Color.red()
        elif len(critical_active) > 2:
            threat_level = "🟡 MODERATE - Enhanced monitoring"
            color = discord.Color.gold()
        else:
            threat_level = "🟢 NORMAL - Routine operations"
            color = discord.Color.green()
        
        embed.add_field(name="Current Threat Level", value=threat_level, inline=False)
        embed.color = color
        
        # Top threats requiring attention
        if critical_active:
            top_threats = "\n".join([
                f"• #{t['id']} - {self.translate_to_business_language(t['category'])}"
                for t in critical_active[:3]
            ])
            embed.add_field(name="⚠️ Requires Attention", value=top_threats, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function to add this cog to the bot"""
    await bot.add_cog(ExecutiveThreatBriefingCog(bot))
