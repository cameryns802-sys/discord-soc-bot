"""
Member Risk Profiler - AI-powered user risk assessment for Sentinel
Analyzes user behavior and flags high-risk profiles for security review
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import re

class MemberRiskProfiler(commands.Cog):
    """AI-powered member risk assessment and profiling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.profile_file = 'data/member_risk_profiles.json'
        self.load_profiles()
    
    def load_profiles(self):
        """Load risk profiles from storage"""
        if not os.path.exists(self.profile_file):
            os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
            with open(self.profile_file, 'w') as f:
                json.dump({}, f)
    
    def get_guild_profiles(self, guild_id):
        """Get risk profiles for a guild"""
        with open(self.profile_file, 'r') as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    
    def save_profiles(self, guild_id, profiles):
        """Save risk profiles"""
        with open(self.profile_file, 'r') as f:
            data = json.load(f)
        data[str(guild_id)] = profiles
        with open(self.profile_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_risk_score(self, member, guild):
        """Calculate risk score for a member (0-100)"""
        score = 0
        factors = []
        
        # Account age factor (0-20 points)
        account_age_days = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        if account_age_days < 7:
            score += 20
            factors.append("Very new account (< 7 days)")
        elif account_age_days < 30:
            score += 10
            factors.append("New account (< 30 days)")
        elif account_age_days < 90:
            score += 5
            factors.append("Relatively new account (< 90 days)")
        
        # Bot/Service account check (-5 points if bot, safe)
        if member.bot:
            score = max(0, score - 5)
            factors.append("Service bot (safer)")
        
        # High privilege roles (10-15 points)
        dangerous_perms = [
            discord.Permissions.administrator,
            discord.Permissions.manage_guild,
            discord.Permissions.manage_roles,
            discord.Permissions.manage_messages
        ]
        
        role_perms = member.guild_permissions
        for perm_obj in dangerous_perms:
            if role_perms & perm_obj:
                score += 15
                factors.append(f"Has privilege: {perm_obj.flag}")
        
        # Member join time (5-15 points if very recent)
        join_age_days = (datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days
        if join_age_days < 1:
            score += 15
            factors.append("Joined today")
        elif join_age_days < 7:
            score += 8
            factors.append("Joined within 7 days")
        
        # Default profile picture (2 points)
        if member.avatar is None:
            score += 2
            factors.append("No custom avatar")
        
        # Account name analysis (5-10 points)
        username_lower = member.name.lower()
        suspicious_keywords = ['bot', 'spam', 'raid', 'attack', 'hack', 'admin', 'owner']
        if any(keyword in username_lower for keyword in suspicious_keywords):
            score += 5
            factors.append("Username contains suspicious keywords")
        
        # Suspicious username patterns (3 points)
        if re.search(r'[0-9]{6,}', member.name):  # Many numbers
            score += 3
            factors.append("Unusual name pattern (many numbers)")
        
        # No roles (5 points)
        if len(member.roles) <= 1:  # Only @everyone
            score += 5
            factors.append("No assigned roles")
        
        # Cap at 100
        return min(100, score), factors
    
    def get_risk_level(self, score):
        """Get risk level name from score"""
        if score >= 80:
            return "🔴 CRITICAL"
        elif score >= 60:
            return "🟠 HIGH"
        elif score >= 40:
            return "🟡 MEDIUM"
        elif score >= 20:
            return "🟢 LOW"
        else:
            return "✅ MINIMAL"
    
    def get_risk_color(self, score):
        """Get color for risk level"""
        if score >= 80:
            return discord.Color.red()
        elif score >= 60:
            return discord.Color.orange()
        elif score >= 40:
            return discord.Color.gold()
        elif score >= 20:
            return discord.Color.yellow()
        else:
            return discord.Color.green()
    
    async def _riskprofile_logic(self, ctx, member: discord.Member = None):
        """Generate risk profile for a member"""
        target = member or ctx.author
        
        score, factors = self.calculate_risk_score(target, ctx.guild)
        
        embed = discord.Embed(
            title=f"{self.get_risk_level(score)} Risk Profile",
            description=f"User: {target.mention}",
            color=self.get_risk_color(score),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Risk Score", value=f"`{score}/100`", inline=True)
        embed.add_field(name="Risk Level", value=self.get_risk_level(score), inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Server Joined", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Roles", value=f"{len(target.roles) - 1} assigned" if len(target.roles) > 1 else "None", inline=True)
        
        if factors:
            risk_factors = "\n".join([f"• {factor}" for factor in factors[:5]])
            embed.add_field(name="Risk Factors", value=risk_factors, inline=False)
        
        # Recommendations
        if score >= 60:
            embed.add_field(name="⚠️ Recommendations", value="🔍 Monitor activity\n⛔ Restrict permissions\n👤 Contact user for verification", inline=False)
        elif score >= 40:
            embed.add_field(name="ℹ️ Suggestions", value="👁️ Keep profile monitored\n🔐 Verify credentials if needed", inline=False)
        
        embed.set_footer(text="Sentinel Risk Profiler | ML-powered assessment")
        embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
        
        await ctx.send(embed=embed)
    
    async def _riskaudit_logic(self, ctx, threshold: int = 50):
        """Audit all members and flag high-risk accounts"""
        if threshold < 0 or threshold > 100:
            await ctx.send("❌ Threshold must be 0-100.")
            return
        
        await ctx.defer() if hasattr(ctx, 'defer') else None
        
        high_risk = []
        for member in ctx.guild.members:
            score, _ = self.calculate_risk_score(member, ctx.guild)
            if score >= threshold:
                high_risk.append((member, score))
        
        high_risk.sort(key=lambda x: x[1], reverse=True)
        
        if not high_risk:
            await ctx.send(f"✅ No members with risk score >= {threshold}")
            return
        
        embed = discord.Embed(
            title=f"🔍 Risk Audit Results",
            description=f"{len(high_risk)} high-risk member(s) found (threshold: {threshold})",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for member, score in high_risk[:10]:
            risk_level = self.get_risk_level(score)
            embed.add_field(
                name=f"{member.name}#{member.discriminator}",
                value=f"Score: `{score}/100` | {risk_level}",
                inline=False
            )
        
        if len(high_risk) > 10:
            embed.add_field(name="... and more", value=f"+{len(high_risk) - 10} additional members", inline=False)
        
        embed.set_footer(text="Review high-risk profiles individually for details")
        
        await ctx.send(embed=embed)
    
    async def _risktimeline_logic(self, ctx):
        """Show recent join timeline with risk scores"""
        # Get recent joiners
        recent = sorted([m for m in ctx.guild.members], key=lambda m: m.joined_at, reverse=True)[:20]
        
        embed = discord.Embed(
            title="🕐 Recent Joins & Risk Assessment",
            description="Last 20 members to join",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        
        for member in recent:
            score, _ = self.calculate_risk_score(member, ctx.guild)
            risk_level = self.get_risk_level(score)
            embed.add_field(
                name=f"{member.name}",
                value=f"Joined: <t:{int(member.joined_at.timestamp())}:R> | {risk_level} ({score})",
                inline=False
            )
        
        embed.set_footer(text="Sentinel Member Risk Profiler")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='riskprofile')
    async def riskprofile_prefix(self, ctx, member: discord.Member = None):
        """Get risk profile for a member - Prefix command"""
        await self._riskprofile_logic(ctx, member)
    
    @commands.command(name='riskaudit')
    async def riskaudit_prefix(self, ctx, threshold: int = 50):
        """Audit all members by risk score - Prefix command"""
        await self._riskaudit_logic(ctx, threshold)
    
    @commands.command(name='risktimeline')
    async def risktimeline_prefix(self, ctx):
        """Show recent joins with risk scores - Prefix command"""
        await self._risktimeline_logic(ctx)

async def setup(bot):
    await bot.add_cog(MemberRiskProfiler(bot))
