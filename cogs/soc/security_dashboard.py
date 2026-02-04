"""
Security Dashboard: Real-time security metrics and server health monitoring
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import json
import os
from cogs.core.pst_timezone import get_now_pst

class SecurityDashboard(commands.Cog):
    """Real-time security metrics and dashboard"""
    
    def __init__(self, bot):
        self.bot = bot
        self.metrics = {}
    
    def _get_security_score(self, guild: discord.Guild) -> int:
        """Calculate server security score (0-100)"""
        score = 50
        
        # Check for 2FA on admins
        admins_with_2fa = sum(1 for member in guild.members if member.guild_permissions.administrator and member.mfa_enabled)
        total_admins = sum(1 for member in guild.members if member.guild_permissions.administrator)
        if total_admins > 0:
            score += int((admins_with_2fa / total_admins) * 10)
        
        # Check server verification level
        verification_levels = {
            discord.VerificationLevel.none: 0,
            discord.VerificationLevel.low: 5,
            discord.VerificationLevel.medium: 10,
            discord.VerificationLevel.high: 15,
            discord.VerificationLevel.very_high: 20
        }
        score += verification_levels.get(guild.verification_level, 0)
        
        # Check for explicit content filter
        filter_levels = {
            discord.ContentFilter.disabled: 0,
            discord.ContentFilter.all_members: 10,
            discord.ContentFilter.no_role: 5
        }
        score += filter_levels.get(guild.explicit_content_filter, 0)
        
        # Check for default notifications
        if guild.default_notifications == discord.NotificationLevel.all_messages:
            score -= 5
        elif guild.default_notifications == discord.NotificationLevel.mentions_only:
            score += 5
        
        return min(score, 100)
    
    @commands.command(name='securitydash')
    @commands.has_permissions(manage_guild=True)
    async def dashboard(self, ctx):
        """View security dashboard"""
        await self._dashboard_logic(ctx)
    
    @app_commands.command(name="securitydash", description="View real-time security dashboard")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dashboard_slash(self, interaction: discord.Interaction):
        """Dashboard using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._dashboard_logic(ctx)
    
    async def _dashboard_logic(self, ctx):
        guild = ctx.guild
        
        # Calculate metrics
        security_score = self._get_security_score(guild)
        
        # Count members and roles
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = len(guild.members) - bot_count
        
        # Count admins and mods
        admins = sum(1 for m in guild.members if m.guild_permissions.administrator)
        mods = sum(1 for m in guild.members if m.guild_permissions.moderate_members or m.guild_permissions.manage_messages)
        
        # Check server settings
        verification = str(guild.verification_level).replace('VerificationLevel.', '').title()
        content_filter = str(guild.explicit_content_filter).replace('ContentFilter.', '').replace('_', ' ').title()
        
        # Create dashboard embed
        embed = discord.Embed(
            title=f"🛡️ {guild.name} - Security Dashboard",
            description="Real-time security metrics and server health",
            color=self._get_score_color(security_score),
            timestamp=get_now_pst()
        )
        
        # Main metrics
        embed.add_field(
            name="🔐 Security Score",
            value=f"```\n{security_score}/100\n```",
            inline=True
        )
        
        embed.add_field(
            name="👥 Members",
            value=f"**Total:** {len(guild.members)}\n**Bots:** {bot_count}\n**Humans:** {human_count}",
            inline=True
        )
        
        embed.add_field(
            name="👮 Staff",
            value=f"**Admins:** {admins}\n**Mods:** {mods}",
            inline=True
        )
        
        # Server configuration
        embed.add_field(
            name="⚙️ Verification",
            value=verification,
            inline=True
        )
        
        embed.add_field(
            name="🚫 Content Filter",
            value=content_filter,
            inline=True
        )
        
        embed.add_field(
            name="📝 Channels",
            value=f"**Text:** {len(guild.text_channels)}\n**Voice:** {len(guild.voice_channels)}\n**Categories:** {len(guild.categories)}",
            inline=True
        )
        
        # Role security
        high_perms = 0
        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                high_perms += 1
        
        embed.add_field(
            name="🔑 Role Security",
            value=f"**High Perms Roles:** {high_perms}\n**Total Roles:** {len(guild.roles)}",
            inline=True
        )
        
        embed.add_field(
            name="2️⃣ 2FA Status",
            value=f"**Owner 2FA:** {'✅ Yes' if guild.owner.mfa_enabled else '❌ No'}",
            inline=True
        )
        
        # Security recommendations
        recommendations = []
        
        if security_score < 50:
            recommendations.append("🔴 Consider improving security score")
        
        if guild.verification_level == discord.VerificationLevel.none:
            recommendations.append("⚠️ Enable server verification")
        
        if guild.explicit_content_filter == discord.ContentFilter.disabled:
            recommendations.append("⚠️ Enable explicit content filter")
        
        if admins > 0:
            admins_with_2fa = sum(1 for m in guild.members if m.guild_permissions.administrator and m.mfa_enabled)
            if admins_with_2fa < admins:
                recommendations.append(f"⚠️ {admins - admins_with_2fa} admin(s) missing 2FA")
        
        if recommendations:
            embed.add_field(
                name="⚡ Recommendations",
                value="\n".join(recommendations[:5]),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Status",
                value="Server appears well-secured",
                inline=False
            )
        
        embed.set_footer(text=f"Server ID: {guild.id} • Created {guild.created_at.strftime('%Y-%m-%d')}")
        
        await ctx.send(embed=embed)
    
    def _get_score_color(self, score: int) -> discord.Color:
        """Get color based on security score"""
        if score >= 80:
            return discord.Color.green()
        elif score >= 60:
            return discord.Color.blue()
        elif score >= 40:
            return discord.Color.gold()
        else:
            return discord.Color.red()
    
    @commands.command(name='securitystatus')
    @commands.has_permissions(manage_guild=True)
    async def securitystatus(self, ctx):
        """Quick security status"""
        await self._securitystatus_logic(ctx)
    
    @app_commands.command(name="securitystatus", description="Quick security status check")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def securitystatus_slash(self, interaction: discord.Interaction):
        """Status using slash command"""
        await interaction.response.defer()
        
        class FakeCtx:
            def __init__(self, interaction):
                self.channel = interaction.channel
                self.author = interaction.user
                self.guild = interaction.guild
            
            async def send(self, **kwargs):
                if isinstance(kwargs.get('embed'), discord.Embed):
                    return await interaction.followup.send(embed=kwargs['embed'])
                return await interaction.followup.send(content=kwargs.get('content', ''))
        
        ctx = FakeCtx(interaction)
        await self._securitystatus_logic(ctx)
    
    async def _securitystatus_logic(self, ctx):
        guild = ctx.guild
        
        status_checks = []
        
        # Check verification
        if guild.verification_level != discord.VerificationLevel.none:
            status_checks.append(("✅ Verification Enabled", guild.verification_level))
        else:
            status_checks.append(("❌ No Verification", "CRITICAL"))
        
        # Check content filter
        if guild.explicit_content_filter != discord.ContentFilter.disabled:
            status_checks.append(("✅ Content Filter Active", guild.explicit_content_filter))
        else:
            status_checks.append(("⚠️ Content Filter Disabled", "WARNING"))
        
        # Check 2FA on owner
        if guild.owner.mfa_enabled:
            status_checks.append(("✅ Owner Has 2FA", "ENABLED"))
        else:
            status_checks.append(("❌ Owner Missing 2FA", "CRITICAL"))
        
        # Check for excessive admins
        admins = sum(1 for m in guild.members if m.guild_permissions.administrator)
        if admins <= 3:
            status_checks.append(("✅ Admin Count Reasonable", admins))
        else:
            status_checks.append(("⚠️ Many Admins", f"{admins} admins"))
        
        embed = discord.Embed(
            title="🔍 Security Status Check",
            color=discord.Color.blue(),
            timestamp=get_now_pst()
        )
        
        for check, status in status_checks:
            embed.add_field(name=check, value=str(status), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityDashboard(bot))

