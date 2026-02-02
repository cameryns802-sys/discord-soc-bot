"""
Security Reports: Generate detailed security reports and statistics
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os

class SecurityReports(commands.Cog):
    """Generate comprehensive security reports"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reports_dir = 'data/security_reports'
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _load_report_data(self):
        """Load report data"""
        report_file = 'data/threat_responses.json'
        if os.path.exists(report_file):
            try:
                with open(report_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @commands.command(name='securityreport')
    @commands.has_permissions(manage_guild=True)
    async def securityreport(self, ctx, period: str = "day"):
        """Generate security report"""
        await self._securityreport_logic(ctx, period)
    
    @app_commands.command(name="securityreport", description="Generate comprehensive security report")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def securityreport_slash(
        self,
        interaction: discord.Interaction,
        period: str = "day"
    ):
        """Report using slash command"""
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
        await self._securityreport_logic(ctx, period.lower())
    
    async def _securityreport_logic(self, ctx, period: str):
        if period not in ['day', 'week', 'month']:
            period = 'day'
        
        # Determine time range
        if period == 'day':
            hours = 24
            period_name = "Last 24 Hours"
        elif period == 'week':
            hours = 24 * 7
            period_name = "Last 7 Days"
        else:
            hours = 24 * 30
            period_name = "Last 30 Days"
        
        time_filter = datetime.now(datetime.UTC) - timedelta(hours=hours)
        
        # Load threat data
        threat_data = self._load_report_data()
        guild_id = str(ctx.guild.id)
        
        # Filter for this guild
        guild_threats = [t for t in threat_data if t.get('guild_id') == guild_id and 
                        datetime.fromisoformat(t['detected_at']) > time_filter]
        
        # Analyze threat types
        threat_counts = {}
        threat_levels = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        total_actions = 0
        
        for threat in guild_threats:
            threat_type = threat.get('type', 'unknown')
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1
            threat_levels[threat.get('level', 'low')] += 1
            total_actions += len(threat.get('actions_taken', []))
        
        # Calculate statistics
        avg_response_time = 0
        if guild_threats:
            avg_response_time = sum(t.get('response_time', 0) for t in guild_threats) / len(guild_threats)
        
        # Create report embed
        embed = discord.Embed(
            title=f"📈 Security Report - {period_name}",
            description=f"Comprehensive security metrics for {ctx.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        # Overview
        embed.add_field(
            name="📊 Overview",
            value=f"**Threats Detected:** {len(guild_threats)}\n**Total Actions:** {total_actions}\n**Avg Response:** {avg_response_time:.1f}s",
            inline=False
        )
        
        # Threat levels breakdown
        embed.add_field(
            name="🔴 Threat Levels",
            value=f"**Critical:** {threat_levels['critical']}\n**High:** {threat_levels['high']}\n**Medium:** {threat_levels['medium']}\n**Low:** {threat_levels['low']}",
            inline=True
        )
        
        # Top threats
        if threat_counts:
            top_threat = max(threat_counts.items(), key=lambda x: x[1])
            embed.add_field(
                name="⚠️ Top Threat Type",
                value=f"{top_threat[0]}: {top_threat[1]} detections",
                inline=True
            )
        
        # Member statistics
        members_online = sum(1 for m in ctx.guild.members if m.status != discord.Status.offline)
        embed.add_field(
            name="👥 Member Activity",
            value=f"**Total:** {len(ctx.guild.members)}\n**Online:** {members_online}\n**Bots:** {sum(1 for m in ctx.guild.members if m.bot)}",
            inline=True
        )
        
        # Security score
        security_score = self._calculate_security_score(ctx.guild, guild_threats)
        embed.add_field(
            name="🔐 Security Score",
            value=f"```\n{security_score}/100\n```",
            inline=True
        )
        
        # Recommendations
        recommendations = self._generate_recommendations(ctx.guild, guild_threats, threat_counts)
        if recommendations:
            embed.add_field(
                name="💡 Recommendations",
                value="\n".join(recommendations[:3]),
                inline=False
            )
        
        # Recent incidents
        if guild_threats:
            recent = guild_threats[-3:]
            recent_text = ""
            for threat in recent:
                recent_text += f"• {threat['type']} ({threat['level']}) - {threat.get('status', 'unknown')}\n"
            
            embed.add_field(
                name="📋 Recent Incidents",
                value=recent_text,
                inline=False
            )
        
        embed.set_footer(text=f"Report generated • Guild: {ctx.guild.id}")
        
        await ctx.send(embed=embed)
    
    def _calculate_security_score(self, guild: discord.Guild, threats: list) -> int:
        """Calculate security score based on threats"""
        base_score = 75
        
        # Deduct for threats
        critical_count = sum(1 for t in threats if t.get('level') == 'critical')
        high_count = sum(1 for t in threats if t.get('level') == 'high')
        
        base_score -= (critical_count * 10)
        base_score -= (high_count * 5)
        
        # Add for verification
        if guild.verification_level != discord.VerificationLevel.none:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _generate_recommendations(self, guild: discord.Guild, threats: list, threat_counts: dict) -> list:
        """Generate security recommendations"""
        recommendations = []
        
        if 'spam' in threat_counts and threat_counts['spam'] > 5:
            recommendations.append("⚠️ High spam detected - Consider stricter automod")
        
        if 'raid' in threat_counts and threat_counts['raid'] > 0:
            recommendations.append("🔴 Raid detected - Review verification settings")
        
        if 'phishing' in threat_counts and threat_counts['phishing'] > 0:
            recommendations.append("⚠️ Phishing links detected - Share safety tips")
        
        if len(threats) == 0:
            recommendations.append("✅ No recent threats - Server appears secure")
        
        if not recommendations:
            recommendations.append("💡 Monitor for new threats and adjust policies as needed")
        
        return recommendations
    
    @commands.command(name='threatsummary')
    @commands.has_permissions(manage_guild=True)
    async def threatsummary(self, ctx):
        """Quick threat summary"""
        await self._threatsummary_logic(ctx)
    
    @app_commands.command(name="threatsummary", description="Quick threat summary")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threatsummary_slash(self, interaction: discord.Interaction):
        """Summary using slash command"""
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
        await self._threatsummary_logic(ctx)
    
    async def _threatsummary_logic(self, ctx):
        threat_data = self._load_report_data()
        guild_id = str(ctx.guild.id)
        guild_threats = [t for t in threat_data if t.get('guild_id') == guild_id]
        
        # Today's threats
        today_filter = datetime.now(datetime.UTC) - timedelta(hours=24)
        today_threats = [t for t in guild_threats if datetime.fromisoformat(t['detected_at']) > today_filter]
        
        embed = discord.Embed(
            title="🚨 Threat Summary",
            color=discord.Color.red() if len(today_threats) > 0 else discord.Color.green(),
            timestamp=datetime.now(datetime.UTC)
        )
        
        embed.add_field(
            name="📊 Today",
            value=f"**Threats:** {len(today_threats)}\n**Active Issues:** {sum(1 for t in today_threats if t.get('status') == 'active')}",
            inline=True
        )
        
        embed.add_field(
            name="📈 All Time",
            value=f"**Total:** {len(guild_threats)}\n**Resolved:** {sum(1 for t in guild_threats if t.get('status') == 'resolved')}",
            inline=True
        )
        
        if today_threats:
            threat_types = {}
            for t in today_threats:
                threat_types[t['type']] = threat_types.get(t['type'], 0) + 1
            
            types_text = "\n".join([f"**{k}:** {v}" for k, v in sorted(threat_types.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(
                name="⚠️ Today's Threat Types",
                value=types_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityReports(bot))
