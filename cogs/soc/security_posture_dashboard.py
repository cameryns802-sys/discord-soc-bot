"""
Security Posture Dashboard - Continuous security health tracking for Sentinel
Real-time security posture scoring, trend analysis, and health monitoring
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import statistics
from cogs.core.pst_timezone import get_now_pst

class SecurityPostureDashboard(commands.Cog):
    """Continuous security posture monitoring and scoring"""
    
    def __init__(self, bot):
        self.bot = bot
        self.posture_file = 'data/security_posture.json'
        self.load_posture_data()
    
    def load_posture_data(self):
        """Load security posture data"""
        if not os.path.exists(self.posture_file):
            os.makedirs(os.path.dirname(self.posture_file), exist_ok=True)
            with open(self.posture_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_posture(self, guild_id):
        """Get security posture for guild"""
        with open(self.posture_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {'scores': [], 'dimensions': {}})
    
    def save_posture(self, guild_id, posture):
        """Save security posture"""
        with open(self.posture_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = posture
        with open(self.posture_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_posture_score(self, guild):
        """Calculate comprehensive security posture score"""
        score = 100
        dimensions = {}
        findings = []
        
        # 1. Identity & Access (30 points)
        iam_score = 30
        iam_findings = []
        
        # Verification level
        if guild.verification_level == discord.VerificationLevel.none:
            iam_score -= 10
            iam_findings.append("❌ No verification required")
        elif guild.verification_level in [discord.VerificationLevel.low, discord.VerificationLevel.medium]:
            iam_score -= 5
            iam_findings.append("⚠️ Low/medium verification")
        else:
            iam_findings.append("✅ High verification level")
        
        # MFA requirement
        if guild.mfa_level == discord.MFALevel.disabled:
            iam_score -= 15
            iam_findings.append("❌ MFA not required")
        else:
            iam_findings.append("✅ MFA required for moderation")
        
        # Admin count
        admin_count = sum(1 for m in guild.members if m.guild_permissions.administrator)
        if admin_count > 5:
            iam_score -= 5
            iam_findings.append(f"⚠️ {admin_count} administrators (recommend <5)")
        else:
            iam_findings.append(f"✅ {admin_count} administrators")
        
        dimensions['identity_access'] = {'score': max(0, iam_score), 'max': 30, 'findings': iam_findings}
        score = score - 30 + dimensions['identity_access']['score']
        
        # 2. Content Protection (25 points)
        content_score = 25
        content_findings = []
        
        # Content filter
        if guild.explicit_content_filter == discord.ContentFilter.disabled:
            content_score -= 15
            content_findings.append("❌ Content filter disabled")
        elif guild.explicit_content_filter == discord.ContentFilter.no_role:
            content_score -= 7
            content_findings.append("⚠️ Partial content filtering")
        else:
            content_findings.append("✅ Full content filtering")
        
        # Default notifications
        if guild.default_notifications == discord.NotificationLevel.all_messages:
            content_score -= 3
            content_findings.append("⚠️ All messages notify by default")
        else:
            content_findings.append("✅ Mentions-only notifications")
        
        # Vanity URL (info only)
        if guild.vanity_url_code:
            content_findings.append(f"ℹ️ Vanity URL: {guild.vanity_url_code}")
        
        dimensions['content_protection'] = {'score': max(0, content_score), 'max': 25, 'findings': content_findings}
        score = score - 25 + dimensions['content_protection']['score']
        
        # 3. Monitoring & Visibility (20 points)
        monitor_score = 20
        monitor_findings = []
        
        # System channel
        if not guild.system_channel:
            monitor_score -= 5
            monitor_findings.append("⚠️ No system channel configured")
        else:
            monitor_findings.append("✅ System channel active")
        
        # Audit log (check if we have access)
        try:
            audit_access = guild.me.guild_permissions.view_audit_log
            if audit_access:
                monitor_findings.append("✅ Audit log access available")
            else:
                monitor_score -= 10
                monitor_findings.append("❌ No audit log access")
        except:
            monitor_score -= 10
            monitor_findings.append("❌ Cannot verify audit log access")
        
        # Widget enabled (optional)
        if guild.widget_enabled:
            monitor_findings.append("ℹ️ Server widget enabled")
        
        dimensions['monitoring'] = {'score': max(0, monitor_score), 'max': 20, 'findings': monitor_findings}
        score = score - 20 + dimensions['monitoring']['score']
        
        # 4. Channel Security (15 points)
        channel_score = 15
        channel_findings = []
        
        # @everyone permissions check
        everyone_role = guild.default_role
        dangerous_perms = [
            discord.Permissions.administrator,
            discord.Permissions.manage_guild,
            discord.Permissions.manage_roles,
            discord.Permissions.manage_channels,
            discord.Permissions.manage_webhooks,
            discord.Permissions.mention_everyone
        ]
        
        dangerous_found = [p[0] for p in everyone_role.permissions if p[1] and any(dp == p[0] for dp in dangerous_perms)]
        if dangerous_found:
            channel_score -= 15
            channel_findings.append(f"❌ @everyone has dangerous permissions: {', '.join(str(p) for p in dangerous_found)}")
        else:
            channel_findings.append("✅ @everyone permissions restricted")
        
        dimensions['channel_security'] = {'score': max(0, channel_score), 'max': 15, 'findings': channel_findings}
        score = score - 15 + dimensions['channel_security']['score']
        
        # 5. Role Management (10 points)
        role_score = 10
        role_findings = []
        
        # Role hierarchy check
        dangerous_roles = sum(1 for r in guild.roles if r.permissions.administrator and r != guild.default_role)
        if dangerous_roles > 3:
            role_score -= 5
            role_findings.append(f"⚠️ {dangerous_roles} roles with administrator")
        else:
            role_findings.append(f"✅ {dangerous_roles} admin roles")
        
        # Total roles
        total_roles = len(guild.roles)
        role_findings.append(f"ℹ️ {total_roles} total roles")
        
        dimensions['role_management'] = {'score': max(0, role_score), 'max': 10, 'findings': role_findings}
        score = score - 10 + dimensions['role_management']['score']
        
        return {
            'overall_score': max(0, min(100, score)),
            'dimensions': dimensions,
            'timestamp': get_now_pst().isoformat()
        }
    
    async def _posture_logic(self, ctx):
        """Show security posture dashboard"""
        result = self.calculate_posture_score(ctx.guild)
        
        # Save score to history
        posture = self.get_guild_posture(ctx.guild.id)
        scores = posture.get('scores', [])
        scores.append({
            'score': result['overall_score'],
            'timestamp': result['timestamp']
        })
        # Keep last 30 scores
        posture['scores'] = scores[-30:]
        posture['dimensions'] = result['dimensions']
        posture['last_scan'] = result['timestamp']
        self.save_posture(ctx.guild.id, posture)
        
        # Determine color
        score = result['overall_score']
        if score >= 90:
            color = discord.Color.green()
            status = "🟢 EXCELLENT"
        elif score >= 75:
            color = discord.Color.blue()
            status = "🔵 GOOD"
        elif score >= 60:
            color = discord.Color.gold()
            status = "🟡 FAIR"
        elif score >= 40:
            color = discord.Color.orange()
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            color = discord.Color.red()
            status = "🔴 CRITICAL"
        
        embed = discord.Embed(
            title="🛡️ Security Posture Dashboard",
            description=f"**Overall Score: {score}/100** - {status}",
            color=color,
            timestamp=get_now_pst()
        )
        
        # Show dimensions
        for dim_name, dim_data in result['dimensions'].items():
            dim_display = dim_name.replace('_', ' ').title()
            dim_score = dim_data['score']
            dim_max = dim_data['max']
            dim_pct = int((dim_score / dim_max) * 100)
            
            # Progress bar
            filled = int(dim_pct / 10)
            bar = "█" * filled + "░" * (10 - filled)
            
            findings_str = "\n".join(dim_data['findings'][:3])
            
            embed.add_field(
                name=f"{dim_display} ({dim_score}/{dim_max})",
                value=f"{bar} {dim_pct}%\n{findings_str}",
                inline=False
            )
        
        embed.set_footer(text="Sentinel Security Posture | Use !posturetrend for trend analysis")
        
        await ctx.send(embed=embed)
    
    async def _posturetrend_logic(self, ctx):
        """Show security posture trend"""
        posture = self.get_guild_posture(ctx.guild.id)
        scores = posture.get('scores', [])
        
        if len(scores) < 2:
            await ctx.send("📊 Not enough data for trend analysis. Run `!posture` at least twice.")
            return
        
        # Calculate trend
        score_values = [s['score'] for s in scores]
        current_score = score_values[-1]
        avg_score = statistics.mean(score_values)
        min_score = min(score_values)
        max_score = max(score_values)
        
        # Trend direction
        if len(score_values) >= 3:
            recent_avg = statistics.mean(score_values[-3:])
            older_avg = statistics.mean(score_values[:-3]) if len(score_values) > 3 else score_values[0]
            
            if recent_avg > older_avg + 5:
                trend = "📈 IMPROVING"
                trend_color = discord.Color.green()
            elif recent_avg < older_avg - 5:
                trend = "📉 DECLINING"
                trend_color = discord.Color.red()
            else:
                trend = "➡️ STABLE"
                trend_color = discord.Color.blue()
        else:
            trend = "➡️ INSUFFICIENT DATA"
            trend_color = discord.Color.greyple()
        
        embed = discord.Embed(
            title="📊 Security Posture Trend Analysis",
            description=f"{len(scores)} data points | {trend}",
            color=trend_color,
            timestamp=get_now_pst()
        )
        
        embed.add_field(name="Current Score", value=f"{current_score}/100", inline=True)
        embed.add_field(name="Average Score", value=f"{avg_score:.1f}/100", inline=True)
        embed.add_field(name="Range", value=f"{min_score}-{max_score}", inline=True)
        
        # Show last 5 scores
        recent_scores = scores[-5:]
        timeline = ""
        for i, s in enumerate(reversed(recent_scores)):
            ts = datetime.fromisoformat(s['timestamp'])
            relative = self._relative_time(ts)
            timeline += f"**{s['score']}/100** - {relative}\n"
        
        embed.add_field(name="Recent History", value=timeline, inline=False)
        
        # Dimension breakdown
        if 'dimensions' in posture:
            dim_scores = []
            for dim_name, dim_data in posture['dimensions'].items():
                dim_display = dim_name.replace('_', ' ').title()
                dim_pct = int((dim_data['score'] / dim_data['max']) * 100)
                dim_scores.append(f"{dim_display}: {dim_pct}%")
            
            embed.add_field(name="Current Dimensions", value="\n".join(dim_scores), inline=False)
        
        embed.set_footer(text="Sentinel Security Posture | Trend analysis")
        
        await ctx.send(embed=embed)
    
    def _relative_time(self, dt):
        """Get relative time string"""
        now = get_now_pst()
        delta = now - dt
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"
    
    async def _posturereset_logic(self, ctx):
        """Reset security posture history"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Administrator permission required.")
            return
        
        posture = {'scores': [], 'dimensions': {}}
        self.save_posture(ctx.guild.id, posture)
        
        await ctx.send("🔄 Security posture history reset.")
    
    @commands.command(name='posture')
    async def posture_prefix(self, ctx):
        """Show security posture dashboard - Prefix command"""
        await self._posture_logic(ctx)
    
    @commands.command(name='posturetrend')
    async def posturetrend_prefix(self, ctx):
        """Show security posture trend - Prefix command"""
        await self._posturetrend_logic(ctx)
    
    @commands.command(name='posturereset')
    async def posturereset_prefix(self, ctx):
        """Reset posture history - Prefix command"""
        await self._posturereset_logic(ctx)

async def setup(bot):
    await bot.add_cog(SecurityPostureDashboard(bot))
