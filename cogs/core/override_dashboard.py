"""Override Tracking Dashboard - Human vs AI Decision Analytics"""
import discord
from discord.ext import commands
from cogs.core.human_override_tracker import tracker
from cogs.core.signal_bus import signal_bus, Signal, SignalType
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os
from cogs.core.pst_timezone import get_now_pst

class OverrideDashboard(commands.Cog):
    """Comprehensive dashboard for tracking human overrides of AI decisions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/override_dashboard.json"
        self.load_data()
    
    def load_data(self):
        """Load dashboard data from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = self._initialize_data()
        else:
            self.data = self._initialize_data()
    
    def _initialize_data(self):
        """Initialize empty dashboard data"""
        return {
            'total_overrides': 0,
            'systems_analyzed': [],
            'bias_scores_history': {},
            'trend_data': []
        }
    
    def save_data(self):
        """Save dashboard data to disk"""
        os.makedirs("data", exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def calculate_bias_analysis(self) -> Dict:
        """Calculate comprehensive bias analysis across all systems"""
        bias_report = {}
        
        if not tracker.overrides:
            return {'total_overrides': 0, 'systems': {}}
        
        # Analyze each system
        systems = set(o['system'] for o in tracker.overrides)
        for system in systems:
            system_overrides = [o for o in tracker.overrides if o['system'] == system]
            disagreements = sum(1 for o in system_overrides if o['disagreement'])
            
            bias_score = tracker.get_bias_score(system)
            stats = tracker.get_override_stats(system)
            
            bias_report[system] = {
                'total_overrides': len(system_overrides),
                'disagreements': disagreements,
                'agreement_rate': stats['agreement_rate'],
                'avg_confidence': stats['avg_confidence'],
                'bias_score': bias_score,
                'risk_level': self._get_risk_level(bias_score)
            }
        
        return {
            'total_overrides': len(tracker.overrides),
            'systems': bias_report,
            'timestamp': get_now_pst().isoformat()
        }
    
    def _get_risk_level(self, bias_score: float) -> str:
        """Determine risk level from bias score"""
        if bias_score > 0.4:
            return "CRITICAL"
        elif bias_score > 0.25:
            return "HIGH"
        elif bias_score > 0.10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_disagreement_patterns(self) -> List[Dict]:
        """Identify most common disagreement patterns"""
        if not tracker.disagreement_matrix:
            return []
        
        patterns = []
        for system, pattern_dict in tracker.disagreement_matrix.items():
            if pattern_dict:
                most_common = max(pattern_dict.items(), key=lambda x: x[1])
                patterns.append({
                    'system': system,
                    'pattern': most_common[0],
                    'frequency': most_common[1]
                })
        
        # Sort by frequency
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        return patterns[:5]  # Top 5 patterns
    
    def get_confidence_trends(self) -> Dict:
        """Analyze confidence score trends over time"""
        if not tracker.overrides:
            return {'trend': 'insufficient_data'}
        
        # Get recent overrides (last 10)
        recent = tracker.overrides[-10:]
        recent_confidence = [o.get('ai_confidence', 0) for o in recent]
        
        if not recent_confidence:
            return {'trend': 'no_data'}
        
        avg_confidence = sum(recent_confidence) / len(recent_confidence)
        trend = "improving" if avg_confidence > 0.7 else "declining" if avg_confidence < 0.5 else "stable"
        
        return {
            'avg_confidence': avg_confidence,
            'trend': trend,
            'samples': len(recent_confidence),
            'min': min(recent_confidence),
            'max': max(recent_confidence)
        }
    
    @commands.command(name='overridesdashboard')
    async def override_dashboard(self, ctx):
        """Display comprehensive human override dashboard (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        # Calculate all analytics
        bias_analysis = self.calculate_bias_analysis()
        disagreement_patterns = self.get_disagreement_patterns()
        confidence_trends = self.get_confidence_trends()
        
        # Main dashboard embed
        embed = discord.Embed(
            title="📊 Human Override Analytics Dashboard",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        # Summary statistics
        embed.add_field(
            name="📈 Overview Statistics",
            value=f"Total Overrides: {bias_analysis['total_overrides']}\n"
                  f"Systems Analyzed: {len(bias_analysis['systems'])}\n"
                  f"Data Points: {len(tracker.overrides)}",
            inline=False
        )
        
        # Risk assessment
        critical_systems = []
        high_systems = []
        for system, data in bias_analysis['systems'].items():
            if data['risk_level'] == 'CRITICAL':
                critical_systems.append(f"{system} ({data['bias_score']:.1%})")
            elif data['risk_level'] == 'HIGH':
                high_systems.append(f"{system} ({data['bias_score']:.1%})")
        
        risk_summary = ""
        if critical_systems:
            risk_summary += f"🔴 CRITICAL: {', '.join(critical_systems)}\n"
        if high_systems:
            risk_summary += f"🟠 HIGH: {', '.join(high_systems)}\n"
        if not risk_summary:
            risk_summary = "✅ No high-risk systems detected"
        
        embed.add_field(
            name="⚠️ Risk Assessment",
            value=risk_summary,
            inline=False
        )
        
        # System-by-system breakdown
        system_details = ""
        for system, data in sorted(bias_analysis['systems'].items())[:5]:
            system_details += (
                f"**{system}**\n"
                f"  Bias: {data['bias_score']:.1%} ({data['risk_level']}) | "
                f"Agreement: {data['agreement_rate']:.1%} | "
                f"Confidence: {data['avg_confidence']:.2f}\n"
            )
        
        if system_details:
            embed.add_field(
                name="🔍 Top Systems",
                value=system_details,
                inline=False
            )
        
        # Confidence trends
        if confidence_trends.get('trend') != 'insufficient_data':
            trend_emoji = "📈" if confidence_trends['trend'] == "improving" else "📉" if confidence_trends['trend'] == "declining" else "→"
            embed.add_field(
                name="📊 Confidence Trends",
                value=f"{trend_emoji} Trend: {confidence_trends['trend']}\n"
                      f"Avg Confidence: {confidence_trends['avg_confidence']:.2f}\n"
                      f"Range: {confidence_trends['min']:.2f} - {confidence_trends['max']:.2f}",
                inline=False
            )
        
        # Top disagreement patterns
        if disagreement_patterns:
            pattern_str = ""
            for i, pattern in enumerate(disagreement_patterns[:3], 1):
                pattern_str += f"{i}. {pattern['system']}: {pattern['frequency']} occurrences\n"
            embed.add_field(
                name="🔄 Top Disagreement Patterns",
                value=pattern_str,
                inline=False
            )
        
        embed.set_footer(text="Use /overridestats <system> for detailed system analysis")
        await ctx.send(embed=embed)
    
    @commands.command(name='biasanalysis')
    async def bias_analysis_cmd(self, ctx, system: str = None):
        """Detailed bias analysis for a specific system or all systems (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        bias_analysis = self.calculate_bias_analysis()
        
        if system:
            if system not in bias_analysis['systems']:
                await ctx.send(f"❌ System '{system}' not found", ephemeral=True)
                return
            
            data = bias_analysis['systems'][system]
            embed = discord.Embed(
                title=f"🔬 Bias Analysis - {system}",
                color=discord.Color.red() if data['risk_level'] == 'CRITICAL' else discord.Color.orange() if data['risk_level'] == 'HIGH' else discord.Color.blue(),
                timestamp=get_now_pst()
            )
            
            embed.add_field(name="Risk Level", value=f"🔴 {data['risk_level']}" if data['risk_level'] == 'CRITICAL' else f"🟠 {data['risk_level']}" if data['risk_level'] == 'HIGH' else f"🟡 {data['risk_level']}", inline=True)
            embed.add_field(name="Bias Score", value=f"{data['bias_score']:.1%}", inline=True)
            embed.add_field(name="Agreement Rate", value=f"{data['agreement_rate']:.1%}", inline=True)
            embed.add_field(name="Total Overrides", value=str(data['total_overrides']), inline=True)
            embed.add_field(name="Disagreements", value=str(data['disagreements']), inline=True)
            embed.add_field(name="Avg AI Confidence", value=f"{data['avg_confidence']:.2f}", inline=True)
            
            # Recommendations
            if data['bias_score'] > 0.25:
                recommendation = "⚠️ **REVIEW REQUIRED**: This system shows significant bias patterns. Consider manual override policies or retraining."
            else:
                recommendation = "✅ **ACCEPTABLE**: Bias levels are within acceptable ranges."
            
            embed.add_field(name="📋 Recommendation", value=recommendation, inline=False)
            
        else:
            # All systems summary
            embed = discord.Embed(
                title="🔬 Comprehensive Bias Analysis",
                description="Bias analysis across all AI systems",
                color=discord.Color.blurple(),
                timestamp=get_now_pst()
            )
            
            all_systems_str = ""
            for system, data in sorted(bias_analysis['systems'].items()):
                risk_emoji = "🔴" if data['risk_level'] == 'CRITICAL' else "🟠" if data['risk_level'] == 'HIGH' else "🟡" if data['risk_level'] == 'MEDIUM' else "🟢"
                all_systems_str += f"{risk_emoji} **{system}**: {data['bias_score']:.1%} bias ({data['total_overrides']} overrides)\n"
            
            if all_systems_str:
                embed.add_field(name="All Systems", value=all_systems_str, inline=False)
            else:
                embed.add_field(name="Status", value="No override data available yet", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='agreementtrends')
    async def agreement_trends_cmd(self, ctx):
        """View human-AI agreement trends over time (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        if not tracker.overrides:
            await ctx.send("❌ No override data available", ephemeral=True)
            return
        
        confidence_trends = self.get_confidence_trends()
        
        embed = discord.Embed(
            title="📉 Human-AI Agreement Trends",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        if confidence_trends.get('trend') != 'insufficient_data':
            embed.add_field(
                name="Confidence Trend",
                value=f"Overall Trend: **{confidence_trends['trend'].upper()}**",
                inline=False
            )
            embed.add_field(
                name="Current Statistics (Last 10)",
                value=f"Average Confidence: {confidence_trends['avg_confidence']:.2f}\n"
                      f"Min: {confidence_trends['min']:.2f}\n"
                      f"Max: {confidence_trends['max']:.2f}\n"
                      f"Samples: {confidence_trends['samples']}",
                inline=False
            )
            
            # Trend interpretation
            if confidence_trends['trend'] == 'improving':
                interpretation = "✅ AI system confidence is improving - fewer disagreements expected"
            elif confidence_trends['trend'] == 'declining':
                interpretation = "⚠️ AI system confidence is declining - monitor closely"
            else:
                interpretation = "→ AI system confidence is stable"
            
            embed.add_field(name="📊 Interpretation", value=interpretation, inline=False)
        else:
            embed.add_field(name="Status", value="Insufficient data for trend analysis", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='overridereport')
    async def override_report_cmd(self, ctx):
        """Generate comprehensive override activity report (owner only)"""
        if ctx.author.id != self.bot.owner_id:
            await ctx.send("❌ Owner only command", ephemeral=True)
            return
        
        if not tracker.overrides:
            await ctx.send("❌ No override data available", ephemeral=True)
            return
        
        # Calculate statistics
        total = len(tracker.overrides)
        disagreements = sum(1 for o in tracker.overrides if o['disagreement'])
        agreement_rate = (total - disagreements) / total if total > 0 else 0
        
        # Get most common disagreement reasons
        reasons = {}
        for override in tracker.overrides:
            if override['disagreement']:
                reason = f"{override['ai_decision']} → {override['human_decision']}"
                reasons[reason] = reasons.get(reason, 0) + 1
        
        top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        
        embed = discord.Embed(
            title="📋 Override Activity Report",
            color=discord.Color.blurple(),
            timestamp=get_now_pst()
        )
        
        embed.add_field(
            name="📊 Summary Statistics",
            value=f"Total Overrides: {total}\n"
                  f"Disagreements: {disagreements}\n"
                  f"Agreement Rate: {agreement_rate:.1%}",
            inline=True
        )
        
        # Timeline
        if tracker.overrides:
            first_override = tracker.overrides[0]['timestamp']
            last_override = tracker.overrides[-1]['timestamp']
            embed.add_field(
                name="📅 Timeline",
                value=f"First: {first_override[:10]}\n"
                      f"Last: {last_override[:10]}\n"
                      f"Total Records: {total}",
                inline=True
            )
        
        # Top reasons for disagreement
        if top_reasons:
            reasons_str = "\n".join([f"{i}. {reason}: {count} times" for i, (reason, count) in enumerate(top_reasons, 1)])
            embed.add_field(
                name="🔄 Top Disagreement Patterns",
                value=reasons_str,
                inline=False
            )
        
        # Recommendations
        if disagreement_rate := (disagreements / total):
            if disagreement_rate > 0.3:
                embed.add_field(
                    name="⚠️ Alert",
                    value="High disagreement rate detected. Review AI system behavior and retraining requirements.",
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OverrideDashboard(bot))
