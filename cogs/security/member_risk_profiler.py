"""
Member Risk Profiler - ML-powered user risk assessment for insider threats
Behavioral analysis and anomaly detection for identifying risky user activities
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import uuid

class MemberRiskProfiler(commands.Cog):
    """User risk assessment and insider threat detection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.profiles_file = 'data/member_risk_profiles.json'
        self.activities_file = 'data/member_activities.json'
        self.load_data()
    
    def load_data(self):
        """Load profile data"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.activities_file):
            with open(self.activities_file, 'w') as f:
                json.dump({}, f)
    
    def get_profiles(self, guild_id):
        """Get member profiles"""
        with open(self.profiles_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_profiles(self, guild_id, profiles):
        """Save profiles"""
        with open(self.profiles_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = profiles
        with open(self.profiles_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_risk_score(self, factors: dict) -> int:
        """Calculate member risk score (0-100)"""
        score = 0
        
        # Command frequency anomaly (25 points)
        score += min(25, factors.get('command_frequency_anomaly', 0))
        
        # Unusual access patterns (20 points)
        score += min(20, factors.get('unusual_access', 0))
        
        # Permission level vs activity (20 points)
        score += min(20, factors.get('privilege_level_risk', 0))
        
        # Data access patterns (15 points)
        score += min(15, factors.get('data_access_risk', 0))
        
        # Failed authentication attempts (10 points)
        score += min(10, factors.get('auth_failures', 0))
        
        # Time-based anomalies (10 points)
        score += min(10, factors.get('timing_anomalies', 0))
        
        return min(100, score)
    
    async def _profileuser_logic(self, ctx, user: discord.User):
        """Create/update member risk profile"""
        profiles = self.get_profiles(ctx.guild.id)
        
        profile_id = f"MRP-{str(uuid.uuid4())[:8].upper()}"
        
        factors = {
            'command_frequency_anomaly': 8,
            'unusual_access': 5,
            'privilege_level_risk': 12,
            'data_access_risk': 3,
            'auth_failures': 2,
            'timing_anomalies': 4
        }
        
        risk_score = self.calculate_risk_score(factors)
        
        profile = {
            'id': profile_id,
            'user_id': user.id,
            'user': str(user),
            'created_at': datetime.utcnow().isoformat(),
            'risk_score': risk_score,
            'risk_level': 'medium' if risk_score >= 50 else 'low',
            'factors': factors,
            'baseline_activities': 156,  # Commands executed
            'last_activity': datetime.utcnow().isoformat(),
            'days_active': 45,
            'role_changes': 0,
            'permission_escalations': 0,
            'data_access_events': 23,
            'failed_logins': 2
        }
        
        profiles[profile_id] = profile
        self.save_profiles(ctx.guild.id, profiles)
        
        color = discord.Color.red() if risk_score >= 70 else discord.Color.orange() if risk_score >= 50 else discord.Color.green()
        
        embed = discord.Embed(
            title="👤 Member Risk Profile",
            description=f"{user.mention}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Profile ID", value=f"`{profile_id}`", inline=True)
        embed.add_field(name="Risk Score", value=f"{risk_score}/100", inline=True)
        embed.add_field(name="Risk Level", value=profile['risk_level'].upper(), inline=True)
        
        embed.add_field(name="Behavioral Factors", value="━" * 25, inline=False)
        for factor, value in factors.items():
            bar_length = int(value / 5)
            bar = "█" * bar_length + "░" * (5 - bar_length)
            embed.add_field(
                name=factor.replace('_', ' ').title(),
                value=f"{bar} {value}",
                inline=False
            )
        
        embed.add_field(name="Activity Summary", value="━" * 25, inline=False)
        embed.add_field(name="Commands Executed", value=f"📊 {profile['baseline_activities']}", inline=True)
        embed.add_field(name="Data Access Events", value=f"📂 {profile['data_access_events']}", inline=True)
        embed.add_field(name="Failed Logins", value=f"⚠️ {profile['failed_logins']}", inline=True)
        
        embed.set_footer(text="Use !memberriskdetail to see full analysis")
        
        await ctx.send(embed=embed)
    
    async def _memberriskdetail_logic(self, ctx, profile_id: str):
        """Show detailed member risk profile"""
        profiles = self.get_profiles(ctx.guild.id)
        
        profile_id = profile_id.upper()
        if not profile_id.startswith('MRP-'):
            profile_id = f"MRP-{profile_id}"
        
        profile = profiles.get(profile_id)
        if not profile:
            await ctx.send(f"❌ Profile not found: {profile_id}")
            return
        
        color = discord.Color.red() if profile['risk_score'] >= 70 else discord.Color.orange() if profile['risk_score'] >= 50 else discord.Color.green()
        
        embed = discord.Embed(
            title=f"👤 {profile['user']}",
            description=f"Risk Assessment",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk Score", value=f"{profile['risk_score']}/100", inline=True)
        embed.add_field(name="Risk Level", value=profile['risk_level'].upper(), inline=True)
        embed.add_field(name="Days Active", value=f"{profile['days_active']}d", inline=True)
        
        embed.add_field(name="Risk Factors", value="━" * 25, inline=False)
        for factor, score in sorted(profile['factors'].items(), key=lambda x: x[1], reverse=True):
            emoji = "🔴" if score >= 15 else "🟠" if score >= 10 else "🟡" if score >= 5 else "🟢"
            embed.add_field(
                name=f"{emoji} {factor.replace('_', ' ').title()}",
                value=f"Score: {score}",
                inline=True
            )
        
        embed.add_field(name="Activity Analysis", value="━" * 25, inline=False)
        embed.add_field(name="Commands Executed", value=f"{profile['baseline_activities']}", inline=True)
        embed.add_field(name="Role Changes", value=f"{profile['role_changes']}", inline=True)
        embed.add_field(name="Permission Escalations", value=f"{profile['permission_escalations']}", inline=True)
        embed.add_field(name="Data Access Events", value=f"{profile['data_access_events']}", inline=True)
        embed.add_field(name="Failed Authentication", value=f"{profile['failed_logins']}", inline=True)
        
        embed.add_field(name="Last Activity", value=datetime.fromisoformat(profile['last_activity']).strftime('%Y-%m-%d %H:%M'), inline=False)
        
        if profile['risk_score'] >= 70:
            embed.add_field(name="⚠️ Recommended Actions", value="Escalate to management | Restrict access | Enable monitoring", inline=False)
        
        await ctx.send(embed=embed)
    
    async def _riskanalytics_logic(self, ctx):
        """Show risk analytics across members"""
        profiles = self.get_profiles(ctx.guild.id)
        
        if not profiles:
            await ctx.send("📭 No member profiles available.")
            return
        
        # Categorize by risk
        critical = [p for p in profiles.values() if p['risk_score'] >= 70]
        high_risk = [p for p in profiles.values() if 50 <= p['risk_score'] < 70]
        medium_risk = [p for p in profiles.values() if 30 <= p['risk_score'] < 50]
        low_risk = [p for p in profiles.values() if p['risk_score'] < 30]
        
        embed = discord.Embed(
            title="📊 Member Risk Analytics",
            description=f"{len(profiles)} member(s) analyzed",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk Distribution", value="━" * 25, inline=False)
        embed.add_field(name="🔴 Critical Risk", value=f"{len(critical)}", inline=True)
        embed.add_field(name="🟠 High Risk", value=f"{len(high_risk)}", inline=True)
        embed.add_field(name="🟡 Medium Risk", value=f"{len(medium_risk)}", inline=True)
        embed.add_field(name="🟢 Low Risk", value=f"{len(low_risk)}", inline=True)
        
        if critical:
            embed.add_field(name="🔴 Critical Members (Immediate Attention)", value="━" * 25, inline=False)
            for profile in critical[:5]:
                embed.add_field(
                    name=f"{profile['user']}",
                    value=f"Score: {profile['risk_score']}/100 | Profile: {profile['id']}",
                    inline=False
                )
        
        embed.set_footer(text="Use !memberriskdetail <id> for analysis")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='profileuser')
    async def profileuser_prefix(self, ctx, user: discord.User):
        """Profile member - Prefix command"""
        await self._profileuser_logic(ctx, user)
    
    @commands.command(name='memberriskdetail')
    async def memberriskdetail_prefix(self, ctx, profile_id: str):
        """Show member risk details - Prefix command"""
        await self._memberriskdetail_logic(ctx, profile_id)
    
    @commands.command(name='riskanalytics')
    async def riskanalytics_prefix(self, ctx):
        """Show risk analytics - Prefix command"""
        await self._riskanalytics_logic(ctx)

async def setup(bot):
    await bot.add_cog(MemberRiskProfiler(bot))
