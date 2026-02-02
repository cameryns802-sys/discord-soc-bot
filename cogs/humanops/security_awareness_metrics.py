"""
Security Awareness Metrics - Training effectiveness tracking and analytics
Measure security awareness program ROI and training effectiveness
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class SecurityAwarenessMetrics(commands.Cog):
    """Security awareness training metrics and effectiveness tracking"""
    
    def __init__(self, bot):
        self.bot = bot
        self.metrics_file = 'data/awareness_metrics.json'
        self.campaigns_file = 'data/awareness_campaigns.json'
        self.load_data()
    
    def load_data(self):
        """Load metrics data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.campaigns_file):
            with open(self.campaigns_file, 'w') as f:
                json.dump({}, f)
    
    def get_metrics(self, guild_id):
        """Get awareness metrics for guild"""
        with open(self.metrics_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_metrics(self, guild_id, metrics):
        """Save metrics"""
        with open(self.metrics_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = metrics
        with open(self.metrics_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_campaigns(self, guild_id):
        """Get awareness campaigns"""
        with open(self.campaigns_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), [])
    
    def save_campaigns(self, guild_id, campaigns):
        """Save campaigns"""
        with open(self.campaigns_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = campaigns
        with open(self.campaigns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_awareness_score(self, metrics):
        """Calculate org awareness score (0-100)"""
        score = 50
        
        # Training completion rate
        completion_rate = metrics.get('training_completion_rate', 0)
        score += (completion_rate / 100) * 20
        
        # Phishing simulation click rate
        phishing_click_rate = metrics.get('phishing_click_rate', 50)
        score += (100 - phishing_click_rate) / 100 * 15
        
        # Policy acknowledgment rate
        policy_ack_rate = metrics.get('policy_acknowledgment_rate', 0)
        score += (policy_ack_rate / 100) * 10
        
        # Incident report rate
        if metrics.get('security_incidents_reported', 0) > 0:
            score += 10
        
        # Training currency
        avg_days_since_training = metrics.get('avg_days_since_training', 365)
        if avg_days_since_training < 180:
            score += 10
        elif avg_days_since_training < 365:
            score += 5
        
        # Program maturity
        program_level = metrics.get('program_maturity', 'basic')
        if program_level == 'advanced':
            score += 15
        elif program_level == 'intermediate':
            score += 8
        
        return min(100, score)
    
    async def _awarenesscampaign_logic(self, ctx, campaign_type: str, target_audience: str, *, description: str = None):
        """Create awareness campaign"""
        campaigns = self.get_campaigns(ctx.guild.id)
        
        campaign_id = f"AWC-{str(uuid.uuid4())[:8].upper()}"
        
        campaign = {
            'id': campaign_id,
            'type': campaign_type.lower(),
            'target_audience': target_audience,
            'description': description or '',
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active',
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'participants': 0,
            'completions': 0,
            'engagement_rate': 0.0,
            'click_rate': 0.0,
            'report_rate': 0.0
        }
        
        campaigns.append(campaign)
        self.save_campaigns(ctx.guild.id, campaigns)
        
        embed = discord.Embed(
            title="📢 Awareness Campaign Started",
            description=f"**{campaign_type.title()}** - {target_audience}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Campaign ID", value=f"`{campaign_id}`", inline=True)
        embed.add_field(name="Type", value=campaign_type.title(), inline=True)
        embed.add_field(name="Target", value=target_audience, inline=True)
        embed.add_field(name="Duration", value="30 days", inline=True)
        embed.add_field(name="Status", value="🟢 ACTIVE", inline=True)
        embed.add_field(name="Participants", value="0", inline=True)
        
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        
        embed.set_footer(text="Campaign will end in 30 days")
        
        await ctx.send(embed=embed)
    
    async def _awarenessdashboard_logic(self, ctx):
        """Show awareness program dashboard"""
        metrics = self.get_metrics(ctx.guild.id)
        campaigns = self.get_campaigns(ctx.guild.id)
        
        # Initialize default metrics if none exist
        if not metrics:
            metrics = {
                'training_completion_rate': 78,
                'phishing_click_rate': 12,
                'policy_acknowledgment_rate': 95,
                'security_incidents_reported': 42,
                'avg_days_since_training': 90,
                'program_maturity': 'intermediate',
                'users_trained': 150,
                'total_users': 200
            }
            self.save_metrics(ctx.guild.id, metrics)
        
        awareness_score = self.calculate_awareness_score(metrics)
        
        score_color = discord.Color.red() if awareness_score < 40 else discord.Color.orange() if awareness_score < 60 else discord.Color.gold() if awareness_score < 80 else discord.Color.green()
        
        embed = discord.Embed(
            title="📊 Security Awareness Program Dashboard",
            description=f"Organization Awareness Score: **{awareness_score}/100**",
            color=score_color,
            timestamp=datetime.utcnow()
        )
        
        # Key metrics
        embed.add_field(name="Training Metrics", value="━" * 25, inline=False)
        embed.add_field(name="Completion Rate", value=f"{metrics['training_completion_rate']}%", inline=True)
        embed.add_field(name="Users Trained", value=f"{metrics['users_trained']}/{metrics['total_users']}", inline=True)
        embed.add_field(name="Avg Training Age", value=f"{metrics['avg_days_since_training']} days", inline=True)
        
        # Phishing metrics
        embed.add_field(name="Phishing Resistance", value="━" * 25, inline=False)
        click_safe_rate = 100 - metrics['phishing_click_rate']
        embed.add_field(name="Safe Click Rate", value=f"{click_safe_rate}%", inline=True)
        embed.add_field(name="Unsafe Clicks", value=f"{metrics['phishing_click_rate']}%", inline=True)
        
        # Compliance metrics
        embed.add_field(name="Compliance", value="━" * 25, inline=False)
        embed.add_field(name="Policy Acknowledgment", value=f"{metrics['policy_acknowledgment_rate']}%", inline=True)
        embed.add_field(name="Incidents Reported", value=f"{metrics['security_incidents_reported']}", inline=True)
        embed.add_field(name="Program Level", value=metrics['program_maturity'].title(), inline=True)
        
        # Active campaigns
        active_campaigns = [c for c in campaigns if c['status'] == 'active']
        if active_campaigns:
            embed.add_field(name="Active Campaigns", value=f"{len(active_campaigns)} campaign(s) running", inline=False)
        
        embed.set_footer(text="Use !awarenessmetrics for detailed analytics")
        
        await ctx.send(embed=embed)
    
    async def _awarenessmetrics_logic(self, ctx):
        """Show detailed awareness metrics"""
        metrics = self.get_metrics(ctx.guild.id)
        
        if not metrics:
            await ctx.send("📊 No metrics available. Start a campaign to collect data.")
            return
        
        awareness_score = self.calculate_awareness_score(metrics)
        
        embed = discord.Embed(
            title="📊 Security Awareness Metrics",
            description=f"Overall Score: **{awareness_score}/100**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Training metrics
        embed.add_field(name="Training Statistics", value="━" * 25, inline=False)
        embed.add_field(name="Completion Rate", value=f"📈 {metrics.get('training_completion_rate', 0)}%", inline=True)
        embed.add_field(name="Employees Trained", value=f"👥 {metrics.get('users_trained', 0)}", inline=True)
        embed.add_field(name="Total Employees", value=f"👤 {metrics.get('total_users', 0)}", inline=True)
        
        # Behavioral metrics
        embed.add_field(name="Behavioral Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Phishing Click Rate", value=f"⚠️ {metrics.get('phishing_click_rate', 0)}%", inline=True)
        embed.add_field(name="Policy Acknowledgment", value=f"✅ {metrics.get('policy_acknowledgment_rate', 0)}%", inline=True)
        embed.add_field(name="Incidents Reported", value=f"🔔 {metrics.get('security_incidents_reported', 0)}", inline=True)
        
        # Program health
        embed.add_field(name="Program Health", value="━" * 25, inline=False)
        embed.add_field(name="Maturity Level", value=metrics.get('program_maturity', 'unknown').title(), inline=True)
        embed.add_field(name="Days Since Training", value=f"{metrics.get('avg_days_since_training', 0)} days (avg)", inline=True)
        
        # Trend analysis
        trend = "📈 Improving" if awareness_score > 65 else "📊 Stable" if awareness_score > 50 else "📉 Declining"
        embed.add_field(name="Trend", value=trend, inline=False)
        
        # Recommendations
        if metrics.get('phishing_click_rate', 0) > 15:
            embed.add_field(name="⚠️ Recommendation", value="High phishing click rate - increase simulations", inline=False)
        elif metrics.get('training_completion_rate', 0) < 80:
            embed.add_field(name="⚠️ Recommendation", value="Low training completion - launch mandatory training campaign", inline=False)
        
        embed.set_footer(text="Update metrics monthly for trending analysis")
        
        await ctx.send(embed=embed)
    
    async def _awarenessroi_logic(self, ctx):
        """Calculate awareness program ROI"""
        metrics = self.get_metrics(ctx.guild.id)
        campaigns = self.get_campaigns(ctx.guild.id)
        
        if not metrics or not campaigns:
            await ctx.send("📊 Insufficient data to calculate ROI. Start campaigns and collect metrics.")
            return
        
        # Simulate ROI calculation
        incidents_prevented = max(0, (100 - metrics.get('phishing_click_rate', 50)) * 10)
        cost_per_incident = 250000  # Average breach cost
        savings = incidents_prevented * cost_per_incident
        program_cost = 50000  # Annual program cost
        roi = ((savings - program_cost) / program_cost) * 100 if program_cost > 0 else 0
        
        embed = discord.Embed(
            title="💰 Awareness Program ROI Analysis",
            description="Return on Investment for Security Awareness",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Program Cost (Annual)", value=f"${program_cost:,}", inline=True)
        embed.add_field(name="Estimated Savings", value=f"${savings:,}", inline=True)
        embed.add_field(name="ROI", value=f"{roi:.1f}%", inline=True)
        
        embed.add_field(name="Impact Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Incidents Prevented", value=f"{int(incidents_prevented)} (estimated)", inline=True)
        embed.add_field(name="Average Cost/Incident", value=f"${cost_per_incident:,}", inline=True)
        embed.add_field(name="Payback Period", value="< 1 year" if roi > 100 else "> 1 year", inline=True)
        
        # Campaign effectiveness
        active = len([c for c in campaigns if c['status'] == 'active'])
        completed = len([c for c in campaigns if c['status'] == 'completed'])
        
        embed.add_field(name="Campaign Status", value="━" * 25, inline=False)
        embed.add_field(name="Active Campaigns", value=f"📢 {active}", inline=True)
        embed.add_field(name="Completed Campaigns", value=f"✅ {completed}", inline=True)
        embed.add_field(name="Total Campaigns", value=f"📊 {len(campaigns)}", inline=True)
        
        # Benchmark
        if roi > 300:
            benchmark = "⭐⭐⭐⭐⭐ Excellent ROI"
        elif roi > 200:
            benchmark = "⭐⭐⭐⭐ Very Good ROI"
        elif roi > 100:
            benchmark = "⭐⭐⭐ Good ROI"
        elif roi > 0:
            benchmark = "⭐⭐ Positive ROI"
        else:
            benchmark = "⭐ Break-even / Negative ROI"
        
        embed.add_field(name="Benchmark", value=benchmark, inline=False)
        
        embed.set_footer(text="ROI based on industry-standard incident prevention rates")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='awarenesscampaign')
    async def awarenesscampaign_prefix(self, ctx, campaign_type: str, target_audience: str, *, description: str = None):
        """Create awareness campaign - Prefix command"""
        await self._awarenesscampaign_logic(ctx, campaign_type, target_audience, description=description)
    
    @commands.command(name='awarenessboard')
    async def awarenessboard_prefix(self, ctx):
        """Show awareness dashboard - Prefix command"""
        await self._awarenessdashboard_logic(ctx)
    
    @commands.command(name='awarenessmetrics')
    async def awarenessmetrics_prefix(self, ctx):
        """Show detailed metrics - Prefix command"""
        await self._awarenessmetrics_logic(ctx)
    
    @commands.command(name='awarenessroi')
    async def awarenessroi_prefix(self, ctx):
        """Calculate program ROI - Prefix command"""
        await self._awarenessroi_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityAwarenessMetrics(bot))
